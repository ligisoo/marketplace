"""
Custom throttle classes for payment endpoints
"""
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class PaymentInitiationThrottle(UserRateThrottle):
    """
    Throttle class for payment initiation endpoints
    Limits payment requests to prevent abuse
    """
    scope = 'payment_initiation'


class CallbackThrottle(AnonRateThrottle):
    """
    Throttle class for M-Pesa callback endpoints
    Higher limits but still protected against abuse
    """
    scope = 'callback'