import os
import django
from django.utils import timezone
from datetime import timedelta
import random
import string

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.tips.models import Tip, TipMatch

User = get_user_model()

def run():
    print("Seeding dummy data...")
    
    # 1. Create Dummy Tipsters
    tipster_names = ['ProAnalyst_KE', 'SoccerGuru', 'OdiExpert', 'BetMaster']
    tipsters = []
    
    for name in tipster_names:
        user, created = User.objects.get_or_create(username=name, defaults={
            'email': f'{name.lower()}@example.com',
            'is_active': True,
        })
        if created:
            user.set_password('password123')
            user.save()
            print(f"Created user: {name}")
        tipsters.append(user)

    # 2. Create Dummy Tips and Matches for them to become "Top Analysts" and show "Recent Insights"
    bookmakers = ['betika', 'sportpesa', 'odibets', 'mozzart']
    
    for i, tipster in enumerate(tipsters):
        # Give them some tips so they show up in Top Analysts
        num_tips = (4 - i) * 5  # 20, 15, 10, 5 tips
        
        for j in range(num_tips):
            bet_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            tip, t_created = Tip.objects.get_or_create(
                tipster=tipster,
                bet_code=bet_code,
                defaults={
                    'bookmaker': random.choice(bookmakers),
                    'odds': round(random.uniform(2.0, 15.0), 2),
                    'status': 'active',
                    'expires_at': timezone.now() + timedelta(days=1),
                    'ocr_processed': True,
                }
            )
            
            # 3. Create Upcoming Matches (only for a few tips so we get hot upcoming matches)
            if t_created and j < 2:
                teams = [
                    ('Arsenal', 'Chelsea'),
                    ('Man United', 'Liverpool'),
                    ('Real Madrid', 'Barcelona'),
                    ('Gor Mahia', 'AFC Leopards'),
                    ('Tusker FC', 'Kenya Police'),
                    ('Bayern Munich', 'Dortmund')
                ]
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

    print("Dummy data seeded successfully!")

if __name__ == '__main__':
    run()
