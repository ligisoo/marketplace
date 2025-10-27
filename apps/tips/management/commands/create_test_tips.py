from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.users.models import User
from apps.tips.models import Tip, TipMatch
import random


class Command(BaseCommand):
    help = 'Create test tips for development'

    def handle(self, *args, **options):
        # Get tipster user
        try:
            tipster = User.objects.get(phone_number='0712345679')
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Tipster user not found. Run create_test_users first.')
            )
            return

        # Sample data
        teams = [
            ('Manchester United', 'Liverpool', 'Premier League'),
            ('Arsenal', 'Chelsea', 'Premier League'),
            ('Real Madrid', 'Barcelona', 'La Liga'),
            ('Bayern Munich', 'Borussia Dortmund', 'Bundesliga'),
            ('AC Milan', 'Inter Milan', 'Serie A'),
            ('Gor Mahia', 'AFC Leopards', 'FKF Premier League'),
            ('Tusker FC', 'KCB FC', 'FKF Premier League'),
        ]
        
        markets = [
            ('Over 2.5 Goals', 'Over', [2.1, 2.5, 2.8]),
            ('Both Teams to Score', 'Yes', [1.8, 2.0, 2.2]),
            ('Match Result', '1', [2.5, 3.0, 3.5]),
            ('Match Result', 'X', [3.0, 3.5, 4.0]),
            ('Match Result', '2', [2.2, 2.8, 3.2]),
            ('Under 2.5 Goals', 'Under', [1.6, 1.8, 2.0]),
        ]
        
        bookmakers = ['betika', 'sportpesa', 'betin', 'mozzart', 'odibets']

        # Create 5 test tips
        for i in range(5):
            # Generate bet code
            bet_code = f'BET{random.randint(100000, 999999)}'
            
            # Skip if bet code already exists
            if Tip.objects.filter(bet_code=bet_code).exists():
                continue
            
            # Random tip data
            bookmaker = random.choice(bookmakers)
            price = random.choice([50, 100, 150, 200, 300, 500])
            num_matches = random.randint(2, 4)
            
            # Calculate total odds
            total_odds = 1.0
            tip_matches = []
            
            for j in range(num_matches):
                home_team, away_team, league = random.choice(teams)
                market, selection, odds_range = random.choice(markets)
                match_odds = random.choice(odds_range)
                total_odds *= match_odds
                
                match_date = timezone.now() + timedelta(
                    hours=random.randint(2, 48)
                )
                
                tip_matches.append({
                    'home_team': home_team,
                    'away_team': away_team,
                    'league': league,
                    'market': market,
                    'selection': selection,
                    'odds': match_odds,
                    'match_date': match_date,
                })
            
            total_odds = round(total_odds, 2)
            expires_at = max([m['match_date'] for m in tip_matches])
            
            # Create tip
            tip = Tip.objects.create(
                tipster=tipster,
                bet_code=bet_code,
                bookmaker=bookmaker,
                odds=total_odds,
                price=price,
                status='active',
                expires_at=expires_at,
                ocr_processed=True,
                ocr_confidence=85.5,
                match_details={
                    'bet_code': bet_code,
                    'total_odds': total_odds,
                    'matches': [
                        {
                            'home_team': match['home_team'],
                            'away_team': match['away_team'],
                            'league': match['league'],
                            'market': match['market'],
                            'selection': match['selection'],
                            'odds': match['odds'],
                            'match_date': match['match_date'].isoformat(),
                        }
                        for match in tip_matches
                    ],
                    'confidence': 85.5,
                    'expires_at': expires_at.isoformat()
                },
                preview_data={
                    'matches': [
                        {
                            'home_team': match['home_team'],
                            'away_team': match['away_team'],
                            'league': match['league'],
                            'market': match['market'],
                        }
                        for match in tip_matches[:2]
                    ],
                    'total_matches': len(tip_matches)
                }
            )
            
            # Create match objects
            for match_data in tip_matches:
                TipMatch.objects.create(
                    tip=tip,
                    **match_data
                )
            
            self.stdout.write(
                self.style.SUCCESS(f'Created tip: {bet_code} with {num_matches} matches')
            )
        
        self.stdout.write(
            self.style.SUCCESS('Test tips created successfully!')
        )