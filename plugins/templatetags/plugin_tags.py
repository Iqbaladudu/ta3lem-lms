"""
Plugin Template Tags

Template tags for using plugin hooks in Django templates.
"""
from django import template
from django.utils.safestring import mark_safe

from plugins.hooks import trigger_template_hook
from plugins.registry import plugin_registry

register = template.Library()


@register.simple_tag(takes_context=True)
def plugin_hook(context, hook_name):
    """
    Trigger a plugin hook and return the combined output.
    
    Usage:
        {% load plugin_tags %}
        {% plugin_hook 'my_custom_hook' %}
    
    Args:
        context: Template context (automatically passed)
        hook_name: Name of the hook to trigger
    
    Returns:
        Combined HTML output from all hook handlers (marked safe)
    """
    request = context.get('request')
    content = trigger_template_hook(hook_name, request, dict(context.flatten()))
    return mark_safe(content)


@register.simple_tag
def is_plugin_enabled(plugin_name):
    """
    Check if a plugin is enabled.
    
    Usage:
        {% load plugin_tags %}
        {% is_plugin_enabled 'pricing' as pricing_enabled %}
        {% if pricing_enabled %}
            Show pricing UI
        {% endif %}
    
    Args:
        plugin_name: Name of the plugin to check
    
    Returns:
        Boolean indicating if plugin is enabled
    """
    plugin = plugin_registry.get(plugin_name)
    return plugin is not None and plugin.is_enabled


@register.simple_tag
def get_plugin_setting(plugin_name, setting_key, default=None):
    """
    Get a specific setting from a plugin.
    
    Usage:
        {% load plugin_tags %}
        {% get_plugin_setting 'pricing' 'default_currency' 'IDR' as currency %}
        {{ currency }}
    
    Args:
        plugin_name: Name of the plugin
        setting_key: Key of the setting to retrieve
        default: Default value if setting not found
    
    Returns:
        The setting value or default
    """
    plugin = plugin_registry.get(plugin_name)
    if plugin and plugin.is_enabled:
        settings = plugin.get_settings()
        return settings.get(setting_key, default)
    return default


@register.inclusion_tag('plugins/plugin_list.html')
def show_enabled_plugins():
    """
    Show list of enabled plugins (for debugging/admin).
    
    Usage:
        {% load plugin_tags %}
        {% show_enabled_plugins %}
    
    Returns:
        Rendered template with list of enabled plugins
    """
    return {
        'plugins': plugin_registry.enabled().values()
    }


@register.simple_tag(takes_context=True)
def plugin_content(context, plugin_name, method_name, **kwargs):
    """
    Call a specific method on a plugin and return its output.
    
    Usage:
        {% load plugin_tags %}
        {% plugin_content 'badges' 'render_widget' user=request.user %}
    
    Args:
        context: Template context
        plugin_name: Name of the plugin
        method_name: Method to call on the plugin
        **kwargs: Arguments to pass to the method
    
    Returns:
        Output from the plugin method
    """
    plugin = plugin_registry.get(plugin_name)
    if not plugin or not plugin.is_enabled:
        return ''
    
    method = getattr(plugin, method_name, None)
    if not callable(method):
        return ''
    
    request = context.get('request')
    try:
        result = method(request=request, context=dict(context.flatten()), **kwargs)
        return mark_safe(result) if result else ''
    except Exception:
        return ''
