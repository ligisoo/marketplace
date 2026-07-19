from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db.models import Sum, Avg, Q
from decimal import Decimal
from django.http import JsonResponse, HttpResponse
import re
from datetime import datetime
from apps.tips.models import Tip
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
    
    all_tips = Tip.objects.filter(tipster=request.user)
    resulted_tips = all_tips.filter(is_resulted=True)
    
    won_tips_count = resulted_tips.filter(is_won=True).count()
    resulted_count = resulted_tips.count()
    win_rate = round((won_tips_count / resulted_count * 100), 1) if resulted_count > 0 else 0

    analyst_stats = {
        'total_tips': all_tips.count(),
        'win_rate': win_rate,
        'won_tips': won_tips_count,
        'active_tips': all_tips.filter(status='active').count(),
    }

    return render(request, 'users/profile.html', {
        'user': request.user,
        'profile': request.user.userprofile,
        'analyst_stats': analyst_stats,
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
