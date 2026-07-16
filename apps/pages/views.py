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
    top_analyst_ids = get_top_analysts()
    limit = getattr(settings, 'PRO_RESTRICTED_TOP_ANALYSTS_COUNT', 10)
    
    # Recent active insights
    recent_insights = Tip.objects.filter(status='active').order_by('-created_at')[:4]
    
    context = {
        'top_analysts': top_analysts,
        'upcoming_matches': upcoming_matches,
        'recent_insights': recent_insights,
        'top_analyst_ids': top_analyst_ids,
        'pro_restricted_limit': limit,
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