"""
API Views for Subscriptions app.
"""

from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, extend_schema_view

from core.api import SuccessResponseMixin, StandardResultsSetPagination
from subscriptions.models import SubscriptionPlan, UserSubscription
from subscriptions.services import SubscriptionService
from .serializers import (
    SubscriptionPlanSerializer,
    SubscriptionPlanDetailSerializer,
    UserSubscriptionSerializer,
    UserSubscriptionDetailSerializer,
    SubscribeSerializer,
    StartTrialSerializer,
    CancelSubscriptionSerializer,
    RenewSubscriptionSerializer,
    SubscriptionStatusSerializer,
)


@extend_schema_view(
    list=extend_schema(
        tags=['Subscriptions'],
        summary='List subscription plans',
        description='List all available subscription plans.'
    ),
    retrieve=extend_schema(
        tags=['Subscriptions'],
        summary='Get subscription plan details',
        description='Get details of a specific subscription plan.'
    ),
)
class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing subscription plans.
    """
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SubscriptionPlanDetailSerializer
        return SubscriptionPlanSerializer
    
    @extend_schema(
        tags=['Subscriptions'],
        summary='Get featured plans',
        description='Get featured subscription plans.'
    )
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """
        Get featured subscription plans.
        """
        plans = self.get_queryset().filter(is_featured=True)
        serializer = self.get_serializer(plans, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Subscriptions'],
        summary='Compare plans',
        description='Get comparison data for all plans.'
    )
    @action(detail=False, methods=['get'])
    def compare(self, request):
        """
        Get plan comparison data.
        """
        plans = self.get_queryset().order_by('display_order', 'price')
        
        # Build comparison matrix
        comparison = {
            'plans': SubscriptionPlanSerializer(plans, many=True).data,
            'features': self._get_unique_features(plans),
        }
        
        return Response(comparison)
    
    def _get_unique_features(self, plans):
        """Get unique features across all plans."""
        features = set()
        for plan in plans:
            if plan.features:
                features.update(plan.features)
        return sorted(list(features))


@extend_schema_view(
    list=extend_schema(
        tags=['Subscriptions'],
        summary='List my subscriptions',
        description='List all subscriptions for the current user.'
    ),
    retrieve=extend_schema(
        tags=['Subscriptions'],
        summary='Get subscription details',
        description='Get details of a specific subscription.'
    ),
)
class UserSubscriptionViewSet(SuccessResponseMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing user subscriptions.
    """
    queryset = UserSubscription.objects.all()
    serializer_class = UserSubscriptionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        return UserSubscription.objects.filter(user=self.request.user).order_by('-started_at')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserSubscriptionDetailSerializer
        return UserSubscriptionSerializer
    
    @extend_schema(
        tags=['Subscriptions'],
        summary='Get current subscription',
        description='Get the current active subscription for the user.'
    )
    @action(detail=False, methods=['get'])
    def current(self, request):
        """
        Get current active subscription.
        """
        subscription = UserSubscription.objects.filter(
            user=request.user,
            status__in=['active', 'trial'],
            current_period_end__gt=timezone.now()
        ).first()
        
        if subscription:
            return self.success_response(
                data=UserSubscriptionDetailSerializer(subscription).data
            )
        
        return self.success_response(data=None, message='No active subscription.')
    
    @extend_schema(
        tags=['Subscriptions'],
        summary='Get subscription status',
        description='Get comprehensive subscription status for the user.',
        responses={200: SubscriptionStatusSerializer}
    )
    @action(detail=False, methods=['get'])
    def status(self, request):
        """
        Get subscription status.
        """
        subscription = UserSubscription.objects.filter(
            user=request.user,
            status__in=['active', 'trial'],
            current_period_end__gt=timezone.now()
        ).first()
        
        # Check if user has used trial before
        has_used_trial = UserSubscription.objects.filter(
            user=request.user,
            status='trial'
        ).exists()
        
        status_data = {
            'has_subscription': subscription is not None,
            'is_active': subscription.is_active() if subscription else False,
            'subscription': UserSubscriptionSerializer(subscription).data if subscription else None,
            'can_access_courses': subscription.is_active() if subscription else False,
            'trial_available': not has_used_trial,
        }
        
        return self.success_response(data=status_data)


