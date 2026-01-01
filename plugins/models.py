"""
Plugin Configuration Models

Database models for storing plugin state and configuration.
"""
from django.db import models
from django.utils import timezone


class PluginConfiguration(models.Model):
    """
    Store plugin enable/disable state and configuration.
    
    Each registered plugin gets a corresponding configuration record
    that persists its enabled state and custom settings.
    """
    
    name = models.CharField(
        max_length=100, 
        unique=True, 
        db_index=True,
        help_text="Unique identifier for the plugin"
    )
    is_enabled = models.BooleanField(
        default=False,
        help_text="Whether the plugin is currently active"
    )
    config = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Plugin-specific configuration as JSON"
    )
    
    # Metadata
    installed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    enabled_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Plugin Configuration"
        verbose_name_plural = "Plugin Configurations"
        ordering = ['name']
    
    def __str__(self):
        status = "enabled" if self.is_enabled else "disabled"
        return f"{self.name} ({status})"
    
    def save(self, *args, **kwargs):
        # Track when plugin was enabled
        if self.is_enabled and not self.enabled_at:
            self.enabled_at = timezone.now()
        elif not self.is_enabled:
            self.enabled_at = None
        super().save(*args, **kwargs)


class PluginHookLog(models.Model):
    """
    Optional: Log hook executions for debugging and analytics.
    Only enabled in debug mode or for specific hooks.
    """
    
    hook_name = models.CharField(max_length=100, db_index=True)
    plugin_name = models.CharField(max_length=100, blank=True)
    execution_time_ms = models.FloatField(default=0)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Plugin Hook Log"
        verbose_name_plural = "Plugin Hook Logs"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['hook_name', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.hook_name} @ {self.created_at}"
