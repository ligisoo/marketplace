import os
import django
import random
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.tips.models import Tip, TipMatch

teams = [
    ('Arsenal', 'Chelsea'),
    ('Man United', 'Liverpool'),
    ('Real Madrid', 'Barcelona'),
    ('Gor Mahia', 'AFC Leopards'),
    ('Tusker FC', 'Kenya Police'),
    ('Bayern Munich', 'Dortmund'),
    ('Juventus', 'AC Milan'),
    ('PSG', 'Marseille'),
    ('Ajax', 'PSV Eindhoven'),
    ('Boca Juniors', 'River Plate')
]

for tip in Tip.objects.all():
    # Only add more matches if it currently has 1
    if tip.matches.count() == 1:
        for _ in range(2):
            home, away = random.choice(teams)
            TipMatch.objects.create(
                tip=tip,
                home_team=home,
                away_team=away,
                league='Premier League',
                match_date=timezone.now() + timedelta(hours=random.randint(2, 48)),
                market='1X2',
                selection=random.choice(['1', 'X', '2']),
                odds=round(random.uniform(1.5, 3.5), 2)
            )
        
    # Update preview data
    matches = list(tip.matches.all())
    tip.preview_data = {
        'matches': [{'home_team': m.home_team, 'away_team': m.away_team, 'league': m.league, 'market': m.market} for m in matches],
        'total_matches': len(matches)
    }
    tip.save(update_fields=['preview_data'])

print('Added matches and updated preview_data for all tips!')
