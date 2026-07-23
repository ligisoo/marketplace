#!/usr/bin/env python
"""
Continuous scheduler for automated tip result verification.

This script runs as a daemon and executes scheduled tasks using the
Python `schedule` library instead of cron.

Usage:
    python run_scheduler.py

To run in background:
    nohup python run_scheduler.py &

Or use systemd service (recommended for production)
"""

import os
import sys
import django
import schedule
import time
import logging
from pathlib import Path
from datetime import datetime

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from django.utils import timezone
from django.core import management
from apps.tips.services import ResultVerifier
from apps.tips.models import Tip
from apps.fixtures.services import APIFootballService
from datetime import timedelta, date as dt_date

# Configure logging
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'tip_scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def run_result_verification():
    """
    Execute the tip result verification task.
    This is the same logic as the management command.
    """
    logger.info("=" * 60)
    logger.info("SCHEDULED RESULT VERIFICATION STARTED")
    logger.info(f"Time: {timezone.now()}")
    logger.info("=" * 60)

    try:
        # Verify today's tips
        verifier = ResultVerifier()
        stats = verifier.verify_tips()

        logger.info("VERIFICATION STATS:")
        logger.info(f"  Tips checked: {stats['tips_checked']}")
        logger.info(f"  Tips verified: {stats['tips_verified']}")
        logger.info(f"  Tips WON: {stats['tips_won']}")
        logger.info(f"  Tips LOST: {stats['tips_lost']}")
        logger.info(f"  Tips pending: {stats['tips_pending']}")
        logger.info(f"  Matches verified: {stats['matches_verified']}")
        logger.info(f"  Matches not found: {stats['matches_not_found']}")

        if stats['tips_verified'] > 0:
            logger.info(
                f"✓ Verified {stats['tips_verified']} tips "
                f"({stats['tips_won']} won, {stats['tips_lost']} lost)"
            )
        else:
            logger.info("No tips verified in this run")

    except Exception as e:
        logger.error(f"Error during scheduled verification: {str(e)}", exc_info=True)

    logger.info("=" * 60)
    logger.info("SCHEDULED RESULT VERIFICATION COMPLETED")
    logger.info("=" * 60)
    logger.info("")  # Blank line for readability


def cleanup_temp_tips():
    """
    Clean up abandoned temporary tip submissions.
    Deletes tips with bet_code starting with 'TEMP_' that are older than 1 hour.
    """
    logger.info("=" * 60)
    logger.info("TEMP TIP CLEANUP STARTED")
    logger.info(f"Time: {timezone.now()}")
    logger.info("=" * 60)

    try:
        hours = 1  # Delete temp tips older than 1 hour
        cutoff_time = timezone.now() - timedelta(hours=hours)

        # Find temporary tips
        temp_tips = Tip.objects.filter(
            bet_code__startswith='TEMP_',
            created_at__lt=cutoff_time
        )

        count = temp_tips.count()

        if count == 0:
            logger.info(f"No temporary tips older than {hours} hour(s) found")
        else:
            logger.info(f"Found {count} temporary tip(s) to delete")

            # Log first few for reference
            for tip in temp_tips[:5]:
                age_hours = (timezone.now() - tip.created_at).total_seconds() / 3600
                logger.info(f"  - {tip.bet_code} (age: {age_hours:.1f}h)")

            if count > 5:
                logger.info(f"  ... and {count - 5} more")

            # Delete temp tips
            temp_tips.delete()
            logger.info(f"✓ Successfully deleted {count} temporary tip(s)")

    except Exception as e:
        logger.error(f"Error during temp tip cleanup: {str(e)}", exc_info=True)

    logger.info("=" * 60)
    logger.info("TEMP TIP CLEANUP COMPLETED")
    logger.info("=" * 60)
    logger.info("")  # Blank line for readability


def fetch_upcoming_fixtures():
    """
    Fetch upcoming fixtures for the next 3 days.
    Runs once per day to minimize API usage.
    """
    logger.info("=" * 60)
    logger.info("UPCOMING FIXTURES FETCH STARTED")
    logger.info(f"Time: {timezone.now()}")
    logger.info("=" * 60)

    try:
        api_service = APIFootballService()

        # Get API usage stats
        stats = api_service.get_api_usage_stats()
        logger.info(f"API Usage: {stats['api_requests']}/{stats['limit']} requests today")
        logger.info(f"Remaining: {stats['remaining']} requests")

        if stats['remaining'] < 10:
            logger.warning("API limit nearly reached, skipping upcoming fixtures fetch")
            return

        # Fetch fixtures for next 3 days
        total_created = 0
        total_updated = 0

        for days_ahead in range(3):
            fetch_date = (datetime.now().date() + timedelta(days=days_ahead))

            if not api_service._can_make_request():
                logger.warning(f"API limit reached, stopped at day {days_ahead}")
                break

            logger.info(f"Fetching fixtures for {fetch_date}")
            response = api_service.fetch_fixtures(date=fetch_date)

            if response:
                created, updated = api_service.save_fixtures(response)
                total_created += created
                total_updated += updated
                logger.info(f"  {fetch_date}: {created} created, {updated} updated")

        logger.info(f"✓ Total: {total_created} created, {total_updated} updated")

    except Exception as e:
        logger.error(f"Error fetching upcoming fixtures: {str(e)}", exc_info=True)

    logger.info("=" * 60)
    logger.info("UPCOMING FIXTURES FETCH COMPLETED")
    logger.info("=" * 60)
    logger.info("")


