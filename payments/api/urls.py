"""
URL configuration for Payments API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    PaymentProviderViewSet,
    OrderViewSet,
    CheckoutView,
    SelectPaymentProviderView,
    UploadPaymentProofView,
    WebhookView,
    PaymentSuccessView,
    PaymentCancelView,
)

router = DefaultRouter()
router.register('providers', PaymentProviderViewSet, basename='provider')
router.register('orders', OrderViewSet, basename='order')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Checkout
    path('checkout/', CheckoutView.as_view(), name='api_checkout'),
    
    # Order operations
    path(
        'orders/<str:order_number>/select-provider/',
        SelectPaymentProviderView.as_view(),
        name='select_provider'
    ),
    path(
        'orders/<str:order_number>/upload-proof/',
        UploadPaymentProofView.as_view(),
        name='upload_proof'
    ),
    path(
        'orders/<str:order_number>/success/',
        PaymentSuccessView.as_view(),
        name='payment_success'
    ),
    path(
        'orders/<str:order_number>/cancel/',
        PaymentCancelView.as_view(),
        name='payment_cancel'
    ),
    
    # Webhooks
    path(
        'webhook/<str:provider_type>/',
        WebhookView.as_view(),
        name='webhook'
    ),
]
