from django.core.management.base import BaseCommand
from subscriptions.services import SubscriptionService


class Command(BaseCommand):
    help = 'Check and expire subscriptions that have passed their end date'

    def handle(self, *args, **options):
        self.stdout.write('Checking for expired subscriptions...')
        
        expired_count = SubscriptionService.check_and_expire_subscriptions()
        
        if expired_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully expired {expired_count} subscription(s)'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    'Note: Course access for these subscriptions has been revoked via signals.'
                )
            )
        else:
            self.stdout.write('No subscriptions to expire')
