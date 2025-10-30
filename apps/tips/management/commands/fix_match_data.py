"""Management command to fix match market/selection data"""
from django.core.management.base import BaseCommand
from apps.tips.models import Tip, TipMatch


class Command(BaseCommand):
    help = 'Fix match market and selection data for tips'

    def add_arguments(self, parser):
        parser.add_argument(
            'bet_code',
            type=str,
            help='Bet code of the tip to fix'
        )

    def handle(self, *args, **options):
        bet_code = options['bet_code']

        self.stdout.write(f'\n=== Fixing Match Data for {bet_code} ===\n')

        try:
            tip = Tip.objects.get(bet_code=bet_code)
            matches = tip.matches.all()

            if not matches.exists():
                self.stdout.write(self.style.WARNING('No matches found for this tip'))
                return

            self.stdout.write(f'Found {matches.count()} match(es)\n')

            for i, match in enumerate(matches, 1):
                self.stdout.write(f'\nMatch {i}: {match.home_team} vs {match.away_team}')
                self.stdout.write(f'  Current Market: "{match.market}"')
                self.stdout.write(f'  Current Selection: "{match.selection}"')
                self.stdout.write(f'  Odds: {match.odds}')

                # Fix common issues
                market = match.market
                selection = match.selection

                # If market is "Home", "1", or similar, it's likely a 1X2 market
                if market in ['Home', '1', 'Away', '2', 'X', 'Draw']:
                    market = '1X2'
                    # Map the selection properly
                    if match.market == 'Home' or match.market == '1':
                        selection = 'Home Win (1)'
                    elif match.market == 'Away' or match.market == '2':
                        selection = 'Away Win (2)'
                    elif match.market == 'X':
                        selection = 'Draw (X)'

                # Clean up selection field
                if selection in ['Your Pick:', '.', '', 'KSH']:
                    # Try to infer from market or odds
                    if market == '1X2':
                        if match.odds < 2.0:
                            selection = 'Home Win (1)'
                        elif match.odds < 3.5:
                            selection = 'Away Win (2)'
                        else:
                            selection = 'Draw (X)'

                # Update match
                if market != match.market or selection != match.selection:
                    match.market = market
                    match.selection = selection
                    match.save()
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Updated to:'))
                    self.stdout.write(f'    Market: "{market}"')
                    self.stdout.write(f'    Selection: "{selection}"')
                else:
                    self.stdout.write(self.style.WARNING('  → No changes needed'))

            self.stdout.write(self.style.SUCCESS(f'\n✓ Finished processing {matches.count()} match(es)'))

        except Tip.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'\n✗ Tip "{bet_code}" not found'))
