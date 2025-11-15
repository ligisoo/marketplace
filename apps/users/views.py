from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db.models import Sum, Avg, Q
from decimal import Decimal
from django.http import JsonResponse
import re
from apps.tips.models import Tip, TipPurchase
from apps.transactions.services import AccountingService
from .forms import RegistrationForm, LoginForm, ProfileEditForm
from .models import User, UserProfile


def register(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful! You can now log in.')
            return redirect('users:login')
    else:
        form = RegistrationForm()
    
    return render(request, 'users/register.html', {'form': form})


def user_login(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            phone_number = form.cleaned_data['phone_number']
            password = form.cleaned_data['password']
            user = authenticate(request, username=phone_number, password=password)
            
            if user:
                login(request, user)
                messages.success(request, f'Welcome back, {user.userprofile.display_name}!')
                
                # Redirect to next page or appropriate dashboard
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                
                # Redirect based on user roles
                if user.userprofile.is_tipster:
                    return redirect('tips:my_tips')
                else:
                    return redirect('tips:marketplace')
    else:
        form = LoginForm()
    
    return render(request, 'users/login.html', {'form': form})


@login_required
def user_logout(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


@login_required
def profile(request):
    """User profile view"""
    
    tipster_stats = None
    if request.user.userprofile.is_tipster:
        all_tips = Tip.objects.filter(tipster=request.user)
        resulted_tips = all_tips.filter(is_resulted=True)
        
        total_revenue = sum(tip.revenue_generated for tip in all_tips)
        tipster_earnings = Decimal(str(total_revenue)) * Decimal('0.60') # Assuming 60% share
        
        won_tips_count = resulted_tips.filter(is_won=True).count()
        resulted_count = resulted_tips.count()
        win_rate = round((won_tips_count / resulted_count * 100), 1) if resulted_count > 0 else 0

        total_sales = TipPurchase.objects.filter(tip__tipster=request.user, status='completed').count()

        tipster_stats = {
            'total_tips': all_tips.count(),
            'total_revenue': total_revenue,
            'total_earnings': tipster_earnings,
            'win_rate': win_rate,
            'total_sales': total_sales,
        }

    return render(request, 'users/profile.html', {
        'user': request.user,
        'profile': request.user.userprofile,
        'tipster_stats': tipster_stats,
    })


@login_required
def edit_profile(request):
    """Edit user profile view"""
    if request.method == 'POST':
        form = ProfileEditForm(
            request.POST,
            request.FILES,
            instance=request.user.userprofile,
            user=request.user
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('users:profile')
    else:
        form = ProfileEditForm(
            instance=request.user.userprofile,
            user=request.user
        )

    return render(request, 'users/edit_profile.html', {'form': form})


@login_required
def withdraw(request):
    """
    Handle withdrawal requests to M-Pesa.
    This will be connected to M-Pesa B2C API once available.
    """
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('users:profile')

    # Check if user is a tipster
    if not request.user.userprofile.is_tipster:
        messages.error(request, 'Only tipsters can withdraw funds.')
        return redirect('users:profile')

    try:
        # Get form data
        amount = Decimal(request.POST.get('amount', '0'))
        mpesa_phone = request.POST.get('mpesa_phone', '').strip()

        # Validate amount
        if amount < Decimal('10'):
            messages.error(request, 'Minimum withdrawal amount is KES 10.')
            return redirect('users:profile')

        # Get user's current balance
        current_balance = request.user.userprofile.get_accounting_balance()

        if amount > current_balance:
            messages.error(request, f'Insufficient balance. You have KES {current_balance}.')
            return redirect('users:profile')

        # Validate phone number
        phone_pattern = r'^(254|0)[17]\d{8}$'
        if not re.match(phone_pattern, mpesa_phone):
            messages.error(request, 'Invalid M-Pesa phone number format.')
            return redirect('users:profile')

        # Normalize phone number to 254 format
        if mpesa_phone.startswith('0'):
            mpesa_phone = '254' + mpesa_phone[1:]

        # Calculate Safaricom commission (you can adjust this based on actual M-Pesa rates)
        # For now, we'll use a placeholder commission structure
        # M-Pesa withdrawal charges vary by amount:
        # 10-100: KES 11
        # 101-500: KES 28
        # 501-1000: KES 33
        # 1001-2500: KES 53
        # 2501-5000: KES 57
        # 5001-7500: KES 78
        # 7501-150000: KES 98

        if amount <= 100:
            safaricom_commission = Decimal('11')
        elif amount <= 500:
            safaricom_commission = Decimal('28')
        elif amount <= 1000:
            safaricom_commission = Decimal('33')
        elif amount <= 2500:
            safaricom_commission = Decimal('53')
        elif amount <= 5000:
            safaricom_commission = Decimal('57')
        elif amount <= 7500:
            safaricom_commission = Decimal('78')
        else:
            safaricom_commission = Decimal('98')

        # Check if user has enough balance including commission
        total_deduction = amount + safaricom_commission
        if total_deduction > current_balance:
            messages.error(
                request,
                f'Insufficient balance. Amount: KES {amount}, Fee: KES {safaricom_commission}, '
                f'Total: KES {total_deduction}, Available: KES {current_balance}.'
            )
            return redirect('users:profile')

        # Record withdrawal in accounting system
        # TODO: Connect to M-Pesa B2C API here
        # For now, we'll just record it in our system
        transaction = AccountingService.record_withdrawal(
            user=request.user,
            amount=amount,
            mpesa_phone=mpesa_phone,
            safaricom_commission=safaricom_commission
        )

        # Sync wallet balance with accounting system
        AccountingService.sync_wallet_balance(request.user)

        messages.success(
            request,
            f'Withdrawal request submitted! KES {amount} will be sent to {mpesa_phone}. '
            f'Transaction fee: KES {safaricom_commission}. '
            f'Reference: {transaction.reference}'
        )
        messages.info(
            request,
            'Note: M-Pesa B2C integration is pending. This withdrawal has been recorded but not yet processed.'
        )

    except ValueError as e:
        messages.error(request, 'Invalid amount entered.')
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')

    return redirect('users:profile')


@login_required
def transaction_history(request):
    """
    Display user's transaction history from the accounting system.
    Shows banking-style statement with running balance.
    """
    # Get date filters from query params (optional)
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Get user's transaction statement
    statement = AccountingService.get_user_statement(
        user=request.user,
        start_date=start_date,
        end_date=end_date
    )

    # Get current balance
    current_balance = request.user.userprofile.get_accounting_balance()

    context = {
        'statement': statement,
        'current_balance': current_balance,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'users/transaction_history.html', context)


def public_profile(request, user_id):
    """Public profile view for other users"""
    user = get_object_or_404(User, id=user_id)
    profile = user.userprofile

    context = {
        'profile_user': user,
        'profile': profile,
    }

    # Add additional context for tipsters
    if profile.is_tipster:
        # TODO: Add tipster stats when tips app is implemented
        context.update({
            'is_tipster': True,
            # 'total_tips': tips_count,
            # 'win_rate': win_rate,
            # 'recent_tips': recent_tips,
        })

    return render(request, 'users/public_profile.html', context)
