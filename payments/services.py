from decimal import Decimal
from typing import Any, Dict, List, TYPE_CHECKING

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone

from .models import Order, PaymentProvider, BankAccount
from .providers import get_provider

if TYPE_CHECKING:
    from django.contrib.auth import get_user_model
    User = get_user_model()


class PaymentService:
    """
    Central service for handling all payment operations.
    Provides a unified interface for working with different payment providers.
    """

    @classmethod
    def get_available_providers(
        cls,
        amount: Decimal,
        currency: str = 'IDR',
        for_subscription: bool = False
    ) -> List[PaymentProvider]:
        """
        Get list of available payment providers for given criteria.
        
        Args:
            amount: Transaction amount
            currency: Currency code
            for_subscription: If True, only return providers that support subscriptions
        """
        providers = PaymentProvider.objects.filter(is_active=True)

        if for_subscription:
            providers = providers.filter(supports_subscription=True)

        result = []
        for provider in providers.order_by('display_order'):
            if provider.is_available_for_amount(amount, currency):
                result.append(provider)

        return result

    @classmethod
    @transaction.atomic
    def create_order(
        cls,
        user: 'User',
        item: Any,
        order_type: str,
        provider: PaymentProvider = None,
        discount_amount: Decimal = Decimal('0'),
        ip_address: str = None,
        user_agent: str = ''
    ) -> Order:
        """
        Create a new order for a purchasable item.
        
        Args:
            user: The user making the purchase
            item: The item being purchased (must have get_price() and get_currency() methods)
            order_type: Type of order ('course', 'bundle', 'subscription')
            provider: Payment provider to use
            discount_amount: Any discount to apply
            ip_address: User's IP address
            user_agent: User's browser user agent
        """
        # Get price from item - supports Purchasable protocol
        if hasattr(item, 'get_price'):
            subtotal = item.get_price()
        elif hasattr(item, 'price'):
            subtotal = item.price
        else:
            raise ValueError("Item must have get_price() method or price attribute")

        if hasattr(item, 'get_currency'):
            currency = item.get_currency()
        elif hasattr(item, 'currency'):
            currency = item.currency
        else:
            currency = 'IDR'

        total_amount = subtotal - discount_amount

        # Get content type for generic foreign key
        content_type = ContentType.objects.get_for_model(item)

        order = Order.objects.create(
            user=user,
            order_type=order_type,
            content_type=content_type,
            object_id=item.id,
            subtotal=subtotal,
            discount_amount=discount_amount,
            total_amount=total_amount,
            currency=currency,
            payment_provider=provider,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return order

    @classmethod
    def initiate_payment(
        cls,
        order: Order,
        provider: PaymentProvider,
        return_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """
        Initiate payment for an order using the specified provider.
        
        Returns:
            For redirect-based providers: {'redirect_url': 'https://...'}
            For manual transfer: {'type': 'manual_transfer', 'bank_accounts': [...], ...}
        """
        order.payment_provider = provider
        order.save(update_fields=['payment_provider', 'updated_at'])

        payment_provider = get_provider(provider.provider_type, provider.config)
        return payment_provider.create_payment(order, return_url, cancel_url)

    @classmethod
    def verify_payment(cls, order: Order, data: Dict[str, Any]) -> bool:
        """
        Verify payment completion (e.g., from return URL callback).
        """
        if not order.payment_provider:
            return False

        payment_provider = get_provider(
            order.payment_provider.provider_type,
            order.payment_provider.config
        )
        return payment_provider.verify_payment(order, data)

    @classmethod
    def handle_webhook(
        cls,
        provider: PaymentProvider,
        payload: bytes,
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Handle webhook from payment gateway.
        Returns processed result with order information.
        """
        payment_provider = get_provider(provider.provider_type, provider.config)
        result = payment_provider.handle_webhook(payload, headers)

        if result.get('success') and result.get('order_number'):
            order = Order.objects.filter(order_number=result['order_number']).first()
            if order:
                status = result.get('status')
                if status == 'completed':
                    order.mark_completed(
                        gateway_payment_id=result.get('gateway_payment_id', '')
                    )
                elif status == 'failed':
                    order.mark_failed(reason=result.get('reason', 'Payment failed'))

        return result

    @classmethod
    @transaction.atomic
    def verify_manual_payment(
        cls,
        order: Order,
        verified_by: 'User',
        notes: str = ''
    ) -> bool:
        """
        Verify a manual bank transfer payment.
        Called by admin after checking payment proof.
        """
        if order.status != 'awaiting_verification':
            return False

        # Set verification fields first (without changing status)
        order.verified_by = verified_by
        order.verified_at = timezone.now()
        order.verification_notes = notes
        
        # mark_completed() will set status to 'completed' and emit signal via save()
        order.mark_completed()
        return True

    @classmethod
    @transaction.atomic
    def reject_manual_payment(
        cls,
        order: Order,
        rejected_by: 'User',
        reason: str
    ) -> bool:
        """
        Reject a manual bank transfer payment.
        """
        if order.status != 'awaiting_verification':
            return False

        order.verified_by = rejected_by
        order.verified_at = timezone.now()
        order.mark_failed(reason=reason)
        return True

    @classmethod
    def get_bank_accounts(cls, provider: PaymentProvider = None) -> List[BankAccount]:
        """
        Get active bank accounts for manual transfer.
        If provider is specified, filter to that provider's accounts.
        """
        queryset = BankAccount.objects.filter(is_active=True)
        if provider:
            queryset = queryset.filter(provider=provider)
        return list(queryset.order_by('display_order'))
