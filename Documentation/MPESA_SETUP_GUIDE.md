# M-Pesa Payment Integration Guide

## 🎉 Good News!
Your M-Pesa payment system is **already fully implemented**! You just need to add your production credentials to enable live payments.

## Current Status

✅ **Completed:**
- M-Pesa service class with STK Push integration
- Payment models (TipPayment)
- Payment initiation endpoint
- Payment callback/webhook handler
- Payment status checking
- Tip purchase integration
- Development mode (works without credentials)

⏳ **Pending:**
- Add production M-Pesa credentials

---

## How to Get M-Pesa Credentials

### Step 1: Access Daraja Portal
1. Go to https://developer.safaricom.co.ke/
2. Log in or create an account
3. Navigate to "My Apps"

### Step 2: Create Production App
1. Click "Create New App"
2. Select **Production** environment
3. Select API: **Lipa Na M-Pesa Online (STK Push/Till)**
4. Fill in app details:
   - App Name: Ligisoo Tips Marketplace
   - Description: Football tips marketplace payment system

### Step 3: Get Your Credentials
After creating the app, you'll receive:
- **Consumer Key** (App Key)
- **Consumer Secret** (App Secret)

### Step 4: Get Till Number & Shortcode
1. Contact Safaricom M-Pesa Business support or your account manager
2. Request:
   - **Till Number** (your M-Pesa business till)
   - **Paybill Shortcode**
   - **Passkey** (for STK Push)

---

## Configuration Steps

### 1. Update .env File
Add your credentials to `/home/walter/marketplace/.env`:

```env
# M-Pesa Production Configuration
MPESA_CONSUMER_KEY=your_consumer_key_here
MPESA_CONSUMER_SECRET=your_consumer_secret_here
MPESA_SHORTCODE=your_paybill_shortcode_here
MPESA_TILL_NUMBER=your_till_number_here
MPESA_PASSKEY=your_passkey_here
```

### 2. Update Callback URL
The current callback URL is set to:
```
https://ligisoo.co.ke/payments/api/callback/
```

**Important:** Make sure this domain is:
- Publicly accessible (no localhost)
- HTTPS enabled (required by M-Pesa)
- Registered in your Daraja app settings

To update the callback URL, edit `/home/walter/marketplace/payments/views.py` line 91:
```python
callback_url = f"https://your-actual-domain.com/payments/api/callback/"
```

### 3. Register Callback URL in Daraja
1. Log into Daraja Portal
2. Go to your Production App
3. Navigate to "URLs" section
4. Add validation and confirmation URLs:
   - **Callback URL**: `https://ligisoo.co.ke/payments/api/callback/`

---

## Testing the Integration

### Development Mode (No Credentials)
The system currently runs in **development mode** when credentials are empty:
- Simulates payment initiation
- Returns fake checkout request IDs
- Useful for frontend testing

### Production Mode Testing

1. **Start the development server:**
```bash
python manage.py runserver
```

2. **Test payment initiation:**
```bash
curl -X POST http://localhost:8000/payments/api/initiate-tip-payment/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token_here" \
  -d '{"tip_id": 1}'
```

3. **Check payment status:**
```bash
curl http://localhost:8000/payments/api/status/CHECKOUT_REQUEST_ID/ \
  -H "Authorization: Bearer your_token_here"
```

---

## How M-Pesa Payment Flow Works

### 1. User Initiates Payment
- User clicks "Pay with M-Pesa" on tip detail page
- Frontend sends POST to `/payments/api/initiate-tip-payment/`
- Request includes tip_id

### 2. System Initiates STK Push
- Creates TipPayment record
- Calls M-Pesa API to send STK Push
- Returns checkout_request_id to frontend

### 3. User Completes Payment
- User receives STK Push prompt on phone
- User enters M-Pesa PIN
- M-Pesa processes payment

### 4. M-Pesa Sends Callback
- M-Pesa sends result to `/payments/api/callback/`
- System updates TipPayment status
- Creates TipPurchase record (if successful)
- Credits tipster wallet (60% commission)

### 5. Frontend Polls for Status
- JavaScript polls `/payments/api/status/<checkout_request_id>/`
- Shows success/failure message
- Redirects to tip detail page

---

## API Endpoints

### 1. Initiate Payment
```
POST /payments/api/initiate-tip-payment/
```

**Request:**
```json
{
  "tip_id": 1
}
```

**Response (Success):**
```json
{
  "checkout_request_id": "ws_CO_12345678901234567890",
  "merchant_request_id": "12345-67890-12345",
  "message": "Payment initiated successfully. Please complete payment on your phone.",
  "amount": "100.00",
  "tip_id": 1,
  "tip_code": "JYR***AV"
}
```

