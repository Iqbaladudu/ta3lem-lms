from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse

from .services import SubscriptionService


def subscription_required(view_func):
    """
    Decorator to check if user has active subscription.
    Redirect to subscription plans page if not.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('student_login')
        
        if not SubscriptionService.user_has_active_subscription(request.user):
            messages.warning(
                request,
                'Anda memerlukan subscription aktif untuk mengakses fitur ini.'
            )
            return redirect('subscriptions:plans')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


class SubscriptionRequiredMixin:
    """
    Mixin for class-based views to check subscription.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('student_login')
        
        if not SubscriptionService.user_has_active_subscription(request.user):
            messages.warning(
                request,
                'Anda memerlukan subscription aktif untuk mengakses fitur ini.'
            )
            return redirect('subscriptions:plans')
        
        return super().dispatch(request, *args, **kwargs)
