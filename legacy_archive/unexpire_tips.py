import os
import sys

sys.path.append('/home/walter/Projects/marketplace')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from apps.tips.models import Tip
from django.utils import timezone
from datetime import timedelta

print("Total Tips:", Tip.objects.count())
active = Tip.objects.filter(status='active')
print("Active Tips:", active.count())
print("Active and not expired:", active.filter(expires_at__gt=timezone.now()).count())

# Unexpire them
updated = active.update(expires_at=timezone.now() + timedelta(days=2))
print("Extended expiration for", updated, "active tips.")
