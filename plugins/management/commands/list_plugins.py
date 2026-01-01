"""
Management command to list all registered plugins.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from plugins.registry import plugin_registry
from plugins.models import PluginConfiguration


class Command(BaseCommand):
    help = 'List all registered plugins and their status'

    def add_arguments(self, parser):
        parser.add_argument(
            '--enabled',
            action='store_true',
            help='Show only enabled plugins',
        )
        parser.add_argument(
            '--disabled',
            action='store_true',
            help='Show only disabled plugins',
        )
        # Note: Use Django's built-in --verbosity (-v) option for verbose output

    def handle(self, *args, **options):
        plugins = plugin_registry.all()
        
        if not plugins:
            self.stdout.write(
                self.style.WARNING('No plugins registered.')
            )
            return
        
        # Filter based on options
        if options['enabled']:
            plugins = {k: v for k, v in plugins.items() if v.is_enabled}
        elif options['disabled']:
            plugins = {k: v for k, v in plugins.items() if not v.is_enabled}
        
        self.stdout.write(
            self.style.SUCCESS(f'\n{"="*60}')
        )
        self.stdout.write(
            self.style.SUCCESS(f' Ta3lem Plugin System - Registered Plugins')
        )
        self.stdout.write(
            self.style.SUCCESS(f'{"="*60}\n')
        )
        
        for name, plugin in sorted(plugins.items()):
            status = self.style.SUCCESS('ENABLED') if plugin.is_enabled else self.style.WARNING('DISABLED')
            
            self.stdout.write(f'  {name}')
            self.stdout.write(f'    Status:      {status}')
            self.stdout.write(f'    Version:     {plugin.version}')
            
            if options['verbosity'] > 1:
                self.stdout.write(f'    Description: {plugin.description or "No description"}')
                self.stdout.write(f'    Author:      {plugin.author or "Unknown"}')
                
                if plugin.requires:
                    self.stdout.write(f'    Requires:    {", ".join(plugin.requires)}')
                
                # Get hooks registered by this plugin
                hooks = plugin.get_hooks()
                if hooks:
                    self.stdout.write(f'    Hooks:       {", ".join(hooks.keys())}')
            
            self.stdout.write('')
        
        # Summary
        total = len(plugin_registry.all())
        enabled = len(plugin_registry.enabled())
        self.stdout.write(
            self.style.SUCCESS(f'{"="*60}')
        )
        self.stdout.write(
            f'  Total: {total} plugins ({enabled} enabled, {total - enabled} disabled)'
        )
        self.stdout.write(
            self.style.SUCCESS(f'{"="*60}\n')
        )
