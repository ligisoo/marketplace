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
from apps.tips.services import ResultVerifier

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


def schedule_jobs():
    """
    Configure all scheduled jobs here.

    You can customize the schedule by modifying the intervals below.
    """

    # Run result verification every 30 minutes
    schedule.every(30).minutes.do(run_result_verification)

    # Alternative schedules (uncomment the one you prefer):

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
