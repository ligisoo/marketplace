import requests
import base64
from datetime import datetime
from django.conf import settings


class MpesaService:
    """M-Pesa API integration service for tip purchases"""
    
    def __init__(self):
        self.consumer_key = getattr(settings, 'MPESA_CONSUMER_KEY', '')
        self.consumer_secret = getattr(settings, 'MPESA_CONSUMER_SECRET', '')
        self.shortcode = getattr(settings, 'MPESA_SHORTCODE', '')
        self.till_number = getattr(settings, 'MPESA_TILL_NUMBER', '')
        self.passkey = getattr(settings, 'MPESA_PASSKEY', '')
        
        # Check if we're in development mode (no M-Pesa credentials)
        self.dev_mode = not all([
            self.consumer_key and self.consumer_key.strip(),
            self.consumer_secret and self.consumer_secret.strip(), 
            self.shortcode and self.shortcode.strip(),
            self.passkey and self.passkey.strip()
        ])
        
        if not self.dev_mode:
            # M-Pesa API URLs (production)
            self.auth_url = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
            self.stk_push_url = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        
    def get_access_token(self):
        """Get M-Pesa access token"""
        try:
            # Create authorization string
            auth_string = f"{self.consumer_key}:{self.consumer_secret}"
            auth_bytes = auth_string.encode('utf-8')
            auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
            
            headers = {
                'Authorization': f'Basic {auth_base64}'
            }
            
            response = requests.get(self.auth_url, headers=headers)
            response_data = response.json()
            
            if response.status_code == 200:
                return response_data['access_token']
            else:
                raise Exception(f"Failed to get access token: {response_data}")
                
        except Exception as e:
            raise Exception(f"M-Pesa authentication failed: {str(e)}")
    
    def generate_password(self):
        """Generate M-Pesa STK push password"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_string = f"{self.shortcode}{self.passkey}{timestamp}"
        password_bytes = password_string.encode('utf-8')
        password_base64 = base64.b64encode(password_bytes).decode('utf-8')
        
        return password_base64, timestamp
    
    def initiate_stk_push(self, phone_number, amount, account_reference, transaction_desc, callback_url):
        """Initiate M-Pesa STK Push payment for tip purchase"""
        
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
            # Get access token
            access_token = self.get_access_token()
            
            # Generate password and timestamp
            password, timestamp = self.generate_password()
            
            # Format phone number to 254XXXXXXXXX format
            phone_number = phone_number.replace('+', '').replace(' ', '').replace('-', '')
            if phone_number.startswith('0'):
                phone_number = '254' + phone_number[1:]
            elif not phone_number.startswith('254'):
                phone_number = '254' + phone_number
            
            # STK Push payload for tip purchases
            payload = {
                "BusinessShortCode": self.shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerBuyGoodsOnline",
                "Amount": int(amount),
                "PartyA": phone_number,
                "PartyB": self.till_number,
                "PhoneNumber": phone_number,
                "CallBackURL": callback_url,
                "AccountReference": account_reference,
                "TransactionDesc": transaction_desc
            }
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(self.stk_push_url, json=payload, headers=headers)
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('ResponseCode') == '0':
                return {
                    'success': True,
                    'checkout_request_id': response_data.get('CheckoutRequestID'),
                    'merchant_request_id': response_data.get('MerchantRequestID'),
                    'customer_message': response_data.get('CustomerMessage'),
                    'response_code': response_data.get('ResponseCode'),
                    'response_description': response_data.get('ResponseDescription')
                }
            else:
                return {
                    'success': False,
                    'error': response_data.get('errorMessage', 'STK Push failed'),
                    'response_code': response_data.get('ResponseCode'),
                    'response_description': response_data.get('ResponseDescription')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"STK Push initiation failed: {str(e)}"
            }