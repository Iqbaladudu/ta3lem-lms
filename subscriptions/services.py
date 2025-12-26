from datetime import timedelta
from typing import Optional, TYPE_CHECKING

from django.db import transaction
from django.utils import timezone

from .models import SubscriptionPlan, UserSubscription

if TYPE_CHECKING:
    from django.contrib.auth import get_user_model
    User = get_user_model()


class SubscriptionService:
    """
    Service layer for subscription management.
    Provides reusable business logic for subscriptions.
    """

    @classmethod
    def get_active_plans(cls):
        """Get all active subscription plans"""
        return SubscriptionPlan.objects.filter(is_active=True).order_by('display_order', 'price')

    @classmethod
    def user_has_active_subscription(cls, user: 'User') -> bool:
        """Check if user has an active subscription"""
        if not user or not user.is_authenticated:
            return False
        return UserSubscription.objects.filter(
            user=user,
            status__in=['active', 'trial'],
            current_period_end__gt=timezone.now()
        ).exists()

    @classmethod
    def get_user_subscription(cls, user: 'User') -> Optional[UserSubscription]:
        """Get user's current active subscription"""
        if not user or not user.is_authenticated:
            return None
        return UserSubscription.objects.filter(
            user=user,
            status__in=['active', 'trial'],
            current_period_end__gt=timezone.now()
        ).select_related('plan').first()

    @classmethod
    @transaction.atomic
    def create_subscription(
        cls,
        user: 'User',
        plan: SubscriptionPlan,
        order=None,
        start_trial: bool = False
    ) -> UserSubscription:
        """
        Create a new subscription for a user.
        
        Args:
            user: The user to create subscription for
            plan: The subscription plan
            order: Associated payment order (optional)
            start_trial: If True, start with trial status
        """
        now = timezone.now()
        
        # Calculate period
        if start_trial and plan.trial_days > 0:
            period_days = plan.trial_days
            status = 'trial'
        else:
            period_days = plan.get_period_days()
            status = 'active'

        subscription = UserSubscription.objects.create(
            user=user,
            plan=plan,
            status=status,
            current_period_start=now,
            current_period_end=now + timedelta(days=period_days),
            order=order,
        )

        return subscription

    @classmethod
    @transaction.atomic
    def renew_subscription(
        cls,
        subscription: UserSubscription,
        order=None
    ) -> UserSubscription:
        """Renew an existing subscription"""
        subscription.renew(order=order)
        return subscription

    @classmethod
    @transaction.atomic
    def cancel_subscription(
        cls,
        subscription: UserSubscription,
        immediately: bool = False,
        reason: str = ''
    ) -> UserSubscription:
        """
        Cancel a subscription.
        
        Args:
            subscription: The subscription to cancel
            immediately: If True, cancel immediately. Otherwise, cancel at period end.
            reason: Optional cancellation reason
        """
        subscription.cancel(immediately=immediately, reason=reason)
        return subscription

    @classmethod
    def check_and_expire_subscriptions(cls):
        """
        Check for expired subscriptions and update their status.
        This should be run periodically (e.g., via cron/celery).
        """
        now = timezone.now()
        
        # Expire subscriptions that have passed their period end
        expired_count = UserSubscription.objects.filter(
            status__in=['active', 'trial'],
            current_period_end__lte=now
        ).update(status='expired')

        # Expire subscriptions marked for cancellation at period end
        cancelled_count = UserSubscription.objects.filter(
            status='active',
            cancel_at_period_end=True,
            current_period_end__lte=now
        ).update(status='cancelled')

        return expired_count + cancelled_count

    @classmethod
    def get_subscription_stats(cls, user: 'User') -> dict:
        """Get subscription statistics for a user"""
        subscription = cls.get_user_subscription(user)
        
        if not subscription:
            return {
                'has_subscription': False,
                'plan': None,
                'status': None,
                'days_remaining': 0,
                'expires_at': None,
            }

        return {
            'has_subscription': True,
            'plan': subscription.plan,
            'status': subscription.status,
            'days_remaining': subscription.days_remaining(),
            'expires_at': subscription.current_period_end,
            'cancel_at_period_end': subscription.cancel_at_period_end,
        }
