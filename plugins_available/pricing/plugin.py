"""
Pricing Plugin for Ta3lem LMS

Enables one-time purchase and subscription pricing for courses.
This plugin provides:
- Pricing UI injection in course templates
- Payment redirect logic
- Price formatting utilities
"""
from plugins.base import PluginBase
from plugins.hooks import CoreHooks, hook


class PricingPlugin(PluginBase):
    """
    Plugin for course pricing functionality.
    Controls one-time purchase and subscription-based access.
    """
    
    name = "pricing"
    version = "1.0.0"
    description = "One-time purchase and pricing for courses"
    author = "Ta3lem Team"
    
    enabled_by_default = True
    requires = []  # No dependencies
    
    default_settings = {
        'enable_one_time_purchase': True,
        'min_price': 0,
        'max_price': 10000000,
        'default_currency': 'IDR',
        'show_original_price': True,  # Show strikethrough original price
    }
    
    def ready(self):
        """Initialize pricing plugin"""
        import logging
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Pricing plugin v{self.version} initialized")
    
    def on_enable(self):
        """Called when pricing is enabled"""
        import logging
        logging.getLogger(__name__).info("Pricing plugin enabled")
    
    def on_disable(self):
        """Called when pricing is disabled"""
        import logging
        logging.getLogger(__name__).info("Pricing plugin disabled")
    
    @hook(CoreHooks.TEMPLATE_COURSE_DETAIL, priority=10)
    def inject_pricing_ui(self, request=None, context=None, **kwargs):
        """
        Inject pricing options into course detail page.
        Returns HTML for the pricing section.
        """
        if not self.is_enabled:
            return ""
        
        course = context.get('course') if context else None
        if not course:
            return ""
        
        # Don't show pricing for free courses
        if course.is_free:
            return ""
        
        settings = self.get_settings()
        if not settings.get('enable_one_time_purchase', True):
            return ""
        
        # Return pricing UI hint (actual rendering done in templates)
        return f'<!-- pricing-enabled price="{course.get_formatted_price()}" -->'
    
    @hook(CoreHooks.PAYMENT_COMPLETED, priority=5)
    def on_payment_completed(self, user=None, order=None, **kwargs):
        """
        Handle successful payment.
        Creates enrollment for purchased course.
        """
        if not order:
            return
        
        self.logger.info(f"Pricing plugin: Payment completed for order {order.order_number}")
        
        # The actual enrollment is handled by Course.on_purchase_completed()
        # This hook is for additional processing (analytics, notifications, etc.)
        return {'plugin': 'pricing', 'status': 'processed'}


def is_pricing_enabled():
    """
    Helper function to check if pricing plugin is enabled.
    Can be used in views and templates.
    """
    from plugins.registry import plugin_registry
    plugin = plugin_registry.get('pricing')
    return plugin is not None and plugin.is_enabled


def get_pricing_settings():
    """Get current pricing plugin settings"""
    from plugins.registry import plugin_registry
    plugin = plugin_registry.get('pricing')
    if plugin and plugin.is_enabled:
        return plugin.get_settings()
    return {}
