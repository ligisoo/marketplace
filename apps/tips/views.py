from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from .models import Tip, TipMatch, TipPurchase, TipView
from .forms import TipSubmissionForm, TipVerificationForm, TipSearchForm
from .ocr import BetslipOCR
import json


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
        
        min_price = form.cleaned_data.get('min_price')
        if min_price:
            tips = tips.filter(price__gte=min_price)
        
        max_price = form.cleaned_data.get('max_price')
        if max_price:
            tips = tips.filter(price__lte=max_price)
        
        sort_by = form.cleaned_data.get('sort_by', '-created_at')
        tips = tips.order_by(sort_by)
    else:
        tips = tips.order_by('-created_at')
    
    # Add purchase count annotation
    tips = tips.annotate(total_purchases=Count('purchases'))
    
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
        # Get IP address, fallback to '127.0.0.1' if not available
        ip_address = request.META.get('REMOTE_ADDR') or request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or '127.0.0.1'
        
        TipView.objects.create(
            tip=tip,
            user=request.user if request.user.is_authenticated else None,
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    
    # Check if user has already purchased this tip
    has_purchased = False
    if request.user.is_authenticated:
        has_purchased = TipPurchase.objects.filter(
            tip=tip, 
            buyer=request.user, 
            status='completed'
        ).exists()
    
    context = {
        'tip': tip,
        'matches': tip.matches.all(),
        'has_purchased': has_purchased,
        'can_purchase': tip.can_be_purchased() and not has_purchased,
    }
    
    return render(request, 'tips/detail.html', context)


@login_required
def my_tips(request):
    """Tipster's dashboard showing their tips"""
    if not request.user.userprofile.is_tipster:
        messages.error(request, 'Only tipsters can access this page.')
        return redirect('tips:marketplace')
    
    tips = Tip.objects.filter(tipster=request.user).order_by('-created_at')
    
    # Add purchase counts
    tips = tips.annotate(total_purchases=Count('purchases'))
    
    # Pagination
    paginator = Paginator(tips, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate stats
    stats = {
        'total_tips': tips.count(),
        'active_tips': tips.filter(status='active').count(),
        'pending_tips': tips.filter(status='pending_approval').count(),
        'total_sales': sum(tip.revenue_generated for tip in tips),
    }
    
    context = {
        'page_obj': page_obj,
        'tips': page_obj.object_list,
        'stats': stats,
    }
    
    return render(request, 'tips/my_tips.html', context)


@login_required
def create_tip(request):
    """Create a new tip - Step 1: Upload betslip"""
    if not request.user.userprofile.is_tipster:
        messages.error(request, 'Only tipsters can create tips.')
        return redirect('tips:marketplace')

    # Clean up old temporary tips (older than 1 hour)
    from datetime import timedelta
    one_hour_ago = timezone.now() - timedelta(hours=1)
    Tip.objects.filter(
        bet_code__startswith='TEMP_',
        created_at__lt=one_hour_ago
    ).delete()

    if request.method == 'POST':
        form = TipSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            # Save the tip temporarily
            tip = form.save(commit=False)
            tip.tipster = request.user
            tip.bet_code = 'TEMP_' + str(timezone.now().timestamp()).replace('.', '')
            tip.odds = 0  # Will be updated in verification step
            tip.expires_at = timezone.now()  # Will be updated in verification step
            tip.save()
            
            # Process OCR
            ocr_service = BetslipOCR()
            ocr_result = ocr_service.process_betslip_image(tip.screenshot)
            
            if ocr_result['success']:
                # Store OCR data
                tip.match_details = ocr_result['data']
                tip.ocr_confidence = ocr_result['confidence']
                tip.save()
                
                # Redirect to verification step
                return redirect('tips:verify_tip', tip_id=tip.id)
            else:
                # OCR failed, delete tip and show error
                tip.delete()
                messages.error(request, f"Failed to process betslip: {ocr_result.get('error', 'Unknown error')}")
    else:
        form = TipSubmissionForm()
    
    return render(request, 'tips/create_tip.html', {'form': form})


@login_required
def verify_tip(request, tip_id):
    """Verify and edit OCR-extracted data - Step 2"""
    import logging
    logger = logging.getLogger(__name__)

    tip = get_object_or_404(Tip, id=tip_id, tipster=request.user)

    if tip.ocr_processed:
        messages.info(request, 'This tip has already been processed.')
        return redirect('tips:my_tips')

    ocr_data = tip.match_details
    matches_data = ocr_data.get('matches', [])

    # Debug logging
    logger.info(f"=== VERIFY TIP DEBUG ===")
    logger.info(f"OCR Data: {json.dumps(ocr_data, indent=2)}")
    logger.info(f"Number of matches: {len(matches_data)}")
    for i, match in enumerate(matches_data):
        logger.info(f"Match {i+1}: {match}")
    
    if request.method == 'POST':
        form = TipVerificationForm(
            request.POST,
            ocr_data=ocr_data,
            matches_data=matches_data
        )
        
        if form.is_valid():
            # Update tip with verified data
            tip.bet_code = form.cleaned_data['bet_code']
            tip.odds = form.cleaned_data['total_odds']
            tip.expires_at = form.cleaned_data['expires_at']
            tip.ocr_processed = True
            
            # Set status based on tipster verification level
            if request.user.userprofile.is_verified:
                tip.status = 'active'
                messages.success(request, 'Tip created and is now live!')
            else:
                tip.status = 'pending_approval'
                messages.success(request, 'Tip submitted for approval. It will be reviewed by our team.')
            
            tip.save()
            
            # Create match objects
            matches_data = form.get_matches_data()
            for match_data in matches_data:
                TipMatch.objects.create(
                    tip=tip,
                    **match_data
                )
            
            # Create preview data for buyers
            preview_matches = matches_data[:2]  # Show first 2 matches
            tip.preview_data = {
                'matches': [
                    {
                        'home_team': match['home_team'],
                        'away_team': match['away_team'],
                        'league': match['league'],
                        'market': match['market'],
                    }
                    for match in preview_matches
                ],
                'total_matches': len(matches_data)
            }
            tip.save()
            
            return redirect('tips:my_tips')
    else:
        form = TipVerificationForm(
            ocr_data=ocr_data,
            matches_data=matches_data
        )
    
    context = {
        'tip': tip,
        'form': form,
        'ocr_data': ocr_data,
        'matches_data': matches_data,
    }
    
    return render(request, 'tips/verify_tip.html', context)


@login_required
@require_http_methods(["POST"])
def purchase_tip(request, tip_id):
    """Initiate tip purchase"""
    tip = get_object_or_404(Tip, id=tip_id)
    
    # Validation checks
    if not tip.can_be_purchased():
        return JsonResponse({
            'success': False,
            'error': 'This tip cannot be purchased at the moment.'
        })
    
    if not request.user.userprofile.is_buyer:
        return JsonResponse({
            'success': False,
            'error': 'Only buyers can purchase tips.'
        })
    
    if request.user == tip.tipster:
        return JsonResponse({
            'success': False,
            'error': 'You cannot purchase your own tip.'
        })
    
    # Check if already purchased
    if TipPurchase.objects.filter(tip=tip, buyer=request.user).exists():
        return JsonResponse({
            'success': False,
            'error': 'You have already purchased this tip.'
        })
    
    # Check wallet balance
    if request.user.userprofile.wallet_balance < tip.price:
        return JsonResponse({
            'success': False,
            'error': 'Insufficient wallet balance. Please add funds.'
        })
    
    # Create purchase record
    try:
        transaction_id = f"TIP_{tip.id}_{request.user.id}_{timezone.now().timestamp()}"
        
        purchase = TipPurchase.objects.create(
            tip=tip,
            buyer=request.user,
            amount=tip.price,
            transaction_id=transaction_id,
            status='completed'  # Simplified for now
        )
        
        # Deduct from buyer's wallet
        request.user.userprofile.wallet_balance -= tip.price
        request.user.userprofile.save()
        
        # Add to tipster's pending balance (would be handled by escrow system)
        # For now, directly add to tipster wallet
        tipster_earning = tip.price * 0.6  # 60% to tipster
        tip.tipster.userprofile.wallet_balance += tipster_earning
        tip.tipster.userprofile.save()
        
        purchase.completed_at = timezone.now()
        purchase.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Tip purchased successfully!',
            'redirect_url': f'/tips/{tip.id}/'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Purchase failed: {str(e)}'
        })


