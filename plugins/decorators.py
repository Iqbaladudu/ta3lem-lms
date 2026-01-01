"""
Plugin Decorators

Decorators for views and functions that require specific plugins.
"""
from functools import wraps

from django.http import HttpResponseNotFound, JsonResponse

from plugins.registry import plugin_registry


def requires_plugin(plugin_name, json_response=False):
    """
    View decorator that requires a specific plugin to be enabled.
    
    Usage:
        @requires_plugin('pricing')
        def purchase_view(request):
            # Only accessible if pricing plugin is enabled
            pass
        
        @requires_plugin('api', json_response=True)
        def api_endpoint(request):
            # Returns JSON error if plugin disabled
            pass
    
    Args:
        plugin_name: Name of the required plugin
        json_response: If True, return JSON error instead of HTML 404
    
    Returns:
        Decorated view function
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            plugin = plugin_registry.get(plugin_name)
            
            if not plugin or not plugin.is_enabled:
                if json_response:
                    return JsonResponse({
                        'error': 'Feature not available',
                        'plugin': plugin_name,
                        'enabled': False
                    }, status=404)
                return HttpResponseNotFound(
                    f"<h1>Feature Not Available</h1>"
                    f"<p>The '{plugin_name}' feature is currently disabled.</p>"
                )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def feature_enabled(plugin_name):
    """
    General decorator for any function that requires a plugin.
    
    Usage:
        @feature_enabled('analytics')
        def track_event(event_name, data):
            # Only runs if analytics plugin is enabled
            pass
    
    Args:
        plugin_name: Name of the required plugin
    
    Returns:
        Decorated function that returns None if plugin disabled
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            plugin = plugin_registry.get(plugin_name)
            
            if not plugin or not plugin.is_enabled:
                return None
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def with_plugin(plugin_name):
    """
    Class decorator that adds plugin instance to class.
    
    Usage:
        @with_plugin('pricing')
        class PricingService:
            def get_price(self, course):
                if self.plugin.is_enabled:
                    return course.price
                return None
    
    Args:
        plugin_name: Name of the plugin to inject
    
    Returns:
        Decorated class with `plugin` attribute
    """
    def decorator(cls):
        original_init = cls.__init__
        
        def new_init(self, *args, **kwargs):
            self.plugin = plugin_registry.get(plugin_name)
            original_init(self, *args, **kwargs)
        
        cls.__init__ = new_init
        return cls
    return decorator
