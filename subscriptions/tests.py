from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from users.models import User
from subscriptions.models import SubscriptionPlan, UserSubscription
from subscriptions.services import SubscriptionService


class SubscriptionPlanModelTest(TestCase):
    def setUp(self):
        self.plan = SubscriptionPlan.objects.create(
            name='Monthly Plan',
            slug='monthly-plan',
            description='Access all courses for one month',
            price=Decimal('99000'),
            currency='IDR',
            billing_cycle='monthly',
            features=['Akses semua kursus', 'Sertifikat'],
            is_active=True
        )

    def test_plan_creation(self):
        self.assertEqual(self.plan.name, 'Monthly Plan')
        self.assertEqual(self.plan.billing_cycle, 'monthly')

    def test_get_period_days(self):
        self.assertEqual(self.plan.get_period_days(), 30)
        
        quarterly = SubscriptionPlan.objects.create(
            name='Quarterly', slug='quarterly',
            price=Decimal('249000'), billing_cycle='quarterly'
        )
        self.assertEqual(quarterly.get_period_days(), 90)

    def test_formatted_price(self):
        self.assertIn('99.000', self.plan.get_formatted_price())

    def test_purchasable_protocol(self):
        self.assertEqual(self.plan.get_price(), Decimal('99000'))
        self.assertEqual(self.plan.get_currency(), 'IDR')
        self.assertIn('Monthly Plan', self.plan.get_display_name())


class UserSubscriptionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.plan = SubscriptionPlan.objects.create(
            name='Monthly Plan',
            slug='monthly-plan',
            price=Decimal('99000'),
            billing_cycle='monthly',
            is_active=True
        )

    def test_subscription_creation(self):
        subscription = SubscriptionService.create_subscription(
            user=self.user,
            plan=self.plan
        )
        self.assertEqual(subscription.status, 'active')
        self.assertTrue(subscription.is_active())

    def test_days_remaining(self):
        subscription = SubscriptionService.create_subscription(
            user=self.user,
            plan=self.plan
        )
        # Should be around 30 days
        self.assertGreater(subscription.days_remaining(), 25)

    def test_subscription_expiry(self):
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            status='active',
            current_period_start=timezone.now() - timedelta(days=35),
            current_period_end=timezone.now() - timedelta(days=5)
        )
        self.assertFalse(subscription.is_active())
        self.assertEqual(subscription.days_remaining(), 0)


class SubscriptionServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.plan = SubscriptionPlan.objects.create(
            name='Monthly Plan',
            slug='monthly-plan',
            price=Decimal('99000'),
            billing_cycle='monthly',
            trial_days=7,
            is_active=True
        )

    def test_user_has_active_subscription(self):
        self.assertFalse(SubscriptionService.user_has_active_subscription(self.user))
        
        SubscriptionService.create_subscription(self.user, self.plan)
        self.assertTrue(SubscriptionService.user_has_active_subscription(self.user))

    def test_get_active_plans(self):
        plans = SubscriptionService.get_active_plans()
        self.assertEqual(len(plans), 1)

    def test_trial_subscription(self):
        subscription = SubscriptionService.create_subscription(
            user=self.user,
            plan=self.plan,
            start_trial=True
        )
        self.assertEqual(subscription.status, 'trial')
        self.assertLessEqual(subscription.days_remaining(), 7)

    def test_cancel_subscription(self):
        subscription = SubscriptionService.create_subscription(
            user=self.user,
            plan=self.plan
        )
        
        SubscriptionService.cancel_subscription(
            subscription,
            immediately=False,
            reason='Too expensive'
        )
        subscription.refresh_from_db()
        self.assertTrue(subscription.cancel_at_period_end)
        self.assertEqual(subscription.cancellation_reason, 'Too expensive')

    def test_renew_subscription(self):
        subscription = SubscriptionService.create_subscription(
            user=self.user,
            plan=self.plan
        )
        old_end = subscription.current_period_end
        
        SubscriptionService.renew_subscription(subscription)
        subscription.refresh_from_db()
        
        self.assertGreater(subscription.current_period_end, old_end)


class SubscriptionViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.plan = SubscriptionPlan.objects.create(
            name='Monthly Plan',
            slug='monthly-plan',
            price=Decimal('99000'),
            billing_cycle='monthly',
            is_active=True,
            is_featured=True
        )

    def test_plans_page_loads(self):
        url = reverse('subscriptions:plans')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Monthly Plan')

    def test_manage_requires_login(self):
        url = reverse('subscriptions:manage')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_manage_page_loads(self):
        self.client.login(username='testuser', password='testpass123')
        url = reverse('subscriptions:manage')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
