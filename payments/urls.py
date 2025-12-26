from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Checkout flow
    path(
        'checkout/<str:order_type>/<int:item_id>/',
        views.CheckoutView.as_view(),
        name='checkout'
    ),
    
    # Manual transfer
    path(
        'transfer/<str:order_number>/',
        views.TransferInstructionsView.as_view(),
        name='transfer_instructions'
    ),
    path(
        'upload-proof/<str:order_number>/',
        views.UploadPaymentProofView.as_view(),
        name='upload_proof'
    ),
    
    # Payment status
    path(
        'status/<str:order_number>/',
        views.PaymentStatusView.as_view(),
        name='payment_status'
    ),
    
    # Gateway callbacks
    path(
        'success/<str:order_number>/',
        views.PaymentSuccessView.as_view(),
        name='payment_success'
    ),
    path(
        'cancel/<str:order_number>/',
        views.PaymentCancelView.as_view(),
        name='payment_cancel'
    ),
    
    # Webhooks
    path(
        'webhook/<str:provider_type>/',
        views.WebhookView.as_view(),
        name='webhook'
    ),
    
    # Instructor Earnings
    path(
        'earnings/',
        views.InstructorEarningsView.as_view(),
        name='instructor_earnings'
    ),
    path(
        'payout/request/',
        views.RequestPayoutView.as_view(),
        name='request_payout'
    ),
    path(
        'payout/<int:payout_id>/',
        views.PayoutDetailView.as_view(),
        name='payout_detail'
    ),
]

