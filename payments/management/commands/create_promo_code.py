from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta
from payments.models import PromoCode


class Command(BaseCommand):
    help = 'Create a new promo code for free Pro membership'

    def add_arguments(self, parser):
        parser.add_argument(
            '--code',
            type=str,
            default='BETA2026',
            help='The promo code string (e.g. BETA2026)'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Pro membership duration in days (default: 30)'
        )
        parser.add_argument(
            '--max-uses',
            type=int,
            default=100,
            help='Maximum number of redemptions allowed (default: 100)'
        )
        parser.add_argument(
            '--expires-days',
            type=int,
            default=None,
            help='Optional days from now when code expires'
        )

    def handle(self, *args, **options):
        code_str = options['code'].strip().upper()
        days = options['days']
        max_uses = options['max_uses']
        expires_days = options['expires_days']

        expires_at = None
        if expires_days:
            expires_at = timezone.now() + timedelta(days=expires_days)

        promo, created = PromoCode.objects.get_or_create(
            code=code_str,
            defaults={
                'pro_duration_days': days,
                'max_uses': max_uses,
                'is_active': True,
                'expires_at': expires_at,
            }
        )

        if not created:
            # Update existing code properties
            promo.pro_duration_days = days
            promo.max_uses = max_uses
            promo.is_active = True
            if expires_at:
                promo.expires_at = expires_at
            promo.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Updated existing promo code "{promo.code}" ({days} days, max {max_uses} uses)'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ Created new promo code "{promo.code}" ({days} days, max {max_uses} uses)'))
