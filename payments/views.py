import uuid
import json
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.http import JsonResponse

from .models import TipPayment
from .services import MpesaService
from apps.tips.models import Tip, TipPurchase

User = get_user_model()


class InitiateTipPaymentView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Initiate M-Pesa STK Push payment for tip purchase"""
        data = request.data
        
        # Check if user has a phone number
        if not request.user.phone_number:
            return Response(
                {'error': 'Phone number is required. Please update your profile first.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate required fields
        tip_id = data.get('tip_id')
        if not tip_id:
            return Response(
                {'error': 'tip_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the tip
        try:
            tip = Tip.objects.get(id=tip_id)
        except Tip.DoesNotExist:
            return Response(
                {'error': 'Tip not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate tip can be purchased
        if not tip.can_be_purchased():
            return Response(
                {'error': 'This tip cannot be purchased at the moment.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user has already purchased this tip
        if TipPurchase.objects.filter(tip=tip, buyer=request.user, status='completed').exists():
            return Response(
                {'error': 'You have already purchased this tip.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user is the tipster
        if request.user == tip.tipster:
            return Response(
                {'error': 'You cannot purchase your own tip.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Generate unique checkout request ID
            checkout_request_id = str(uuid.uuid4())
            
            # Create payment record
            payment = TipPayment.objects.create(
                user=request.user,
                tip=tip,
                checkout_request_id=checkout_request_id,
                merchant_request_id='',  # Will be updated after M-Pesa response
                phone_number=request.user.phone_number,
                amount=tip.price,
                status='pending'
            )
            
            # Initialize M-Pesa service
            mpesa_service = MpesaService()
            
            # Generate callback URL
            callback_url = f"https://ligisoo.co.ke/payments/api/callback/"
            
            # Initiate STK Push
            mpesa_result = mpesa_service.initiate_stk_push(
                phone_number=request.user.phone_number,
                amount=tip.price,
                account_reference=f"TIP_{tip.id}",
                transaction_desc=f"Ligisoo Tip Purchase - {tip.bet_code[:8]}***",
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
                'amount': tip.price,
                'tip_id': tip.id,
                'tip_code': f"{tip.bet_code[:3]}***{tip.bet_code[-2:]}"
            })
            
        except Exception as e:
            return Response(
                {'error': f'Payment initiation failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TipPaymentCallbackView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Handle M-Pesa payment callback for tip purchases"""
        try:
            callback_data = request.data
            
            # Extract checkout request ID from callback
            checkout_request_id = callback_data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')
            
            if not checkout_request_id:
                return Response({'error': 'Invalid callback data'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Find payment
            try:
                payment = TipPayment.objects.get(checkout_request_id=checkout_request_id)
            except TipPayment.DoesNotExist:
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
                
                # Create TipPurchase record
                transaction_id = f"MPESA_{payment.tip.id}_{payment.user.id}_{timezone.now().timestamp()}"
                
                tip_purchase = TipPurchase.objects.create(
                    tip=payment.tip,
                    buyer=payment.user,
                    amount=payment.amount,
                    transaction_id=transaction_id,
                    status='completed',
                    completed_at=timezone.now()
                )
                
                # Add to tipster's earnings (simplified for now)
                from decimal import Decimal
                tipster_earning = payment.amount * Decimal('0.6')  # 60% to tipster
                payment.tip.tipster.userprofile.wallet_balance += tipster_earning
                payment.tip.tipster.userprofile.save()
                
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


class TipPaymentStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, checkout_request_id):
        """Get tip payment status"""
        try:
            payment = TipPayment.objects.get(
                checkout_request_id=checkout_request_id,
                user=request.user
            )
            
            return Response({
                'checkout_request_id': checkout_request_id,
                'status': payment.status,
                'amount': payment.amount,
                'tip_id': payment.tip.id,
                'tip_code': f"{payment.tip.bet_code[:3]}***{payment.tip.bet_code[-2:]}",
                'mpesa_receipt_number': payment.mpesa_receipt_number,
                'created_at': payment.created_at,
                'completed_at': payment.completed_at
            })
            
        except TipPayment.DoesNotExist:
            return Response(
                {'error': 'Payment not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
