from django.db import transaction as db_transaction
from django.utils import timezone
from decimal import Decimal
from .models import Account, Transaction, AccountingEntry


class AccountingService:
    """Service for creating double-entry accounting transactions"""

    @staticmethod
    def _create_entry(transaction, account, entry_type, amount, description):
        """Helper to create an accounting entry"""
        return AccountingEntry.objects.create(
            transaction=transaction,
            account=account,
            entry_type=entry_type,
            amount=amount,
            description=description
        )

    @staticmethod
    @db_transaction.atomic
    def record_deposit(user, amount, mpesa_receipt_number=None):
        """
        Record a wallet deposit from M-Pesa.

        Accounting entries:
        - Debit: User Wallet (asset increases)
        - Credit: M-Pesa Mirror Account (asset decreases - money leaves Safaricom account)

        Args:
            user: User making the deposit
            amount: Deposit amount
            mpesa_receipt_number: M-Pesa receipt number

        Returns:
            Transaction object
        """
        # Get accounts
        user_wallet = Account.get_or_create_user_wallet(user)
        mpesa_mirror = Account.get_mpesa_mirror_account()

        # Create transaction
        reference = f"DEP_{user.id}_{timezone.now().timestamp()}"
        if mpesa_receipt_number:
            reference = f"DEP_{mpesa_receipt_number}"

        txn = Transaction.objects.create(
            reference=reference,
            transaction_type='deposit',
            description=f'Wallet deposit via M-Pesa',
            user=user,
            amount=amount,
            metadata={
                'mpesa_receipt': mpesa_receipt_number,
                'deposit_type': 'mpesa'
            }
        )

        # Create entries
        AccountingService._create_entry(
            txn, user_wallet, 'debit', amount,
            f'Deposit to wallet via M-Pesa'
        )
        AccountingService._create_entry(
            txn, mpesa_mirror, 'credit', amount,
            f'Deposit from M-Pesa mirror account'
        )

        return txn

    @staticmethod
    @db_transaction.atomic
    def record_tip_purchase(buyer, tipster, tip, amount):
        """
        Record a tip purchase using wallet balance.

        Accounting entries:
        - Debit: Tipster Wallet (60% - asset increases)
        - Debit: Platform Revenue (40% - revenue increases via debit to revenue account)
        - Credit: Buyer Wallet (100% - asset decreases)

        Args:
            buyer: User purchasing the tip
            tipster: User who created the tip
            tip: Tip object being purchased
            amount: Purchase amount

        Returns:
            Transaction object
        """
        # Get accounts
        buyer_wallet = Account.get_or_create_user_wallet(buyer)
        tipster_wallet = Account.get_or_create_user_wallet(tipster)
        platform_revenue = Account.get_platform_revenue_account()

        # Calculate split
        platform_share = amount * Decimal('0.40')  # 40% platform
        tipster_share = amount * Decimal('0.60')   # 60% tipster

        # Create transaction
        reference = f"TIP_{tip.id}_{buyer.id}_{timezone.now().timestamp()}"

        txn = Transaction.objects.create(
            reference=reference,
            transaction_type='purchase',
            description=f'Purchase of tip {tip.bet_code}',
            user=buyer,
            amount=amount,
            metadata={
                'tip_id': tip.id,
                'bet_code': tip.bet_code,
                'tipster_id': tipster.id,
                'platform_share': str(platform_share),
                'tipster_share': str(tipster_share)
            }
        )

        # Create entries
        # Credit buyer's wallet (money out)
        AccountingService._create_entry(
            txn, buyer_wallet, 'credit', amount,
            f'Payment for tip {tip.bet_code}'
        )

        # Debit tipster's wallet (money in - 60%)
        AccountingService._create_entry(
            txn, tipster_wallet, 'debit', tipster_share,
            f'Earnings from tip {tip.bet_code} (60%)'
        )

        # Credit platform revenue (revenue in - 40%)
        # Note: For revenue accounts, credit increases the balance
        AccountingService._create_entry(
            txn, platform_revenue, 'credit', platform_share,
            f'Platform fee from tip {tip.bet_code} (40%)'
        )

        return txn

    @staticmethod
    @db_transaction.atomic
    def record_tip_purchase_with_mpesa(buyer, tipster, tip, amount, mpesa_receipt_number=None):
        """
        Record a tip purchase paid directly via M-Pesa (not using wallet).

        Accounting entries:
        - Debit: M-Pesa Mirror Account (asset increases - money comes into Safaricom account)
        - Debit: Tipster Wallet (60% - asset increases)
        - Credit: Platform Revenue (40% - revenue increases)

        Args:
            buyer: User purchasing the tip
            tipster: User who created the tip
            tip: Tip object being purchased
            amount: Purchase amount
            mpesa_receipt_number: M-Pesa receipt number

        Returns:
            Transaction object
        """
        # Get accounts
        mpesa_mirror = Account.get_mpesa_mirror_account()
        tipster_wallet = Account.get_or_create_user_wallet(tipster)
        platform_revenue = Account.get_platform_revenue_account()

        # Calculate split
        platform_share = amount * Decimal('0.40')  # 40% platform
        tipster_share = amount * Decimal('0.60')   # 60% tipster

        # Create transaction
        reference = f"TIP_MPESA_{tip.id}_{buyer.id}_{timezone.now().timestamp()}"
        if mpesa_receipt_number:
            reference = f"TIP_{mpesa_receipt_number}"

        txn = Transaction.objects.create(
            reference=reference,
            transaction_type='purchase',
            description=f'Purchase of tip {tip.bet_code} via M-Pesa',
            user=buyer,
            amount=amount,
            metadata={
                'tip_id': tip.id,
                'bet_code': tip.bet_code,
                'tipster_id': tipster.id,
                'platform_share': str(platform_share),
                'tipster_share': str(tipster_share),
                'mpesa_receipt': mpesa_receipt_number,
                'payment_method': 'mpesa'
            }
        )

        # Create entries
        # Debit M-Pesa mirror (money in from customer)
        AccountingService._create_entry(
            txn, mpesa_mirror, 'debit', amount,
            f'M-Pesa payment for tip {tip.bet_code}'
        )

        # Debit tipster's wallet (money allocated to tipster - 60%)
        AccountingService._create_entry(
            txn, tipster_wallet, 'debit', tipster_share,
            f'Earnings from tip {tip.bet_code} (60%)'
        )

        # Credit platform revenue (revenue earned - 40%)
        AccountingService._create_entry(
            txn, platform_revenue, 'credit', platform_share,
            f'Platform fee from tip {tip.bet_code} (40%)'
        )

        return txn

    @staticmethod
    @db_transaction.atomic
    def record_withdrawal(user, amount, mpesa_phone, safaricom_commission=Decimal('0')):
        """
        Record a wallet withdrawal to M-Pesa.

        Accounting entries (without commission):
        - Debit: M-Pesa Mirror Account (asset increases - money comes back to Safaricom account)
        - Credit: User Wallet (asset decreases)

        If there's a Safaricom commission:
        - Debit: Safaricom Commission (expense increases)
        - Credit: M-Pesa Mirror Account (additional asset decrease for commission)

        Args:
            user: User making the withdrawal
            amount: Withdrawal amount (net amount to user)
            mpesa_phone: M-Pesa phone number
            safaricom_commission: Commission charged by Safaricom

        Returns:
            Transaction object
        """
        # Get accounts
        user_wallet = Account.get_or_create_user_wallet(user)
        mpesa_mirror = Account.get_mpesa_mirror_account()
        safaricom_commission_account = Account.get_safaricom_commission_account()

        # Total amount withdrawn from user's wallet
        total_withdrawal = amount + safaricom_commission

        # Create transaction
        reference = f"WD_{user.id}_{timezone.now().timestamp()}"

        txn = Transaction.objects.create(
            reference=reference,
            transaction_type='withdrawal',
            description=f'Wallet withdrawal to M-Pesa {mpesa_phone}',
            user=user,
            amount=total_withdrawal,
            metadata={
                'mpesa_phone': mpesa_phone,
                'net_amount': str(amount),
                'safaricom_commission': str(safaricom_commission),
                'total_withdrawal': str(total_withdrawal)
            }
        )

        # Create entries
        # Credit user's wallet (total amount out including commission)
        AccountingService._create_entry(
            txn, user_wallet, 'credit', total_withdrawal,
            f'Withdrawal to M-Pesa {mpesa_phone}'
        )

        # Debit M-Pesa mirror (net amount sent to user)
        AccountingService._create_entry(
            txn, mpesa_mirror, 'debit', amount,
            f'Withdrawal to {mpesa_phone}'
        )

        # If there's a commission, record it as an expense
        if safaricom_commission > 0:
            AccountingService._create_entry(
                txn, safaricom_commission_account, 'debit', safaricom_commission,
                f'Safaricom withdrawal commission'
            )

        return txn

    @staticmethod
    def get_user_statement(user, start_date=None, end_date=None):
        """
        Get a banking-style statement for a user's wallet.
        Includes both wallet transactions and M-Pesa direct purchases for complete history.

        Args:
            user: User to get statement for
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of entries with running balance
        """
        user_wallet = Account.get_or_create_user_wallet(user)

        # Get all wallet entries for this account
        entries = AccountingEntry.objects.filter(
            account=user_wallet,
            is_void=False
        ).select_related('transaction').order_by('created_at')

        # Get M-Pesa direct purchases (where buyer's wallet wasn't involved)
        mpesa_purchases = Transaction.objects.filter(
            user=user,
            transaction_type='purchase',
            metadata__payment_method='mpesa'
        ).exclude(
            # Exclude if there's already a wallet entry for this transaction
            id__in=entries.values_list('transaction_id', flat=True)
        )

        # Apply date filters if provided
        if start_date:
            entries = entries.filter(created_at__gte=start_date)
            mpesa_purchases = mpesa_purchases.filter(created_at__gte=start_date)
        if end_date:
            entries = entries.filter(created_at__lte=end_date)
            mpesa_purchases = mpesa_purchases.filter(created_at__lte=end_date)

        # Build statement with running balance
        statement = []
        balance = Decimal('0')

        # Create combined list of entries and M-Pesa purchases
        items = []

        # Add wallet entries
        for entry in entries:
            items.append({
                'type': 'wallet_entry',
                'date': entry.created_at,
                'entry': entry
            })

        # Add M-Pesa purchases
        for txn in mpesa_purchases:
            items.append({
                'type': 'mpesa_purchase',
                'date': txn.created_at,
                'transaction': txn
            })

        # Sort by date
        items.sort(key=lambda x: x['date'])

        # Process items chronologically
        for item in items:
            if item['type'] == 'wallet_entry':
                entry = item['entry']
                # Update balance for wallet entries
                if entry.entry_type == 'debit':
                    balance += entry.amount
                else:  # credit
                    balance -= entry.amount

                statement.append({
                    'date': entry.created_at,
                    'reference': entry.transaction.reference,
                    'description': entry.description,
                    'debit': entry.amount if entry.entry_type == 'debit' else None,
                    'credit': entry.amount if entry.entry_type == 'credit' else None,
                    'balance': balance,
                    'transaction_type': entry.transaction.get_transaction_type_display()
                })
            else:  # mpesa_purchase
                txn = item['transaction']
                # M-Pesa purchases don't affect wallet balance, but shown for records
                statement.append({
                    'date': txn.created_at,
                    'reference': txn.reference,
                    'description': f"{txn.description} (Paid via M-Pesa)",
                    'debit': None,
                    'credit': None,  # No wallet impact
                    'balance': balance,  # Balance unchanged
                    'transaction_type': txn.get_transaction_type_display(),
                    'paid_amount': txn.amount,  # Store actual amount paid for display
                    'payment_method': 'M-Pesa'
                })

        return statement

    @staticmethod
    def get_gl_statement(account_code, start_date=None, end_date=None):
        """
        Get a statement for a GL account (e.g., M-Pesa Mirror, Platform Revenue).

        Args:
            account_code: Account code (e.g., 'MPESA_MIRROR', 'PLATFORM_REVENUE')
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of entries with running balance
        """
        try:
            account = Account.objects.get(code=account_code)
        except Account.DoesNotExist:
            return []

        # Get all entries for this account
        entries = AccountingEntry.objects.filter(
            account=account,
            is_void=False
        ).select_related('transaction').order_by('created_at')

        # Apply date filters if provided
        if start_date:
            entries = entries.filter(created_at__gte=start_date)
        if end_date:
            entries = entries.filter(created_at__lte=end_date)

        # Calculate running balance based on account type
        statement = []
        balance = Decimal('0')

        for entry in entries:
            if account.account_type in ['asset', 'expense']:
                # Debit increases, Credit decreases
                if entry.entry_type == 'debit':
                    balance += entry.amount
                else:
                    balance -= entry.amount
            else:  # revenue
                # Credit increases, Debit decreases
                if entry.entry_type == 'credit':
                    balance += entry.amount
                else:
                    balance -= entry.amount

            statement.append({
                'date': entry.created_at,
                'reference': entry.transaction.reference,
                'description': entry.description,
                'debit': entry.amount if entry.entry_type == 'debit' else None,
                'credit': entry.amount if entry.entry_type == 'credit' else None,
                'balance': balance,
                'transaction_type': entry.transaction.get_transaction_type_display()
            })

        return statement

    @staticmethod
    def sync_wallet_balance(user):
        """
        Sync the user's wallet_balance field with the accounting balance.
        This ensures the legacy wallet_balance field matches accounting records.

        Args:
            user: User to sync balance for

        Returns:
            Tuple of (accounting_balance, old_wallet_balance, difference)
        """
        wallet_account = Account.get_or_create_user_wallet(user)
        accounting_balance = wallet_account.get_balance()
        old_wallet_balance = user.userprofile.wallet_balance

        # Update the legacy field
        user.userprofile.wallet_balance = accounting_balance
        user.userprofile.save(update_fields=['wallet_balance'])

        difference = accounting_balance - old_wallet_balance

        return (accounting_balance, old_wallet_balance, difference)
