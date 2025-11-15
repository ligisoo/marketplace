from django.db import models
from django.db.models import Sum
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal


class Account(models.Model):
    """Represents an account in the double-entry accounting system"""

    ACCOUNT_TYPE_CHOICES = [
        ('asset', 'Asset'),
        ('revenue', 'Revenue'),
        ('expense', 'Expense'),
    ]

    # Account identification
    code = models.CharField(max_length=20, unique=True, help_text='Unique account code (e.g., MPESA_MIRROR, USER_1234)')
    name = models.CharField(max_length=200, help_text='Account name')
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)

    # For user wallet accounts
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='wallet_account',
        help_text='User who owns this wallet account (null for GL accounts)'
    )

    # Metadata
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']
        indexes = [
            models.Index(fields=['account_type', 'is_active']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def get_balance(self):
        """Calculate current balance based on account type and entries"""
        debits = self.entries.filter(entry_type='debit', is_void=False).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')

        credits = self.entries.filter(entry_type='credit', is_void=False).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')

        # Asset accounts: Debit increases, Credit decreases
        # Revenue accounts: Credit increases, Debit decreases
        # Expense accounts: Debit increases, Credit decreases
        if self.account_type in ['asset', 'expense']:
            return debits - credits
        else:  # revenue
            return credits - debits

    @classmethod
    def get_or_create_user_wallet(cls, user):
        """Get or create a wallet account for a user"""
        account, created = cls.objects.get_or_create(
            user=user,
            defaults={
                'code': f'USER_{user.id}',
                'name': f'Wallet - {user.phone_number}',
                'account_type': 'asset',
                'description': f'Wallet account for user {user.phone_number}'
            }
        )
        return account

    @classmethod
    def get_mpesa_mirror_account(cls):
        """Get the M-Pesa B2C Mirror GL account"""
        account, created = cls.objects.get_or_create(
            code='MPESA_MIRROR',
            defaults={
                'name': 'M-Pesa B2C Mirror Account',
                'account_type': 'asset',
                'description': 'Mirrors the actual M-Pesa B2C Paybill account at Safaricom'
            }
        )
        return account

    @classmethod
    def get_platform_revenue_account(cls):
        """Get the Platform Fee Revenue GL account"""
        account, created = cls.objects.get_or_create(
            code='PLATFORM_REVENUE',
            defaults={
                'name': 'Platform Fee Revenue',
                'account_type': 'revenue',
                'description': 'Platform commission/fees earned from tips sold (40% of each tip sale)'
            }
        )
        return account

    @classmethod
    def get_safaricom_commission_account(cls):
        """Get the Safaricom Withdrawal Commission GL account"""
        account, created = cls.objects.get_or_create(
            code='SAFARICOM_COMMISSION',
            defaults={
                'name': 'Safaricom Withdrawal Commission',
                'account_type': 'expense',
                'description': 'Commissions charged by Safaricom for withdrawals'
            }
        )
        return account


class Transaction(models.Model):
    """Represents a transaction grouping related accounting entries"""

    TRANSACTION_TYPE_CHOICES = [
        ('deposit', 'Wallet Deposit'),
        ('purchase', 'Tip Purchase'),
        ('withdrawal', 'Wallet Withdrawal'),
        ('commission', 'Commission'),
    ]

    # Transaction identification
    reference = models.CharField(max_length=100, unique=True, help_text='Unique transaction reference')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    description = models.TextField()

    # Related objects
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions',
        help_text='Primary user involved in the transaction'
    )

    # Financial details
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Status
    is_void = models.BooleanField(default=False, help_text='Whether this transaction has been voided')
    void_reason = models.TextField(blank=True)
    voided_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    metadata = models.JSONField(default=dict, blank=True, help_text='Additional transaction data')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_transactions'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'transaction_type']),
            models.Index(fields=['transaction_type', 'created_at']),
            models.Index(fields=['reference']),
        ]

    def __str__(self):
        return f"{self.reference} - {self.get_transaction_type_display()} - KES {self.amount}"

    def clean(self):
        """Validate that debits equal credits"""
        if self.pk:
            debits = self.entries.filter(entry_type='debit', is_void=False).aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0')

            credits = self.entries.filter(entry_type='credit', is_void=False).aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0')

            if debits != credits:
                raise ValidationError(f'Debits ({debits}) must equal credits ({credits})')

    def void(self, reason=''):
        """Void this transaction and all its entries"""
        self.is_void = True
        self.void_reason = reason
        self.voided_at = timezone.now()
        self.save()

        # Void all entries
        self.entries.update(is_void=True)


class AccountingEntry(models.Model):
    """Represents a single debit or credit entry in the accounting system"""

    ENTRY_TYPE_CHOICES = [
        ('debit', 'Debit'),
        ('credit', 'Credit'),
    ]

    # Entry details
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='entries')
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPE_CHOICES)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='entries')
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Description
    description = models.CharField(max_length=500)

    # Status
    is_void = models.BooleanField(default=False)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Accounting Entries'
        indexes = [
            models.Index(fields=['account', 'entry_type']),
            models.Index(fields=['transaction', 'entry_type']),
        ]

    def __str__(self):
        return f"{self.get_entry_type_display()} - {self.account.code} - KES {self.amount}"

    def save(self, *args, **kwargs):
        # Ensure amount is positive
        if self.amount < 0:
            raise ValidationError('Amount must be positive')
        super().save(*args, **kwargs)
