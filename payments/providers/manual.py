from datetime import timedelta
from typing import Any, Dict, TYPE_CHECKING

from django.utils import timezone

from . import PaymentProviderBase, register_provider

if TYPE_CHECKING:
    from payments.models import Order


class ManualTransferProvider(PaymentProviderBase):
    """
    Payment provider for manual bank transfers.
    
    Instead of redirecting to a gateway, this provider returns
    bank account details and allows users to upload proof of transfer.
    """

    def create_payment(
        self,
        order: 'Order',
        return_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """
        Return bank account details for manual transfer.
        Sets order status to 'awaiting_verification'.
        """
        from payments.models import BankAccount

        # Get active bank accounts for this provider
        bank_accounts = BankAccount.objects.filter(
            provider=order.payment_provider,
            is_active=True
        ).order_by('display_order')

        # Set payment deadline (configurable, default 24 hours)
        expiry_hours = self.config.get('expiry_hours', 24)
        order.expires_at = timezone.now() + timedelta(hours=expiry_hours)
        order.status = 'awaiting_verification'
        order.save(update_fields=['expires_at', 'status', 'updated_at'])

        return {
            'type': 'manual_transfer',
            'order_number': order.order_number,
            'amount': float(order.total_amount),
            'currency': order.currency,
            'formatted_amount': order.get_formatted_total(),
            'expires_at': order.expires_at.isoformat(),
            'bank_accounts': [
                {
                    'id': acc.id,
                    'bank_name': acc.bank_name,
                    'bank_code': acc.bank_code,
                    'account_number': acc.account_number,
                    'account_holder': acc.account_holder,
                    'instructions': acc.instructions,
                }
                for acc in bank_accounts
            ],
        }

    def verify_payment(self, order: 'Order', data: Dict[str, Any]) -> bool:
        """
        Manual verification - this is called by admin action, not automatically.
        For auto-verification, this would always return True (admin verified).
        """
        return True


# Register this provider
register_provider('manual_transfer', ManualTransferProvider)
