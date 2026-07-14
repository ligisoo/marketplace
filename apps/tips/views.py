from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
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
        search = form.cleaned_data.get('search')
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
            
        sort_by = form.cleaned_data.get('sort_by', '-created_at')
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
    if tip.is_premium:
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

                # Check cache first (MD5 hash-based caching)
                screenshot.seek(0)
                file_data = screenshot.read()
                screenshot.seek(0)

                file_hash = hashlib.md5(file_data).hexdigest()
                cache_key = f'betslip_{file_hash}'

                cached_result = cache.get(cache_key)
                if cached_result:
                    logger.info(f"✓ Cache hit! Using cached extraction result.")
                    extraction_result = copy.deepcopy(cached_result)
                else:
                    logger.info(f"Cache miss. Processing with Gemini...")
                    extraction_result = process_betslip_image(screenshot)

                    # Cache successful results for 24 hours
                    if extraction_result.get('success'):
                        cache.set(cache_key, extraction_result, 86400)

                if not extraction_result.get('success'):
                    error_msg = extraction_result.get('error', 'Failed to extract prediction slip data')
                    messages.error(request, f'Error: {error_msg}')
                    return render(request, 'tips/create_tip.html', {'form': form})

                # Extract data
                betslip_data = extraction_result['data']
                matches = betslip_data.get('matches', [])

                if not matches:
                    messages.error(request, 'No matches found in the prediction slip. Please upload a clear image.')
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
                latest_match_date = timezone.now() + timedelta(days=1)
                for match_data in matches:
                    match_date = parse_match_date(
                        match_data.get('match_date'),
                        match_data.get('match_time')
                    )
                    if match_date > latest_match_date:
                        latest_match_date = match_date

                tip.expires_at = latest_match_date
                tip.status = 'draft'  # Draft status for verification step
                tip.save()

                # Create TipMatch records
                for match_data in matches:
                    match_date = parse_match_date(
                        match_data.get('match_date'),
                        match_data.get('match_time')
                    )

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
        'win_rate': 0,
        'active_tips': active_tips.count(),
        'historical_tips': historical_tips.count(),
        'avg_odds': resulted_tips.aggregate(Avg('odds'))['odds__avg'] or 0,
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
    from django.db.models import Count, Sum, Q, Avg

    User = get_user_model()

    # Get all tipsters with their stats
    tipsters = User.objects.all().select_related('userprofile')

    # Calculate stats for each tipster
    leaderboard_data = []

    for tipster in tipsters:
        all_tips = Tip.objects.filter(tipster=tipster)
        resulted_tips = all_tips.filter(is_resulted=True)
        total_tips = all_tips.count()
        resulted_count = resulted_tips.count()
        won_tips = resulted_tips.filter(is_won=True).count()
        win_rate = round((won_tips / resulted_count * 100), 1) if resulted_count > 0 else 0
        avg_odds = resulted_tips.aggregate(avg=Avg('odds'))['avg'] or 0
        active_tips = all_tips.filter(status='active').count()

        if total_tips > 0:
            leaderboard_data.append({
                'tipster': tipster,
                'profile': getattr(tipster, 'userprofile', None),
                'total_tips': total_tips,
                'won_tips': won_tips,
                'win_rate': win_rate,
                'avg_odds': round(avg_odds, 2) if avg_odds else 0,
                'active_tips': active_tips,
                'resulted_count': resulted_count,
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

    context = {
        'leaderboard': leaderboard_data,
        'sort_by': sort_by,
    }

    return render(request, 'tips/leaderboard.html', context)
