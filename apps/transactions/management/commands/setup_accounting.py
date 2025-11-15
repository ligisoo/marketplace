from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.transactions.models import Account
from apps.transactions.services import AccountingService
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Setup accounting system and migrate existing wallet balances'

    def add_arguments(self, parser):
        parser.add_argument(
            '--migrate-balances',
            action='store_true',
            help='Migrate existing wallet balances to accounting system',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up accounting system...'))

        # Create GL accounts
        self.stdout.write('Creating GL accounts...')
        mpesa_mirror = Account.get_mpesa_mirror_account()
        platform_revenue = Account.get_platform_revenue_account()
        safaricom_commission = Account.get_safaricom_commission_account()

        self.stdout.write(self.style.SUCCESS(f'  ✓ {mpesa_mirror.code} - {mpesa_mirror.name}'))
        self.stdout.write(self.style.SUCCESS(f'  ✓ {platform_revenue.code} - {platform_revenue.name}'))
        self.stdout.write(self.style.SUCCESS(f'  ✓ {safaricom_commission.code} - {safaricom_commission.name}'))

        # Create user wallet accounts
        self.stdout.write('\nCreating user wallet accounts...')
        users = User.objects.all()
        created_count = 0

        for user in users:
            account, created = Account.objects.get_or_create(
                user=user,
                defaults={
                    'code': f'USER_{user.id}',
                    'name': f'Wallet - {user.phone_number}',
                    'account_type': 'asset',
                    'description': f'Wallet account for user {user.phone_number}'
                }
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {created_count} new wallet accounts'))

        # Migrate existing balances if requested
        if options['migrate_balances']:
            self.stdout.write('\nMigrating existing wallet balances...')
            migrated_count = 0
            total_balance = Decimal('0')

            for user in users:
                if hasattr(user, 'userprofile') and user.userprofile.wallet_balance > 0:
                    balance = user.userprofile.wallet_balance

                    # Create deposit entry to initialize the balance
                    try:
                        AccountingService.record_deposit(
                            user=user,
                            amount=balance,
                            mpesa_receipt_number=f'MIGRATION_{user.id}'
                        )

                        migrated_count += 1
                        total_balance += balance

                        self.stdout.write(
                            f'  ✓ Migrated {user.phone_number}: KES {balance:,.2f}'
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'  ✗ Failed to migrate {user.phone_number}: {str(e)}')
                        )

            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Migrated {migrated_count} balances totaling KES {total_balance:,.2f}'
                )
            )

        # Display summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('Accounting system setup complete!'))
        self.stdout.write('='*60)

        self.stdout.write('\nGL Accounts:')
        for account in Account.objects.filter(user__isnull=True):
            balance = account.get_balance()
            self.stdout.write(f'  {account.code:20s} KES {balance:>15,.2f}')

        total_user_balances = sum(
            account.get_balance()
            for account in Account.objects.filter(user__isnull=False)
        )
        self.stdout.write(f'\nTotal User Wallet Balances: KES {total_user_balances:,.2f}')

        self.stdout.write('\nNext steps:')
        self.stdout.write('  1. Review the accounting entries in Django admin')
        self.stdout.write('  2. Verify balances match your expectations')
        self.stdout.write('  3. Use AccountingService for all future transactions')
