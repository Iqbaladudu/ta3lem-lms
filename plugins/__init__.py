"""
Ta3lem Plugin System

A modular plugin architecture for extending LMS functionality.
"""
from .base import PluginBase
from .registry import plugin_registry
from .hooks import CoreHooks, trigger_hook, hook, trigger_template_hook, register_hook
from .decorators import requires_plugin, feature_enabled, with_plugin

__all__ = [
    # Core classes
    'PluginBase',
    'plugin_registry',
    
    # Hook system
    'CoreHooks',
    'trigger_hook',
    'trigger_template_hook',
    'register_hook',
    'hook',
    
    # Decorators
    'requires_plugin',
    'feature_enabled',
    'with_plugin',
]
