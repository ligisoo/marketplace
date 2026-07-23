from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from .models import Tip, TipMatch
from .forms import TipSubmissionForm, TipVerificationForm, TipSearchForm

from datetime import datetime, timedelta
from decimal import Decimal
import json
import logging

logger = logging.getLogger(__name__)


def marketplace(request):
    """Browse active tips in the marketplace"""
    form = TipSearchForm(request.GET or None)
    tips = Tip.objects.filter(status='active', expires_at__gt=timezone.now())
    
    # Apply search filters
    if form.is_valid():
        search = form.cleaned_data.get('q')
        if search:
            tips = tips.filter(
                Q(bet_code__icontains=search) |
                Q(tipster__username__icontains=search) |
                Q(tipster__phone_number__icontains=search) |
                Q(matches__home_team__icontains=search) |
                Q(matches__away_team__icontains=search)
            ).distinct()
        
        bookmaker = form.cleaned_data.get('bookmaker')
        if bookmaker:
            tips = tips.filter(bookmaker=bookmaker)
        
        min_odds = form.cleaned_data.get('min_odds')
        if min_odds:
            tips = tips.filter(odds__gte=min_odds)
        
        max_odds = form.cleaned_data.get('max_odds')
        if max_odds:
            tips = tips.filter(odds__lte=max_odds)
            
        sort_by = form.cleaned_data.get('sort_by') or '-created_at'
        tips = tips.order_by(sort_by)
    else:
        tips = tips.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(tips, 12)  # 12 tips per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'tips': page_obj.object_list,
    }
    
    return render(request, 'tips/marketplace.html', context)


def tip_detail(request, tip_id):
    """Detailed view of a specific tip"""
    tip = get_object_or_404(Tip, id=tip_id)
    
    # Track view for analytics (skip if user is the tipster)
    if request.user != tip.tipster:
        # Note: TipView model has been removed. We can track views in a different way or remove this logic.
        pass
        
    can_view_matches = True
    
    # Restrict access to slips from Top N Analysts for free users
    from .utils import get_top_analysts
    
    # If the user is the tipster themselves, they can always view it
    if request.user != tip.tipster:
        # Check if this tip is from a Top Analyst
        top_ids = get_top_analysts()
        
        if tip.tipster.id in top_ids:
            # If so, check if the current user is a Pro subscriber
            if not request.user.is_authenticated or not request.user.userprofile.is_pro_active:
                can_view_matches = False
            
    context = {
        'tip': tip,
        'matches': tip.matches.all(),
        'can_view_matches': can_view_matches,
    }
    
    return render(request, 'tips/detail.html', context)


@login_required
def my_tips(request):
    """Analyst's dashboard showing their tips"""
    
    # Get filter parameter for My Tips section
    tip_filter = request.GET.get('filter', 'all')  # all, active, archived
    
    # Base queryset for user's tips
    base_tips = Tip.objects.filter(tipster=request.user)
    
    # Apply filter
    if tip_filter == 'active':
        my_selling_tips = base_tips.filter(status='active').order_by('-created_at')
    elif tip_filter == 'archived':
        my_selling_tips = base_tips.filter(status='archived').order_by('-created_at')
    else:  # 'all'
        # Show active tips first, then archived, then others
        from django.db.models import Case, When, Value, IntegerField
        my_selling_tips = base_tips.annotate(
            status_order=Case(
                When(status='active', then=Value(1)),
                When(status='archived', then=Value(2)),
                default=Value(3),
                output_field=IntegerField()
            )
        ).order_by('status_order', '-created_at')
    
    # Pagination for selling tips
    selling_paginator = Paginator(my_selling_tips, 9)  # 9 tips per page for better grid layout
    selling_page_number = request.GET.get('selling_page')
    selling_page_obj = selling_paginator.get_page(selling_page_number)

    # Stats for selling tips (always calculate from all tips)
    all_tips = base_tips
    selling_stats = {
        'total_tips': all_tips.count(),
        'active_tips': all_tips.filter(status='active').count(),
        'pending_tips': all_tips.filter(status='pending_approval').count(),
        'archived_tips': all_tips.filter(status='archived').count(),
        'current_filter': tip_filter,
    }

    context = {
        'selling_page_obj': selling_page_obj,
        'selling_tips': selling_page_obj.object_list,
        'selling_stats': selling_stats,
    }
    
    return render(request, 'tips/my_tips.html', context)


