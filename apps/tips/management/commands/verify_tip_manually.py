from django.core.management.base import BaseCommand, CommandError
from apps.tips.models import Tip
from apps.tips.services.result_verifier import ResultVerifier
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Manually verifies the result of a specific tip by its ID.'

    def add_arguments(self, parser):
        parser.add_argument(
            'tip_id',
            type=int,
            help='The ID of the tip to verify.'
        )
        parser.add_argument(
            '--fetch-from-api',
            action='store_true',
            help='Force fetching fresh fixture data from API-Football for relevant dates.',
        )

    def handle(self, *args, **options):
        tip_id = options['tip_id']
        fetch_from_api = options['fetch_from_api']

        try:
            tip = Tip.objects.get(id=tip_id)
        except Tip.DoesNotExist:
            raise CommandError(f'Tip with ID {tip_id} does not exist.')

        self.stdout.write(f"Attempting to verify tip ID: {tip_id} (Bet Code: {tip.bet_code})...")

        verifier = ResultVerifier()

        # If fetch_from_api is true, we need to call verify_tips with the date of the tip
        # to ensure fresh data is pulled for the relevant period.
        if fetch_from_api:
            self.stdout.write(self.style.WARNING("Forcing API fetch for relevant dates..."))
            # Determine relevant dates for the tip's matches
            # For simplicity, fetch for the tip's creation date and a few days around it
            # A more robust solution might iterate through tip.matches.all() to get all unique match dates
            tip_date = tip.created_at.strftime('%Y-%m-%d')
            # The verify_tips method expects a date string and fetch_from_api boolean
            # It handles fetching for today and yesterday if date is None, but here we want specific date
            # So we call it with the tip_date
            verifier.verify_tips(date=tip_date, fetch_from_api=True)
            # Also fetch for yesterday and tomorrow to cover edge cases
            yesterday = (datetime.strptime(tip_date, '%Y-%m-%d').date() - timedelta(days=1)).strftime('%Y-%m-%d')
            tomorrow = (datetime.strptime(tip_date, '%Y-%m-%d').date() + timedelta(days=1)).strftime('%Y-%m-%d')
            verifier.verify_tips(date=yesterday, fetch_from_api=True)
            verifier.verify_tips(date=tomorrow, fetch_from_api=True)
            self.stdout.write(self.style.WARNING("API fetch complete. Proceeding with verification."))


        try:
            # Call the internal method directly to verify a single tip
            result = verifier._verify_tip(tip) 

            if result['status'] == 'verified':
                self.stdout.write(self.style.SUCCESS(
                    f"Tip {tip_id} successfully verified. "
                    f"Result: {'WON' if result['is_won'] else 'LOST'}"
                ))
                self.stdout.write(f"  Matches verified: {result['matches_verified']}")
                self.stdout.write(f"  Matches not found: {result['matches_not_found']}")
            elif result['status'] == 'pending':
                self.stdout.write(self.style.WARNING(
                    f"Tip {tip_id} remains PENDING. "
                    f"Reason: Not all matches could be verified or are not yet finished."
                ))
                self.stdout.write(f"  Matches verified: {result['matches_verified']}")
                self.stdout.write(f"  Matches not found: {result['matches_not_found']}")
            else:
                self.stdout.write(self.style.ERROR(f"Tip {tip_id} verification failed with status: {result['status']}"))

        except Exception as e:
            raise CommandError(f"An unexpected error occurred during verification: {str(e)}")
