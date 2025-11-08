"""
Management command to generate payment records for tipsters based on their sales
Usage: python manage.py generate_payments --period monthly
       python manage.py generate_payments --start 2024-01-01 --end 2024-01-31
"""
from django.core.management.base import BaseCommand
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from apps.tips.models import TipsterPayment, TipPurchase, Tip
from apps.users.models import User


class Command(BaseCommand):
    help = 'Generate payment records for tipsters based on tip sales'

    def add_arguments(self, parser):
        parser.add_argument(
            '--period',
            type=str,
            choices=['weekly', 'monthly', 'custom'],
            default='monthly',
            help='Payment period (weekly, monthly, or custom)'
        )
        parser.add_argument(
            '--start',
            type=str,
            help='Start date (YYYY-MM-DD) for custom period'
        )
        parser.add_argument(
            '--end',
            type=str,
            help='End date (YYYY-MM-DD) for custom period'
        )
        parser.add_argument(
            '--tipster',
            type=str,
            help='Generate payment for specific tipster (username or phone)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview payments without creating records'
        )

    def handle(self, *args, **options):
        period = options['period']
        dry_run = options['dry_run']

        # Determine period dates
        if period == 'custom':
            if not options['start'] or not options['end']:
                self.stdout.write(self.style.ERROR(
                    'Custom period requires --start and --end dates'
                ))
                return

            period_start = datetime.strptime(options['start'], '%Y-%m-%d')
            period_end = datetime.strptime(options['end'], '%Y-%m-%d')
            period_start = timezone.make_aware(period_start)
            period_end = timezone.make_aware(period_end.replace(hour=23, minute=59, second=59))

        elif period == 'weekly':
            # Last 7 days
            period_end = timezone.now()
            period_start = period_end - timedelta(days=7)

        else:  # monthly
            # Last month
            today = timezone.now()
            first_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            period_start = (first_of_month - timedelta(days=1)).replace(day=1)
            period_end = first_of_month - timedelta(seconds=1)

        self.stdout.write(self.style.SUCCESS(
            f'\nGenerating payments for period: {period_start.strftime("%Y-%m-%d")} to {period_end.strftime("%Y-%m-%d")}\n'
        ))

        # Get tipsters with sales in this period
        purchases_in_period = TipPurchase.objects.filter(
            status='completed',
            completed_at__gte=period_start,
            completed_at__lte=period_end
        )

        # Filter by specific tipster if provided
        if options['tipster']:
            tipster_filter = options['tipster']
            purchases_in_period = purchases_in_period.filter(
                tip__tipster__username=tipster_filter
            ) | purchases_in_period.filter(
                tip__tipster__phone_number=tipster_filter
            )

        # Group by tipster
        tipster_data = purchases_in_period.values('tip__tipster').annotate(
            total_revenue=Sum('amount'),
            purchase_count=Count('id')
        )

        payment_records_created = 0
        total_amount_to_pay = 0

        self.stdout.write('\n' + '='*80)
        self.stdout.write('PAYMENT SCHEDULE REPORT')
        self.stdout.write('='*80 + '\n')

        for data in tipster_data:
            tipster = User.objects.get(id=data['tip__tipster'])
            total_revenue = data['total_revenue']
            purchase_count = data['purchase_count']

            # Calculate tipster share (60%)
            tipster_share = total_revenue * Decimal('0.60')
            platform_share = total_revenue * Decimal('0.40')

            # Count unique tips sold
            tips_sold = purchases_in_period.filter(
                tip__tipster=tipster
            ).values('tip').distinct().count()

            # Display info
            self.stdout.write(f'\nTipster: {tipster.userprofile.display_name}')
            self.stdout.write(f'  Phone: {tipster.phone_number}')
            self.stdout.write(f'  Tips Sold: {tips_sold}')
            self.stdout.write(f'  Total Purchases: {purchase_count}')
            self.stdout.write(f'  Total Revenue: KES {total_revenue:,.2f}')
            self.stdout.write(f'  Platform Share (40%): KES {platform_share:,.2f}')
            self.stdout.write(self.style.SUCCESS(
                f'  Tipster Payment (60%): KES {tipster_share:,.2f}'
            ))

            total_amount_to_pay += tipster_share

            if not dry_run:
                # Check if payment record already exists for this period
                existing_payment = TipsterPayment.objects.filter(
                    tipster=tipster,
                    period_start=period_start,
                    period_end=period_end
                ).first()

                if existing_payment:
                    self.stdout.write(self.style.WARNING(
                        f'  Status: Payment record already exists (ID: {existing_payment.id})'
                    ))
                else:
                    # Create payment record
                    payment = TipsterPayment.objects.create(
                        tipster=tipster,
                        period_start=period_start,
                        period_end=period_end,
                        total_revenue=total_revenue,
                        platform_commission=40.00,
                        tipster_share=tipster_share,
                        tips_count=tips_sold,
                        purchases_count=purchase_count,
                        status='pending'
                    )
                    payment_records_created += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'  Status: Payment record created (ID: {payment.id})'
                    ))

        self.stdout.write('\n' + '='*80)
        self.stdout.write('SUMMARY')
        self.stdout.write('='*80)
        self.stdout.write(f'Total Tipsters: {len(tipster_data)}')
        self.stdout.write(f'Total Amount to Pay: KES {total_amount_to_pay:,.2f}')

        if dry_run:
            self.stdout.write(self.style.WARNING(
                '\nDRY RUN MODE: No payment records were created.'
            ))
            self.stdout.write('Run without --dry-run to create payment records.\n')
        else:
            self.stdout.write(self.style.SUCCESS(
                f'\nSuccessfully created {payment_records_created} payment records.'
            ))
            if payment_records_created > 0:
                self.stdout.write('\nNext steps:')
                self.stdout.write('1. Go to Django Admin -> Tipster Payments')
                self.stdout.write('2. Select the payment records')
                self.stdout.write('3. Use "Export Detailed Report with Summary" action')
                self.stdout.write('4. Download the CSV file for processing payments\n')
