"""
Commerce Plugin for Ta3lem LMS

Unified plugin for payments and subscriptions functionality.
Uses facade pattern to wrap existing apps without database changes.
"""
import logging
from plugins.base import PluginBase
from plugins.hooks import CoreHooks, hook


class CommercePlugin(PluginBase):
    """
    Unified commerce plugin controlling payments and subscriptions.
    """
    
    name = "commerce"
    version = "1.0.0"
    description = "Unified payments and subscription management"
    author = "Ta3lem Team"
    
    enabled_by_default = True
    requires = []
    
    default_settings = {
        # Payments
        'payments_enabled': True,
        'default_currency': 'IDR',
        'payment_expiry_hours': 24,
        
        # Subscriptions
        'subscriptions_enabled': True,
        'trial_days': 7,
        'show_subscription_cta': True,
        
        # UI
        'show_pricing_on_course': True,
        'highlight_savings': True,
    }
    
    def ready(self):
        """Initialize commerce plugin"""
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Commerce plugin v{self.version} initialized")
    
    def on_enable(self):
        """Called when commerce is enabled"""
        logging.getLogger(__name__).info("Commerce plugin enabled")
    
    def on_disable(self):
        """Called when commerce is disabled"""
        logging.getLogger(__name__).info("Commerce plugin disabled")
    
    # =========================================
    # Payment Hooks
    # =========================================
    
    @hook(CoreHooks.PAYMENT_COMPLETED, priority=5)
    def on_payment_completed(self, order=None, user=None, **kwargs):
        """
        Handle successful payment completion.
        Delegate to appropriate handler based on order type.
        """
        if not order:
            return None
        
        self.logger.info(f"Commerce: Payment completed for order {order.order_number}")
        
        if order.order_type == 'subscription':
            return self._handle_subscription_payment(order, user)
        elif order.order_type == 'course':
            return self._handle_course_payment(order, user)
        
        return {'plugin': 'commerce', 'status': 'processed'}
    
    def _handle_subscription_payment(self, order, user):
        """Handle subscription purchase"""
        try:
            from .facades.subscriptions import SubscriptionFacade
            facade = SubscriptionFacade()
            facade.activate_subscription(user, order)
            return {'type': 'subscription', 'activated': True}
        except Exception as e:
            self.logger.error(f"Subscription activation failed: {e}")
            return {'type': 'subscription', 'error': str(e)}
    
    def _handle_course_payment(self, order, user):
        """Handle course purchase - enrollment handled by courses app"""
        return {'type': 'course', 'status': 'delegated_to_courses'}
    
    # =========================================
    # Subscription Hooks
    # =========================================
    
    @hook(CoreHooks.SUBSCRIPTION_CREATED, priority=10)
    def on_subscription_created(self, subscription=None, user=None, **kwargs):
        """Log new subscription creation"""
        if not subscription:
            return
        
        self.logger.info(f"New subscription: {user} - {subscription.plan.name}")
        return {'plugin': 'commerce', 'event': 'subscription_created'}
    
    @hook(CoreHooks.SUBSCRIPTION_CANCELLED, priority=10)
    def on_subscription_cancelled(self, subscription=None, user=None, **kwargs):
        """Log subscription cancellation"""
        if not subscription:
            return
        
        self.logger.info(f"Subscription cancelled: {user} - {subscription.plan.name}")
        return {'plugin': 'commerce', 'event': 'subscription_cancelled'}
    
    # =========================================
    # Template Hooks
    # =========================================
    
    @hook(CoreHooks.TEMPLATE_COURSE_DETAIL, priority=15)
    def inject_pricing_ui(self, request=None, context=None, **kwargs):
        """Inject pricing/subscription UI into course detail"""
        if not self.is_enabled:
            return ""
        
        course = context.get('course') if context else None
        if not course or course.is_free:
            return ""
        
        settings = self.get_settings()
        if not settings.get('show_pricing_on_course', True):
            return ""
        
        # Return marker for template processing
        return '<!-- commerce-pricing-enabled -->'
    
    # =========================================
    # API Methods (for facades to use)
    # =========================================
    
    def is_payments_enabled(self):
        """Check if payments feature is enabled"""
        if not self.is_enabled:
            return False
        return self.get_settings().get('payments_enabled', True)
    
    def is_subscriptions_enabled(self):
        """Check if subscriptions feature is enabled"""
        if not self.is_enabled:
            return False
        return self.get_settings().get('subscriptions_enabled', True)


# =========================================
# Helper functions for external use
# =========================================

def is_commerce_enabled():
    """Check if commerce plugin is enabled"""
    from plugins.registry import plugin_registry
    plugin = plugin_registry.get('commerce')
    return plugin is not None and plugin.is_enabled


def is_payments_enabled():
    """Check if payments are enabled"""
    from plugins.registry import plugin_registry
    plugin = plugin_registry.get('commerce')
    if not plugin or not plugin.is_enabled:
        return False
    return plugin.is_payments_enabled()


def is_subscriptions_enabled():
    """Check if subscriptions are enabled"""
    from plugins.registry import plugin_registry
    plugin = plugin_registry.get('commerce')
    if not plugin or not plugin.is_enabled:
        return False
    return plugin.is_subscriptions_enabled()


def get_commerce_settings():
    """Get commerce plugin settings"""
    from plugins.registry import plugin_registry
    plugin = plugin_registry.get('commerce')
    if plugin and plugin.is_enabled:
        return plugin.get_settings()
    return {}