def fetch_live_fixtures():
    """
    Fetch currently live fixtures from API-Football for real-time score updates.
    Optimized: Only queries the API if there are active tips with matches currently playing.
    """
    logger.info("=" * 60)
    logger.info("LIVE FIXTURES API FETCH STARTED")
    logger.info(f"Time: {timezone.now()}")
    logger.info("=" * 60)

    try:
        from apps.tips.models import TipMatch
        from datetime import timedelta
        
        now = timezone.now()
        # Check if any active tip has matches that kicked off in the last 3.5 hours, or start in next 15 mins
        has_active_matches = TipMatch.objects.filter(
            tip__status='active',
            match_date__gte=now - timedelta(hours=3, minutes=30),
            match_date__lte=now + timedelta(minutes=15)
        ).exists()

        if not has_active_matches:
            logger.info("No active matches in tips currently playing. Skipping API-Football fetch to save quota.")
            logger.info("=" * 60)
            logger.info("LIVE FIXTURES API FETCH COMPLETED (SKIPPED)")
            logger.info("=" * 60)
            logger.info("")
            return

        from apps.fixtures.services import APIFootballService
        api_service = APIFootballService()

        # Check API-Football usage
        stats = api_service.get_api_usage_stats()
        logger.info(f"API Usage: {stats['api_requests']}/{stats['limit']} requests today")

        if stats['remaining'] >= 5:
            logger.info("Fetching live fixtures from API-Football...")
            response = api_service.fetch_live_fixtures()
            if response:
                created, updated = api_service.save_fixtures(response)
                logger.info(f"✓ API-Football: {created} created, {updated} updated")
        else:
            logger.warning("API limit nearly reached, skipping API fetch")

        # Log currently live matches in DB
        from apps.fixtures.models import Fixture
        live_matches = Fixture.objects.filter(status_short__in=['1H', '2H', 'HT', 'ET', 'P'])[:5]
        if live_matches.exists():
            logger.info("Currently live matches in DB:")
            for match in live_matches:
                logger.info(f"  {match.home_team.name} {match.home_goals}-{match.away_goals} {match.away_team.name} ({match.status_short})")

    except Exception as e:
        logger.error(f"Error fetching live fixtures: {str(e)}", exc_info=True)

    logger.info("=" * 60)
    logger.info("LIVE FIXTURES API FETCH COMPLETED")
    logger.info("=" * 60)
    logger.info("")


def scrape_live_fixtures():
    """
    Scrape real-time scores using the free scraper.
    Runs frequently without consuming API quota.
    """
    logger.info("=" * 60)
    logger.info("FREE SCRAPER RUN STARTED")
    logger.info(f"Time: {timezone.now()}")
    logger.info("=" * 60)

    try:
        from apps.fixtures.services import LivescoreCzScraper
        logger.info("Scraping real-time scores from livescore.cz...")
        scraper = LivescoreCzScraper()
        scrape_stats = scraper.scrape_and_sync()
        logger.info(
            f"✓ Livescore.cz: {scrape_stats['scraped']} matches scraped, "
            f"{scrape_stats['updated']} updated, {scrape_stats['created']} created in DB"
        )
    except Exception as e:
        logger.error(f"Error in free scraper run: {str(e)}", exc_info=True)

    logger.info("=" * 60)
    logger.info("FREE SCRAPER RUN COMPLETED")
    logger.info("=" * 60)
    logger.info("")


def run_tip_archiving():
    """
    Archives expired active tips.
    """
    logger.info("=" * 60)
    logger.info("TIP ARCHIVING STARTED")
    logger.info(f"Time: {timezone.now()}")
    logger.info("=" * 60)

    try:
        expired_tips = Tip.objects.filter(
            status='active',
            expires_at__lte=timezone.now()
        )
        
        archived_count = 0
        for tip in expired_tips:
            tip.auto_archive_if_expired()
            archived_count += 1
        
        logger.info(f"Archived {archived_count} expired tips.")

    except Exception as e:
        logger.error(f"Error during tip archiving: {str(e)}", exc_info=True)

    logger.info("=" * 60)
    logger.info("TIP ARCHIVING COMPLETED")
    logger.info("=" * 60)
    logger.info("")


