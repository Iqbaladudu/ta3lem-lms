from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('plans/', views.PlanListView.as_view(), name='plans'),
    path('subscribe/<slug:plan_slug>/', views.SubscribeView.as_view(), name='subscribe'),
    path('trial/<slug:plan_slug>/', views.StartTrialView.as_view(), name='start_trial'),
    path('manage/', views.ManageSubscriptionView.as_view(), name='manage'),
    path('cancel/', views.CancelSubscriptionView.as_view(), name='cancel'),
]
