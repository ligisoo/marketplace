# Tipster Payment System

Complete guide for managing and processing tipster payments for revenue earned from tip sales.

## Overview

The Tipster Payment System tracks and manages payments to tipsters based on their tip sales. The platform operates on a **60/40 revenue split**:
- **Tipsters receive: 60%** of each sale
- **Platform receives: 40%** commission

## Features

1. **Automated Payment Calculation**: Automatically calculates payments based on completed purchases
2. **Flexible Payment Periods**: Generate payments for weekly, monthly, or custom date ranges
3. **Downloadable Reports**: Export payment schedules as CSV files for processing
4. **Payment Status Tracking**: Track payment status (Pending, Processing, Completed, Failed, Cancelled)
5. **Multiple Payment Methods**: Support for M-Pesa, Bank Transfer, PayPal, and other methods
6. **Audit Trail**: Track who processed payments and when

---

## Database Model

### TipsterPayment Model Fields

| Field | Type | Description |
|-------|------|-------------|
| `tipster` | ForeignKey | The tipster receiving payment |
| `period_start` | DateTime | Start of payment period |
| `period_end` | DateTime | End of payment period |
| `total_revenue` | Decimal | Total revenue from tip sales |
| `platform_commission` | Decimal | Platform commission % (default: 40%) |
| `tipster_share` | Decimal | Amount to pay tipster (60%) |
| `tips_count` | Integer | Number of unique tips sold |
| `purchases_count` | Integer | Total number of purchases |
| `status` | CharField | Payment status |
| `payment_method` | CharField | Method used (M-Pesa, Bank, etc) |
| `transaction_reference` | CharField | M-Pesa code or bank reference |
| `phone_number` | CharField | M-Pesa phone number |
| `paid_at` | DateTime | When payment was completed |
| `processed_by` | ForeignKey | Admin user who processed payment |
| `notes` | TextField | Additional payment notes |

---

## How to Use

### Step 1: Generate Payment Records

Run the management command to calculate and create payment records for a specific period:

#### Monthly Payments (Last Month)
```bash
python manage.py generate_payments --period monthly
```

#### Weekly Payments (Last 7 Days)
```bash
python manage.py generate_payments --period weekly
```

#### Custom Date Range
```bash
python manage.py generate_payments --period custom --start 2024-11-01 --end 2024-11-30
```

#### Preview Without Creating Records (Dry Run)
```bash
python manage.py generate_payments --period monthly --dry-run
```

#### Generate for Specific Tipster
```bash
python manage.py generate_payments --period monthly --tipster 0725771129
```

### Step 2: Review Payment Records in Django Admin

1. Go to **Django Admin** → **Tips** → **Tipster Payments**
2. Review the generated payment records
3. Verify amounts and tipster details
4. Filter by status, date, or tipster

### Step 3: Export Payment Schedule

Select payment records and use admin actions:

#### Option 1: Simple CSV Export
- Select payment records
- Choose action: **"Export to CSV (Downloadable)"**
- Download the CSV file

#### Option 2: Detailed Report with Summary
- Select payment records
- Choose action: **"Export Detailed Report with Summary (CSV)"**
- This includes:
  - Summary totals at the top
  - Individual payment details
  - Sorted by highest payment amount

**Report includes:**
- Tipster name and phone number
- Payment period
- Total revenue generated
- Platform commission (40%)
- Tipster payment amount (60%)
- Number of tips sold
- Number of purchases
- Payment status and method
- Transaction reference
- Notes

### Step 4: Process Payments

#### Mark as Processing
1. Select pending payment records
2. Choose action: **"Mark as Processing"**
3. This indicates you've started processing the payment

#### Complete Payment
1. Process payment via M-Pesa, bank transfer, etc.
2. Open the payment record in admin
3. Fill in:
   - Payment method (M-Pesa, Bank Transfer, etc.)
   - Transaction reference (M-Pesa code or bank reference)
   - Phone number (if M-Pesa)
   - Notes (optional)
4. Select action: **"Mark as Completed (Paid)"**
5. This automatically sets the `paid_at` timestamp

---

## Payment Workflow Example

### Scenario: Monthly Payment Run for November 2024

1. **Generate Payment Records**
   ```bash
   python manage.py generate_payments --period custom --start 2024-11-01 --end 2024-11-30
   ```

   **Output:**
   ```
   Generating payments for period: 2024-11-01 to 2024-11-30

   PAYMENT SCHEDULE REPORT
   ================================================================================

   Tipster: Gladys
     Phone: 0725771129
     Tips Sold: 15
     Total Purchases: 45
     Total Revenue: KES 4,500.00
     Platform Share (40%): KES 1,800.00
     Tipster Payment (60%): KES 2,700.00
     Status: Payment record created (ID: 1)

   Tipster: John Doe
     Phone: 0712345678
     Tips Sold: 8
     Total Purchases: 20
     Total Revenue: KES 2,000.00
     Platform Share (40%): KES 800.00
     Tipster Payment (60%): KES 1,200.00
     Status: Payment record created (ID: 2)

   SUMMARY
   ================================================================================
   Total Tipsters: 2
   Total Amount to Pay: KES 3,900.00

   Successfully created 2 payment records.
   ```

