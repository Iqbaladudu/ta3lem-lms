"""
Midtrans payment provider implementation.
Requires midtransclient package: pip install midtransclient
"""
from typing import Any, Dict, TYPE_CHECKING

from . import PaymentProviderBase, register_provider

if TYPE_CHECKING:
    from payments.models import Order


class MidtransProvider(PaymentProviderBase):
    """
    Midtrans payment provider for Indonesian payments.
    
    Configuration:
    {
        "server_key": "...",
        "client_key": "...",
        "is_production": false
    }
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._snap = None

    @property
    def snap(self):
        """Lazy-load Midtrans Snap"""
        if self._snap is None:
            try:
                import midtransclient
                self._snap = midtransclient.Snap(
                    is_production=self.config.get('is_production', False),
                    server_key=self.config.get('server_key', ''),
                    client_key=self.config.get('client_key', '')
                )
            except ImportError:
                raise ImportError("Midtrans package not installed. Run: pip install midtransclient")
        return self._snap

    def create_payment(
        self,
        order: 'Order',
        return_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """Create Midtrans Snap transaction"""
        transaction = self.snap.create_transaction({
            'transaction_details': {
                'order_id': order.order_number,
                'gross_amount': int(order.total_amount),
            },
            'customer_details': {
                'first_name': order.user.first_name or order.user.username,
                'last_name': order.user.last_name or '',
                'email': order.user.email,
            },
            'callbacks': {
                'finish': return_url,
            }
        })

        order.gateway_order_id = order.order_number
        order.status = 'processing'
        order.gateway_response = transaction
        order.save(update_fields=['gateway_order_id', 'status', 'gateway_response', 'updated_at'])

        return {
            'redirect_url': transaction.get('redirect_url'),
            'token': transaction.get('token'),
        }

    def verify_payment(self, order: 'Order', data: Dict[str, Any]) -> bool:
        """Verify payment status via API"""
        try:
            import midtransclient
            core = midtransclient.CoreApi(
                is_production=self.config.get('is_production', False),
                server_key=self.config.get('server_key', ''),
                client_key=self.config.get('client_key', '')
            )
            status = core.transactions.status(order.order_number)
            
            if status.get('transaction_status') in ['capture', 'settlement']:
                order.mark_completed(gateway_payment_id=status.get('transaction_id', ''))
                return True
        except Exception:
            pass
        return False

    def handle_webhook(self, payload: bytes, headers: Dict[str, str]) -> Dict[str, Any]:
        """Handle Midtrans notification webhook"""
        import json
        import hashlib

        try:
            data = json.loads(payload)
        except json.JSONDecodeError as e:
            return {'success': False, 'error': str(e)}

        # Verify signature
        server_key = self.config.get('server_key', '')
        order_id = data.get('order_id', '')
        status_code = data.get('status_code', '')
        gross_amount = data.get('gross_amount', '')
        signature = data.get('signature_key', '')

        expected_signature = hashlib.sha512(
            f"{order_id}{status_code}{gross_amount}{server_key}".encode()
        ).hexdigest()

        if signature != expected_signature:
            return {'success': False, 'error': 'Invalid signature'}

        transaction_status = data.get('transaction_status')
        
        if transaction_status in ['capture', 'settlement']:
            return {
                'success': True,
                'order_number': order_id,
                'status': 'completed',
                'gateway_payment_id': data.get('transaction_id'),
            }
        elif transaction_status in ['deny', 'cancel', 'expire']:
            return {
                'success': True,
                'order_number': order_id,
                'status': 'failed',
                'reason': transaction_status,
            }

        return {'success': True, 'status': 'pending'}


# Register provider
register_provider('midtrans', MidtransProvider)
