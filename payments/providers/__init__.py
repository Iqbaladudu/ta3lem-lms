from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from payments.models import Order


class PaymentProviderBase(ABC):
    """
    Abstract base class for all payment providers.
    
    Each provider must implement these methods to integrate with
    the payment system.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize provider with configuration from PaymentProvider model"""
        self.config = config

    @abstractmethod
    def create_payment(
        self,
        order: 'Order',
        return_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """
        Create a payment for the given order.
        
        Returns dict with:
        - For redirect-based (Stripe/Midtrans): {'redirect_url': 'https://...'}
        - For manual transfer: {'type': 'manual_transfer', 'bank_accounts': [...], ...}
        """
        pass

    @abstractmethod
    def verify_payment(self, order: 'Order', data: Dict[str, Any]) -> bool:
        """
        Verify a payment (e.g., from return URL callback).
        Returns True if payment is verified successfully.
        """
        pass

    def handle_webhook(self, payload: bytes, headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Handle webhook/callback from payment gateway.
        Override in providers that support webhooks.
        
        Returns dict with:
        - 'success': bool
        - 'order_number': str (if success)
        - 'status': str ('completed', 'failed', etc.)
        - 'error': str (if failed)
        """
        raise NotImplementedError("This provider doesn't support webhooks")

    def supports_subscription(self) -> bool:
        """Whether this provider supports recurring payments"""
        return False

    def create_subscription(
        self,
        user: Any,
        plan: Any,
        return_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """Create a subscription. Override in providers that support subscriptions."""
        raise NotImplementedError("This provider doesn't support subscriptions")

    def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel a subscription. Override in providers that support subscriptions."""
        raise NotImplementedError("This provider doesn't support subscriptions")

    def process_refund(self, order: 'Order', amount: Decimal = None) -> bool:
        """Process a refund. Override in providers that support refunds."""
        raise NotImplementedError("This provider doesn't support refunds")


# Provider registry
_providers: Dict[str, type] = {}


def register_provider(provider_type: str, provider_class: type):
    """Register a payment provider class"""
    if not issubclass(provider_class, PaymentProviderBase):
        raise TypeError(f"{provider_class} must be a subclass of PaymentProviderBase")
    _providers[provider_type] = provider_class


def get_provider_class(provider_type: str) -> type:
    """Get a registered provider class by type"""
    if provider_type not in _providers:
        raise ValueError(f"Unknown provider type: {provider_type}")
    return _providers[provider_type]


def get_provider(provider_type: str, config: Dict[str, Any]) -> PaymentProviderBase:
    """Get an initialized provider instance"""
    provider_class = get_provider_class(provider_type)
    return provider_class(config)


# Import provider modules to trigger their registration
# These must come after the registry functions are defined
from . import manual  # noqa: F401, E402
from . import stripe  # noqa: F401, E402
from . import midtrans  # noqa: F401, E402
