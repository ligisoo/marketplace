from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from .models import Tip, TipMatch, TipPurchase, TipView
from .forms import TipSubmissionForm, TipVerificationForm, TipSearchForm
from .ocr import BetslipOCR
from apps.transactions.pdf_utils import StatementPDFGenerator
from datetime import datetime
from decimal import Decimal
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
    """Tipster's dashboard showing their tips and purchases"""
    
    # Get filter parameter for My Tips section
    tip_filter = request.GET.get('filter', 'all')  # all, active, archived
    
    # Base queryset for user's tips
    base_tips = Tip.objects.filter(tipster=request.user).annotate(total_purchases=Count('purchases'))
    
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
        'total_sales': sum(tip.revenue_generated for tip in all_tips),
        'current_filter': tip_filter,
    }

    # Data for "My Purchases"
    my_purchased_tips = TipPurchase.objects.filter(
        buyer=request.user,
        status='completed'
    ).select_related('tip', 'tip__tipster').order_by('-created_at')

    # Pagination for purchased tips
    purchases_paginator = Paginator(my_purchased_tips, 10)
    purchases_page_number = request.GET.get('purchases_page')
    purchases_page_obj = purchases_paginator.get_page(purchases_page_number)

    # Stats for purchased tips
    purchases_stats = {
        'total_purchases': my_purchased_tips.count(),
        'total_spent': sum(p.amount for p in my_purchased_tips),
        'won_tips': my_purchased_tips.filter(tip__is_resulted=True, tip__is_won=True).count(),
        'lost_tips': my_purchased_tips.filter(tip__is_resulted=True, tip__is_won=False).count(),
        'pending_tips': my_purchased_tips.filter(tip__is_resulted=False).count(),
    }

    context = {
        'selling_page_obj': selling_page_obj,
        'selling_tips': selling_page_obj.object_list,
        'selling_stats': selling_stats,
        'purchases_page_obj': purchases_page_obj,
        'purchases': purchases_page_obj.object_list,
        'purchases_stats': purchases_stats,
        'is_tipster': request.user.userprofile.is_tipster,
    }
    
    return render(request, 'tips/my_tips.html', context)


@login_required
def earnings_dashboard(request):
    """Tipster earnings dashboard with detailed analytics"""
    if not request.user.userprofile.is_tipster:
        messages.error(request, 'Only tipsters can access this page.')
        return redirect('tips:marketplace')

    from django.db.models import Sum, Count, Q
    from datetime import timedelta
    from decimal import Decimal

    # Get all tipster's tips
    all_tips = Tip.objects.filter(tipster=request.user)

    # Calculate total revenue
    total_revenue = sum(tip.revenue_generated for tip in all_tips)

    # Calculate earnings split (60/40)
    platform_commission_rate = Decimal('0.40')
    tipster_share_rate = Decimal('0.60')

    tipster_earnings = Decimal(str(total_revenue)) * tipster_share_rate
    platform_commission = Decimal(str(total_revenue)) * platform_commission_rate

    # Get completed purchases
    all_purchases = TipPurchase.objects.filter(
        tip__tipster=request.user,
        status='completed'
    ).select_related('tip')

    # Anonymous buyer statistics
    unique_buyers_count = all_purchases.values('buyer').distinct().count()

    # Repeat customers (buyers who purchased more than once)
    buyer_purchase_counts = all_purchases.values('buyer').annotate(
        purchase_count=Count('id')
    )
    repeat_customers = sum(1 for b in buyer_purchase_counts if b['purchase_count'] > 1)

    # Time-based analytics
    now = timezone.now()
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)

    # This month's earnings
    this_month_purchases = all_purchases.filter(completed_at__gte=this_month_start)
    this_month_revenue = sum(p.amount for p in this_month_purchases)
    this_month_earnings = Decimal(str(this_month_revenue)) * tipster_share_rate

    # Last month's earnings
    last_month_purchases = all_purchases.filter(
        completed_at__gte=last_month_start,
        completed_at__lt=this_month_start
    )
    last_month_revenue = sum(p.amount for p in last_month_purchases)
    last_month_earnings = Decimal(str(last_month_revenue)) * tipster_share_rate

    # Calculate growth
    if last_month_earnings > 0:
        growth_percentage = ((this_month_earnings - last_month_earnings) / last_month_earnings) * 100
    else:
        growth_percentage = 100 if this_month_earnings > 0 else 0

    # Top performing tips (by revenue)
    top_tips_by_revenue = []
    for tip in all_tips:
        revenue = tip.revenue_generated
        if revenue > 0:
            top_tips_by_revenue.append({
                'tip': tip,
                'revenue': revenue,
                'earnings': Decimal(str(revenue)) * tipster_share_rate,
                'purchases': tip.purchase_count,
            })

    top_tips_by_revenue.sort(key=lambda x: x['revenue'], reverse=True)
    top_tips_by_revenue = top_tips_by_revenue[:5]  # Top 5

    # Top tips by purchase count
    top_tips_by_sales = []
    for tip in all_tips:
        purchase_count = tip.purchase_count
        if purchase_count > 0:
            top_tips_by_sales.append({
                'tip': tip,
                'purchases': purchase_count,
                'revenue': tip.revenue_generated,
                'earnings': Decimal(str(tip.revenue_generated)) * tipster_share_rate,
            })

    top_tips_by_sales.sort(key=lambda x: x['purchases'], reverse=True)
    top_tips_by_sales = top_tips_by_sales[:5]  # Top 5

    # Recent transactions (last 10, anonymous)
    recent_transactions = all_purchases.order_by('-completed_at')[:10]

    # Weekly breakdown (last 4 weeks)
    weekly_data = []
    for week_num in range(4):
        week_end = now - timedelta(days=week_num * 7)
        week_start = week_end - timedelta(days=7)

        week_purchases = all_purchases.filter(
            completed_at__gte=week_start,
            completed_at__lt=week_end
        )
        week_revenue = sum(p.amount for p in week_purchases)
        week_earnings = Decimal(str(week_revenue)) * tipster_share_rate

        weekly_data.insert(0, {
            'week_label': f"{week_start.strftime('%b %d')} - {week_end.strftime('%b %d')}",
            'revenue': week_revenue,
            'earnings': week_earnings,
            'purchases': week_purchases.count(),
        })

    context = {
        # Overall earnings
        'total_revenue': total_revenue,
        'tipster_earnings': tipster_earnings,
        'platform_commission': platform_commission,
        'tipster_share_percentage': 60,
        'platform_commission_percentage': 40,

        # Monthly stats
        'this_month_revenue': this_month_revenue,
        'this_month_earnings': this_month_earnings,
        'last_month_earnings': last_month_earnings,
        'growth_percentage': round(growth_percentage, 1),

        # Buyer statistics (anonymous)
        'total_purchases': all_purchases.count(),
        'unique_buyers': unique_buyers_count,
        'repeat_customers': repeat_customers,

        # Top performing tips
        'top_tips_by_revenue': top_tips_by_revenue,
        'top_tips_by_sales': top_tips_by_sales,

        # Recent activity
        'recent_transactions': recent_transactions,

        # Weekly breakdown
        'weekly_data': weekly_data,

        # General stats
        'total_tips': all_tips.count(),
        'active_tips': all_tips.filter(status='active').count(),
    }

    return render(request, 'tips/earnings_dashboard.html', context)


