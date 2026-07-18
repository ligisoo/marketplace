from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count
from django.contrib.auth import get_user_model
from apps.tips.models import Tip, TipMatch
import markdown

User = get_user_model()

def home_view(request):
    # Top analysts by number of tips posted
    top_analysts = User.objects.annotate(tip_count=Count('tips')).filter(tip_count__gt=0).order_by('-tip_count')[:4]
    
    # Upcoming distinct matches
    upcoming_matches = TipMatch.objects.filter(
        match_date__gt=timezone.now()
    ).values('home_team', 'away_team', 'match_date').distinct().order_by('match_date')[:4]
    
    # Get IDs of Top Analysts restricted to Pro
    from apps.tips.utils import get_top_analysts
    from django.conf import settings
    from django.db.models import Q
    
    top_analyst_ids = get_top_analysts()
    limit = getattr(settings, 'PRO_RESTRICTED_TOP_ANALYSTS_COUNT', 10)
    
    # Recent active insights
    recent_insights = Tip.objects.filter(status='active').order_by('-created_at')[:4]
    
    # Dynamic Platform Stats:
    # 1. Win Rate of Top 10 Analysts
    tipsters = User.objects.annotate(
        total_resulted=Count('tips', filter=Q(tips__is_resulted=True)),
        total_won=Count('tips', filter=Q(tips__is_resulted=True, tips__is_won=True))
    ).filter(total_resulted__gt=0)
    
    rates = [round((t.total_won / t.total_resulted * 100), 1) for t in tipsters]
    rates.sort(reverse=True)
    top_rates = rates[:10]
    
    if top_rates:
        win_rate_top_10 = round(sum(top_rates) / len(top_rates), 1)
    else:
        win_rate_top_10 = 78.4  # Fallback marketing stat if no resulted tips exist
        
    # 2. Active Predictions Count
    active_count = Tip.objects.filter(status='active', expires_at__gt=timezone.now()).count()
    if active_count > 0:
        active_predictions = f"{active_count:,}"
    else:
        active_predictions = "2,450+"  # Fallback marketing stat if no active predictions exist
    
    context = {
        'top_analysts': top_analysts,
        'upcoming_matches': upcoming_matches,
        'recent_insights': recent_insights,
        'top_analyst_ids': top_analyst_ids,
        'pro_restricted_limit': limit,
        'win_rate_top_10': win_rate_top_10,
        'active_predictions': active_predictions,
    }
    return render(request, 'home.html', context)

def about_view(request):
    with open('ABOUT.md', 'r') as f:
        content = f.read()
    html_content = markdown.markdown(content)
    return render(request, 'pages/about.html', {'content': html_content})

def help_center_view(request):
    with open('HELP_CENTER.md', 'r') as f:
        content = f.read()
    html_content = markdown.markdown(content)
    return render(request, 'pages/help_center.html', {'content': html_content})

def privacy_policy_view(request):
    with open('PRIVACY_POLICY.md', 'r') as f:
        content = f.read()
    html_content = markdown.markdown(content)
    return render(request, 'pages/privacy_policy.html', {'content': html_content})

def terms_of_service_view(request):
    with open('TERMS_OF_SERVICE.md', 'r') as f:
        content = f.read()
    html_content = markdown.markdown(content)
    return render(request, 'pages/terms_of_service.html', {'content': html_content})