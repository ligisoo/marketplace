import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()
from apps.tips.models import Tip
count = Tip.objects.filter(status='pending_approval').update(status='active')
print(f'Updated {count} tips to active')
