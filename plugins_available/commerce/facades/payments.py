"""
Payment Facade

Wrapper for payments app functionality.
Returns safe defaults when commerce plugin is disabled.
"""
import logging

logger = logging.getLogger(__name__)


class PaymentFacade:
    """
    Facade for payment operations.
    Wraps payments.services.PaymentService with graceful degradation.
    """
    
    def __init__(self):
        self._service = None
    
    @property
    def service(self):
        """Lazy load PaymentService"""
        if self._service is None:
            try:
                from payments.services import PaymentService
                self._service = PaymentService
            except ImportError:
                logger.warning("PaymentService not available")
                self._service = False
        return self._service if self._service else None
    
    def is_available(self):
        """Check if payments are available"""
        from plugins_available.commerce.plugin import is_payments_enabled
        return is_payments_enabled() and self.service is not None
    
    def create_order(self, user, item, order_type='course', provider=None):
        """
        Create a new order.
        
        Args:
            user: User making the purchase
            item: Course, Bundle, or SubscriptionPlan
            order_type: 'course', 'bundle', or 'subscription'
            provider: Payment provider to use
        
        Returns:
            Order instance or None if failed/disabled
        """
        if not self.is_available():
            logger.warning("Payments disabled, cannot create order")
            return None
        
        try:
            return self.service.create_order(
                user=user,
                item=item,
                order_type=order_type,
                provider=provider
            )
        except Exception as e:
            logger.error(f"Failed to create order: {e}")
            return None
    
    def get_order(self, order_id=None, order_number=None):
        """
        Get order by ID or order number.
        
        Args:
            order_id: Order primary key
            order_number: Order number string
        
        Returns:
            Order instance or None
        """
        if not self.is_available():
            return None
        
        try:
            from payments.models import Order
            
            if order_id:
                return Order.objects.filter(pk=order_id).first()
            elif order_number:
                return Order.objects.filter(order_number=order_number).first()
            return None
        except Exception as e:
            logger.error(f"Failed to get order: {e}")
            return None
    
    def get_user_orders(self, user, status=None):
        """
        Get orders for a user.
        
        Args:
            user: User to get orders for
            status: Optional status filter
        
        Returns:
            QuerySet of orders or empty list
        """
        if not self.is_available():
            return []
        
        try:
            from payments.models import Order
            
            qs = Order.objects.filter(user=user)
            if status:
                qs = qs.filter(status=status)
            return qs
        except Exception:
            return []
    
    def complete_payment(self, order, gateway_payment_id=''):
        """
        Mark order as completed.
        
        Args:
            order: Order to complete
            gateway_payment_id: Payment gateway reference
        
        Returns:
            bool indicating success
        """
        if not self.is_available() or not order:
            return False
        
        try:
            order.mark_completed(gateway_payment_id=gateway_payment_id)
            return True
        except Exception as e:
            logger.error(f"Failed to complete payment: {e}")
            return False
    
    def get_available_providers(self, active_only=True):
        """
        Get available payment providers.
        
        Args:
            active_only: Only return active providers
        
        Returns:
            QuerySet of PaymentProvider or empty list
        """
        if not self.is_available():
            return []
        
        try:
            from payments.models import PaymentProvider
            
            qs = PaymentProvider.objects.all()
            if active_only:
                qs = qs.filter(is_active=True)
            return qs
        except Exception:
            return []


# =========================================
# Convenience functions
# =========================================

_facade = None


def get_payment_facade():
    """Get singleton PaymentFacade instance"""
    global _facade
    if _facade is None:
        _facade = PaymentFacade()
    return _facade


def create_order(user, item, order_type='course', provider=None):
    """Convenience function for creating orders"""
    return get_payment_facade().create_order(user, item, order_type, provider)


def get_order(order_id=None, order_number=None):
    """Convenience function for getting orders"""
    return get_payment_facade().get_order(order_id, order_number)


def get_user_orders(user, status=None):
    """Convenience function for getting user orders"""
    return get_payment_facade().get_user_orders(user, status)


def complete_payment(order, gateway_payment_id=''):
    """Convenience function for completing payments"""
    return get_payment_facade().complete_payment(order, gateway_payment_id)
