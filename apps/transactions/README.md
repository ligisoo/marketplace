# Double-Entry Accounting System

This app implements a comprehensive double-entry accounting system for the tipster marketplace, providing proper financial tracking, audit trails, and reconciliation capabilities.

## Overview

The accounting system tracks all financial transactions using standard double-entry bookkeeping principles:
- Every transaction has equal debits and credits
- User wallets are tracked as asset accounts
- Platform revenue and expenses are properly recorded
- Full audit trail for all financial movements

## Models

### Account
Represents an account in the accounting system (user wallets or GL accounts).

**Account Types:**
- `asset`: User wallets, M-Pesa mirror account
- `revenue`: Platform fee revenue
- `expense`: Safaricom withdrawal commissions

**Key GL Accounts:**
- `MPESA_MIRROR`: Mirrors the M-Pesa B2C Paybill account at Safaricom
- `PLATFORM_REVENUE`: Platform commission from tip sales (40%)
- `SAFARICOM_COMMISSION`: Withdrawal fees charged by Safaricom
- `USER_{id}`: Individual user wallet accounts

### Transaction
Groups related accounting entries together. Each transaction has:
- Unique reference number
- Transaction type (deposit, purchase, withdrawal, commission)
- Associated user
- Metadata for reconciliation

### AccountingEntry
Individual debit or credit entries that make up a transaction.
- Every entry belongs to a transaction
- Can be either debit or credit
- Links to an account
- Includes description for clarity

## Transaction Flows

### 1. Wallet Deposit (M-Pesa)
When a user deposits money via M-Pesa:
```
Debit:  User Wallet (asset ↑)
Credit: M-Pesa Mirror (asset ↓)
```

### 2. Tip Purchase (Wallet)
When a user purchases a tip using wallet balance:
```
Credit: Buyer Wallet (asset ↓)    [100%]
Debit:  Tipster Wallet (asset ↑)  [60%]
Credit: Platform Revenue (rev ↑)  [40%]
```

### 3. Tip Purchase (Direct M-Pesa)
When a user purchases a tip directly via M-Pesa:
```
Debit:  M-Pesa Mirror (asset ↑)   [100%]
Debit:  Tipster Wallet (asset ↑)  [60%]
Credit: Platform Revenue (rev ↑)  [40%]
```

### 4. Withdrawal
When a user withdraws money to M-Pesa:
```
Credit: User Wallet (asset ↓)              [total]
Debit:  M-Pesa Mirror (asset ↑)            [net to user]
Debit:  Safaricom Commission (expense ↑)   [commission]
```

## Usage

### Recording Transactions

Use the `AccountingService` class for all financial transactions:

```python
from apps.transactions.services import AccountingService

# Record a deposit
txn = AccountingService.record_deposit(
    user=user,
    amount=Decimal('100.00'),
    mpesa_receipt_number='ABC123'
)

# Record a tip purchase (wallet)
txn = AccountingService.record_tip_purchase(
    buyer=buyer,
    tipster=tipster,
    tip=tip,
    amount=tip.price
)

# Record a tip purchase (M-Pesa)
txn = AccountingService.record_tip_purchase_with_mpesa(
    buyer=buyer,
    tipster=tipster,
    tip=tip,
    amount=tip.price,
    mpesa_receipt_number='XYZ789'
)

# Record a withdrawal
txn = AccountingService.record_withdrawal(
    user=user,
    amount=Decimal('50.00'),
    mpesa_phone='254712345678',
    safaricom_commission=Decimal('5.00')
)
```

### Getting Statements

```python
# Get user wallet statement
statement = AccountingService.get_user_statement(
    user=user,
    start_date=start,
    end_date=end
)

# Get GL account statement
statement = AccountingService.get_gl_statement(
    account_code='MPESA_MIRROR',
    start_date=start,
    end_date=end
)
```

### Syncing Balances

The `wallet_balance` field on UserProfile is kept for backward compatibility but is synced with the accounting system:

```python
# Sync user's wallet_balance with accounting
accounting_balance, old_balance, difference = AccountingService.sync_wallet_balance(user)

# Get accounting balance programmatically
balance = user.userprofile.get_accounting_balance()
```

## Setup

### 1. Run Migrations
```bash
python manage.py migrate transactions
```

### 2. Setup Accounting System
```bash
# Create GL accounts and user wallet accounts
python manage.py setup_accounting

# Migrate existing wallet balances (run once only)
python manage.py setup_accounting --migrate-balances
```

### 3. Verify in Admin
Visit Django admin:
- `/admin/transactions/account/` - View all accounts and balances
- `/admin/transactions/transaction/` - View all transactions
- `/admin/transactions/accountingentry/` - View all entries

## Admin Features

The admin interface provides:
- **Accounts**: View balances, GL statements, sync wallet balances
- **Transactions**: View entries, balance verification (debits = credits)
- **Entries**: Read-only view of all accounting entries
- **Actions**: Sync wallet balances, view statements

## Reconciliation

To reconcile with M-Pesa statements:

1. Get the M-Pesa Mirror account statement from admin
2. Compare with M-Pesa B2C Paybill statement from Safaricom
3. Verify that:
   - All deposits match M-Pesa C2B transactions
   - All withdrawals match M-Pesa B2C payouts
   - Balance matches (accounting for in-flight transactions)

## Balance Integrity

The system maintains balance integrity through:
- Database constraints (unique transaction references)
- Atomic transactions (all-or-nothing commits)
- Balance validation (debits must equal credits)
- Read-only entries (prevent manual modifications)
- Void mechanism (never delete, only void transactions)

## Important Notes

1. **Never modify accounting entries directly** - Always use AccountingService
2. **Never delete transactions** - Use the void mechanism if needed
3. **Sync wallet balances** after accounting transactions to keep UserProfile.wallet_balance updated
4. **Test thoroughly** before deploying to production
5. **Backup regularly** - accounting data is critical

## Migration from Legacy System

If you have existing wallet balances:

1. Run `python manage.py setup_accounting --migrate-balances` once
2. This creates deposit entries for all existing balances
3. Verify balances in admin match your records
4. From this point forward, all transactions will use the accounting system

## Troubleshooting

**Problem**: Wallet balance doesn't match accounting balance
**Solution**: Run `AccountingService.sync_wallet_balance(user)` for the affected user

**Problem**: Transaction debits don't equal credits
**Solution**: Check the transaction in admin, review the metadata, and if necessary create a correcting entry

**Problem**: M-Pesa balance doesn't reconcile
**Solution**: Review the M-Pesa Mirror account statement, compare with Safaricom statement, identify missing transactions

## Future Enhancements

Potential improvements:
- Automated reconciliation with M-Pesa API
- Statement export (PDF, Excel)
- Custom admin views for GL statements
- Scheduled balance verification
- Email alerts for reconciliation discrepancies
