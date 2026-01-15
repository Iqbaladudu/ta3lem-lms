"""
API Views for Payments app.
"""

from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, extend_schema_view

from core.api import SuccessResponseMixin, StandardResultsSetPagination, IsOwner
from payments.models import Order, PaymentProvider, BankAccount
from .serializers import (
    OrderSerializer,
    OrderDetailSerializer,
    OrderCreateSerializer,
    PaymentProviderSerializer,
    BankAccountSerializer,
    PaymentProofUploadSerializer,
    OrderStatusSerializer,
    CheckoutResponseSerializer,
    WebhookPayloadSerializer,
)


@extend_schema_view(
    list=extend_schema(
        tags=['Payments'],
        summary='List payment providers',
        description='List all available payment providers.'
    ),
    retrieve=extend_schema(
        tags=['Payments'],
        summary='Get payment provider details',
        description='Get details of a specific payment provider.'
    ),
)
class PaymentProviderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing payment providers.
    """
    queryset = PaymentProvider.objects.filter(is_active=True)
    serializer_class = PaymentProviderSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    
    @extend_schema(
        tags=['Payments'],
        summary='List bank accounts',
        description='Get bank accounts for a payment provider.'
    )
    @action(detail=True, methods=['get'])
    def bank_accounts(self, request, pk=None):
        """
        Get bank accounts for manual transfer provider.
        """
        provider = self.get_object()
        accounts = provider.bank_accounts.filter(is_active=True)
        serializer = BankAccountSerializer(accounts, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        tags=['Payments'],
        summary='List my orders',
        description='List all orders for the current user.'
    ),
    retrieve=extend_schema(
        tags=['Payments'],
        summary='Get order details',
        description='Get details of a specific order.'
    ),
)
class OrderViewSet(SuccessResponseMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing orders.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filterset_fields = ['status', 'order_type']
    ordering = ['-created_at']
    lookup_field = 'order_number'
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OrderDetailSerializer
        return OrderSerializer
    
    @extend_schema(
        tags=['Payments'],
        summary='Get order status',
        description='Get the current status of an order.'
    )
    @action(detail=True, methods=['get'])
    def status(self, request, order_number=None):
        """
        Get order status.
        """
        order = self.get_object()
        
        status_data = {
            'order_number': order.order_number,
            'status': order.status,
            'status_display': order.get_status_display(),
            'is_paid': order.status == 'completed',
            'is_expired': order.is_expired(),
            'can_upload_proof': order.status in ['pending', 'awaiting_verification'],
            'next_action': self._get_next_action(order),
        }
        
        return self.success_response(data=status_data)
    
    def _get_next_action(self, order):
        if order.status == 'pending':
            if order.payment_provider and order.payment_provider.provider_type == 'manual_transfer':
                return 'upload_payment_proof'
            return 'complete_payment'
        elif order.status == 'awaiting_verification':
            return 'wait_for_verification'
        elif order.status == 'completed':
            return None
        return None


@extend_schema(tags=['Payments'])
class CheckoutView(SuccessResponseMixin, APIView):
    """
    Checkout endpoint for creating orders.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary='Create checkout',
        description='Create a new order for a course or subscription.',
        request=OrderCreateSerializer,
        responses={201: CheckoutResponseSerializer}
    )
    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        order_type = serializer.validated_data['order_type']
        item = serializer.validated_data['item']
        
        # Get content type for the item
        content_type = ContentType.objects.get_for_model(item)
        
        # Get available payment providers
        providers = PaymentProvider.objects.filter(
            is_active=True
        ).order_by('display_order')
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            order_type=order_type,
            content_type=content_type,
            object_id=item.pk,
            subtotal=item.get_price(),
            total_amount=item.get_price(),
            currency=item.get_currency(),
            status='pending',
            expires_at=timezone.now() + timedelta(hours=24),
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        
        # Get bank accounts for manual transfer
        bank_accounts = BankAccount.objects.filter(
            provider__provider_type='manual_transfer',
            provider__is_active=True,
            is_active=True
        )
        
        return Response({
            'success': True,
            'order': OrderSerializer(order).data,
            'available_providers': PaymentProviderSerializer(providers, many=True).data,
            'bank_accounts': BankAccountSerializer(bank_accounts, many=True).data,
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Payments'])
class SelectPaymentProviderView(SuccessResponseMixin, APIView):
    """
    Select payment provider for an order.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary='Select payment provider',
        description='Select a payment provider for an existing order.'
    )
    def post(self, request, order_number):
        order = get_object_or_404(
            Order,
            order_number=order_number,
            user=request.user,
            status='pending'
        )
        
        provider_id = request.data.get('provider_id')
        provider = get_object_or_404(PaymentProvider, pk=provider_id, is_active=True)
        
        # Validate provider supports the amount and currency
        if not provider.is_available_for_amount(order.total_amount, order.currency):
            return Response({
                'success': False,
                'message': 'This payment provider is not available for this order.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        order.payment_provider = provider
        order.save()
        
        # If manual transfer, include bank account info
        response_data = {
            'success': True,
            'order': OrderSerializer(order).data,
        }
        
        if provider.provider_type == 'manual_transfer':
            bank_accounts = provider.bank_accounts.filter(is_active=True)
            response_data['bank_accounts'] = BankAccountSerializer(bank_accounts, many=True).data
        
        return Response(response_data)


@extend_schema(tags=['Payments'])
class UploadPaymentProofView(SuccessResponseMixin, APIView):
    """
    Upload payment proof for manual transfer orders.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary='Upload payment proof',
        description='Upload payment proof for a manual transfer order.',
        request=PaymentProofUploadSerializer
    )
    def post(self, request, order_number):
        order = get_object_or_404(
            Order,
            order_number=order_number,
            user=request.user,
            status__in=['pending', 'awaiting_verification']
        )
        
        serializer = PaymentProofUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        order.payment_proof = serializer.validated_data['payment_proof']
        order.transfer_amount = serializer.validated_data['transfer_amount']
        order.transfer_date = serializer.validated_data['transfer_date']
        order.transfer_notes = serializer.validated_data.get('transfer_notes', '')
        order.status = 'awaiting_verification'
        order.save()
        
        return self.success_response(
            data=OrderDetailSerializer(order).data,
            message='Payment proof uploaded. Awaiting verification.'
        )


@extend_schema(tags=['Payments'])
class WebhookView(APIView):
    """
    Webhook endpoint for payment provider callbacks.
    
    Security Note: Each payment provider should implement proper webhook 
    signature verification in production. The verification is provider-specific:
    - Stripe: Uses Stripe-Signature header
    - Midtrans: Uses signature_key verification
    - Xendit: Uses x-callback-token header
    """
    permission_classes = [AllowAny]
    authentication_classes = []
    
    @extend_schema(
        summary='Payment webhook',
        description='Webhook endpoint for payment provider callbacks.',
        request=WebhookPayloadSerializer
    )
    def post(self, request, provider_type):
        """
        Handle webhook from payment provider.
        """
        import logging
        import hashlib
        import hmac
        
        logger = logging.getLogger(__name__)
        
        try:
            provider = PaymentProvider.objects.get(
                provider_type=provider_type,
                is_active=True
            )
        except PaymentProvider.DoesNotExist:
            logger.warning(f'Webhook received for invalid provider: {provider_type}')
            return Response(
                {'error': 'Invalid provider'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify webhook signature based on provider type
        if not self._verify_webhook_signature(request, provider):
            logger.warning(f'Webhook signature verification failed for provider: {provider_type}')
            return Response(
                {'error': 'Invalid signature'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Log the webhook for debugging
        logger.info(f'Webhook received from {provider_type}: {request.data}')
        
        # Get order from webhook data
        order_id = request.data.get('order_id') or request.data.get('external_id')
        if not order_id:
            return Response(
                {'error': 'Order ID not provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            order = Order.objects.get(
                gateway_order_id=order_id,
                payment_provider=provider
            )
        except Order.DoesNotExist:
            logger.warning(f'Order not found for webhook: {order_id}')
            return Response(
                {'error': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update order based on webhook status
        webhook_status = request.data.get('status', '').lower()
        
        if webhook_status in ['paid', 'completed', 'settlement', 'capture']:
            order.mark_completed(
                gateway_payment_id=request.data.get('transaction_id', '')
            )
        elif webhook_status in ['failed', 'denied', 'cancelled']:
            order.mark_failed(reason=f'Payment {webhook_status}')
        
        return Response({'status': 'ok'})
    
    def _verify_webhook_signature(self, request, provider):
        """
        Verify webhook signature based on provider type.
        Returns True if verification passes or is not implemented for provider.
        """
        import hmac
        import hashlib
        
        provider_config = provider.config or {}
        
        if provider.provider_type == 'stripe':
            # Stripe webhook verification
            webhook_secret = provider_config.get('webhook_secret')
            if not webhook_secret:
                return True  # Skip if not configured
            
            signature = request.headers.get('Stripe-Signature')
            if not signature:
                return False
            
            # In production, use stripe library for proper verification
            # stripe.Webhook.construct_event(payload, signature, webhook_secret)
            return True  # Placeholder - implement full Stripe verification
            
        elif provider.provider_type == 'midtrans':
            # Midtrans signature verification
            server_key = provider_config.get('server_key')
            if not server_key:
                return True  # Skip if not configured
            
            # Midtrans signature: SHA512(order_id + status_code + gross_amount + server_key)
            order_id = request.data.get('order_id', '')
            status_code = request.data.get('status_code', '')
            gross_amount = request.data.get('gross_amount', '')
            
            signature_string = f"{order_id}{status_code}{gross_amount}{server_key}"
            expected_signature = hashlib.sha512(signature_string.encode()).hexdigest()
            actual_signature = request.data.get('signature_key', '')
            
            return hmac.compare_digest(expected_signature, actual_signature)
            
        elif provider.provider_type == 'xendit':
            # Xendit callback token verification
            callback_token = provider_config.get('callback_token')
            if not callback_token:
                return True  # Skip if not configured
            
            request_token = request.headers.get('x-callback-token')
            if not request_token:
                return False
            
            return hmac.compare_digest(callback_token, request_token)
        
        # Manual transfer doesn't have webhooks
        return True


@extend_schema(tags=['Payments'])
class PaymentSuccessView(SuccessResponseMixin, APIView):
    """
    Payment success callback page.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary='Payment success',
        description='Get payment success status after redirect from payment provider.'
    )
    def get(self, request, order_number):
        order = get_object_or_404(
            Order,
            order_number=order_number,
            user=request.user
        )
        
        return self.success_response(
            data=OrderSerializer(order).data,
            message='Payment processed successfully.' if order.status == 'completed' else 'Payment is being processed.'
        )


@extend_schema(tags=['Payments'])
class PaymentCancelView(SuccessResponseMixin, APIView):
    """
    Payment cancellation endpoint.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary='Cancel payment',
        description='Cancel a pending payment order.'
    )
    def post(self, request, order_number):
        order = get_object_or_404(
            Order,
            order_number=order_number,
            user=request.user,
            status='pending'
        )
        
        order.status = 'cancelled'
        order.save()
        
        return self.success_response(
            data=OrderSerializer(order).data,
            message='Order cancelled.'
        )
