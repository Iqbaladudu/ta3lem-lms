"""
Serializers for Subscriptions API.
"""

from rest_framework import serializers

from subscriptions.models import SubscriptionPlan, UserSubscription
from users.api.serializers import UserSerializer


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """
    Serializer for SubscriptionPlan model.
    """
    formatted_price = serializers.SerializerMethodField()
    savings_percentage = serializers.SerializerMethodField()
    period_days = serializers.SerializerMethodField()
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'currency',
            'billing_cycle', 'formatted_price', 'original_price',
            'savings_percentage', 'period_days', 'features',
            'max_concurrent_courses', 'includes_certificate',
            'priority_support', 'is_featured', 'trial_days', 'display_order'
        ]
        read_only_fields = ['id', 'slug']
    
    def get_formatted_price(self, obj):
        return obj.get_formatted_price()
    
    def get_savings_percentage(self, obj):
        return obj.get_savings_percentage()
    
    def get_period_days(self, obj):
        return obj.get_period_days()


class SubscriptionPlanDetailSerializer(SubscriptionPlanSerializer):
    """
    Detailed serializer for SubscriptionPlan with subscriber count.
    """
    subscriber_count = serializers.SerializerMethodField()
    
    class Meta(SubscriptionPlanSerializer.Meta):
        fields = SubscriptionPlanSerializer.Meta.fields + ['subscriber_count']
    
    def get_subscriber_count(self, obj):
        return obj.subscribers.filter(status__in=['active', 'trial']).count()


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for UserSubscription model.
    """
    plan = SubscriptionPlanSerializer(read_only=True)
    is_active = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSubscription
        fields = [
            'id', 'plan', 'status', 'started_at',
            'current_period_start', 'current_period_end',
            'cancelled_at', 'auto_renew', 'cancel_at_period_end',
            'is_active', 'days_remaining'
        ]
        read_only_fields = ['id', 'started_at']
    
    def get_is_active(self, obj):
        return obj.is_active()
    
    def get_days_remaining(self, obj):
        return obj.days_remaining()


class UserSubscriptionDetailSerializer(UserSubscriptionSerializer):
    """
    Detailed serializer for UserSubscription with order info.
    """
    user = UserSerializer(read_only=True)
    cancellation_reason = serializers.CharField(read_only=True)
    
    class Meta(UserSubscriptionSerializer.Meta):
        fields = UserSubscriptionSerializer.Meta.fields + [
            'user', 'cancellation_reason', 'gateway_subscription_id'
        ]


class SubscribeSerializer(serializers.Serializer):
    """
    Serializer for creating a subscription.
    """
    plan_slug = serializers.SlugField()
    
    def validate_plan_slug(self, value):
        try:
            plan = SubscriptionPlan.objects.get(slug=value, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError("Subscription plan not found.")
        return value


class StartTrialSerializer(serializers.Serializer):
    """
    Serializer for starting a trial subscription.
    """
    plan_slug = serializers.SlugField()
    
    def validate_plan_slug(self, value):
        try:
            plan = SubscriptionPlan.objects.get(slug=value, is_active=True)
            if plan.trial_days == 0:
                raise serializers.ValidationError("This plan does not offer a trial.")
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError("Subscription plan not found.")
        return value


class CancelSubscriptionSerializer(serializers.Serializer):
    """
    Serializer for cancelling a subscription.
    """
    immediately = serializers.BooleanField(default=False)
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500)


class RenewSubscriptionSerializer(serializers.Serializer):
    """
    Serializer for renewing a subscription.
    """
    plan_slug = serializers.SlugField(required=False)


class SubscriptionStatusSerializer(serializers.Serializer):
    """
    Serializer for subscription status response.
    """
    has_subscription = serializers.BooleanField()
    is_active = serializers.BooleanField()
    subscription = UserSubscriptionSerializer(allow_null=True)
    can_access_courses = serializers.BooleanField()
    trial_available = serializers.BooleanField()


class AvailablePlansSerializer(serializers.Serializer):
    """
    Serializer for available plans response.
    """
    plans = SubscriptionPlanSerializer(many=True)
    current_subscription = UserSubscriptionSerializer(allow_null=True)
    recommended_plan = SubscriptionPlanSerializer(allow_null=True)
