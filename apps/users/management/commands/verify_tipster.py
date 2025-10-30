"""Management command to verify tipsters"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.users.models import User


class Command(BaseCommand):
    help = 'Verify a tipster so their tips go live automatically'

    def add_arguments(self, parser):
        parser.add_argument(
            'identifier',
            type=str,
            help='Phone number or username of the tipster'
        )
        parser.add_argument(
            '--unverify',
            action='store_true',
            help='Remove verification status'
        )

    def handle(self, *args, **options):
        identifier = options['identifier']
        unverify = options.get('unverify', False)

        self.stdout.write(f'\nSearching for tipster: {identifier}...')

        try:
            # Try to find user by phone or username
            try:
                user = User.objects.get(phone_number=identifier)
            except User.DoesNotExist:
                user = User.objects.get(username=identifier)

            self.stdout.write(self.style.SUCCESS(f'\n✓ Found user: {user.username or user.phone_number}'))
            self.stdout.write(f'  Phone: {user.phone_number}')
            self.stdout.write(f'  Is Tipster: {user.userprofile.is_tipster}')
            self.stdout.write(f'  Currently Verified: {user.userprofile.is_verified}')

            # Check if user is a tipster
            if not user.userprofile.is_tipster:
                self.stdout.write(self.style.ERROR('\n✗ This user is not a tipster!'))
                self.stdout.write('  Only tipsters can be verified.')
                return

            # Verify or unverify
            if unverify:
                user.userprofile.is_verified = False
                user.userprofile.verification_date = None
                user.userprofile.save()
                self.stdout.write(self.style.WARNING(f'\n✓ Verification removed for {user.username or user.phone_number}'))
                self.stdout.write('  Future tips will require approval.')
            else:
                user.userprofile.is_verified = True
                user.userprofile.verification_date = timezone.now()
                user.userprofile.save()
                self.stdout.write(self.style.SUCCESS(f'\n✓ {user.username or user.phone_number} is now a verified tipster!'))
                self.stdout.write('  Future tips will go live automatically.')
                self.stdout.write(f'  Verified on: {user.userprofile.verification_date.strftime("%Y-%m-%d %H:%M")}')

            # Show tip statistics
            from apps.tips.models import Tip
            total_tips = Tip.objects.filter(tipster=user).count()
            pending = Tip.objects.filter(tipster=user, status='pending_approval').count()
            active = Tip.objects.filter(tipster=user, status='active').count()

            self.stdout.write(f'\n📊 Tip Statistics:')
            self.stdout.write(f'  Total Tips: {total_tips}')
            self.stdout.write(f'  Active: {active}')
            self.stdout.write(f'  Pending: {pending}')

            if pending > 0 and not unverify:
                self.stdout.write(self.style.WARNING(f'\n⚠ Note: {pending} tip(s) still pending approval'))
                self.stdout.write('  Run: python manage.py approve_gladys_tips')

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'\n✗ User "{identifier}" not found'))
            self.stdout.write('\nAvailable tipsters:')
            tipsters = User.objects.filter(userprofile__is_tipster=True)
            for tipster in tipsters[:10]:
                self.stdout.write(f'  • {tipster.username or tipster.phone_number} '
                                f'(verified: {tipster.userprofile.is_verified})')
