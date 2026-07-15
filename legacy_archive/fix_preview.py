import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.tips.models import Tip

for tip in Tip.objects.all():
    matches = list(tip.matches.all()[:2])
    tip.preview_data = {
        'matches': [{'home_team': m.home_team, 'away_team': m.away_team, 'league': m.league, 'market': m.market} for m in matches],
        'total_matches': tip.matches.count()
    }
    tip.save(update_fields=['preview_data'])

print('Updated preview_data for all tips!')
