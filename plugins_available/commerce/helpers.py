"""
Commerce Helpers

Helper functions for use in views and templates.
Provides safe access to commerce features with graceful degradation.
"""


def is_commerce_enabled():
    """Check if commerce plugin is enabled"""
    try:
        from plugins_available.commerce.plugin import is_commerce_enabled as _check
        return _check()
    except ImportError:
        return False


def is_payments_enabled():
    """Check if payments are enabled"""
    try:
        from plugins_available.commerce.plugin import is_payments_enabled as _check
        return _check()
    except ImportError:
        return False


def is_subscriptions_enabled():
    """Check if subscriptions are enabled"""
    try:
        from plugins_available.commerce.plugin import is_subscriptions_enabled as _check
        return _check()
    except ImportError:
        return False


def get_user_subscription_status(user):
    """
    Get user's subscription status for templates.
    
    Returns dict with subscription info or empty dict if disabled.
    """
    if not user or not user.is_authenticated:
        return {'has_subscription': False}
    
    if not is_subscriptions_enabled():
        return {'has_subscription': False, 'disabled': True}
    
    try:
        from .facades.subscriptions import get_subscription_facade
        facade = get_subscription_facade()
        
        subscription = facade.get_active_subscription(user)
        if subscription:
            return {
                'has_subscription': True,
                'subscription': subscription,
                'plan_name': subscription.plan.name,
                'days_remaining': subscription.days_remaining(),
                'expires_at': subscription.current_period_end,
            }
        return {'has_subscription': False}
    except Exception:
        return {'has_subscription': False, 'error': True}


def get_course_pricing_info(course, user=None):
    """
    Get pricing info for a course.
    
    Returns dict with pricing details for template display.
    """
    if not course:
        return {}
    
    info = {
        'is_free': course.is_free,
        'price': course.price if hasattr(course, 'price') else 0,
        'formatted_price': course.get_formatted_price() if hasattr(course, 'get_formatted_price') else '',
        'pricing_type': getattr(course, 'pricing_type', 'free'),
    }
    
    # Check commerce status
    info['commerce_enabled'] = is_commerce_enabled()
    info['payments_enabled'] = is_payments_enabled()
    info['subscriptions_enabled'] = is_subscriptions_enabled()
    
    # Check user access
    if user and user.is_authenticated:
        info['is_enrolled'] = course.is_user_enrolled(user) if hasattr(course, 'is_user_enrolled') else False
        
        if is_subscriptions_enabled():
            from .facades.subscriptions import has_active_subscription
            info['has_subscription'] = has_active_subscription(user)
            info['can_access_via_subscription'] = (
                info['has_subscription'] and 
                getattr(course, 'pricing_type', '') in ['subscription_only', 'both']
            )
    else:
        info['is_enrolled'] = False
        info['has_subscription'] = False
        info['can_access_via_subscription'] = False
    
    return info


def get_checkout_context(request, item, order_type='course'):
    """
    Get context for checkout page.
    
    Args:
        request: HTTP request
        item: Course or SubscriptionPlan
        order_type: 'course' or 'subscription'
    
    Returns:
        Dict with checkout context
    """
    if not is_payments_enabled():
        return {'payments_disabled': True}
    
    try:
        from .facades.payments import get_payment_facade
        facade = get_payment_facade()
        
        return {
            'item': item,
            'order_type': order_type,
            'providers': facade.get_available_providers(),
            'currency': item.get_currency() if hasattr(item, 'get_currency') else 'IDR',
            'amount': item.get_price() if hasattr(item, 'get_price') else item.price,
        }
    except Exception as e:
        return {'error': str(e)}
