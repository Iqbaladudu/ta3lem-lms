"""
Subscription Facade

Wrapper for subscriptions app functionality.
Returns safe defaults when commerce plugin is disabled.
"""
import logging

logger = logging.getLogger(__name__)


class SubscriptionFacade:
    """
    Facade for subscription operations.
    Wraps subscriptions.services.SubscriptionService with graceful degradation.
    """
    
    def __init__(self):
        self._service = None
    
    @property
    def service(self):
        """Lazy load SubscriptionService"""
        if self._service is None:
            try:
                from subscriptions.services import SubscriptionService
                self._service = SubscriptionService
            except ImportError:
                logger.warning("SubscriptionService not available")
                self._service = False
        return self._service if self._service else None
    
    def is_available(self):
        """Check if subscriptions are available"""
        from plugins_available.commerce.plugin import is_subscriptions_enabled
        return is_subscriptions_enabled() and self.service is not None
    
    def get_active_subscription(self, user):
        """
        Get user's active subscription.
        
        Args:
            user: User to check
        
        Returns:
            UserSubscription or None
        """
        if not self.is_available() or not user:
            return None
        
        try:
            return self.service.get_active_subscription(user)
        except Exception as e:
            logger.error(f"Failed to get subscription: {e}")
            return None
    
    def has_active_subscription(self, user):
        """
        Check if user has active subscription.
        
        Args:
            user: User to check
        
        Returns:
            bool
        """
        if not self.is_available() or not user:
            return False
        
        try:
            return self.service.user_has_active_subscription(user)
        except Exception as e:
            logger.error(f"Failed to check subscription: {e}")
            return False
    
    def user_has_active_subscription(self, user):
        """Alias for has_active_subscription"""
        return self.has_active_subscription(user)
    
    def create_subscription(self, user, plan, order=None):
        """
        Create subscription for user.
        
        Args:
            user: User to subscribe
            plan: SubscriptionPlan
            order: Optional related Order
        
        Returns:
            UserSubscription or None
        """
        if not self.is_available():
            logger.warning("Subscriptions disabled")
            return None
        
        try:
            return self.service.create_subscription(user, plan, order)
        except Exception as e:
            logger.error(f"Failed to create subscription: {e}")
            return None
    
    def activate_subscription(self, user, order):
        """
        Activate subscription from completed order.
        
        Args:
            user: User to activate for
            order: Completed payment order
        
        Returns:
            UserSubscription or None
        """
        if not self.is_available() or not order:
            return None
        
        try:
            # Get plan from order item
            plan = order.item
            return self.service.create_subscription(user, plan, order)
        except Exception as e:
            logger.error(f"Failed to activate subscription: {e}")
            return None
    
    def cancel_subscription(self, subscription, immediately=False, reason=''):
        """
        Cancel a subscription.
        
        Args:
            subscription: UserSubscription to cancel
            immediately: If True, cancel now. Otherwise at period end.
            reason: Cancellation reason
        
        Returns:
            bool indicating success
        """
        if not self.is_available() or not subscription:
            return False
        
        try:
            subscription.cancel(immediately=immediately, reason=reason)
            return True
        except Exception as e:
            logger.error(f"Failed to cancel subscription: {e}")
            return False
    
    def get_available_plans(self, active_only=True):
        """
        Get available subscription plans.
        
        Args:
            active_only: Only return active plans
        
        Returns:
            QuerySet of SubscriptionPlan or empty list
        """
        if not self.is_available():
            return []
        
        try:
            from subscriptions.models import SubscriptionPlan
            
            qs = SubscriptionPlan.objects.all()
            if active_only:
                qs = qs.filter(is_active=True)
            return qs.order_by('display_order', 'price')
        except Exception:
            return []
    
    def can_access_course(self, user, course):
        """
        Check if user can access course via subscription.
        
        Args:
            user: User to check
            course: Course to check access for
        
        Returns:
            bool
        """
        if not self.is_available():
            return False
        
        # Check if course supports subscription access
        if not hasattr(course, 'pricing_type'):
            return False
        
        if course.pricing_type not in ['subscription_only', 'both']:
            return False
        
        return self.has_active_subscription(user)


# =========================================
# Convenience functions
# =========================================

_facade = None


def get_subscription_facade():
    """Get singleton SubscriptionFacade instance"""
    global _facade
    if _facade is None:
        _facade = SubscriptionFacade()
    return _facade


def has_active_subscription(user):
    """Check if user has active subscription"""
    return get_subscription_facade().has_active_subscription(user)


def user_has_active_subscription(user):
    """Alias for has_active_subscription"""
    return has_active_subscription(user)


def get_active_subscription(user):
    """Get user's active subscription"""
    return get_subscription_facade().get_active_subscription(user)


def can_access_via_subscription(user, course):
    """Check if user can access course via subscription"""
    return get_subscription_facade().can_access_course(user, course)


def get_available_plans(active_only=True):
    """Get available subscription plans"""
    return get_subscription_facade().get_available_plans(active_only)
