import uuid
import json
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import SubscriptionPayment
from .services import MpesaService
from .security import mpesa_security_required
from .throttles import PaymentInitiationThrottle, CallbackThrottle
from apps.users.models import UserProfile

User = get_user_model()


class InitiateSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [PaymentInitiationThrottle]
    
    def post(self, request):
        """Initiate M-Pesa STK Push payment for Pro Subscription"""
        data = request.data
        
        # Check if user has a phone number
        if not request.user.phone_number:
            return Response(
                {'error': 'Phone number is required. Please update your profile first.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate required fields
        tier = data.get('tier', 'monthly')
        idempotency_key = data.get('idempotency_key')
        
        if tier not in ['weekly', 'monthly', 'annual']:
            return Response(
                {'error': 'Invalid subscription tier. Choose weekly, monthly, or annual.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if not idempotency_key:
            return Response(
                {'error': 'idempotency_key is required to prevent duplicate payments'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if tier == 'weekly':
            amount = settings.SUBSCRIPTION_PRICE_WEEKLY
        elif tier == 'monthly':
            amount = settings.SUBSCRIPTION_PRICE_MONTHLY
        else:
            amount = settings.SUBSCRIPTION_PRICE_ANNUAL
        
        # Check for idempotency - return existing payment if same key used
        try:
            existing_payment = SubscriptionPayment.objects.get(
                user=request.user, 
                idempotency_key=idempotency_key
            )
            return Response({
                'message': 'Payment already initiated with this idempotency key',
                'checkout_request_id': existing_payment.checkout_request_id,
                'status': existing_payment.status,
                'merchant_request_id': existing_payment.merchant_request_id
            })
        except SubscriptionPayment.DoesNotExist:
            pass
        
        try:
            # Generate unique checkout request ID
            checkout_request_id = str(uuid.uuid4())
            
            # Create payment record
            payment = SubscriptionPayment.objects.create(
                user=request.user,
                tier=tier,
                checkout_request_id=checkout_request_id,
                merchant_request_id='',  # Will be updated after M-Pesa response
                phone_number=request.user.phone_number,
                amount=amount,
                status='pending',
                idempotency_key=idempotency_key
            )
            
            # Initialize M-Pesa service
            mpesa_service = MpesaService()
            
            # Get callback URL from settings
            callback_url = getattr(settings, 'MPESA_CALLBACK_URL', 'https://ligisoo.co.ke/api/callback/subscription')
            
            # Initiate STK Push
            mpesa_result = mpesa_service.initiate_stk_push(
                phone_number=request.user.phone_number,
                amount=amount,
                account_reference=f"SUB_{request.user.id}",
                transaction_desc=f"Ligisoo {tier.capitalize()} Pro Subscription",
                callback_url=callback_url
            )
            
            if not mpesa_result['success']:
                # Delete the payment record if M-Pesa initiation failed
                payment.delete()
                return Response(
                    {'error': mpesa_result['error']}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update payment with M-Pesa response
            payment.merchant_request_id = mpesa_result.get('merchant_request_id', '')
            payment.checkout_request_id = mpesa_result.get('checkout_request_id', checkout_request_id)
            payment.response_code = mpesa_result.get('response_code', '0')
            payment.response_description = mpesa_result.get('response_description', 'Success')
            payment.save()
            
            return Response({
                'checkout_request_id': payment.checkout_request_id,
                'merchant_request_id': payment.merchant_request_id,
                'message': mpesa_result.get('customer_message', 'Payment initiated successfully. Please complete payment on your phone.'),
                'amount': amount,
                'tier': tier
            })
            
        except Exception as e:
            return Response(
                {'error': f'Payment initiation failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class SubscriptionCallbackView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [CallbackThrottle]

    @mpesa_security_required
    def post(self, request):
        """Handle M-Pesa payment callback for pro subscriptions"""
        import logging
        logger = logging.getLogger(__name__)

        try:
            callback_data = request.data
            logger.info(f"M-Pesa callback received: {json.dumps(callback_data)}")

            # Extract checkout request ID from callback
            checkout_request_id = callback_data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')

            if not checkout_request_id:
                logger.error(f"Invalid callback data - no checkout request ID: {callback_data}")
                return Response({'error': 'Invalid callback data'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Find payment
            try:
                payment = SubscriptionPayment.objects.get(checkout_request_id=checkout_request_id)
            except SubscriptionPayment.DoesNotExist:
                return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Process callback data
            stk_callback = callback_data.get('Body', {}).get('stkCallback', {})
            result_code = stk_callback.get('ResultCode', -1)
            
            if result_code == 0:  # Success
                # Extract payment details
                callback_metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
                mpesa_receipt_number = None
                
                for item in callback_metadata:
                    if item.get('Name') == 'MpesaReceiptNumber':
                        mpesa_receipt_number = item.get('Value')
                        break
                
                # Update payment
                payment.status = 'completed'
                payment.mpesa_receipt_number = mpesa_receipt_number or ''
                payment.callback_data = callback_data
                payment.completed_at = timezone.now()
                payment.save()

                # Extend subscription in UserProfile
                user_profile = payment.user.userprofile
                user_profile.is_pro = True
                
                # Add time based on tier
                days_to_add = 7 if payment.tier == 'weekly' else (30 if payment.tier == 'monthly' else 365)
                now = timezone.now()
                
                if user_profile.pro_expires_at and user_profile.pro_expires_at > now:
                    user_profile.pro_expires_at += timedelta(days=days_to_add)
                else:
                    user_profile.pro_expires_at = now + timedelta(days=days_to_add)
                
                user_profile.save()
                
            else:  # Failed
                payment.status = 'failed'
                payment.callback_data = callback_data
                payment.response_description = stk_callback.get('ResultDesc', 'Payment failed')
                payment.save()
            
            return Response({'status': 'success'})
            
        except Exception as e:
            return Response(
                {'error': f'Callback processing failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SubscriptionStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, checkout_request_id):
        """Get subscription payment status"""
        try:
            payment = SubscriptionPayment.objects.get(
                checkout_request_id=checkout_request_id,
                user=request.user
            )

            # If payment is still pending, query M-Pesa for status
            if payment.status == 'pending':
                mpesa_service = MpesaService()
                query_result = mpesa_service.query_stk_push(checkout_request_id)

                if query_result.get('success'):
                    result_code = str(query_result.get('result_code', ''))

                    # ResultCode '0' means successful payment
                    if result_code == '0':
                        # Update payment to completed
                        payment.status = 'completed'
                        mpesa_receipt = f"QUERY_{timezone.now().timestamp()}"
                        payment.mpesa_receipt_number = mpesa_receipt
                        payment.completed_at = timezone.now()
                        payment.save()
                        
                        # Extend subscription in UserProfile
                        user_profile = payment.user.userprofile
                        user_profile.is_pro = True
                        
                        # Add time based on tier
                        days_to_add = 7 if payment.tier == 'weekly' else (30 if payment.tier == 'monthly' else 365)
                        now = timezone.now()
                        
                        if user_profile.pro_expires_at and user_profile.pro_expires_at > now:
                            user_profile.pro_expires_at += timedelta(days=days_to_add)
                        else:
                            user_profile.pro_expires_at = now + timedelta(days=days_to_add)
                        
                        user_profile.save()

                    elif result_code in ['1', '1032', '1037', '2001']:
                        payment.status = 'failed'
                        payment.response_description = query_result.get('result_desc', 'Payment failed')
                        payment.save()

            return Response({
                'checkout_request_id': checkout_request_id,
                'status': payment.status,
                'amount': payment.amount,
                'tier': payment.tier,
                'mpesa_receipt_number': payment.mpesa_receipt_number,
                'created_at': payment.created_at,
                'completed_at': payment.completed_at
            })

        except SubscriptionPayment.DoesNotExist:
            return Response(
                {'error': 'Payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def pricing_view(request):
    """Render the pricing page"""
    context = {
        'weekly_price': settings.SUBSCRIPTION_PRICE_WEEKLY,
        'monthly_price': settings.SUBSCRIPTION_PRICE_MONTHLY,
        'annual_price': settings.SUBSCRIPTION_PRICE_ANNUAL,
    }
    return render(request, 'payments/pricing.html', context)

@login_required
def checkout_view(request):
    tier = request.GET.get('tier', 'monthly')
    
    if tier == 'weekly':
        amount = settings.SUBSCRIPTION_PRICE_WEEKLY
    elif tier == 'monthly':
        amount = settings.SUBSCRIPTION_PRICE_MONTHLY
    else:
        amount = settings.SUBSCRIPTION_PRICE_ANNUAL
    context = {
        'tier': tier,
        'amount': amount,
        'tier_display': tier.capitalize()
    }
    return render(request, 'payments/checkout.html', context)
