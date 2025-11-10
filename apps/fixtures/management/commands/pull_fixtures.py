from django.core.management.base import BaseCommand, CommandError
from apps.fixtures.services import APIFootballService
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Pulls fixtures from API-Football for a given date and saves them to the database.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='The date to fetch fixtures for in YYYY-MM-DD format. Defaults to today.',
            default=datetime.now().strftime('%Y-%m-%d')
        )
        parser.add_argument(
            '--days-ahead',
            type=int,
            help='Number of days ahead from the --date to fetch fixtures for. Defaults to 0 (only the specified date).',
            default=0
        )
        parser.add_argument(
            '--force-refresh',
            action='store_true',
            help='Force a refresh from the API, ignoring any cached data.',
        )

    def handle(self, *args, **options):
        date_str = options['date']
        days_ahead = options['days_ahead']
        force_refresh = options['force_refresh']

        try:
            start_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            raise CommandError('Date must be in YYYY-MM-DD format.')

        self.stdout.write(f"Pulling fixtures starting from: {start_date} for {days_ahead + 1} day(s)வுகளை...")

        service = APIFootballService()
        
        total_created = 0
        total_updated = 0

        for i in range(days_ahead + 1):
            current_date = start_date + timedelta(days=i)
            self.stdout.write(f"Processing fixtures for {current_date.strftime('%Y-%m-%d')}")

            # Check API usage before making a call
            usage_stats = service.get_api_usage_stats()
            self.stdout.write(f"  API Usage Today: {usage_stats['api_requests']}/{usage_stats['limit']} requests made.")
            if usage_stats['api_requests'] >= usage_stats['limit'] and not force_refresh:
                self.stdout.write(self.style.WARNING(
                    '  API daily limit reached. Skipping further API calls. '
                    'To bypass, use --force-refresh if you have a higher limit or wait until tomorrow.'
                ))
                # Still try to fetch from cache if available
                api_response = service.fetch_fixtures(date=current_date, use_cache=True, force_refresh=False)
                if api_response:
                    self.stdout.write(self.style.WARNING(f"  Using cached data for {current_date.strftime('%Y-%m-%d')} due to API limit."))
                else:
                    self.stdout.write(self.style.WARNING(f"  No cached data available for {current_date.strftime('%Y-%m-%d')}. Skipping."))
                    continue
            else:
                api_response = service.fetch_fixtures(date=current_date, force_refresh=force_refresh)


            if not api_response or 'response' not in api_response or not api_response['response']:
                self.stdout.write(self.style.WARNING(f"  No fixtures found or failed to fetch from API for {current_date.strftime('%Y-%m-%d')}. Skipping."))
                continue

            self.stdout.write(f"  Found {len(api_response['response'])} fixtures in API response for {current_date.strftime('%Y-%m-%d')}.")
            self.stdout.write("  Saving fixtures to the database...")

            created_count, updated_count = service.save_fixtures(api_response)
            total_created += created_count
            total_updated += updated_count
            self.stdout.write(self.style.SUCCESS(f"  {created_count} created, {updated_count} updated for {current_date.strftime('%Y-%m-%d')}."))

        self.stdout.write(self.style.SUCCESS(
            f"\nOverall: Successfully processed fixtures. "
            f"Total Created: {total_created}, Total Updated: {total_updated}"
        ))
