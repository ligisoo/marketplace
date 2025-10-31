import requests
import base64
from datetime import datetime
from django.conf import settings


class MpesaService:
    """M-Pesa API integration service for tip purchases (STK)"""

    def __init__(self):
        self.consumer_key = getattr(settings, 'MPESA_CONSUMER_KEY', '')
        self.consumer_secret = getattr(settings, 'MPESA_CONSUMER_SECRET', '')
        self.shortcode = getattr(settings, 'MPESA_SHORTCODE', '')      # should be the Till for BuyGoods
        self.till_number = getattr(settings, 'MPESA_TILL_NUMBER', '')  # should match the Till used for STK
        self.passkey = getattr(settings, 'MPESA_PASSKEY', '')
        self.env = getattr(settings, 'MPESA_ENV', 'production').lower()  # 'production' or 'sandbox'

        # Development mode if any core cred is missing
        self.dev_mode = not all([
            str(self.consumer_key).strip(),
            str(self.consumer_secret).strip(),
            str(self.shortcode).strip(),
            str(self.passkey).strip()
        ])

        # Base URLs
        base = "https://api.safaricom.co.ke" if self.env == "production" else "https://sandbox.safaricom.co.ke"
        self.auth_url = f"{base}/oauth/v1/generate?grant_type=client_credentials"
        self.stk_push_url = f"{base}/mpesa/stkpush/v1/processrequest"

        # For BuyGoods/Till STK, these MUST match and be the Till
        # If MPESA_TILL_NUMBER is set, force BusinessShortCode to it
        if self.till_number:
            self.business_shortcode = self.till_number
        else:
            self.business_shortcode = self.shortcode

        # Hard guard: BuyGoods requires BSC == PartyB and = Till
        if not self.dev_mode:
            if not self.business_shortcode or not self.business_shortcode.isdigit():
                raise ValueError("Invalid BusinessShortCode/Till. Ensure MPESA_TILL_NUMBER or MPESA_SHORTCODE is set to your Till number.")
            if self.till_number and self.business_shortcode != self.till_number:
                raise ValueError("For CustomerBuyGoodsOnline, BusinessShortCode must equal PartyB and both must be the Till number. Set MPESA_SHORTCODE=MPESA_TILL_NUMBER.")
            # At this point, for BuyGoods we consider:
            # BusinessShortCode == PartyB == Till number
            # Passkey must be for this exact Till.

    def get_access_token(self):
        """Get M-Pesa access token"""
        try:
            auth_string = f"{self.consumer_key}:{self.consumer_secret}"
            auth_base64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
            headers = {'Authorization': f'Basic {auth_base64}'}
            response = requests.get(self.auth_url, headers=headers, timeout=30)
            data = response.json()
            if response.status_code == 200 and 'access_token' in data:
                return data['access_token']
            raise Exception(f"Failed to get access token: {data}")
        except Exception as e:
            raise Exception(f"M-Pesa authentication failed: {str(e)}")

    def generate_password(self):
        """Generate M-Pesa STK password for BuyGoods (Till)"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        # IMPORTANT: password uses BusinessShortCode (the Till), not an unrelated shortcode.
        password_raw = f"{self.business_shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(password_raw.encode('utf-8')).decode('utf-8')
        return password, timestamp

    def initiate_stk_push(self, phone_number, amount, account_reference, transaction_desc, callback_url):
        """Initiate M-Pesa STK Push payment for tip purchase (BuyGoods/Till)"""

        # Development mode simulation
        if self.dev_mode:
            import uuid
            return {
                'success': True,
                'checkout_request_id': str(uuid.uuid4()),
                'merchant_request_id': f'DEV_MERCHANT_{uuid.uuid4()}',
                'customer_message': 'DEV MODE: Payment simulation - tip will be purchased automatically in 30 seconds',
                'response_code': '0',
                'response_description': 'Development mode simulation'
            }

        try:
            access_token = self.get_access_token()
            password, timestamp = self.generate_password()

            # Normalize phone -> 2547XXXXXXXX
            msisdn = phone_number.replace('+', '').replace(' ', '').replace('-', '')
            if msisdn.startswith('0'):
                msisdn = '254' + msisdn[1:]
            elif not msisdn.startswith('254'):
                msisdn = '254' + msisdn

            # Keep short per Daraja guidelines
            account_ref = (account_reference or '')[:12]
            txn_desc = (transaction_desc or '')[:20]

            payload = {
                "BusinessShortCode": self.business_shortcode,          # Till number
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerBuyGoodsOnline",
                "Amount": int(amount),
                "PartyA": msisdn,                                      # customer
                "PartyB": self.business_shortcode,                     # MUST match BSC and be the Till
                "PhoneNumber": msisdn,
                "CallBackURL": callback_url,                           # must be public HTTPS and respond 200 fast
                "AccountReference": account_ref,
                "TransactionDesc": txn_desc
            }

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            response = requests.post(self.stk_push_url, json=payload, headers=headers, timeout=30)
            try:
                data = response.json()
            except ValueError:
                data = {"raw": response.text}

            ok = (response.status_code == 200) and (data.get('ResponseCode') == '0')

            return {
                'success': ok,
                'http_status': response.status_code,
                'payload_sent': payload,
                'raw_response': data,
                'checkout_request_id': data.get('CheckoutRequestID'),
                'merchant_request_id': data.get('MerchantRequestID'),
                'customer_message': data.get('CustomerMessage'),
                'error': None if ok else (data.get('errorMessage') or data.get('ResponseDescription') or 'STK Push failed')
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"STK Push initiation failed: {str(e)}"
            }
