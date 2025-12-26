from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import ListView, DetailView
from django.http import Http404

from core.utils import is_feature_enabled
from .models import SubscriptionPlan, UserSubscription
from .services import SubscriptionService


class PlanListView(ListView):
    """Display available subscription plans"""
    model = SubscriptionPlan
    template_name = 'subscriptions/plans.html'
    context_object_name = 'plans'

    def dispatch(self, request, *args, **kwargs):
        # Check if subscription feature is enabled
        if not is_feature_enabled('subscriptions'):
            messages.info(request, 'Fitur subscription tidak tersedia saat ini.')
            return redirect('course_list')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return SubscriptionService.get_active_plans()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Check if user has active subscription
        if self.request.user.is_authenticated:
            context['current_subscription'] = SubscriptionService.get_user_subscription(
                self.request.user
            )
        
        return context


class SubscribeView(LoginRequiredMixin, View):
    """Handle subscription checkout redirect"""

    def dispatch(self, request, *args, **kwargs):
        # Check if subscription feature is enabled
        if not is_feature_enabled('subscriptions'):
            raise Http404("Subscription feature is not available")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, plan_slug):
        plan = get_object_or_404(SubscriptionPlan, slug=plan_slug, is_active=True)
        
        # Check if user already has active subscription
        existing = SubscriptionService.get_user_subscription(request.user)
        if existing:
            messages.info(
                request,
                f'Anda sudah memiliki subscription aktif ({existing.plan.name}). '
                'Silakan batalkan terlebih dahulu jika ingin berganti plan.'
            )
            return redirect('subscriptions:manage')

        # Redirect to payment checkout
        return redirect('payments:checkout', order_type='subscription', item_id=plan.id)


class StartTrialView(LoginRequiredMixin, View):
    """Start a free trial for a plan"""

    def dispatch(self, request, *args, **kwargs):
        # Check if subscription feature is enabled
        if not is_feature_enabled('subscriptions'):
            raise Http404("Subscription feature is not available")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, plan_slug):
        plan = get_object_or_404(SubscriptionPlan, slug=plan_slug, is_active=True)
        
        # Check trial availability from global settings
        from core.utils import get_subscription_settings
        sub_settings = get_subscription_settings()
        
        if not sub_settings['trial_enabled'] or plan.trial_days <= 0:
            messages.error(request, 'Free trial tidak tersedia untuk plan ini.')
            return redirect('subscriptions:plans')

        # Check if user already had a subscription
        if UserSubscription.objects.filter(user=request.user).exists():
            messages.error(request, 'Anda sudah pernah menggunakan subscription sebelumnya.')
            return redirect('subscriptions:plans')

        # Create trial subscription
        subscription = SubscriptionService.create_subscription(
            user=request.user,
            plan=plan,
            start_trial=True
        )

        messages.success(
            request,
            f'Selamat! Trial {plan.trial_days} hari untuk {plan.name} telah aktif.'
        )
        return redirect('subscriptions:manage')


class ManageSubscriptionView(LoginRequiredMixin, View):
    """Manage current subscription"""
    template_name = 'subscriptions/manage.html'

    def dispatch(self, request, *args, **kwargs):
        # Check if subscription feature is enabled
        if not is_feature_enabled('subscriptions'):
            messages.info(request, 'Fitur subscription tidak tersedia.')
            return redirect('course_list')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        subscription = SubscriptionService.get_user_subscription(request.user)
        stats = SubscriptionService.get_subscription_stats(request.user)
        
        # Get subscription history
        history = UserSubscription.objects.filter(
            user=request.user
        ).select_related('plan', 'order').order_by('-started_at')[:10]

        context = {
            'subscription': subscription,
            'stats': stats,
            'history': history,
        }
        return render(request, self.template_name, context)


class CancelSubscriptionView(LoginRequiredMixin, View):
    """Cancel current subscription"""

    def dispatch(self, request, *args, **kwargs):
        # Check if subscription feature is enabled
        if not is_feature_enabled('subscriptions'):
            raise Http404("Subscription feature is not available")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        subscription = SubscriptionService.get_user_subscription(request.user)
        if not subscription:
            messages.error(request, 'Anda tidak memiliki subscription aktif.')
            return redirect('subscriptions:plans')

        return render(request, 'subscriptions/cancel_confirm.html', {
            'subscription': subscription
        })

    def post(self, request):
        subscription = SubscriptionService.get_user_subscription(request.user)
        if not subscription:
            messages.error(request, 'Anda tidak memiliki subscription aktif.')
            return redirect('subscriptions:plans')

        reason = request.POST.get('reason', '')
        immediately = request.POST.get('immediately') == 'true'

        SubscriptionService.cancel_subscription(
            subscription,
            immediately=immediately,
            reason=reason
        )

        if immediately:
            messages.success(request, 'Subscription Anda telah dibatalkan.')
        else:
            messages.success(
                request,
                f'Subscription Anda akan berakhir pada {subscription.current_period_end.strftime("%d %b %Y")}.'
            )

        return redirect('subscriptions:manage')
