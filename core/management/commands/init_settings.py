"""
Management command to initialize global settings with default values
"""

from django.core.management.base import BaseCommand
from core.models import GlobalSettings


class Command(BaseCommand):
    help = 'Initialize global settings with default values'

    def handle(self, *args, **options):
        self.stdout.write('Initializing global settings...')
        
        settings, created = GlobalSettings.objects.get_or_create(pk=1)
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    '✓ Global settings created with default values'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Global settings already exist (not modified)'
                )
            )
        
        self.stdout.write('\nCurrent settings:')
        self.stdout.write(f'  Site Name: {settings.site_name}')
        self.stdout.write(f'  Subscriptions Enabled: {settings.enable_subscriptions}')
        self.stdout.write(f'  One-Time Purchase Enabled: {settings.enable_one_time_purchase}')
        self.stdout.write(f'  Free Courses Enabled: {settings.enable_free_courses}')
        self.stdout.write(f'  Maintenance Mode: {settings.maintenance_mode}')
        
        self.stdout.write(
            self.style.SUCCESS(
                '\n✓ You can now edit settings in Django Admin: /admin/core/globalsettings/'
            )
        )
