from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.tips.models import Tip


class Command(BaseCommand):
    help = 'Clean up abandoned temporary tip submissions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=1,
            help='Delete temporary tips older than this many hours (default: 1)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        hours = options['hours']
        dry_run = options['dry_run']
        
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        # Find temporary tips
        temp_tips = Tip.objects.filter(
            bet_code__startswith='TEMP_',
            created_at__lt=cutoff_time
        )
        
        count = temp_tips.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS(
                f'No temporary tips older than {hours} hour(s) found.'
            ))
            return
        
        # Show what will be deleted
        self.stdout.write(f'Found {count} temporary tip(s) to delete:')
        for tip in temp_tips[:10]:  # Show first 10
            age_hours = (timezone.now() - tip.created_at).total_seconds() / 3600
            self.stdout.write(f'  - {tip.bet_code} (age: {age_hours:.1f}h, tipster: {tip.tipster.phone_number})')
        
        if count > 10:
            self.stdout.write(f'  ... and {count - 10} more')
        
        # Delete or dry run
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'DRY RUN: Would delete {count} tip(s). Run without --dry-run to actually delete.'
            ))
        else:
            temp_tips.delete()
            self.stdout.write(self.style.SUCCESS(
                f'Successfully deleted {count} temporary tip(s).'
            ))
