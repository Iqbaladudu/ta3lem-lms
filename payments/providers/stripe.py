"""
Stripe payment provider implementation.
Requires stripe package: pip install stripe
"""
from typing import Any, Dict, TYPE_CHECKING

from . import PaymentProviderBase, register_provider

if TYPE_CHECKING:
    from payments.models import Order


class StripeProvider(PaymentProviderBase):
    """
    Stripe payment provider for one-time and subscription payments.
    
    Configuration:
    {
        "public_key": "pk_test_...",
        "secret_key": "sk_test_...",
        "webhook_secret": "whsec_..."
    }
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._stripe = None

    @property
    def stripe(self):
        """Lazy-load stripe module"""
        if self._stripe is None:
            try:
                import stripe
                stripe.api_key = self.config.get('secret_key', '')
                self._stripe = stripe
            except ImportError:
                raise ImportError("Stripe package not installed. Run: pip install stripe")
        return self._stripe

    def create_payment(
        self,
        order: 'Order',
        return_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """Create Stripe Checkout Session"""
        session = self.stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': order.currency.lower(),
                    'product_data': {
                        'name': str(order.item) if order.item else f"Order {order.order_number}",
                    },
                    'unit_amount': int(order.total_amount * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=return_url + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=cancel_url,
            client_reference_id=order.order_number,
            metadata={'order_id': str(order.id)},
        )

        order.gateway_order_id = session.id
        order.status = 'processing'
        order.save(update_fields=['gateway_order_id', 'status', 'updated_at'])

        return {
            'redirect_url': session.url,
            'session_id': session.id,
        }

    def verify_payment(self, order: 'Order', data: Dict[str, Any]) -> bool:
        """Verify payment from return URL"""
        session_id = data.get('session_id')
        if not session_id:
            return False

        try:
            session = self.stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == 'paid':
                order.mark_completed(gateway_payment_id=session.payment_intent)
                return True
        except Exception:
            pass
        return False

    def handle_webhook(self, payload: bytes, headers: Dict[str, str]) -> Dict[str, Any]:
        """Handle Stripe webhook"""
        webhook_secret = self.config.get('webhook_secret', '')
        sig_header = headers.get('stripe-signature', '')

        try:
            event = self.stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except (ValueError, self.stripe.error.SignatureVerificationError) as e:
            return {'success': False, 'error': str(e)}

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            return {
                'success': True,
                'order_number': session.get('client_reference_id'),
                'status': 'completed',
                'gateway_payment_id': session.get('payment_intent'),
            }

        return {'success': True, 'status': 'ignored'}

    def supports_subscription(self) -> bool:
        return True


# Register provider
register_provider('stripe', StripeProvider)
