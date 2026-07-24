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
        ('annual', 'Annual (KES 4000)'),
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


class PromoCode(models.Model):
    """Promotional / Welcome discount codes granting free Pro membership"""

    code = models.CharField(max_length=50, unique=True, db_index=True, help_text="Unique uppercase promo code (e.g. BETA2026)")
    pro_duration_days = models.PositiveIntegerField(default=30, help_text="Number of Pro membership days granted upon redemption")
    max_uses = models.PositiveIntegerField(default=100, help_text="Maximum allowed redemptions across all users")
    used_count = models.PositiveIntegerField(default=0, help_text="Total number of times redeemed")
    is_active = models.BooleanField(default=True, help_text="Whether code is active and redeemable")
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Optional expiration date for promo code")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments_promo_code'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} ({self.pro_duration_days} days) - {self.used_count}/{self.max_uses} used"

    def save(self, *args, **kwargs):
        if self.code:
            self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        """Check if promo code can be redeemed"""
        if not self.is_active:
            return False
        if self.used_count >= self.max_uses:
            return False
        if self.expires_at and self.expires_at <= timezone.now():
            return False
        return True


class PromoCodeRedemption(models.Model):
    """Tracks user redemptions of promo codes"""

    promo_code = models.ForeignKey(PromoCode, on_delete=models.CASCADE, related_name='redemptions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='promo_redemptions')
    redeemed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payments_promo_code_redemption'
        ordering = ['-redeemed_at']
        constraints = [
            models.UniqueConstraint(
                fields=['promo_code', 'user'],
                name='unique_user_promo_redemption'
            )
        ]

    def __str__(self):
        return f"{self.user} redeemed {self.promo_code.code} at {self.redeemed_at.strftime('%Y-%m-%d %H:%M')}"