@extend_schema(tags=['Subscriptions'])
class SubscribeView(SuccessResponseMixin, APIView):
    """
    Subscribe to a plan.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary='Subscribe to plan',
        description='Start a subscription to the specified plan.',
        request=SubscribeSerializer
    )
    def post(self, request):
        serializer = SubscribeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        plan_slug = serializer.validated_data['plan_slug']
        plan = get_object_or_404(SubscriptionPlan, slug=plan_slug, is_active=True)
        
        # Check if user already has active subscription
        existing = UserSubscription.objects.filter(
            user=request.user,
            status__in=['active', 'trial'],
            current_period_end__gt=timezone.now()
        ).first()
        
        if existing:
            return Response({
                'success': False,
                'message': 'You already have an active subscription.',
                'current_subscription': UserSubscriptionSerializer(existing).data
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Redirect to payment for paid plans
        return Response({
            'success': True,
            'message': 'Please complete payment to activate subscription.',
            'payment_required': True,
            'checkout_url': f'/api/v1/payments/checkout/',
            'checkout_data': {
                'order_type': 'subscription',
                'item_id': plan.id
            }
        })


@extend_schema(tags=['Subscriptions'])
class StartTrialView(SuccessResponseMixin, APIView):
    """
    Start a trial subscription.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary='Start trial',
        description='Start a trial subscription for the specified plan.',
        request=StartTrialSerializer
    )
    def post(self, request):
        serializer = StartTrialSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        plan_slug = serializer.validated_data['plan_slug']
        plan = get_object_or_404(SubscriptionPlan, slug=plan_slug, is_active=True)
        
        # Check if user already has/had a trial
        existing_trial = UserSubscription.objects.filter(
            user=request.user,
            status__in=['trial', 'active', 'cancelled', 'expired']
        ).exists()
        
        if existing_trial:
            return Response({
                'success': False,
                'message': 'You have already used your trial or have an active subscription.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create trial subscription
        now = timezone.now()
        trial_end = now + timedelta(days=plan.trial_days)
        
        subscription = UserSubscription.objects.create(
            user=request.user,
            plan=plan,
            status='trial',
            current_period_start=now,
            current_period_end=trial_end,
            auto_renew=True
        )
        
        return self.success_response(
            data=UserSubscriptionSerializer(subscription).data,
            message=f'Trial started! You have {plan.trial_days} days of free access.',
            status_code=status.HTTP_201_CREATED
        )


@extend_schema(tags=['Subscriptions'])
class CancelSubscriptionView(SuccessResponseMixin, APIView):
    """
    Cancel a subscription.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary='Cancel subscription',
        description='Cancel the current subscription.',
        request=CancelSubscriptionSerializer
    )
    def post(self, request):
        serializer = CancelSubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        subscription = UserSubscription.objects.filter(
            user=request.user,
            status__in=['active', 'trial'],
            current_period_end__gt=timezone.now()
        ).first()
        
        if not subscription:
            return Response({
                'success': False,
                'message': 'No active subscription to cancel.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        immediately = serializer.validated_data.get('immediately', False)
        reason = serializer.validated_data.get('reason', '')
        
        subscription.cancel(immediately=immediately, reason=reason)
        
        if immediately:
            message = 'Subscription cancelled immediately.'
        else:
            message = f'Subscription will be cancelled at the end of the billing period ({subscription.current_period_end.strftime("%Y-%m-%d")}).'
        
        return self.success_response(
            data=UserSubscriptionSerializer(subscription).data,
            message=message
        )


@extend_schema(tags=['Subscriptions'])
class RenewSubscriptionView(SuccessResponseMixin, APIView):
    """
    Renew a subscription.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary='Renew subscription',
        description='Renew an expired or cancelled subscription.',
        request=RenewSubscriptionSerializer
    )
    def post(self, request):
        serializer = RenewSubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get the most recent subscription
        subscription = UserSubscription.objects.filter(
            user=request.user
        ).order_by('-started_at').first()
        
        if not subscription:
            return Response({
                'success': False,
                'message': 'No subscription found. Please subscribe to a plan.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        plan_slug = serializer.validated_data.get('plan_slug')
        if plan_slug:
            plan = get_object_or_404(SubscriptionPlan, slug=plan_slug, is_active=True)
        else:
            plan = subscription.plan
        
        # Redirect to payment
        return Response({
            'success': True,
            'message': 'Please complete payment to renew subscription.',
            'payment_required': True,
            'checkout_url': f'/api/v1/payments/checkout/',
            'checkout_data': {
                'order_type': 'subscription',
                'item_id': plan.id
            }
        })


@extend_schema(tags=['Subscriptions'])
class ToggleAutoRenewView(SuccessResponseMixin, APIView):
    """
    Toggle auto-renewal for subscription.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary='Toggle auto-renew',
        description='Toggle auto-renewal setting for the current subscription.'
    )
    def post(self, request):
        subscription = UserSubscription.objects.filter(
            user=request.user,
            status__in=['active', 'trial'],
            current_period_end__gt=timezone.now()
        ).first()
        
        if not subscription:
            return Response({
                'success': False,
                'message': 'No active subscription found.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        subscription.auto_renew = not subscription.auto_renew
        subscription.save()
        
        message = 'Auto-renewal enabled.' if subscription.auto_renew else 'Auto-renewal disabled.'
        
        return self.success_response(
            data=UserSubscriptionSerializer(subscription).data,
            message=message
        )
