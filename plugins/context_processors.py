"""
Plugin Context Processors

Injects plugin-related variables into template context.
"""
from .registry import plugin_registry
from .hooks import trigger_template_hook, CoreHooks


def plugins_context(request):
    """
    Add plugin-related context to all templates.
    
    Provides:
    - enabled_plugins: Dict of enabled plugins
    - template_hooks: Object for accessing template hooks
    """
    
    class TemplateHooks:
        """Helper class for triggering template hooks in templates."""
        
        def __init__(self, request):
            self._request = request
        
        def _get_hook_content(self, hook_name):
            return trigger_template_hook(hook_name, self._request)
        
        @property
        def head(self):
            """Content to inject in <head>"""
            return self._get_hook_content(CoreHooks.TEMPLATE_HEAD)
        
        @property
        def body_start(self):
            """Content to inject at start of <body>"""
            return self._get_hook_content(CoreHooks.TEMPLATE_BODY_START)
        
        @property
        def body_end(self):
            """Content to inject at end of <body>"""
            return self._get_hook_content(CoreHooks.TEMPLATE_BODY_END)
        
        @property
        def sidebar(self):
            """Content to inject in sidebar"""
            return self._get_hook_content(CoreHooks.TEMPLATE_SIDEBAR)
        
        @property
        def footer(self):
            """Content to inject in footer"""
            return self._get_hook_content(CoreHooks.TEMPLATE_FOOTER)
        
        def custom(self, hook_name):
            """Get content for a custom hook"""
            return self._get_hook_content(hook_name)
    
    return {
        'enabled_plugins': plugin_registry.enabled(),
        'template_hooks': TemplateHooks(request),
    }
