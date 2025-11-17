"""
Add idempotency key fields to payment models for preventing duplicate transactions
"""
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('payments', '0002_walletdeposit'),
    ]

    operations = [
        migrations.AddField(
            model_name='tippayment',
            name='idempotency_key',
            field=models.CharField(max_length=255, null=True, blank=True, db_index=True),
        ),
        migrations.AddField(
            model_name='walletdeposit',
            name='idempotency_key',
            field=models.CharField(max_length=255, null=True, blank=True, db_index=True),
        ),
        migrations.AddConstraint(
            model_name='tippayment',
            constraint=models.UniqueConstraint(
                fields=['user', 'tip', 'idempotency_key'],
                condition=models.Q(idempotency_key__isnull=False),
                name='unique_tip_payment_idempotency'
            ),
        ),
        migrations.AddConstraint(
            model_name='walletdeposit',
            constraint=models.UniqueConstraint(
                fields=['user', 'amount', 'idempotency_key'],
                condition=models.Q(idempotency_key__isnull=False),
                name='unique_wallet_deposit_idempotency'
            ),
        ),
    ]