def run_stuck_match_recovery():
    """
    Detect and recover matches that appear to be stuck in live status.
    """
    logger.info("=" * 60)
    logger.info("STUCK MATCH RECOVERY STARTED")
    logger.info(f"Time: {timezone.now()}")
    logger.info("=" * 60)

    try:
        api_service = APIFootballService()
        
        # Get API usage stats first
        stats = api_service.get_api_usage_stats()
        logger.info(f"API Usage: {stats['api_requests']}/{stats['limit']} requests today")
        logger.info(f"Remaining: {stats['remaining']} requests")

        # Only run if we have sufficient API quota
        if stats['remaining'] < 10:
            logger.warning("Insufficient API quota for stuck match recovery (need at least 10)")
            return
            
        # Run stuck match recovery
        recovery_stats = api_service.run_stuck_match_recovery()
        
        logger.info("RECOVERY STATS:")
        logger.info(f"  Stuck matches found: {recovery_stats['stuck_matches_found']}")
        logger.info(f"  Successfully recovered: {recovery_stats['recovered_successfully']}")
        logger.info(f"  Recovery failed: {recovery_stats['recovery_failed']}")
        logger.info(f"  API requests used: {recovery_stats['api_requests_used']}")
        
        if recovery_stats['recovered_successfully'] > 0:
            logger.info(f"✓ Successfully recovered {recovery_stats['recovered_successfully']} stuck matches")
        elif recovery_stats['stuck_matches_found'] == 0:
            logger.info("No stuck matches found - all good!")
        else:
            logger.warning(f"Found {recovery_stats['stuck_matches_found']} stuck matches but recovery failed")

    except Exception as e:
        logger.error(f"Error during stuck match recovery: {str(e)}", exc_info=True)

    logger.info("=" * 60)
    logger.info("STUCK MATCH RECOVERY COMPLETED")
    logger.info("=" * 60)
    logger.info("")


def schedule_jobs():
    """
    Configure all scheduled jobs here.

    You can customize the schedule by modifying the intervals below.
    """

    # Job 1: Fetch upcoming fixtures once per day at 3 AM
    # API Usage: 3 calls per day (fetches 3 days ahead)
    schedule.every().day.at("03:00").do(fetch_upcoming_fixtures)

    # Job 2: Fetch live fixtures from API every 15 minutes (only runs when active tips have matches playing)
    schedule.every(15).minutes.do(fetch_live_fixtures)

    # Job 3: Scrape live scores from free source every 10 minutes (unconditional & free)
    schedule.every(10).minutes.do(scrape_live_fixtures)

    # Job 4: Run result verification every 15 minutes (without API fetch, use DB only)
    schedule.every(15).minutes.do(run_result_verification)

    # Job 5: Clean up temporary tips every hour
    schedule.every().hour.do(cleanup_temp_tips)

    # Job 6: Archive expired tips every hour
    schedule.every().hour.do(run_tip_archiving)

    # Job 7: Detect and recover stuck matches every 30 minutes (offset from live fixtures)
    schedule.every(30).minutes.do(run_stuck_match_recovery)

    # Alternative schedules for result verification (uncomment the one you prefer):

    # Every hour
    # schedule.every().hour.do(run_result_verification)

    # Every hour at :30 minutes past
    # schedule.every().hour.at(":30").do(run_result_verification)

    # Every day at specific times
    # schedule.every().day.at("22:00").do(run_result_verification)  # 10 PM
    # schedule.every().day.at("00:00").do(run_result_verification)  # Midnight
    # schedule.every().day.at("12:00").do(run_result_verification)  # Noon

    # Every 2 hours
    # schedule.every(2).hours.do(run_result_verification)

    logger.info("Scheduler configured with the following jobs:")
    for job in schedule.get_jobs():
        logger.info(f"  - {job}")


def main():
    """Main scheduler loop"""
    logger.info("=" * 60)
    logger.info("TIP RESULT VERIFICATION SCHEDULER STARTING")
    logger.info(f"Started at: {datetime.now()}")
    logger.info("=" * 60)

    # Configure scheduled jobs
    schedule_jobs()

    logger.info("Scheduler is running. Press Ctrl+C to stop.")
    logger.info("")

    # Run the scheduler loop
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)  # Check every second

    except KeyboardInterrupt:
        logger.info("")
        logger.info("=" * 60)
        logger.info("SCHEDULER STOPPED BY USER")
        logger.info(f"Stopped at: {datetime.now()}")
        logger.info("=" * 60)
        sys.exit(0)

    except Exception as e:
        logger.error(f"Scheduler crashed: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
