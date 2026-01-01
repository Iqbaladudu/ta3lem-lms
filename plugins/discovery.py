"""
Plugin Discovery

Automatic discovery and initialization of plugins from 
installed Django apps and custom plugin directories.
"""
import importlib
import logging
from pathlib import Path
from typing import List, Type, Optional

from django.apps import apps
from django.conf import settings

from .base import PluginBase
from .registry import plugin_registry
from .models import PluginConfiguration

logger = logging.getLogger(__name__)


def discover_plugins() -> List[str]:
    """
    Discover and register all available plugins.
    
    Searches for plugins in:
    1. INSTALLED_APPS that have a plugin.py file
    2. Custom plugin directories from settings.PLUGINS['PLUGIN_DIRS']
    
    Returns:
        List of discovered plugin names
    """
    discovered = []
    
    # Get plugin settings
    plugin_settings = getattr(settings, 'PLUGINS', {})
    auto_discover = plugin_settings.get('AUTO_DISCOVER', True)
    plugin_dirs = plugin_settings.get('PLUGIN_DIRS', [])
    enabled_plugins = plugin_settings.get('ENABLED_PLUGINS', [])
    
    if auto_discover:
        # Discover from installed apps
        discovered.extend(_discover_from_apps())
    
    # Discover from custom directories
    for plugin_dir in plugin_dirs:
        discovered.extend(_discover_from_directory(plugin_dir))
    
    # Enable plugins based on settings and database
    _enable_configured_plugins(enabled_plugins)
    
    logger.info(f"Discovered {len(discovered)} plugins: {discovered}")
    return discovered


def _discover_from_apps() -> List[str]:
    """Discover plugins from installed Django apps."""
    discovered = []
    
    for app_config in apps.get_app_configs():
        # Skip Django's own apps and plugins app itself
        if app_config.name.startswith('django.') or app_config.name == 'plugins':
            continue
        
        # Try to import plugin.py from the app
        try:
            plugin_module = importlib.import_module(f"{app_config.name}.plugin")
            plugin_class = _find_plugin_class(plugin_module)
            
            if plugin_class:
                plugin = plugin_registry.register(plugin_class, app_config)
                if plugin:
                    discovered.append(plugin.name)
                    
        except ImportError:
            # No plugin.py in this app, that's fine
            pass
        except Exception as e:
            logger.error(f"Error loading plugin from {app_config.name}: {e}")
    
    return discovered


def _discover_from_directory(plugin_dir) -> List[str]:
    """Discover plugins from a custom directory."""
    discovered = []
    path = Path(plugin_dir)
    
    if not path.exists():
        logger.warning(f"Plugin directory does not exist: {plugin_dir}")
        return discovered
    
    for item in path.iterdir():
        if item.is_dir() and (item / 'plugin.py').exists():
            try:
                # Add to Python path if needed
                import sys
                if str(path) not in sys.path:
                    sys.path.insert(0, str(path))
                
                # Import plugin module
                plugin_module = importlib.import_module(f"{item.name}.plugin")
                plugin_class = _find_plugin_class(plugin_module)
                
                if plugin_class:
                    plugin = plugin_registry.register(plugin_class)
                    if plugin:
                        discovered.append(plugin.name)
                        
            except Exception as e:
                logger.error(f"Error loading plugin from {item}: {e}")
    
    return discovered


def _find_plugin_class(module) -> Optional[Type[PluginBase]]:
    """Find a PluginBase subclass in a module."""
    for name in dir(module):
        obj = getattr(module, name)
        if (isinstance(obj, type) and 
            issubclass(obj, PluginBase) and 
            obj is not PluginBase and
            obj.name):  # Must have a name
            return obj
    return None


def _enable_configured_plugins(enabled_plugins: List[str]) -> None:
    """Enable plugins based on settings and database configuration."""
    # Check if database is ready by trying a simple operation
    db_ready = False
    try:
        from django.db import connection
        from django.db.utils import OperationalError, ProgrammingError
        
        # Check if the table exists
        table_names = connection.introspection.table_names()
        if 'plugins_pluginconfiguration' in table_names:
            db_ready = True
            _sync_plugin_configs()
    except (OperationalError, ProgrammingError, Exception) as e:
        # Database might not be ready yet (migrations not run)
        logger.debug(f"Database not ready for plugin config: {e}")
        db_ready = False
    
    if db_ready:
        # Enable based on database configuration
        try:
            for config in PluginConfiguration.objects.filter(is_enabled=True):
                plugin = plugin_registry.get(config.name)
                if plugin:
                    plugin.update_settings(config.config)
                    plugin_registry.enable_plugin(config.name)
        except Exception as e:
            logger.warning(f"Could not load plugin configs from database: {e}")
    
    # Also enable any from settings that aren't enabled yet
    for name in enabled_plugins:
        plugin = plugin_registry.get(name)
        if plugin and not plugin.is_enabled:
            plugin_registry.enable_plugin(name)


def _sync_plugin_configs() -> None:
    """Sync registered plugins with database configurations."""
    for name, plugin in plugin_registry.all().items():
        config, created = PluginConfiguration.objects.get_or_create(
            name=name,
            defaults={
                'is_enabled': plugin.enabled_by_default,
                'config': plugin.default_settings,
            }
        )
        if created:
            logger.info(f"Created configuration for plugin: {name}")

