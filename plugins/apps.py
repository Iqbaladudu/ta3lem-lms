from django.apps import AppConfig


class PluginsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plugins'
    verbose_name = 'Plugin Management'

    def ready(self):
        """Initialize plugin system when Django starts."""
        from .discovery import discover_plugins
        discover_plugins()
