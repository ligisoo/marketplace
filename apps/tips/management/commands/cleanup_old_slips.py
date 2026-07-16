from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.tips.models import Tip
from datetime import timedelta
import os

class Command(BaseCommand):
    help = 'Deletes screenshot files for expired tips older than X days to save disk space'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days', 
            type=int, 
            default=30, 
            help='Days after expiration to delete the image (default: 30)'
        )

    def handle(self, *args, **options):
        days = options['days']
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Find tips that are expired before cutoff date, and still have a screenshot
        # Using expires_at which holds the date of the last match in the slip
        old_tips = Tip.objects.filter(
            expires_at__lt=cutoff_date,
            screenshot__isnull=False
        ).exclude(screenshot='')
        
        count = 0
        bytes_saved = 0
        
        for tip in old_tips:
            if tip.screenshot:
                try:
                    file_size = tip.screenshot.size
                    # delete(save=True) deletes the physical file and sets the field to None
                    tip.screenshot.delete(save=True)
                    bytes_saved += file_size
                    count += 1
                except FileNotFoundError:
                    # File already missing from disk, just clear the DB field
                    tip.screenshot = None
                    tip.save(update_fields=['screenshot'])
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error processing tip {tip.id}: {str(e)}'))
                    
        mb_saved = bytes_saved / (1024 * 1024)
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully deleted {count} old tip images. Saved {mb_saved:.2f} MB.'
            )
        )