def tipster_profile(request, tipster_id):
    """Public tipster profile with their tips"""
    from django.contrib.auth import get_user_model
    from django.db.models import Avg
    User = get_user_model()
    
    tipster = get_object_or_404(
        User,
        id=tipster_id,
        userprofile__is_tipster=True
    )
    
    # Get tipster's active tips
    tips = Tip.objects.filter(
        tipster=tipster,
        status='active'
    ).order_by('-created_at')[:10]

    # Calculate stats (matching leaderboard logic)
    all_tips = Tip.objects.filter(tipster=tipster)
    resulted_tips = all_tips.filter(is_resulted=True)

    stats = {
        'total_tips': all_tips.count(),  # All tips, not just resulted
        'resulted_tips': resulted_tips.count(),  # Track resulted separately
        'won_tips': resulted_tips.filter(is_won=True).count(),
        'win_rate': 0,
        'total_sales': sum(tip.revenue_generated for tip in all_tips),
        'active_tips': all_tips.filter(status='active').count(),
        'total_purchases': sum(tip.purchase_count for tip in all_tips),
        'avg_odds': resulted_tips.aggregate(Avg('odds'))['odds__avg'] or 0,
    }

    # Calculate win rate only from resulted tips
    if stats['resulted_tips'] > 0:
        stats['win_rate'] = round((stats['won_tips'] / stats['resulted_tips']) * 100, 1)
    
    context = {
        'tipster': tipster,
        'profile': tipster.userprofile,
        'tips': tips,
        'stats': stats,
    }

    return render(request, 'tips/tipster_profile.html', context)