@login_required
def create_tip(request):
    """Create a new tip - Process betslip synchronously"""
    if request.method == 'POST':
        form = TipSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Process betslip synchronously
                from .betslip_extractor import process_betslip_image
                from .utils import parse_match_date
                from django.core.cache import cache
                import hashlib
                import copy

                screenshot = form.cleaned_data['screenshot']
                bet_code = form.cleaned_data['bet_code']  # From user input

                logger.info("Processing betslip image with Gemini...")
                extraction_result = process_betslip_image(screenshot)

                if not extraction_result.get('success'):
                    error_msg = extraction_result.get('error', 'Failed to extract prediction slip data')
                    form.add_error(None, error_msg)
                    return render(request, 'tips/create_tip.html', {'form': form})

                # Extract data
                betslip_data = extraction_result['data']
                matches = betslip_data.get('matches', [])

                if not matches:
                    error_msg = 'No matches found in the prediction slip. Please upload a clear image.'
                    form.add_error(None, error_msg)
                    return render(request, 'tips/create_tip.html', {'form': form})

                # Create tip with extracted data
                tip = form.save(commit=False)
                tip.tipster = request.user
                tip.bet_code = bet_code  # Use user-provided bet code
                tip.odds = betslip_data.get('total_odds', 1.0)
                tip.match_details = betslip_data
                tip.ocr_processed = True
                tip.ocr_confidence = extraction_result.get('confidence', 95.0)

                # Calculate expires_at from latest match date
                latest_match_date = None
                has_invalid_dates = False

                for match_data in matches:
                    parsed_date = parse_match_date(
                        match_data.get('match_date'),
                        match_data.get('match_time')
                    )
                    if not parsed_date:
                        has_invalid_dates = True
                        break
                    if latest_match_date is None or parsed_date > latest_match_date:
                        latest_match_date = parsed_date

                if has_invalid_dates or not latest_match_date:
                    error_msg = 'Invalid Prediction Slip: The uploaded image is missing match kickoff dates and times. Please upload a prediction slip screenshot from your account history that clearly displays match dates and kickoff times.'
                    form.add_error(None, error_msg)
                    return render(request, 'tips/create_tip.html', {'form': form})

                tip.expires_at = latest_match_date
                tip.status = 'draft'  # Draft status for verification step
                tip.save()

                # Create TipMatch records
                for match_data in matches:
                    match_date = parse_match_date(
                        match_data.get('match_date'),
                        match_data.get('match_time')
                    ) or timezone.now()

                    TipMatch.objects.create(
                        tip=tip,
                        home_team=match_data.get('home_team', 'Unknown'),
                        away_team=match_data.get('away_team', 'Unknown'),
                        league='Unknown League',
                        match_date=match_date,
                        market=match_data.get('market', 'Unknown'),
                        selection=match_data.get('selection', 'Unknown'),
                        odds=float(match_data.get('odds', 1.0))
                    )

                # Create preview data
                preview_matches = matches[:2]
                tip.preview_data = {
                    'matches': [
                        {
                            'home_team': match.get('home_team'),
                            'away_team': match.get('away_team'),
                            'league': 'Unknown League',
                            'market': match.get('market'),
                        }
                        for match in preview_matches
                    ],
                    'total_matches': len(matches)
                }
                tip.save()

                # Redirect to verification step
                messages.success(request, 'Prediction slip processed successfully! Please verify the extracted data.')
                return redirect('tips:verify_tip', tip_id=tip.id)

            except Exception as e:
                logger.error(f"Error creating tip: {str(e)}", exc_info=True)
                messages.error(request, f'Error creating tip: {str(e)}')
                return render(request, 'tips/create_tip.html', {'form': form})
    else:
        form = TipSubmissionForm()

    return render(request, 'tips/create_tip.html', {
        'form': form
    })


