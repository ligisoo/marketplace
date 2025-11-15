from django import template
from django.utils.html import format_html
from django.utils import timezone
from apps.fixtures.models import Fixture

register = template.Library()

@register.filter
def format_timedelta(timedelta):
    if not timedelta:
        return ""
    
    hours, remainder = divmod(timedelta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    if timedelta.days > 0:
        return f"{timedelta.days}d {hours}h"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


@register.simple_tag
def get_match_status(tip_match):
    """Get the current status of a match from the fixtures table"""
    try:
        # Find the corresponding fixture using the API ID
        fixture = Fixture.objects.filter(api_id=tip_match.api_match_id).first()
        
        if not fixture:
            return {
                'is_live': False,
                'is_finished': False,
                'has_started': False,
                'score': None,
                'elapsed': None,
                'status': 'Unknown'
            }
        
        # Check if match has started based on time
        now = timezone.now()
        time_based_started = tip_match.match_date <= now
        
        # Determine status based on fixture status
        live_statuses = ['1H', '2H', 'HT', 'ET', 'P', 'BT']  # Live match statuses
        finished_statuses = ['FT', 'AET', 'PEN', 'AWD', 'WO', 'ABD', 'CANC']  # Finished statuses
        
        is_live = fixture.status_short in live_statuses
        is_finished = fixture.status_short in finished_statuses
        has_started = time_based_started or is_live or is_finished
        
        # Format score if available
        score = None
        if fixture.home_goals is not None and fixture.away_goals is not None:
            score = f"{fixture.home_goals}-{fixture.away_goals}"
        
        return {
            'is_live': is_live,
            'is_finished': is_finished,
            'has_started': has_started,
            'score': score,
            'elapsed': fixture.elapsed,
            'status': fixture.status_long or fixture.status_short,
            'status_short': fixture.status_short
        }
        
    except Exception:
        # Fallback to time-based logic if fixture lookup fails
        now = timezone.now()
        time_based_started = tip_match.match_date <= now
        
        return {
            'is_live': False,
            'is_finished': False,
            'has_started': time_based_started,
            'score': None,
            'elapsed': None,
            'status': 'Unknown'
        }
