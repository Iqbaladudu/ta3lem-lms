from django.conf import settings
from django.core.mail import send_mail
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .signals import payment_completed, payment_failed


@receiver(payment_completed)
def send_payment_success_email(sender, order, user, **kwargs):
    """Send email notification when payment is completed"""
    if not user.email or not user.email_notifications:
        return

    subject = f'Pembayaran Berhasil - {order.order_number}'
    
    html_message = render_to_string('payments/emails/payment_success.html', {
        'order': order,
        'user': user,
    })
    plain_message = strip_tags(html_message)

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=True,
        )
    except Exception:
        pass  # Log in production


@receiver(payment_completed)
def create_instructor_earning(sender, order, user, **kwargs):
    """Create instructor earning record when course payment completes"""
    try:
        from .earnings_service import EarningsService
        EarningsService.create_earning_from_order(order)
    except Exception:
        pass  # Log in production


@receiver(payment_failed)
def send_payment_failed_email(sender, order, reason, **kwargs):
    """Send email notification when payment fails"""
    user = order.user
    if not user.email or not user.email_notifications:
        return

    subject = f'Pembayaran Gagal - {order.order_number}'
    
    html_message = render_to_string('payments/emails/payment_failed.html', {
        'order': order,
        'user': user,
        'reason': reason,
    })
    plain_message = strip_tags(html_message)

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=True,
        )
    except Exception:
        pass


def send_verification_pending_email(order):
    """Send email when manual payment proof is uploaded"""
    user = order.user
    if not user.email:
        return

    subject = f'Bukti Transfer Diterima - {order.order_number}'
    
    html_message = render_to_string('payments/emails/verification_pending.html', {
        'order': order,
        'user': user,
    })
    plain_message = strip_tags(html_message)

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=True,
        )
    except Exception:
        pass
