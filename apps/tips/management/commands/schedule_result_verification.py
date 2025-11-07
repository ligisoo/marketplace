"""
Django management command to run scheduled result verification.

This command should be run via cron or a task scheduler.

Recommended schedule:
    */30 * * * * - Every 30 minutes (to catch finished matches)
    0 * * * * - Every hour
    0 0,12,18,22 * * * - At specific times (midnight, noon, 6pm, 10pm)

Usage:
    python manage.py schedule_result_verification
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.tips.services import ResultVerifier
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Scheduled task to automatically verify tip results'

    def handle(self, *args, **options):
        logger.info("="*60)
        logger.info("SCHEDULED RESULT VERIFICATION STARTED")
        logger.info(f"Time: {timezone.now()}")
        logger.info("="*60)

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
                self.stdout.write(self.style.SUCCESS(
                    f"✓ Verified {stats['tips_verified']} tips "
                    f"({stats['tips_won']} won, {stats['tips_lost']} lost)"
                ))
            else:
                logger.info("No tips verified in this run")

        except Exception as e:
            logger.error(f"Error during scheduled verification: {str(e)}", exc_info=True)
            self.stdout.write(self.style.ERROR(f"✗ Error: {str(e)}"))

        logger.info("="*60)
        logger.info("SCHEDULED RESULT VERIFICATION COMPLETED")
        logger.info("="*60)
