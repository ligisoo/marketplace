from django.db import models
from django.conf import settings


class AdminNotification(models.Model):
    """Notifications for admin dashboard about system events"""
    
    LEVEL_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='warning')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional link to related tip
    related_tip = models.ForeignKey(
        'tips.Tip',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='admin_notifications'
    )
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"[{self.level.upper()}] {self.title}"