2. **Go to Django Admin**
   - Navigate to **Tipster Payments**
   - Review the 2 new payment records

3. **Export Payment Schedule**
   - Select both records
   - Action: "Export Detailed Report with Summary (CSV)"
   - Download file: `tipster_payments_excel_20241130_143022.csv`

4. **Process Payments**
   - For each tipster:
     - Send M-Pesa payment
     - Open payment record
     - Enter M-Pesa confirmation code
     - Mark as completed

---

## Admin Actions Available

| Action | Description |
|--------|-------------|
| View selected payment schedule | Shows count of selected records |
| Export to CSV (Downloadable) | Simple CSV with all payment details |
| Export Detailed Report with Summary (CSV) | CSV with totals and summary at top |
| Mark as Processing | Change status to Processing |
| Mark as Completed (Paid) | Mark payment as completed and set paid_at |
| Mark as Pending | Reset status to Pending |

---

## Payment Statuses

| Status | Description |
|--------|-------------|
| **Pending** | Payment calculated but not yet processed |
| **Processing** | Payment is being processed |
| **Completed** | Payment successfully sent to tipster |
| **Failed** | Payment attempt failed |
| **Cancelled** | Payment cancelled (e.g., refund, dispute) |

---

## Tips for Using the System

### Best Practices

1. **Run dry-run first**: Always test with `--dry-run` to preview before creating records
2. **Check for duplicates**: The system prevents duplicate payments for the same period
3. **Export before processing**: Download CSV before making payments for your records
4. **Track transaction references**: Always enter M-Pesa codes or bank references
5. **Add notes**: Use the notes field for any special circumstances

### Avoiding Double Payments

The system prevents duplicate payment records:
- Can't create multiple payments for the same tipster and same period
- If you try to regenerate, it will skip existing records

### Handling Corrections

If you need to adjust a payment:
1. Mark the incorrect payment as "Cancelled"
2. Create a new payment record manually in Django Admin
3. Add notes explaining the correction

---

## CSV Export Format

### Simple CSV Export
```csv
Tipster Name,Phone Number,Period Start,Period End,Total Revenue (KES),Platform Commission (%),Platform Amount (KES),Tipster Share (KES),Tips Sold,Total Purchases,Status,Payment Method,Transaction Reference,M-Pesa Phone,Paid Date,Notes
Gladys,0725771129,2024-11-01 00:00,2024-11-30 23:59,4500.00,40.00,1800.00,2700.00,15,45,Pending,,,,,
```

### Detailed Report with Summary
```csv
LIGISOO TIPSTER PAYMENT SCHEDULE
Generated: 2024-11-30 14:30:22
Total Records: 2

SUMMARY
Total Revenue:,KES 6,500.00
Total Tipster Payments:,KES 3,900.00
Total Platform Commission:,KES 2,600.00
Total Tips Sold:,23
Total Purchases:,65

Tipster Name,Phone Number,Period Start,Period End,Total Revenue (KES),Platform Share (KES),Tipster Share (KES),Tips Sold,Purchases,Status,Payment Method,Transaction Ref,M-Pesa Phone,Paid Date,Notes
Gladys,0725771129,2024-11-01,2024-11-30,4500.00,1800.00,2700.00,15,45,Pending,,,,,
```

---

## Technical Details

### Management Command Location
`apps/tips/management/commands/generate_payments.py`

### Admin Configuration Location
`apps/tips/admin.py` - `TipsterPaymentAdmin` class

### Model Location
`apps/tips/models.py` - `TipsterPayment` model

### Migration
`apps/tips/migrations/0004_tipsterpayment.py`

---

## Troubleshooting

### Issue: No payment records generated
**Solution**: Check if there are any completed purchases in the period
```bash
python manage.py generate_payments --period monthly --dry-run
```

### Issue: Can't create duplicate payments
**Solution**: This is intentional. If you need to regenerate, delete the existing payment records first or use a different date range.

### Issue: Revenue doesn't match expected
**Solution**:
- Verify purchases are marked as 'completed' status
- Check the date range matches your expectations
- Use `--dry-run` to see detailed breakdown

---

## Future Enhancements

Potential additions to the payment system:
- [ ] Automated M-Pesa API integration for direct payments
- [ ] Email notifications to tipsters when payments are ready
- [ ] Payment batch processing for multiple tipsters at once
- [ ] Payment history dashboard for tipsters
- [ ] Automatic payment generation on schedule (cron job)

---

## Support

For questions or issues with the payment system:
1. Check this documentation
2. Review the Django Admin payment records
3. Run commands with `--dry-run` to preview
4. Contact system administrator

---

**Last Updated**: November 2024
**Version**: 1.0
