from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
import string

from django.contrib.auth import get_user_model
from apps.tips.models import Tip, TipMatch

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds dummy users and tips for the homepage'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding dummy data...")
        
        # 1. Create Dummy Tipsters
        tipster_names = ['ProAnalyst_KE', 'SoccerGuru', 'OdiExpert', 'BetMaster']
        tipsters = []
        
        for i, name in enumerate(tipster_names):
            user, created = User.objects.get_or_create(username=name, defaults={
                'email': f'{name.lower()}@example.com',
                'phone_number': f'+254700{1000 + i}',
                'is_active': True,
            })
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f"Created user: {name}")
            tipsters.append(user)

        # 2. Create Dummy Tips and Matches
        bookmakers = ['betika', 'sportpesa', 'odibets', 'mozzart']
        
        for i, tipster in enumerate(tipsters):
            num_tips = (4 - i) * 5
            
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

        self.stdout.write(self.style.SUCCESS("Dummy data seeded successfully!"))
