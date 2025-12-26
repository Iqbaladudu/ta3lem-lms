"""
Context processor to make global settings available in all templates
"""

from .models import GlobalSettings


def global_settings(request):
    """
    Add global settings to template context.
    
    Usage in templates:
        {{ settings.site_name }}
        {{ settings.enable_subscriptions }}
        etc.
    """
    return {
        'settings': GlobalSettings.get_settings()
    }
