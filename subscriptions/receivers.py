from django.db.models.signals import post_save
from django.dispatch import receiver
from payments.signals import payment_completed

from .models import SubscriptionPlan, UserSubscription
from .services import SubscriptionService


@receiver(payment_completed)
def activate_subscription_on_payment(sender, order, user, **kwargs):
    """
    When payment for a subscription plan completes, activate the subscription.
    """
    # Check if the purchased item is a SubscriptionPlan
    if not isinstance(order.item, SubscriptionPlan):
        return

    plan = order.item

    # Check if user already has an active subscription
    existing = SubscriptionService.get_user_subscription(user)
    
    if existing:
        # Renew existing subscription
        SubscriptionService.renew_subscription(existing, order=order)
    else:
        # Create new subscription
        SubscriptionService.create_subscription(
            user=user,
            plan=plan,
            order=order,
            start_trial=False  # Trial would be handled separately
        )


@receiver(post_save, sender=UserSubscription)
def handle_subscription_status_change(sender, instance, created, **kwargs):
    """
    Handle subscription expiry and renewal.
    Revoke or restore course access based on subscription status.
    """
    if created:
        # New subscription - no action needed yet
        return
    
    # Check if status changed to expired/cancelled
    if instance.status in ['expired', 'cancelled']:
        # Import here to avoid circular imports
        from courses.access_service import EnrollmentService
        
        # Revoke access to subscription-based enrollments
        count = EnrollmentService.revoke_subscription_access(
            user=instance.user,
            subscription=instance
        )
        
        if count > 0:
            # Optional: Send email notification
            try:
                from subscriptions.emails import send_subscription_expired_email
                send_subscription_expired_email(instance.user, instance, count)
            except ImportError:
                pass  # Email function not implemented yet
    
    # Check if status changed to active (renewal)
    elif instance.status in ['active', 'trial']:
        from courses.access_service import EnrollmentService
        
        # Restore access if subscription was renewed
        count = EnrollmentService.restore_subscription_access(
            user=instance.user,
            subscription=instance
        )

