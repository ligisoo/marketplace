I'll move the finalized prompt to a new canvas artifact for you:

```markdown
# Task: Implement Double-Entry Accounting System for Tipster Marketplace

I need help implementing a comprehensive accounting system for my tipster marketplace app. The system should handle purchases, wallet balances, withdrawals, and deposits using banking principles.

## Core Requirements:

### 1. User Account Structure
- Each user should have a wallet account that tracks their balance
- All transactions (deposits, withdrawals, purchases) must be recorded as accounting entries
- Users should be able to view a banking-style statement showing all accounting entries, including M-Pesa withdrawal commissions

### 2. Payment Methods
Users can deposit funds directly to their wallets and purchase tips using either:
- Direct M-Pesa payment
- Wallet balance

### 3. General Ledger Accounts
Create the following GL accounts:
- **M-Pesa B2C Mirror Account**: Mirrors the actual M-Pesa B2C Paybill account at Safaricom (where funds are deposited/withdrawn)
- **Safaricom Withdrawal Commission Account**: Tracks commissions charged by Safaricom for withdrawals
- **Platform Fee Revenue Account**: Tracks marketplace commission/fees earned from tips sold (40% of each tip sale)

### 4. Reconciliation Features
- Generate GL/Bank statements from the marketplace app
- Enable reconciliation of app statements with M-Pesa B2C Paybill statements from Safaricom
- Track any discrepancies between internal records and M-Pesa statements

### 5. Accounting Entries
Implement proper double-entry bookkeeping for:
- Wallet deposits (from M-Pesa)
- Tip purchases (both M-Pesa and wallet)
- Withdrawals to M-Pesa
- Commission deductions (Safaricom withdrawal fees and platform fees)
- Revenue split: 40% platform fee, 60% to tipster

## Implementation Notes:
- **Front-end Interface**: All accounting features (statements, reconciliation tools, GL reports) should be accessible through the Django admin dashboard, NOT the marketplace front-end
- Users will see their wallet balances and transaction history in the marketplace, but administrative accounting functions are admin-only

## Questions to Address:
- What's the best database schema for this accounting system?
- How should we structure the chart of accounts?
- What's the recommended approach for transaction logging to ensure audit trails?
- How can we automate the reconciliation process?

## Expected Output:
Please provide implementation guidance including database models, transaction flows, and code examples.
```

The prompt is now in the canvas and ready to use with Claude Code!