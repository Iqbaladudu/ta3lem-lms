"""
URL configuration for Subscriptions API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    SubscriptionPlanViewSet,
    UserSubscriptionViewSet,
    SubscribeView,
    StartTrialView,
    CancelSubscriptionView,
    RenewSubscriptionView,
    ToggleAutoRenewView,
)

router = DefaultRouter()
router.register('plans', SubscriptionPlanViewSet, basename='plan')
router.register('subscriptions', UserSubscriptionViewSet, basename='subscription')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Subscription actions
    path('subscribe/', SubscribeView.as_view(), name='subscribe'),
    path('trial/', StartTrialView.as_view(), name='start_trial'),
    path('cancel/', CancelSubscriptionView.as_view(), name='cancel_subscription'),
    path('renew/', RenewSubscriptionView.as_view(), name='renew_subscription'),
    path('auto-renew/', ToggleAutoRenewView.as_view(), name='toggle_auto_renew'),
]