### 2. Check Payment Status
```
GET /payments/api/status/<checkout_request_id>/
```

**Response:**
```json
{
  "checkout_request_id": "ws_CO_12345678901234567890",
  "status": "completed",
  "amount": "100.00",
  "tip_id": 1,
  "tip_code": "JYR***AV",
  "mpesa_receipt_number": "PGH12345678",
  "created_at": "2025-10-30T20:00:00Z",
  "completed_at": "2025-10-30T20:01:30Z"
}
```

### 3. M-Pesa Callback (Webhook)
```
POST /payments/api/callback/
```
This is called by M-Pesa automatically - you don't need to call it manually.

---

## Payment Status Flow

```
┌─────────┐     ┌───────────┐     ┌───────────┐     ┌────────────┐
│ pending │ ──> │ completed │     │  failed   │     │ cancelled  │
└─────────┘     └───────────┘     └───────────┘     └────────────┘
     │                                   ▲                  ▲
     │                                   │                  │
     └───────────────────────────────────┴──────────────────┘
```

- **pending**: Payment initiated, waiting for user action
- **completed**: Payment successful, tip purchased
- **failed**: Payment failed (user cancelled, insufficient funds, etc.)
- **cancelled**: Payment cancelled by system

---

## Revenue Sharing

The system automatically handles revenue sharing:

1. **Buyer pays**: KES 100 (example tip price)
2. **Tipster earns**: KES 60 (60%)
3. **Platform fee**: KES 40 (40%)

This is configured in `/home/walter/marketplace/payments/views.py` line 188:
```python
tipster_earning = payment.amount * Decimal('0.6')  # 60% to tipster
```

---

## Security Considerations

✅ **Already Implemented:**
- Authentication required for payment initiation
- User can only check their own payment status
- Callback endpoint is public (required by M-Pesa)
- Duplicate purchase prevention
- Transaction ID generation

⚠️ **Additional Security (Recommended):**

1. **Enable CSRF protection for callbacks:**
   - M-Pesa callbacks may fail with CSRF
   - The callback view already uses `AllowAny` permission
   - Consider adding IP whitelist for M-Pesa servers

2. **Webhook signature verification:**
   - Verify callbacks are actually from M-Pesa
   - Check source IP against M-Pesa IP ranges

3. **Rate limiting:**
   - Add rate limiting to prevent abuse
   - Consider using Django Ratelimit

---

## Troubleshooting

### Issue: "Payment initiation failed"
**Solution:**
- Check M-Pesa credentials in .env
- Verify internet connection
- Check M-Pesa API status

### Issue: "Callback not received"
**Solution:**
- Verify callback URL is publicly accessible
- Check HTTPS is enabled
- Verify URL registered in Daraja portal
- Check server logs for callback attempts

### Issue: "Invalid phone number format"
**Solution:**
- Phone number is auto-formatted to 254XXXXXXXXX
- Ensure user phone number is valid Kenyan number
- Check user profile has phone number set

### Issue: "Development mode simulation"
**Solution:**
- This means M-Pesa credentials are not set
- Add credentials to .env file
- Restart Django server

---

## Testing Checklist

Before going live, test these scenarios:

- [ ] Successful payment flow
- [ ] Failed payment (user cancels)
- [ ] Insufficient funds
- [ ] Invalid phone number
- [ ] Already purchased tip
- [ ] Expired tip
- [ ] Callback receives and processes correctly
- [ ] Tipster wallet credited correctly
- [ ] TipPurchase record created
- [ ] Payment status polling works
- [ ] Error messages display correctly

---

## Contact & Support

### Safaricom M-Pesa Support
- Email: apisupport@safaricom.co.ke
- Phone: 0722000000
- Portal: https://developer.safaricom.co.ke/support

### Documentation
- Daraja API Docs: https://developer.safaricom.co.ke/docs
- STK Push Guide: https://developer.safaricom.co.ke/APIs/MpesaExpressSimulate

---

## Quick Start Summary

1. Get M-Pesa credentials from Daraja Portal
2. Add credentials to `.env` file
3. Update callback URL to your domain
4. Register callback URL in Daraja
5. Test with small amounts first
6. Monitor logs for any issues
7. Go live! 🚀

**Current Mode:** Development (simulation)
**To Enable Production:** Add credentials to .env and restart server

---

Generated: 2025-10-30
Marketplace: Ligisoo Tips Platform
