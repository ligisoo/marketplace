from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class SubscriptionPayment(models.Model):
    """M-Pesa payment for Pro Subscriptions"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    TIER_CHOICES = [
        ('weekly', 'Weekly (KES 100)'),
        ('monthly', 'Monthly (KES 400)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscription_payments')
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='monthly')
    
    # M-Pesa specific fields
    checkout_request_id = models.CharField(max_length=100, unique=True)
    merchant_request_id = models.CharField(max_length=100)
    mpesa_receipt_number = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Response data from M-Pesa
    response_code = models.CharField(max_length=10, blank=True)
    response_description = models.CharField(max_length=200, blank=True)
    callback_data = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    idempotency_key = models.CharField(max_length=255, null=True, blank=True, db_index=True)

    def __str__(self):
        return f"Pro Subscription ({self.tier}) - {self.user.phone_number} - KES {self.amount}"

    class Meta:
        db_table = 'payments_subscription_payment'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'idempotency_key'],
                condition=models.Q(idempotency_key__isnull=False),
                name='unique_subscription_idempotency'
            ),
        ]
