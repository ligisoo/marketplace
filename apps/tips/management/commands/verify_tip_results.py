"""
Django management command to verify tip results using livescore data.

Usage:
    python manage.py verify_tip_results
    python manage.py verify_tip_results --date 2025-11-07
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.tips.services import ResultVerifier


class Command(BaseCommand):
    help = 'Verify tip results using livescore data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date to verify in format YYYY-MM-DD (default: today)',
            default=None
        )

    def handle(self, *args, **options):
        date = options['date']

        if date:
            self.stdout.write(f"Verifying tips for date: {date}")
        else:
            self.stdout.write(f"Verifying tips for today: {timezone.now().date()}")

        # Run verification
        verifier = ResultVerifier()
        stats = verifier.verify_tips(date=date)

        # Display results
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("VERIFICATION COMPLETE"))
        self.stdout.write("="*60)

        self.stdout.write(f"Tips checked:        {stats['tips_checked']}")
        self.stdout.write(f"Tips verified:       {stats['tips_verified']}")
        self.stdout.write(self.style.SUCCESS(f"Tips WON:            {stats['tips_won']}"))
        self.stdout.write(self.style.ERROR(f"Tips LOST:           {stats['tips_lost']}"))
        self.stdout.write(f"Tips pending:        {stats['tips_pending']}")
        self.stdout.write(f"Matches verified:    {stats['matches_verified']}")
        self.stdout.write(f"Matches not found:   {stats['matches_not_found']}")

        self.stdout.write("="*60 + "\n")

        if stats['tips_verified'] > 0:
            self.stdout.write(self.style.SUCCESS(
                f"✓ Successfully verified {stats['tips_verified']} tips"
            ))
        else:
            self.stdout.write(self.style.WARNING(
                "No tips were verified. Check if there are expired tips with results available."
            ))
