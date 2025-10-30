"""Management command to approve Gladys's pending tips"""
from django.core.management.base import BaseCommand
from apps.users.models import User
from apps.tips.models import Tip


class Command(BaseCommand):
    help = 'Approve all pending tips from Gladys'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n=== Approving Gladys\'s Tips ===\n'))

        try:
            # Find Gladys
            gladys = User.objects.get(username='Gladys')
            self.stdout.write(f'Found Gladys: {gladys.phone_number}')

            # Get her pending tips
            pending_tips = Tip.objects.filter(
                tipster=gladys,
                status='pending_approval'
            )

            if not pending_tips.exists():
                self.stdout.write(self.style.WARNING('\n✓ No pending tips found for Gladys'))
                return

            self.stdout.write(f'\nFound {pending_tips.count()} pending tip(s):\n')

            # Approve each tip
            for tip in pending_tips:
                self.stdout.write(f'  • Bet Code: {tip.bet_code}')
                self.stdout.write(f'    Odds: {tip.odds}')
                self.stdout.write(f'    Price: KES {tip.price}')
                self.stdout.write(f'    Created: {tip.created_at.strftime("%Y-%m-%d %H:%M")}')

                # Approve it
                tip.status = 'active'
                tip.save()

                self.stdout.write(self.style.SUCCESS(f'    ✓ Approved!\n'))

            self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully approved {pending_tips.count()} tip(s)!'))
            self.stdout.write('\nTips are now live on the marketplace.')

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('\n✗ User "Gladys" not found'))
