from apps.tips.models import Tip
from django.utils import timezone
print("Total Active Tips:", Tip.objects.filter(status='active', expires_at__gt=timezone.now()).count())