def leaderboard(request):
    """Leaderboard showing top tipsters by various metrics"""
    from django.contrib.auth import get_user_model
    from django.db.models import Count, Sum, Q, Avg

    User = get_user_model()

    # Get all tipsters with their stats
    tipsters = User.objects.filter(
        userprofile__is_tipster=True
    ).select_related('userprofile')

    # Calculate stats for each tipster
    leaderboard_data = []

    for tipster in tipsters:
        # Get all tips (not just resulted ones)
        all_tips = Tip.objects.filter(tipster=tipster)

        # Get resulted tips for win rate calculation
        resulted_tips = all_tips.filter(is_resulted=True)

        # Count total tips (all tips, not just resulted)
        total_tips = all_tips.count()

        # Win rate is only for resulted tips
        resulted_count = resulted_tips.count()
        won_tips = resulted_tips.filter(is_won=True).count()
        win_rate = round((won_tips / resulted_count * 100), 1) if resulted_count > 0 else 0

        # Calculate total sales
        total_sales = sum(tip.revenue_generated for tip in all_tips)

        # Calculate average odds (only from resulted tips)
        avg_odds = resulted_tips.aggregate(avg=Avg('odds'))['avg'] or 0

        # Total purchases across all tips
        total_purchases = sum(tip.purchase_count for tip in all_tips)

        # Active tips count
        active_tips = all_tips.filter(status='active').count()

        # Include tipsters with at least 1 tip (resulted or not)
        if total_tips > 0:
            leaderboard_data.append({
                'tipster': tipster,
                'profile': tipster.userprofile,
                'total_tips': total_tips,
                'won_tips': won_tips,
                'win_rate': win_rate,
                'total_sales': total_sales,
                'avg_odds': round(avg_odds, 2) if avg_odds else 0,
                'total_purchases': total_purchases,
                'active_tips': active_tips,
                'resulted_count': resulted_count,  # Track how many are resulted
            })

    # Default sorting
    sort_by = request.GET.get('sort', 'win_rate')

    # Sort leaderboard
    if sort_by == 'win_rate':
        leaderboard_data.sort(key=lambda x: (x['win_rate'], x['total_tips']), reverse=True)
    elif sort_by == 'total_tips':
        leaderboard_data.sort(key=lambda x: x['total_tips'], reverse=True)
    elif sort_by == 'total_sales':
        leaderboard_data.sort(key=lambda x: x['total_sales'], reverse=True)
    elif sort_by == 'total_purchases':
        leaderboard_data.sort(key=lambda x: x['total_purchases'], reverse=True)
    else:
        leaderboard_data.sort(key=lambda x: x['win_rate'], reverse=True)

    # Add rank numbers
    for idx, tipster_data in enumerate(leaderboard_data, 1):
        tipster_data['rank'] = idx

    context = {
        'leaderboard': leaderboard_data,
        'sort_by': sort_by,
    }

    return render(request, 'tips/leaderboard.html', context)
