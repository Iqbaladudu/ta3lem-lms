"""
Plugin Base Class

Abstract base class that all Ta3lem plugins must inherit from.
Provides lifecycle hooks, configuration, and integration points.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from django.apps import AppConfig


class PluginBase(ABC):
    """
    Abstract base class for all Ta3lem plugins.
    
    Plugins must inherit from this class and implement required methods.
    
    Example:
        class MyPlugin(PluginBase):
            name = "my_plugin"
            version = "1.0.0"
            description = "My awesome plugin"
            
            def ready(self):
                # Plugin initialization
                pass
    """
    
    # Plugin metadata - MUST be defined by subclass
    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    
    # Plugin configuration
    enabled_by_default: bool = False
    requires: List[str] = []  # List of required plugin names
    
    # Default settings for this plugin
    default_settings: Dict[str, Any] = {}
    
    def __init__(self, app_config: 'AppConfig' = None):
        """
        Initialize plugin instance.
        
        Args:
            app_config: Django AppConfig for this plugin's app
        """
        self.app_config = app_config
        self._is_enabled = False
        self._settings: Dict[str, Any] = {}
    
    @abstractmethod
    def ready(self) -> None:
        """
        Called when plugin is loaded and enabled.
        
        Use this to:
        - Import signals
        - Register handlers
        - Initialize plugin state
        """
        pass
    
    def enable(self) -> None:
        """Enable the plugin."""
        self._is_enabled = True
        self.on_enable()
    
    def disable(self) -> None:
        """Disable the plugin."""
        self._is_enabled = False
        self.on_disable()
    
    def on_enable(self) -> None:
        """
        Hook called when plugin is enabled.
        Override in subclass for custom behavior.
        """
        pass
    
    def on_disable(self) -> None:
        """
        Hook called when plugin is disabled.
        Override in subclass for custom behavior.
        """
        pass
    
    @property
    def is_enabled(self) -> bool:
        """Check if plugin is currently enabled."""
        return self._is_enabled
    
    def get_urls(self) -> List:
        """
        Return URL patterns for this plugin.
        Override if plugin provides URL endpoints.
        
        Returns:
            List of URL patterns
        """
        return []
    
    def get_admin_urls(self) -> List:
        """
        Return admin URL patterns.
        Override if plugin provides admin endpoints.
        
        Returns:
            List of admin URL patterns
        """
        return []
    
    def get_template_context(self, request) -> Dict[str, Any]:
        """
        Return extra template context.
        Override to inject context into templates.
        
        Args:
            request: Django request object
            
        Returns:
            Dict of context variables
        """
        return {}
    
    def get_settings(self) -> Dict[str, Any]:
        """
        Return plugin settings merged with defaults.
        
        Returns:
            Dict of plugin settings
        """
        settings = self.default_settings.copy()
        settings.update(self._settings)
        return settings
    
    def update_settings(self, settings: Dict[str, Any]) -> None:
        """
        Update plugin settings.
        
        Args:
            settings: Dict of settings to update
        """
        self._settings.update(settings)
    
    def get_hooks(self) -> Dict[str, callable]:
        """
        Return hook handlers registered by this plugin.
        
        Scans for methods decorated with @hook decorator.
        
        Returns:
            Dict mapping hook names to handler functions
        """
        hooks = {}
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if callable(attr) and hasattr(attr, '_hook_name'):
                hooks[attr._hook_name] = attr
        return hooks
    
    def __repr__(self) -> str:
        status = "enabled" if self._is_enabled else "disabled"
        return f"<{self.__class__.__name__} '{self.name}' ({status})>"
