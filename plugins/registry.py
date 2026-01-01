"""
Plugin Registry

Central registry for managing all plugins.
Thread-safe plugin registration, lookup, and hook execution.
"""
import logging
from typing import Dict, List, Type, Optional, Tuple, Any
from threading import Lock

from .base import PluginBase

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Singleton registry for managing all plugins.
    
    Provides:
    - Plugin registration and lookup
    - Hook registration and execution
    - Plugin dependency checking
    - Thread-safe operations
    """
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._plugins: Dict[str, PluginBase] = {}
                cls._instance._hooks: Dict[str, List[Tuple[int, callable]]] = {}
                cls._instance._initialized = False
            return cls._instance
    
    def register(self, plugin_class: Type[PluginBase], 
                 app_config=None) -> Optional[PluginBase]:
        """
        Register a plugin class.
        
        Args:
            plugin_class: Plugin class to register (must inherit from PluginBase)
            app_config: Optional Django AppConfig for the plugin
            
        Returns:
            Instantiated plugin or None if registration failed
            
        Raises:
            ValueError: If plugin has no name or missing dependencies
        """
        if not plugin_class.name:
            raise ValueError(f"Plugin {plugin_class} must have a 'name' attribute")
        
        if plugin_class.name in self._plugins:
            logger.warning(f"Plugin '{plugin_class.name}' already registered, skipping")
            return self._plugins[plugin_class.name]
        
        # Check dependencies
        for req in plugin_class.requires:
            if req not in self._plugins:
                logger.error(
                    f"Plugin '{plugin_class.name}' requires '{req}' which is not loaded"
                )
                raise ValueError(
                    f"Plugin '{plugin_class.name}' requires '{req}' which is not loaded"
                )
        
        # Instantiate plugin
        plugin = plugin_class(app_config)
        self._plugins[plugin_class.name] = plugin
        
        # Register plugin's hooks
        for hook_name, handler in plugin.get_hooks().items():
            self.register_hook(hook_name, handler)
        
        logger.info(f"Registered plugin: {plugin_class.name} v{plugin_class.version}")
        return plugin
    
    def unregister(self, name: str) -> bool:
        """
        Unregister a plugin by name.
        
        Args:
            name: Plugin name to unregister
            
        Returns:
            True if plugin was unregistered, False if not found
        """
        if name in self._plugins:
            plugin = self._plugins[name]
            if plugin.is_enabled:
                plugin.disable()
            del self._plugins[name]
            logger.info(f"Unregistered plugin: {name}")
            return True
        return False
    
    def get(self, name: str) -> Optional[PluginBase]:
        """
        Get a plugin by name.
        
        Args:
            name: Plugin name
            
        Returns:
            Plugin instance or None if not found
        """
        return self._plugins.get(name)
    
    def all(self) -> Dict[str, PluginBase]:
        """
        Get all registered plugins.
        
        Returns:
            Dict mapping plugin names to instances
        """
        return self._plugins.copy()
    
    def enabled(self) -> Dict[str, PluginBase]:
        """
        Get all enabled plugins.
        
        Returns:
            Dict of enabled plugins
        """
        return {k: v for k, v in self._plugins.items() if v.is_enabled}
    
    def enable_plugin(self, name: str) -> bool:
        """
        Enable a plugin by name.
        
        Args:
            name: Plugin name to enable
            
        Returns:
            True if enabled, False if not found
        """
        plugin = self.get(name)
        if plugin:
            plugin.enable()
            plugin.ready()
            logger.info(f"Enabled plugin: {name}")
            return True
        return False
    
    def disable_plugin(self, name: str) -> bool:
        """
        Disable a plugin by name.
        
        Args:
            name: Plugin name to disable
            
        Returns:
            True if disabled, False if not found
        """
        plugin = self.get(name)
        if plugin:
            plugin.disable()
            logger.info(f"Disabled plugin: {name}")
            return True
        return False
    
    def register_hook(self, hook_name: str, handler: callable, 
                      priority: int = 10) -> None:
        """
        Register a hook handler with priority.
        
        Args:
            hook_name: Name of hook to attach to
            handler: Callable to execute when hook is triggered
            priority: Lower numbers execute first (default: 10)
        """
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        self._hooks[hook_name].append((priority, handler))
        # Sort by priority (lower first)
        self._hooks[hook_name].sort(key=lambda x: x[0])
    
    def execute_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """
        Execute all handlers for a hook.
        
        Args:
            hook_name: Name of hook to execute
            *args, **kwargs: Arguments to pass to handlers
            
        Returns:
            List of non-None results from handlers
        """
        results = []
        for priority, handler in self._hooks.get(hook_name, []):
            try:
                result = handler(*args, **kwargs)
                if result is not None:
                    results.append(result)
            except Exception as e:
                logger.error(f"Error in hook handler {handler} for {hook_name}: {e}")
        return results
    
    def get_hooks(self, hook_name: str) -> List[Tuple[int, callable]]:
        """
        Get all handlers for a hook.
        
        Args:
            hook_name: Name of hook
            
        Returns:
            List of (priority, handler) tuples
        """
        return self._hooks.get(hook_name, []).copy()
    
    def clear(self) -> None:
        """Clear all plugins and hooks. Use with caution."""
        for plugin in self._plugins.values():
            if plugin.is_enabled:
                plugin.disable()
        self._plugins.clear()
        self._hooks.clear()
        logger.info("Plugin registry cleared")


# Global registry instance
plugin_registry = PluginRegistry()
