"""
Security utilities for payment processing
"""
import hashlib
import hmac
import base64
import json
from django.conf import settings
from django.http import HttpResponseForbidden
from rest_framework.response import Response
from rest_framework import status
import ipaddress


class MPesaSecurityMixin:
    """Security utilities for M-Pesa callback verification"""
    
    # Safaricom's known IP ranges for M-Pesa callbacks
    SAFARICOM_IP_RANGES = [
        '196.201.214.0/24',  # Primary M-Pesa callback range
        '196.201.214.200/29',  # Secondary range
        '41.90.174.0/24',  # Additional known range
    ]
    
    def verify_mpesa_callback_ip(self, request):
        """Verify that the callback comes from Safaricom's IP ranges"""
        client_ip = self.get_client_ip(request)
        
        if not client_ip:
            return False
            
        try:
            client_ip_obj = ipaddress.ip_address(client_ip)
            for ip_range in self.SAFARICOM_IP_RANGES:
                if client_ip_obj in ipaddress.ip_network(ip_range):
                    return True
            return False
        except (ipaddress.AddressValueError, ValueError):
            return False
    
    def get_client_ip(self, request):
        """Get the real client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def verify_mpesa_signature(self, request_body, signature):
        """
        Verify M-Pesa callback signature using HMAC
        Note: This is a placeholder - actual signature verification depends on 
        Safaricom's specific implementation
        """
        if not signature or not hasattr(settings, 'MPESA_CALLBACK_SECRET'):
            return False
            
        try:
            expected_signature = hmac.new(
                settings.MPESA_CALLBACK_SECRET.encode(),
                request_body.encode() if isinstance(request_body, str) else request_body,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception:
            return False
    
    def validate_callback_structure(self, callback_data):
        """Validate that callback has required M-Pesa structure"""
        required_fields = ['Body', 'TransactionType', 'TransID', 'TransTime', 'TransAmount']
        
        try:
            if 'Body' not in callback_data:
                return False
                
            body = callback_data['Body']
            if 'stkCallback' not in body:
                return False
                
            stk_callback = body['stkCallback']
            
            # Check for required fields in STK callback
            if 'MerchantRequestID' not in stk_callback or 'CheckoutRequestID' not in stk_callback:
                return False
                
            return True
        except (KeyError, TypeError):
            return False


def mpesa_security_required(view_func):
    """Decorator to enforce M-Pesa security checks on callback views"""
    def wrapper(self, request, *args, **kwargs):
        # Skip security in development/testing
        if settings.DEBUG or getattr(settings, 'SKIP_MPESA_SECURITY', False):
            return view_func(self, request, *args, **kwargs)
        
        # Initialize security mixin
        security = MPesaSecurityMixin()
        
        # Verify IP address
        if not security.verify_mpesa_callback_ip(request):
            return Response(
                {'error': 'Unauthorized IP address'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Verify signature if present
        signature = request.META.get('HTTP_X_MPESA_SIGNATURE')
        if signature:
            request_body = request.body
            if not security.verify_mpesa_signature(request_body, signature):
                return Response(
                    {'error': 'Invalid signature'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Validate callback structure
        if hasattr(request, 'data') and request.data:
            if not security.validate_callback_structure(request.data):
                return Response(
                    {'error': 'Invalid callback structure'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return view_func(self, request, *args, **kwargs)
    
    return wrapper