@login_required
def download_earnings_statement(request):
    """
    Generate and download PDF earnings statement for sellers/tipsters.
    """
    if not request.user.userprofile.is_tipster:
        messages.error(request, 'Only tipsters can access this page.')
        return redirect('tips:marketplace')

    # Get all tipster's tips
    all_tips = Tip.objects.filter(tipster=request.user)

    # Calculate total revenue
    total_revenue = sum(tip.revenue_generated for tip in all_tips)

    # Calculate earnings split (60/40)
    platform_commission_rate = Decimal('0.40')
    tipster_share_rate = Decimal('0.60')

    tipster_earnings = Decimal(str(total_revenue)) * tipster_share_rate
    platform_commission = Decimal(str(total_revenue)) * platform_commission_rate

    # Get completed purchases
    all_purchases = TipPurchase.objects.filter(
        tip__tipster=request.user,
        status='completed'
    ).select_related('tip', 'buyer')

    # Anonymous buyer statistics
    unique_buyers_count = all_purchases.values('buyer').distinct().count()

    # Repeat customers (buyers who purchased more than once)
    buyer_purchase_counts = all_purchases.values('buyer').annotate(
        purchase_count=Count('id')
    )
    repeat_customers = sum(1 for b in buyer_purchase_counts if b['purchase_count'] > 1)

    # Recent transactions for PDF
    recent_transactions = []
    for purchase in all_purchases.order_by('-completed_at')[:20]:  # Last 20 transactions
        recent_transactions.append({
            'date': purchase.completed_at or purchase.created_at,
            'tip_title': f"{purchase.tip.bookmaker.title()} Tip ({purchase.tip.bet_code})",
            'amount': purchase.amount,
            'tipster_share': Decimal(str(purchase.amount)) * tipster_share_rate,
        })

    # Prepare earnings data for PDF
    earnings_data = {
        'total_revenue': total_revenue,
        'platform_commission': platform_commission,
        'tipster_earnings': tipster_earnings,
        'total_purchases': all_purchases.count(),
        'unique_buyers': unique_buyers_count,
        'repeat_customers': repeat_customers,
        'tips_count': all_tips.count(),
        'recent_transactions': recent_transactions,
    }

    # Generate PDF
    pdf_generator = StatementPDFGenerator()
    pdf_buffer = pdf_generator.generate_seller_statement(
        user=request.user,
        earnings_data=earnings_data
    )

    # Create response with PDF
    response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')

    # Generate filename with date
    filename = f"earnings_statement_{request.user.phone_number}_{datetime.now().strftime('%Y%m%d')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response


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
            # Save the tip with pending status
            tip = form.save(commit=False)
            tip.tipster = request.user
            tip.bet_code = 'TEMP_' + str(timezone.now().timestamp()).replace('.', '')
            tip.odds = 0  # Will be updated by background processing
            tip.expires_at = timezone.now()  # Will be updated by background processing
            tip.processing_status = 'pending'
            tip.save()

            # Enqueue background processing task
            from .task_queue import enqueue_task
            from .background_tasks import process_betslip_async, processing_callback

            task_id = enqueue_task(
                process_betslip_async,
                tip.id,
                callback=processing_callback
            )

            # Show success message
            messages.success(
                request,
                'Your bet link has been captured for processing. '
                'You will be notified once processing is complete.'
            )

            # Redirect to processing status page
            return redirect('tips:tip_processing_status', tip_id=tip.id)
    else:
        form = TipSubmissionForm()

    # Get active provider to pass to template
    from .models import OCRProviderSettings
    ocr_provider = OCRProviderSettings.get_active_provider()

    return render(request, 'tips/create_tip.html', {
        'form': form,
        'ocr_provider': ocr_provider
    })


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
def tip_processing_status(request, tip_id):
    """Show processing status of a tip"""
    tip = get_object_or_404(Tip, id=tip_id)

    # Only tipster who created the tip can view this
    if tip.tipster != request.user:
        messages.error(request, 'You do not have permission to view this tip.')
        return redirect('tips:my_tips')

    # If processing is complete, redirect to verify page
    if tip.processing_status == 'completed' and tip.ocr_processed:
        return redirect('tips:verify_tip', tip_id=tip.id)

    context = {
        'tip': tip,
    }

    return render(request, 'tips/processing_status.html', context)


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
    
    # Create purchase record with accounting entries
    try:
        from apps.transactions.services import AccountingService
        from django.db import transaction as db_transaction

        with db_transaction.atomic():
            # Create accounting entries for the purchase
            accounting_txn = AccountingService.record_tip_purchase(
                buyer=request.user,
                tipster=tip.tipster,
                tip=tip,
                amount=tip.price
            )

            # Create TipPurchase record
            purchase = TipPurchase.objects.create(
                tip=tip,
                buyer=request.user,
                amount=tip.price,
                transaction_id=accounting_txn.reference,
                status='completed',
                completed_at=timezone.now()
            )

            # Sync wallet balances with accounting
            AccountingService.sync_wallet_balance(request.user)
            AccountingService.sync_wallet_balance(tip.tipster)

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
        'total_sales': sum(tip.revenue_generated for tip in all_tips),
        'active_tips': active_tips.count(),
        'historical_tips': historical_tips.count(),
        'total_purchases': sum(tip.purchase_count for tip in all_tips),
        'avg_odds': resulted_tips.aggregate(Avg('odds'))['odds__avg'] or 0,
    }

    # Calculate win rate only from resulted tips
    if stats['resulted_tips'] > 0:
        stats['win_rate'] = round((stats['won_tips'] / stats['resulted_tips']) * 100, 1)
    
    context = {
        'tipster': tipster,
        'profile': tipster.userprofile,
        'active_page_obj': active_page_obj,
        'active_tips': active_page_obj.object_list,
        'historical_page_obj': historical_page_obj,
        'historical_tips': historical_page_obj.object_list,
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

    # Sort leaderboard with better tiebreakers
    if sort_by == 'win_rate':
        # Sort by: win_rate (desc), resulted_count (desc), total_purchases (desc), total_sales (desc)
        # This puts tipsters with results first, then by popularity and sales
        leaderboard_data.sort(
            key=lambda x: (
                x['resulted_count'] > 0,  # Tipsters with results first
                x['win_rate'],
                x['total_purchases'],
                x['total_sales'],
                x['total_tips']
            ),
            reverse=True
        )
    elif sort_by == 'total_tips':
        # Sort by: total_tips (desc), win_rate (desc), total_purchases (desc)
        leaderboard_data.sort(
            key=lambda x: (
                x['total_tips'],
                x['win_rate'],
                x['total_purchases'],
                x['total_sales']
            ),
            reverse=True
        )
    elif sort_by == 'total_sales':
        # Sort by: total_sales (desc), total_purchases (desc), win_rate (desc)
        leaderboard_data.sort(
            key=lambda x: (
                x['total_sales'],
                x['total_purchases'],
                x['win_rate'],
                x['total_tips']
            ),
            reverse=True
        )
    elif sort_by == 'total_purchases':
        # Sort by: total_purchases (desc), total_sales (desc), win_rate (desc)
        leaderboard_data.sort(
            key=lambda x: (
                x['total_purchases'],
                x['total_sales'],
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
                x['total_purchases'],
                x['total_sales']
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
