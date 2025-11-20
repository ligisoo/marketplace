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