@login_required
def verify_tip(request, tip_id):
    """Verify extracted betslip data - Step 2"""
    tip = get_object_or_404(Tip, id=tip_id, tipster=request.user)

    # Only allow verification of draft tips
    if tip.status != 'draft':
        messages.info(request, 'This tip has already been published.')
        return redirect('tips:my_tips')

    # Get extracted matches
    matches = TipMatch.objects.filter(tip=tip).order_by('id')

    context = {
        'tip': tip,
        'matches': matches,
        'num_matches': matches.count(),
    }

    return render(request, 'tips/verify_tip.html', context)


@login_required
@require_http_methods(["POST"])
def approve_tip(request, tip_id):
    """Approve and publish a verified tip - Step 3"""
    tip = get_object_or_404(Tip, id=tip_id, tipster=request.user)

    # Only allow approval of draft tips
    if tip.status != 'draft':
        messages.warning(request, 'This tip has already been published.')
        return redirect('tips:my_tips')

    # Set status to active immediately (no manual moderation required)
    tip.status = 'active'

    tip.save()

    # Redirect to success page
    return redirect('tips:tip_published', tip_id=tip.id)


@login_required
@require_http_methods(["POST"])
def cancel_tip(request, tip_id):
    """Cancel and delete a draft tip"""
    tip = get_object_or_404(Tip, id=tip_id, tipster=request.user)

    # Only allow cancellation of draft tips
    if tip.status != 'draft':
        messages.warning(request, 'Cannot cancel a published tip.')
        return redirect('tips:my_tips')

    bet_code = tip.bet_code
    tip.delete()
    messages.info(request, f'Tip ({bet_code}) cancelled and deleted.')
    return redirect('tips:create_tip')


@login_required
def tip_published(request, tip_id):
    """Success page after publishing a tip - Step 3 completion"""
    tip = get_object_or_404(Tip, id=tip_id, tipster=request.user)

    # Only show this page for recently published tips (active or pending_approval)
    if tip.status not in ['active', 'pending_approval']:
        return redirect('tips:my_tips')

    # Get matches for display
    matches = TipMatch.objects.filter(tip=tip).order_by('id')

    context = {
        'tip': tip,
        'matches': matches,
    }

    return render(request, 'tips/tip_published.html', context)


@login_required
def tip_processing_status(request, tip_id):
    """Show processing status (legacy page for old background-processed tips)"""
    tip = get_object_or_404(Tip, id=tip_id)

    # Only tipster who created the tip can view this
    if tip.tipster != request.user:
        messages.error(request, 'You do not have permission to view this tip.')
        return redirect('tips:my_tips')

    # If tip was processed synchronously (new flow), redirect immediately
    if tip.ocr_processed and tip.matches.exists():
        messages.success(request, 'Your tip is ready!')
        return redirect('tips:my_tips')

    # If processing failed, show error and options
    if getattr(tip, 'processing_status', None) == 'failed':
        context = {
            'tip': tip,
            'error': getattr(tip, 'processing_error', 'Unknown error occurred during processing'),
            'failed': True
        }
        return render(request, 'tips/processing_status.html', context)

    # If processing is complete from old background task, redirect to verify
    if getattr(tip, 'processing_status', None) == 'completed' and tip.ocr_processed:
        return redirect('tips:verify_tip', tip_id=tip.id)

    # Still processing (old background tasks) or pending
    context = {
        'tip': tip,
        'failed': False
    }

    return render(request, 'tips/processing_status.html', context)


@login_required
@require_http_methods(["POST"])
def delete_failed_tip(request, tip_id):
    """Delete a failed tip"""
    tip = get_object_or_404(Tip, id=tip_id, tipster=request.user)

    # Only allow deletion of failed or temporary tips
    if getattr(tip, 'processing_status', None) == 'failed' or tip.bet_code.startswith('TEMP_'):
        bet_code = tip.bet_code
        tip.delete()
        messages.success(request, f'Failed tip ({bet_code}) has been deleted.')
    else:
        messages.error(request, 'Only failed tips can be deleted this way.')

    return redirect('tips:my_tips')


