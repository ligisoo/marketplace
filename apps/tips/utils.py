"""
Utility functions for tips app
"""
import logging
from datetime import datetime, timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)


def parse_match_date(date_str: str, time_str: str = None) -> datetime:
    """
    Parse match date from various formats (DD/MM/YY, DD/MM/YYYY) to datetime

    Args:
        date_str: Date string in format "DD/MM/YY" or "DD/MM/YYYY"
        time_str: Optional time string in format "HH:MM"

    Returns:
        datetime object in the timezone
    """
    try:
        if not date_str:
            # Default to tomorrow if no date
            return timezone.now() + timedelta(days=1)

        # Parse date: DD/MM/YY or DD/MM/YYYY
        date_parts = date_str.strip().split('/')
        if len(date_parts) != 3:
            logger.warning(f"Invalid date format: {date_str}, using tomorrow")
            return timezone.now() + timedelta(days=1)

        day = int(date_parts[0])
        month = int(date_parts[1])
        year = int(date_parts[2])

        # Handle 2-digit year (YY format)
        if year < 100:
            # Assume 20XX for years 00-99
            year += 2000

        # Parse time if provided
        hour = 0
        minute = 0
        if time_str:
            time_parts = time_str.strip().split(':')
            if len(time_parts) >= 2:
                hour = int(time_parts[0])
                minute = int(time_parts[1])

        # Create datetime object
        match_datetime = datetime(year, month, day, hour, minute)

        # Make timezone aware
        match_datetime = timezone.make_aware(match_datetime)

        return match_datetime

    except (ValueError, IndexError) as e:
        logger.error(f"Failed to parse date '{date_str}' time '{time_str}': {e}")
        # Fallback to tomorrow
        return timezone.now() + timedelta(days=1)

def get_top_analysts():
    """
    Returns a list of User IDs representing the top N analysts by win rate.
    Uses the same logic as the leaderboard view but optimized.
    N is determined by settings.PRO_RESTRICTED_TOP_ANALYSTS_COUNT.
    """
    from django.contrib.auth import get_user_model
    from django.conf import settings
    from apps.tips.models import Tip
    from django.db.models import Count, Q
    
    User = get_user_model()
    
    # Get tipsters who have at least one tip
    tipsters = User.objects.annotate(
        total_tips_count=Count('tips'),
        total_resulted=Count('tips', filter=Q(tips__is_resulted=True)),
        total_won=Count('tips', filter=Q(tips__is_resulted=True, tips__is_won=True))
    ).filter(total_tips_count__gt=0)
    
    leaderboard_data = []
    for tipster in tipsters:
        win_rate = round((tipster.total_won / tipster.total_resulted * 100), 1) if tipster.total_resulted > 0 else 0
        leaderboard_data.append({
            'id': tipster.id,
            'win_rate': win_rate,
            'total_tips': tipster.total_tips_count,
            'resulted_count': tipster.total_resulted
        })
        
    # Sort by win rate, then total tips (matching leaderboard logic)
    leaderboard_data.sort(
        key=lambda x: (x['resulted_count'] > 0, x['win_rate'], x['total_tips']),
        reverse=True
    )
        

    
    limit = getattr(settings, 'PRO_RESTRICTED_TOP_ANALYSTS_COUNT', 10)
    # Return top N IDs
    return [t['id'] for t in leaderboard_data[:limit]]
