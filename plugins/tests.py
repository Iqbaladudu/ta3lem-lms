"""
Plugin Tests

Unit tests for the plugin system.
"""
from django.test import TestCase, override_settings
from unittest.mock import MagicMock, patch

from .base import PluginBase
from .registry import PluginRegistry
from .hooks import CoreHooks, hook, trigger_hook, register_hook


class TestPlugin(PluginBase):
    """Test plugin for unit tests."""
    name = "test_plugin"
    version = "1.0.0"
    description = "A test plugin"
    author = "Test Author"
    
    def ready(self):
        pass


class DependentPlugin(PluginBase):
    """Plugin with dependencies for testing."""
    name = "dependent_plugin"
    version = "1.0.0"
    requires = ["test_plugin"]
    
    def ready(self):
        pass


class PluginBaseTestCase(TestCase):
    """Tests for PluginBase class."""
    
    def test_plugin_initialization(self):
        """Test plugin can be initialized."""
        plugin = TestPlugin()
        self.assertEqual(plugin.name, "test_plugin")
        self.assertEqual(plugin.version, "1.0.0")
        self.assertFalse(plugin.is_enabled)
    
    def test_plugin_enable_disable(self):
        """Test plugin enable/disable lifecycle."""
        plugin = TestPlugin()
        
        plugin.enable()
        self.assertTrue(plugin.is_enabled)
        
        plugin.disable()
        self.assertFalse(plugin.is_enabled)
    
    def test_plugin_hooks_discovery(self):
        """Test that @hook decorated methods are discovered."""
        
        class PluginWithHooks(PluginBase):
            name = "hook_plugin"
            
            def ready(self):
                pass
            
            @hook(CoreHooks.COURSE_COMPLETED)
            def on_course_completed(self, **kwargs):
                return "completed"
        
        plugin = PluginWithHooks()
        hooks = plugin.get_hooks()
        
        self.assertIn(CoreHooks.COURSE_COMPLETED.value, hooks)


class PluginRegistryTestCase(TestCase):
    """Tests for PluginRegistry class."""
    
    def setUp(self):
        self.registry = PluginRegistry()
        self.registry.clear()
    
    def tearDown(self):
        self.registry.clear()
    
    def test_register_plugin(self):
        """Test plugin registration."""
        plugin = self.registry.register(TestPlugin)
        
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.name, "test_plugin")
        self.assertIn("test_plugin", self.registry.all())
    
    def test_get_plugin(self):
        """Test getting plugin by name."""
        self.registry.register(TestPlugin)
        
        plugin = self.registry.get("test_plugin")
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.name, "test_plugin")
        
        none_plugin = self.registry.get("nonexistent")
        self.assertIsNone(none_plugin)
    
    def test_enable_disable_plugin(self):
        """Test enabling/disabling through registry."""
        self.registry.register(TestPlugin)
        
        self.registry.enable_plugin("test_plugin")
        self.assertTrue(self.registry.get("test_plugin").is_enabled)
        self.assertIn("test_plugin", self.registry.enabled())
        
        self.registry.disable_plugin("test_plugin")
        self.assertFalse(self.registry.get("test_plugin").is_enabled)
        self.assertNotIn("test_plugin", self.registry.enabled())
    
    def test_dependency_check(self):
        """Test that dependencies are checked during registration."""
        # Should fail because test_plugin is not registered
        with self.assertRaises(ValueError):
            self.registry.register(DependentPlugin)
        
        # Should succeed after registering dependency
        self.registry.register(TestPlugin)
        plugin = self.registry.register(DependentPlugin)
        self.assertIsNotNone(plugin)


class HooksTestCase(TestCase):
    """Tests for hook system."""
    
    def setUp(self):
        self.registry = PluginRegistry()
        self.registry.clear()
    
    def tearDown(self):
        self.registry.clear()
    
    def test_register_and_trigger_hook(self):
        """Test registering and triggering hooks."""
        results = []
        
        def handler(**kwargs):
            results.append("called")
            return "result"
        
        register_hook(CoreHooks.COURSE_COMPLETED, handler)
        
        trigger_results = trigger_hook(CoreHooks.COURSE_COMPLETED, user="test")
        
        self.assertEqual(len(results), 1)
        self.assertIn("result", trigger_results)
    
    def test_hook_priority(self):
        """Test hooks execute in priority order."""
        call_order = []
        
        def handler1(**kwargs):
            call_order.append("handler1")
        
        def handler2(**kwargs):
            call_order.append("handler2")
        
        def handler3(**kwargs):
            call_order.append("handler3")
        
        register_hook("test.priority", handler2, priority=10)
        register_hook("test.priority", handler1, priority=5)
        register_hook("test.priority", handler3, priority=15)
        
        trigger_hook("test.priority")
        
        self.assertEqual(call_order, ["handler1", "handler2", "handler3"])
    
    def test_hook_decorator(self):
        """Test @hook decorator."""
        
        @hook(CoreHooks.USER_REGISTERED)
        def on_user_registered(**kwargs):
            return "registered"
        
        self.assertEqual(on_user_registered._hook_name, CoreHooks.USER_REGISTERED.value)