def tipster_profile(request, tipster_id):
    """Public tipster profile with their tips"""
    from django.contrib.auth import get_user_model
    from django.db.models import Avg
    User = get_user_model()
    
    tipster = get_object_or_404(
        User,
        id=tipster_id
    )
    
    # Block access to profile if this is a Top Analyst and user is not Pro
    from .utils import get_top_analysts
    from django.conf import settings
    if request.user != tipster:
        if tipster.id in get_top_analysts():
            if not request.user.is_authenticated or not request.user.userprofile.is_pro_active:
                from django.contrib import messages
                from django.shortcuts import redirect
                limit = getattr(settings, 'PRO_RESTRICTED_TOP_ANALYSTS_COUNT', 10)
                messages.info(request, f"This analyst is in the Top {limit}! Their profile and prediction slips are exclusive to Pro subscribers. Upgrade to unlock!")
                return redirect('payments:pricing')
    
    # Get tipster's active tips
    active_tips = Tip.objects.filter(
        tipster=tipster,
        status='active'
    ).order_by('-created_at')

    # Get tipster's historical tips (archived, resulted, etc.)
    historical_tips = Tip.objects.filter(
        tipster=tipster
    ).exclude(status='active').order_by('-created_at')

    # Pagination for active tips
    active_paginator = Paginator(active_tips, 6)  # 6 tips per page
    active_page_number = request.GET.get('active_page')
    active_page_obj = active_paginator.get_page(active_page_number)

    # Pagination for historical tips
    historical_paginator = Paginator(historical_tips, 10)  # 10 tips per page
    historical_page_number = request.GET.get('historical_page')
    historical_page_obj = historical_paginator.get_page(historical_page_number)

    # Calculate stats (matching leaderboard logic)
    all_tips = Tip.objects.filter(tipster=tipster)
    resulted_tips = all_tips.filter(is_resulted=True)

    stats = {
        'total_tips': all_tips.count(),  # All tips, not just resulted
        'resulted_tips': resulted_tips.count(),  # Track resulted separately
        'won_tips': resulted_tips.filter(is_won=True).count(),
        'lost_tips': resulted_tips.filter(is_won=False).count(),
        'win_rate': 0,
        'active_tips': active_tips.count(),
        'historical_tips': historical_tips.count(),
        'avg_odds': all_tips.aggregate(Avg('odds'))['odds__avg'] or 0,
    }

    # Calculate win rate only from resulted tips
    if stats['resulted_tips'] > 0:
        stats['win_rate'] = round((stats['won_tips'] / stats['resulted_tips']) * 100, 1)
    
    context = {
        'tipster': tipster,
        'profile': getattr(tipster, 'userprofile', None),
        'active_page_obj': active_page_obj,
        'active_tips': active_page_obj.object_list,
        'historical_page_obj': historical_page_obj,
        'historical_tips': historical_page_obj.object_list,
        'stats': stats,
    }

    return render(request, 'tips/tipster_profile.html', context)


def leaderboard(request):
    """Leaderboard showing top tipsters by win rate"""
    from django.contrib.auth import get_user_model
    from django.db.models import Count, Q, Avg

    User = get_user_model()

    # Get all tipsters with annotated stats to avoid N+1 queries
    tipsters = User.objects.annotate(
        total_tips_count=Count('tips'),
        resulted_count=Count('tips', filter=Q(tips__is_resulted=True)),
        won_tips=Count('tips', filter=Q(tips__is_resulted=True, tips__is_won=True)),
        active_tips=Count('tips', filter=Q(tips__status='active')),
        avg_odds=Avg('tips__odds')
    ).filter(total_tips_count__gt=0).select_related('userprofile')

    # Calculate stats for each tipster
    leaderboard_data = []

    for tipster in tipsters:
        win_rate = round((tipster.won_tips / tipster.resulted_count * 100), 1) if tipster.resulted_count > 0 else 0.0
        avg_odds = float(tipster.avg_odds) if tipster.avg_odds else 0.0

        leaderboard_data.append({
            'tipster': tipster,
            'profile': getattr(tipster, 'userprofile', None),
            'total_tips': tipster.total_tips_count,
            'won_tips': tipster.won_tips,
            'win_rate': win_rate,
            'avg_odds': round(avg_odds, 2),
            'active_tips': tipster.active_tips,
            'resulted_count': tipster.resulted_count,
        })

    # Default sorting
    sort_by = request.GET.get('sort', 'win_rate')

    if sort_by == 'win_rate':
        leaderboard_data.sort(
            key=lambda x: (
                x['resulted_count'] > 0,
                x['win_rate'],
                x['total_tips']
            ),
            reverse=True
        )
    elif sort_by == 'total_tips':
        leaderboard_data.sort(
            key=lambda x: (
                x['total_tips'],
                x['win_rate'],
                x['resulted_count']
            ),
            reverse=True
        )
    elif sort_by == 'avg_odds':
        leaderboard_data.sort(
            key=lambda x: (
                x['avg_odds'],
                x['win_rate'],
                x['total_tips']
            ),
            reverse=True
        )
    else:
        # Default to win_rate sorting
        leaderboard_data.sort(
            key=lambda x: (
                x['resulted_count'] > 0,
                x['win_rate'],
                x['total_tips']
            ),
            reverse=True
        )

    # Add rank numbers
    for idx, tipster_data in enumerate(leaderboard_data, 1):
        tipster_data['rank'] = idx

    from django.conf import settings
    limit = getattr(settings, 'PRO_RESTRICTED_TOP_ANALYSTS_COUNT', 10)

    user_has_tips = False
    if request.user.is_authenticated:
        user_has_tips = any(d['tipster'].id == request.user.id for d in leaderboard_data)

    context = {
        'leaderboard': leaderboard_data,
        'sort_by': sort_by,
        'pro_restricted_limit': limit,
        'user_has_tips': user_has_tips,
    }

    return render(request, 'tips/leaderboard.html', context)


