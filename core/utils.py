"""
Utility functions for accessing global settings
"""

from .models import GlobalSettings


def get_setting(key, default=None):
    """
    Get a specific setting value by key.
    
    Usage:
        from core.utils import get_setting
        
        site_name = get_setting('site_name')
        if get_setting('enable_subscriptions'):
            # do something
    """
    try:
        settings = GlobalSettings.get_settings()
        return getattr(settings, key, default)
    except Exception:
        return default


def is_feature_enabled(feature_name):
    """
    Check if a feature is enabled.
    
    Usage:
        from core.utils import is_feature_enabled
        
        if is_feature_enabled('subscriptions'):
            # subscription code
    """
    try:
        settings = GlobalSettings.get_settings()
        return settings.is_feature_enabled(feature_name)
    except Exception:
        return False


def is_maintenance_mode():
    """Check if site is in maintenance mode"""
    return get_setting('maintenance_mode', False)


def get_site_info():
    """
    Get basic site information.
    
    Returns dict with site_name, site_tagline, contact_email
    """
    try:
        settings = GlobalSettings.get_settings()
        return {
            'site_name': settings.site_name,
            'site_tagline': settings.site_tagline,
            'site_description': settings.site_description,
            'contact_email': settings.contact_email,
        }
    except Exception:
        return {
            'site_name': 'Ta3lem LMS',
            'site_tagline': 'Platform Belajar Online Terdepan',
            'site_description': '',
            'contact_email': 'support@ta3lem.com',
        }


def get_payment_settings():
    """Get payment-related settings"""
    try:
        settings = GlobalSettings.get_settings()
        return {
            'currency': settings.payment_currency,
            'commission_percentage': settings.platform_commission_percentage,
            'minimum_payout': settings.minimum_payout_amount,
        }
    except Exception:
        return {
            'currency': 'IDR',
            'commission_percentage': 20.00,
            'minimum_payout': 100000,
        }


def get_subscription_settings():
    """Get subscription-related settings"""
    try:
        settings = GlobalSettings.get_settings()
        return {
            'trial_enabled': settings.subscription_trial_enabled,
            'trial_days': settings.subscription_trial_days,
            'grace_period_days': settings.subscription_grace_period_days,
            'auto_renew': settings.subscription_auto_renew,
        }
    except Exception:
        return {
            'trial_enabled': True,
            'trial_days': 7,
            'grace_period_days': 3,
            'auto_renew': True,
        }
