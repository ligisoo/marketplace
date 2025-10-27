from django.core.management.base import BaseCommand
from apps.users.models import User, UserProfile


class Command(BaseCommand):
    help = 'Create test users for development'

    def handle(self, *args, **options):
        # Create admin user
        if not User.objects.filter(phone_number='0712345678').exists():
            admin_user = User.objects.create_user(
                phone_number='0712345678',
                username='admin',
                password='admin123',
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write(
                self.style.SUCCESS(f'Created admin user: {admin_user.phone_number}')
            )
        
        # Create test tipster
        if not User.objects.filter(phone_number='0712345679').exists():
            tipster_user = User.objects.create_user(
                phone_number='0712345679',
                username='tipster1',
                password='test123'
            )
            tipster_user.userprofile.user_type = 'tipster'
            tipster_user.userprofile.bio = 'Expert football tipster with 5+ years experience'
            tipster_user.userprofile.save()
            self.stdout.write(
                self.style.SUCCESS(f'Created tipster user: {tipster_user.phone_number}')
            )
        
        # Create test buyer
        if not User.objects.filter(phone_number='0712345680').exists():
            buyer_user = User.objects.create_user(
                phone_number='0712345680',
                username='buyer1',
                password='test123'
            )
            buyer_user.userprofile.user_type = 'buyer'
            buyer_user.userprofile.wallet_balance = 1000.00
            buyer_user.userprofile.save()
            self.stdout.write(
                self.style.SUCCESS(f'Created buyer user: {buyer_user.phone_number}')
            )
        
        self.stdout.write(
            self.style.SUCCESS('Test users created successfully!')
        )