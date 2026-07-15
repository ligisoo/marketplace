import os
import sys

sys.path.append('/home/walter/Projects/marketplace')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from apps.tips.models import Tip
from django.utils import timezone

print("Total Tips:", Tip.objects.count())
print("Active Tips:", Tip.objects.filter(status='active').count())
print("Active and not expired:", Tip.objects.filter(status='active', expires_at__gt=timezone.now()).count())
