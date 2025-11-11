from django import template
from django.utils.html import format_html

register = template.Library()

@register.filter
def format_timedelta(timedelta):
    if not timedelta:
        return ""
    
    hours, remainder = divmod(timedelta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    if timedelta.days > 0:
        return f"{timedelta.days}d {hours}h"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"
