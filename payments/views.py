import uuid
import json
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import TipPayment, WalletDeposit
from .services import MpesaService
from .security import mpesa_security_required
from .throttles import PaymentInitiationThrottle, CallbackThrottle
from apps.tips.models import Tip, TipPurchase

User = get_user_model()


class InitiateTipPaymentView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [PaymentInitiationThrottle]
    
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
        idempotency_key = data.get('idempotency_key')
        
        if not tip_id:
            return Response(
                {'error': 'tip_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if not idempotency_key:
            return Response(
                {'error': 'idempotency_key is required to prevent duplicate payments'}, 
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
        
        # Check for idempotency - return existing payment if same key used
        try:
            existing_payment = TipPayment.objects.get(
                user=request.user, 
                tip=tip, 
                idempotency_key=idempotency_key
            )
            return Response({
                'message': 'Payment already initiated with this idempotency key',
                'checkout_request_id': existing_payment.checkout_request_id,
                'status': existing_payment.status,
                'merchant_request_id': existing_payment.merchant_request_id
            })
        except TipPayment.DoesNotExist:
            pass
        
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
                status='pending',
                idempotency_key=idempotency_key
            )
            
            # Initialize M-Pesa service
            mpesa_service = MpesaService()
            
            # Get callback URL from settings
            callback_url = getattr(settings, 'MPESA_CALLBACK_URL', 'https://ligisoo.co.ke/api/callback')
            
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


@method_decorator(csrf_exempt, name='dispatch')
class TipPaymentCallbackView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [CallbackThrottle]

    @mpesa_security_required
    def post(self, request):
        """Handle M-Pesa payment callback for tip purchases"""
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

                # Create accounting entries for M-Pesa purchase
                from apps.transactions.services import AccountingService
                from django.db import transaction as db_txn

                with db_txn.atomic():
                    # Record tip purchase with M-Pesa
                    accounting_txn = AccountingService.record_tip_purchase_with_mpesa(
                        buyer=payment.user,
                        tipster=payment.tip.tipster,
                        tip=payment.tip,
                        amount=payment.amount,
                        mpesa_receipt_number=mpesa_receipt_number
                    )

                    # Create TipPurchase record
                    tip_purchase = TipPurchase.objects.create(
                        tip=payment.tip,
                        buyer=payment.user,
                        amount=payment.amount,
                        transaction_id=accounting_txn.reference,
                        mpesa_receipt=mpesa_receipt_number or '',
                        status='completed',
                        completed_at=timezone.now()
                    )

                    # Sync tipster's wallet balance with accounting
                    AccountingService.sync_wallet_balance(payment.tip.tipster)
                
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

                        # Create accounting entries for M-Pesa purchase
                        from apps.transactions.services import AccountingService
                        from django.db import transaction as db_txn

                        with db_txn.atomic():
                            # Record tip purchase with M-Pesa
                            accounting_txn = AccountingService.record_tip_purchase_with_mpesa(
                                buyer=payment.user,
                                tipster=payment.tip.tipster,
                                tip=payment.tip,
                                amount=payment.amount,
                                mpesa_receipt_number=mpesa_receipt
                            )

                            # Create TipPurchase record
                            TipPurchase.objects.get_or_create(
                                tip=payment.tip,
                                buyer=payment.user,
                                defaults={
                                    'amount': payment.amount,
                                    'transaction_id': accounting_txn.reference,
                                    'mpesa_receipt': mpesa_receipt,
                                    'status': 'completed',
                                    'completed_at': timezone.now()
                                }
                            )

                            # Sync tipster's wallet balance with accounting
                            AccountingService.sync_wallet_balance(payment.tip.tipster)

                    # ResultCode '1032' means user cancelled
                    # ResultCode '1037' means timeout (user didn't enter PIN)
                    # ResultCode '1' means insufficient funds
                    elif result_code in ['1', '1032', '1037', '2001']:
                        payment.status = 'failed'
                        payment.response_description = query_result.get('result_desc', 'Payment failed')
                        payment.save()

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


class InitiateDepositView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [PaymentInitiationThrottle]
    
    def post(self, request):
        """Initiate M-Pesa STK Push payment for wallet deposit"""
        data = request.data
        
        # Check if user has a phone number
        if not request.user.phone_number:
            return Response(
                {'error': 'Phone number is required. Please update your profile first.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate required fields
        amount = data.get('amount')
        idempotency_key = data.get('idempotency_key')
        
        if not amount:
            return Response(
                {'error': 'amount is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if not idempotency_key:
            return Response(
                {'error': 'idempotency_key is required to prevent duplicate deposits'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate amount
        try:
            amount = float(amount)
            if amount < 10:
                return Response(
                    {'error': 'Minimum deposit amount is KES 10'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            if amount > 150000:
                return Response(
                    {'error': 'Maximum deposit amount is KES 150,000'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid amount'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check for idempotency - return existing deposit if same key used
        try:
            existing_deposit = WalletDeposit.objects.get(
                user=request.user, 
                amount=amount, 
                idempotency_key=idempotency_key
            )
            return Response({
                'message': 'Deposit already initiated with this idempotency key',
                'checkout_request_id': existing_deposit.checkout_request_id,
                'status': existing_deposit.status,
                'merchant_request_id': existing_deposit.merchant_request_id,
                'amount': existing_deposit.amount
            })
        except WalletDeposit.DoesNotExist:
            pass
        
        try:
            # Generate unique checkout request ID
            checkout_request_id = str(uuid.uuid4())
            
            # Create deposit record
            deposit = WalletDeposit.objects.create(
                user=request.user,
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
            callback_url = getattr(settings, 'MPESA_DEPOSIT_CALLBACK_URL', 
                                 getattr(settings, 'MPESA_CALLBACK_URL', 'https://ligisoo.co.ke/api/deposit-callback'))
            
            # Initiate STK Push
            mpesa_result = mpesa_service.initiate_stk_push(
                phone_number=request.user.phone_number,
                amount=amount,
                account_reference=f"DEPOSIT_{request.user.id}",
                transaction_desc=f"Ligisoo Wallet Deposit",
                callback_url=callback_url
            )
            
            if not mpesa_result['success']:
                # Delete the deposit record if M-Pesa initiation failed
                deposit.delete()
                return Response(
                    {'error': mpesa_result['error']}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update deposit with M-Pesa response
            deposit.merchant_request_id = mpesa_result.get('merchant_request_id', '')
            deposit.checkout_request_id = mpesa_result.get('checkout_request_id', checkout_request_id)
            deposit.response_code = mpesa_result.get('response_code', '0')
            deposit.response_description = mpesa_result.get('response_description', 'Success')
            deposit.save()
            
            return Response({
                'checkout_request_id': deposit.checkout_request_id,
                'merchant_request_id': deposit.merchant_request_id,
                'message': mpesa_result.get('customer_message', 'Deposit initiated successfully. Please complete payment on your phone.'),
                'amount': amount
            })
            
        except Exception as e:
            return Response(
                {'error': f'Deposit initiation failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class DepositCallbackView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [CallbackThrottle]

    @mpesa_security_required
    def post(self, request):
        """Handle M-Pesa payment callback for wallet deposits"""
        import logging
        logger = logging.getLogger(__name__)

        try:
            callback_data = request.data
            logger.info(f"M-Pesa deposit callback received: {json.dumps(callback_data)}")

            # Extract checkout request ID from callback
            checkout_request_id = callback_data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')

            if not checkout_request_id:
                logger.error(f"Invalid callback data - no checkout request ID: {callback_data}")
                return Response({'error': 'Invalid callback data'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Find deposit
            try:
                deposit = WalletDeposit.objects.get(checkout_request_id=checkout_request_id)
            except WalletDeposit.DoesNotExist:
                return Response({'error': 'Deposit not found'}, status=status.HTTP_404_NOT_FOUND)
            
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
                
                # Update deposit
                deposit.status = 'completed'
                deposit.mpesa_receipt_number = mpesa_receipt_number or ''
                deposit.callback_data = callback_data
                deposit.completed_at = timezone.now()
                deposit.save()

                # Create accounting entry for deposit
                from apps.transactions.services import AccountingService
                from django.db import transaction as db_txn

                with db_txn.atomic():
                    # Record deposit
                    accounting_txn = AccountingService.record_deposit(
                        user=deposit.user,
                        amount=deposit.amount,
                        mpesa_receipt_number=mpesa_receipt_number
                    )

                    # Sync user's wallet balance with accounting
                    AccountingService.sync_wallet_balance(deposit.user)
                
                logger.info(f"Deposit completed successfully: {deposit.id} - {mpesa_receipt_number}")
                
            else:  # Failed
                deposit.status = 'failed'
                deposit.callback_data = callback_data
                deposit.response_description = stk_callback.get('ResultDesc', 'Payment failed')
                deposit.save()
                
                logger.warning(f"Deposit failed: {deposit.id} - Result Code: {result_code}")
            
            return Response({'status': 'success'})
            
        except Exception as e:
            logger.error(f"Deposit callback processing failed: {str(e)}")
            return Response(
                {'error': f'Callback processing failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DepositStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, checkout_request_id):
        """Get deposit payment status"""
        try:
            deposit = WalletDeposit.objects.get(
                checkout_request_id=checkout_request_id,
                user=request.user
            )

            # If deposit is still pending, query M-Pesa for status
            if deposit.status == 'pending':
                mpesa_service = MpesaService()
                query_result = mpesa_service.query_stk_push(checkout_request_id)

                if query_result.get('success'):
                    result_code = str(query_result.get('result_code', ''))

                    # ResultCode '0' means successful payment
                    if result_code == '0':
                        # Update deposit to completed
                        deposit.status = 'completed'
                        mpesa_receipt = f"QUERY_{timezone.now().timestamp()}"
                        deposit.mpesa_receipt_number = mpesa_receipt
                        deposit.completed_at = timezone.now()
                        deposit.save()

                        # Create accounting entry for deposit
                        from apps.transactions.services import AccountingService
                        from django.db import transaction as db_txn

                        with db_txn.atomic():
                            # Record deposit
                            accounting_txn = AccountingService.record_deposit(
                                user=deposit.user,
                                amount=deposit.amount,
                                mpesa_receipt_number=mpesa_receipt
                            )

                            # Sync user's wallet balance with accounting
                            AccountingService.sync_wallet_balance(deposit.user)

                    elif result_code in ['1', '1032', '1037', '2001']:
                        deposit.status = 'failed'
                        deposit.response_description = query_result.get('result_desc', 'Payment failed')
                        deposit.save()

            return Response({
                'checkout_request_id': checkout_request_id,
                'status': deposit.status,
                'amount': deposit.amount,
                'mpesa_receipt_number': deposit.mpesa_receipt_number,
                'created_at': deposit.created_at,
                'completed_at': deposit.completed_at
            })

        except WalletDeposit.DoesNotExist:
            return Response(
                {'error': 'Deposit not found'},
                status=status.HTTP_404_NOT_FOUND
            )
