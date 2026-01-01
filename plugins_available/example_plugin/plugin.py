"""
Example Plugin for Ta3lem LMS

This is a template plugin demonstrating how to create
plugins for the Ta3lem Learning Management System.

To create your own plugin:
1. Copy this directory as a template
2. Rename and update the plugin class
3. Implement your functionality
4. Add to INSTALLED_APPS or plugins_available/
"""
from plugins.base import PluginBase
from plugins.hooks import CoreHooks, hook


class ExamplePlugin(PluginBase):
    """
    Example plugin demonstrating plugin architecture.
    
    This plugin:
    - Logs when users complete courses
    - Adds a welcome message to templates
    """
    
    # Required: unique plugin identifier
    name = "example_plugin"
    
    # Metadata
    version = "1.0.0"
    description = "Example plugin demonstrating the plugin architecture"
    author = "Ta3lem Team"
    
    # Configuration
    enabled_by_default = False  # Must be explicitly enabled
    requires = []  # No dependencies
    
    # Default settings for this plugin
    default_settings = {
        'welcome_message': 'Welcome to Ta3lem LMS!',
        'log_completions': True,
    }
    
    def ready(self):
        """
        Called when plugin is loaded and enabled.
        Use this for initialization.
        """
        import logging
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Example plugin v{self.version} initialized")
    
    def on_enable(self):
        """Called when plugin is enabled."""
        import logging
        logging.getLogger(__name__).info("Example plugin enabled")
    
    def on_disable(self):
        """Called when plugin is disabled."""
        import logging
        logging.getLogger(__name__).info("Example plugin disabled")
    
    # === Hook Handlers ===
    
    @hook(CoreHooks.COURSE_COMPLETED, priority=10)
    def on_course_completed(self, user=None, course=None, enrollment=None, **kwargs):
        """
        Called when a user completes a course.
        
        Args:
            user: The user who completed the course
            course: The course that was completed
            enrollment: The enrollment record
        """
        settings = self.get_settings()
        
        if settings.get('log_completions', True):
            self.logger.info(
                f"Course completed: {user} finished {course}"
            )
        
        # Return value can be collected by the hook trigger
        return {
            'user_id': user.id if user else None,
            'course_id': course.id if course else None,
        }
    
    @hook(CoreHooks.TEMPLATE_BODY_END, priority=100)
    def inject_footer_content(self, request=None, **kwargs):
        """
        Inject content at the end of the body.
        
        Returns HTML to be included in templates.
        """
        settings = self.get_settings()
        message = settings.get('welcome_message', '')
        
        # Return HTML to inject
        return f'''
        <script>
            console.log("Example Plugin: {message}");
        </script>
        '''
    
    # === URL Patterns (optional) ===
    
    def get_urls(self):
        """
        Return URL patterns for this plugin.
        These will be included under /plugins/example_plugin/
        """
        # Example:
        # from django.urls import path
        # from . import views
        # return [
        #     path('dashboard/', views.dashboard, name='example_dashboard'),
        # ]
        return []