@staff_member_required
def manual_resolution(request):
    """Admin dashboard to manually resolve stuck slips"""
    
    if request.method == 'POST':
        action = request.POST.get('action')
        match_id = request.POST.get('match_id')
        
        if match_id and action in ['won', 'lost', 'void']:
            match = get_object_or_404(TipMatch, id=match_id)
            match.is_resulted = True
            
            if action == 'won':
                match.is_won = True
                match.actual_result = 'Manual Win'
            elif action == 'lost':
                match.is_won = False
                match.actual_result = 'Manual Loss'
            elif action == 'void':
                match.is_won = True  # Treat void as won so accumulator continues
                match.actual_result = 'Void / Push'
                match.odds = Decimal('1.00')  # Reset odds to 1.0
                
            match.save()
            
            # Check if all matches in tip are resulted
            tip = match.tip
            if tip.matches.filter(is_resulted=False).count() == 0:
                tip_won = not tip.matches.filter(is_won=False).exists()
                tip.is_resulted = True
                tip.is_won = tip_won
                tip.status = 'archived'
                tip.result_verified_at = timezone.now()
                
                # Recalculate tip odds if voided
                total_odds = Decimal('1.00')
                for m in tip.matches.all():
                    total_odds *= m.odds
                tip.odds = round(total_odds, 2)
                tip.save()
                
                messages.success(request, f"Tip {tip.bet_code or tip.id} fully graded as {'WON' if tip_won else 'LOST'}")
            else:
                messages.success(request, f"Match manually graded as {action.upper()}")
                
        return redirect('tips:manual_resolution')
        
    # Get tips that are active, past expiry, and not resulted
    # We add an hour grace period to be safe
    stuck_tips = Tip.objects.filter(
        status='active',
        is_resulted=False,
        expires_at__lt=timezone.now() - timedelta(hours=2)
    ).prefetch_related('matches').order_by('expires_at')
    
    return render(request, 'tips/manual_resolution.html', {
        'stuck_tips': stuck_tips
    })

def tip_live_scores(request, tip_id):
    """AJAX endpoint to get live scores for a tip"""
    tip = get_object_or_404(Tip, id=tip_id)
    
    live_matches = []
    for match in tip.matches.all():
        if match.api_match_id and not match.is_resulted:
            from apps.fixtures.models import Fixture
            fixture = Fixture.objects.filter(api_id=match.api_match_id).first()
            if fixture:
                live_matches.append({
                    'id': match.id,
                    'is_live': fixture.is_live,
                    'is_finished': fixture.is_finished,
                    'score': fixture.get_result_string() if fixture.home_goals is not None else None,
                    'elapsed': fixture.elapsed,
                    'status_short': fixture.status_short
                })
                
    return JsonResponse({'matches': live_matches})
