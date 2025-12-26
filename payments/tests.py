from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType

from users.models import User
from courses.models import Course, Subject
from payments.models import PaymentProvider, BankAccount, Order
from payments.services import PaymentService


class PaymentProviderModelTest(TestCase):
    def setUp(self):
        self.provider = PaymentProvider.objects.create(
            name='Manual Transfer',
            provider_type='manual_transfer',
            display_name='Transfer Bank',
            supported_currencies=['IDR', 'USD'],
            min_amount=Decimal('10000'),
            is_active=True
        )

    def test_provider_creation(self):
        self.assertEqual(self.provider.name, 'Manual Transfer')
        self.assertEqual(self.provider.provider_type, 'manual_transfer')

    def test_provider_availability(self):
        # Within limits
        self.assertTrue(self.provider.is_available_for_amount(50000, 'IDR'))
        # Below minimum
        self.assertFalse(self.provider.is_available_for_amount(5000, 'IDR'))
        # Unsupported currency
        self.assertFalse(self.provider.is_available_for_amount(50000, 'EUR'))


class BankAccountModelTest(TestCase):
    def setUp(self):
        self.provider = PaymentProvider.objects.create(
            name='Manual Transfer',
            provider_type='manual_transfer',
            display_name='Transfer Bank',
            is_active=True
        )
        self.bank = BankAccount.objects.create(
            provider=self.provider,
            bank_name='Bank Central Asia',
            bank_code='BCA',
            account_number='1234567890',
            account_holder='PT Ta3lem Indonesia',
            is_active=True
        )

    def test_bank_account_str(self):
        self.assertIn('BCA', str(self.bank))
        self.assertIn('1234567890', str(self.bank))


class OrderModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.subject = Subject.objects.create(title='Programming', slug='programming')
        self.course = Course.objects.create(
            owner=self.user,
            subject=self.subject,
            title='Python Basics',
            slug='python-basics',
            overview='Learn Python',
            is_free=False,
            price=Decimal('100000'),
            pricing_type='one_time',
            status='published'
        )
        self.provider = PaymentProvider.objects.create(
            name='Manual Transfer',
            provider_type='manual_transfer',
            display_name='Transfer Bank',
            is_active=True
        )

    def test_order_creation(self):
        order = PaymentService.create_order(
            user=self.user,
            item=self.course,
            order_type='course',
            provider=self.provider
        )
        self.assertIsNotNone(order.order_number)
        self.assertEqual(order.total_amount, Decimal('100000'))
        self.assertEqual(order.status, 'pending')

    def test_order_number_format(self):
        order = PaymentService.create_order(
            user=self.user,
            item=self.course,
            order_type='course'
        )
        self.assertTrue(order.order_number.startswith('TA3-'))


class PaymentServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.subject = Subject.objects.create(title='Programming', slug='programming')
        self.course = Course.objects.create(
            owner=self.user,
            subject=self.subject,
            title='Python Basics',
            slug='python-basics',
            overview='Learn Python',
            is_free=False,
            price=Decimal('100000'),
            pricing_type='one_time',
            status='published'
        )
        self.provider = PaymentProvider.objects.create(
            name='Manual Transfer',
            provider_type='manual_transfer',
            display_name='Transfer Bank',
            supported_currencies=['IDR'],
            is_active=True
        )
        BankAccount.objects.create(
            provider=self.provider,
            bank_name='BCA',
            bank_code='BCA',
            account_number='123456',
            account_holder='Test',
            is_active=True
        )

    def test_get_available_providers(self):
        providers = PaymentService.get_available_providers(
            amount=Decimal('100000'),
            currency='IDR'
        )
        self.assertEqual(len(providers), 1)
        self.assertEqual(providers[0].provider_type, 'manual_transfer')

    def test_create_order_with_purchasable(self):
        order = PaymentService.create_order(
            user=self.user,
            item=self.course,
            order_type='course'
        )
        self.assertEqual(order.total_amount, self.course.get_price())
        self.assertEqual(order.currency, self.course.get_currency())

    def test_verify_manual_payment(self):
        order = PaymentService.create_order(
            user=self.user,
            item=self.course,
            order_type='course',
            provider=self.provider
        )
        order.status = 'awaiting_verification'
        order.save()

        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass'
        )

        result = PaymentService.verify_manual_payment(
            order=order,
            verified_by=admin_user,
            notes='Payment verified'
        )
        self.assertTrue(result)
        order.refresh_from_db()
        self.assertEqual(order.status, 'completed')


class CheckoutViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.subject = Subject.objects.create(title='Programming', slug='programming')
        self.course = Course.objects.create(
            owner=self.user,
            subject=self.subject,
            title='Python Basics',
            slug='python-basics',
            overview='Learn Python',
            is_free=False,
            price=Decimal('100000'),
            pricing_type='one_time',
            status='published'
        )
        self.provider = PaymentProvider.objects.create(
            name='Manual Transfer',
            provider_type='manual_transfer',
            display_name='Transfer Bank',
            supported_currencies=['IDR'],
            is_active=True
        )

    def test_checkout_requires_login(self):
        url = reverse('payments:checkout', args=['course', self.course.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_checkout_page_loads(self):
        self.client.login(username='testuser', password='testpass123')
        url = reverse('payments:checkout', args=['course', self.course.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Checkout')
