from .services import SubscriptionService


def subscription_context(request):
    """
    Add subscription info to all templates.
    """
    context = {
        'user_has_subscription': False,
        'user_subscription': None,
    }
    
    if request.user.is_authenticated and request.user.role == 'student':
        subscription = SubscriptionService.get_user_subscription(request.user)
        context['user_has_subscription'] = subscription is not None
        context['user_subscription'] = subscription
    
    return context
