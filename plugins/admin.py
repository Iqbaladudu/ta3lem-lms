"""
Plugin Admin Interface

Django admin configuration for managing plugins.
"""
from django.contrib import admin
from django.utils.html import format_html

from .models import PluginConfiguration, PluginHookLog
from .registry import plugin_registry


@admin.register(PluginConfiguration)
class PluginConfigurationAdmin(admin.ModelAdmin):
    """Admin interface for plugin configuration."""
    
    list_display = [
        'name', 
        'is_enabled_display', 
        'version_display', 
        'description_display',
        'updated_at'
    ]
    list_filter = ['is_enabled']
    search_fields = ['name']
    readonly_fields = ['name', 'installed_at', 'enabled_at', 'plugin_info']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'is_enabled', 'plugin_info')
        }),
        ('Configuration', {
            'fields': ('config',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('installed_at', 'enabled_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_enabled_display(self, obj):
        if obj.is_enabled:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Enabled</span>'
            )
        return format_html(
            '<span style="color: gray;">✗ Disabled</span>'
        )
    is_enabled_display.short_description = "Status"
    is_enabled_display.admin_order_field = 'is_enabled'
    
    def version_display(self, obj):
        plugin = plugin_registry.get(obj.name)
        if plugin:
            return plugin.version
        return format_html('<span style="color: red;">Not Loaded</span>')
    version_display.short_description = "Version"
    
    def description_display(self, obj):
        plugin = plugin_registry.get(obj.name)
        if plugin:
            return plugin.description[:50] + "..." if len(plugin.description) > 50 else plugin.description
        return "-"
    description_display.short_description = "Description"
    
    def plugin_info(self, obj):
        plugin = plugin_registry.get(obj.name)
        if not plugin:
            return format_html(
                '<span style="color: red;">Plugin not loaded in registry</span>'
            )
        
        return format_html(
            '''
            <table style="margin: 10px 0;">
                <tr><td><strong>Version:</strong></td><td>{}</td></tr>
                <tr><td><strong>Author:</strong></td><td>{}</td></tr>
                <tr><td><strong>Description:</strong></td><td>{}</td></tr>
                <tr><td><strong>Dependencies:</strong></td><td>{}</td></tr>
            </table>
            ''',
            plugin.version,
            plugin.author or 'Unknown',
            plugin.description or 'No description',
            ', '.join(plugin.requires) or 'None'
        )
    plugin_info.short_description = "Plugin Information"
    
    def has_add_permission(self, request):
        # Plugins are auto-discovered, not manually added
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion, just disable
        return False
    
    def save_model(self, request, obj, form, change):
        """Handle enable/disable through admin."""
        super().save_model(request, obj, form, change)
        
        # Sync with registry
        if obj.is_enabled:
            plugin_registry.enable_plugin(obj.name)
        else:
            plugin_registry.disable_plugin(obj.name)


@admin.register(PluginHookLog)
class PluginHookLogAdmin(admin.ModelAdmin):
    """Admin interface for hook execution logs."""
    
    list_display = [
        'hook_name', 
        'plugin_name', 
        'success_display', 
        'execution_time_ms',
        'created_at'
    ]
    list_filter = ['success', 'hook_name', 'plugin_name']
    search_fields = ['hook_name', 'plugin_name', 'error_message']
    readonly_fields = [
        'hook_name', 'plugin_name', 'execution_time_ms', 
        'success', 'error_message', 'created_at'
    ]
    
    def success_display(self, obj):
        if obj.success:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    success_display.short_description = "Success"
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
