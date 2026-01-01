"""
Subscriptions Plugin for Ta3lem LMS

Enables subscription-based access to courses.
This plugin provides:
- Subscription plan display
- Subscription access checking
- Subscription-related hooks
"""
from plugins.base import PluginBase
from plugins.hooks import CoreHooks, hook


class SubscriptionsPlugin(PluginBase):
    """
    Plugin for subscription-based course access.
    Works in conjunction with the existing subscriptions app.
    """
    
    name = "subscriptions_feature"
    version = "1.0.0"
    description = "Subscription-based access to all courses"
    author = "Ta3lem Team"
    
    enabled_by_default = True
    requires = ["pricing"]  # Depends on pricing plugin
    
    default_settings = {
        'enable_trial': True,
        'trial_days': 7,
        'show_subscription_cta': True,
        'highlight_savings': True,
    }
    
    def ready(self):
        """Initialize subscriptions plugin"""
        import logging
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Subscriptions plugin v{self.version} initialized")
    
    def on_enable(self):
        """Called when subscriptions feature is enabled"""
        import logging
        logging.getLogger(__name__).info("Subscriptions plugin enabled")
    
    def on_disable(self):
        """Called when subscriptions feature is disabled"""
        import logging
        logging.getLogger(__name__).info("Subscriptions plugin disabled")
    
    @hook(CoreHooks.TEMPLATE_COURSE_DETAIL, priority=20)
    def inject_subscription_ui(self, request=None, context=None, **kwargs):
        """
        Inject subscription options into course detail page.
        Shows subscription CTA for subscription-enabled courses.
        """
        if not self.is_enabled:
            return ""
        
        course = context.get('course') if context else None
        if not course:
            return ""
        
        # Only show for subscription-compatible courses
        if not course.supports_subscription():
            return ""
        
        settings = self.get_settings()
        if not settings.get('show_subscription_cta', True):
            return ""
        
        # Check if user already has subscription
        if request and request.user.is_authenticated:
            if request.user.has_active_subscription():
                return '<!-- user-has-subscription -->'
        
        return '<!-- subscription-cta-enabled -->'
    
    @hook(CoreHooks.COURSE_ENROLLED, priority=10)
    def check_subscription_access(self, user=None, course=None, enrollment=None, **kwargs):
        """
        Verify subscription access on enrollment.
        Returns subscription status.
        """
        if not self.is_enabled or not user or not course:
            return None
        
        # Only relevant for subscription-only or both pricing types
        if course.pricing_type not in ['subscription_only', 'both']:
            return None
        
        try:
            from subscriptions.services import SubscriptionService
            has_subscription = SubscriptionService.user_has_active_subscription(user)
            
            return {
                'has_subscription': has_subscription,
                'can_access': has_subscription or enrollment.payment_status == 'paid'
            }
        except ImportError:
            self.logger.warning("Subscriptions app not available")
            return None
    
    @hook(CoreHooks.SUBSCRIPTION_CREATED, priority=5)
    def on_subscription_created(self, user=None, subscription=None, **kwargs):
        """Handle new subscription creation"""
        if not subscription:
            return
        
        self.logger.info(
            f"New subscription: {user.username} subscribed to {subscription.plan.name}"
        )
        return {'plugin': 'subscriptions_feature', 'status': 'processed'}
    
    @hook(CoreHooks.SUBSCRIPTION_CANCELLED, priority=5)
    def on_subscription_cancelled(self, user=None, subscription=None, **kwargs):
        """Handle subscription cancellation"""
        if not subscription:
            return
        
        self.logger.info(
            f"Subscription cancelled: {user.username} - {subscription.plan.name}"
        )
        return {'plugin': 'subscriptions_feature', 'status': 'processed'}


def is_subscriptions_enabled():
    """
    Helper function to check if subscriptions plugin is enabled.
    Can be used in views and templates.
    """
    from plugins.registry import plugin_registry
    plugin = plugin_registry.get('subscriptions_feature')
    return plugin is not None and plugin.is_enabled


def get_subscription_settings():
    """Get current subscription plugin settings"""
    from plugins.registry import plugin_registry
    plugin = plugin_registry.get('subscriptions_feature')
    if plugin and plugin.is_enabled:
        return plugin.get_settings()
    return {}
