from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class SubscriptionPlan(models.Model):
    """Subscription plan for accessing all courses"""

    BILLING_CYCLE_CHOICES = [
        ('monthly', 'Bulanan'),
        ('quarterly', '3 Bulan'),
        ('yearly', 'Tahunan'),
    ]

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='IDR')
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES)

    # Original price for showing discount
    original_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Original price before discount (for display)'
    )

    # Features as JSON list
    features = models.JSONField(
        default=list,
        help_text='List of features included, e.g. ["Akses semua kursus", "Sertifikat"]'
    )

    # Limits
    max_concurrent_courses = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Max courses that can be accessed simultaneously (null=unlimited)'
    )
    includes_certificate = models.BooleanField(default=True)
    priority_support = models.BooleanField(default=False)

    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)

    # Trial
    trial_days = models.PositiveIntegerField(
        default=0,
        help_text='Number of free trial days (0 = no trial)'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'price']
        verbose_name = 'Subscription Plan'
        verbose_name_plural = 'Subscription Plans'

    def __str__(self):
        return f"{self.name} ({self.get_billing_cycle_display()})"

    def get_price(self):
        """Implement Purchasable protocol"""
        return self.price

    def get_currency(self):
        """Implement Purchasable protocol"""
        return self.currency

    def get_display_name(self):
        """Implement Purchasable protocol"""
        return str(self)

    def get_formatted_price(self):
        """Get formatted price string"""
        if self.currency == 'IDR':
            return f"Rp {self.price:,.0f}".replace(',', '.')
        elif self.currency == 'USD':
            return f"${self.price:,.2f}"
        elif self.currency == 'EUR':
            return f"€{self.price:,.2f}"
        return f"{self.price} {self.currency}"

    def get_period_days(self):
        """Get subscription period in days"""
        periods = {
            'monthly': 30,
            'quarterly': 90,
            'yearly': 365,
        }
        return periods.get(self.billing_cycle, 30)

    def get_savings_percentage(self):
        """Calculate savings compared to original price"""
        if not self.original_price or self.original_price <= self.price:
            return 0
        return int(((self.original_price - self.price) / self.original_price) * 100)


class UserSubscription(models.Model):
    """Active subscription for a user"""

    STATUS_CHOICES = [
        ('trial', 'Trial'),
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='subscribers'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    # Period dates
    started_at = models.DateTimeField(auto_now_add=True)
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    cancelled_at = models.DateTimeField(null=True, blank=True)

    # Link to payment order
    order = models.ForeignKey(
        'payments.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subscriptions'
    )

    # For automatic renewal with gateway
    gateway_subscription_id = models.CharField(max_length=100, blank=True)
    auto_renew = models.BooleanField(default=True)

    # Cancellation
    cancel_at_period_end = models.BooleanField(default=False)
    cancellation_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['current_period_end']),
            models.Index(fields=['status', 'current_period_end']),
        ]
        verbose_name = 'User Subscription'
        verbose_name_plural = 'User Subscriptions'

    def __str__(self):
        return f"{self.user.username} - {self.plan.name} ({self.get_status_display()})"

    def is_active(self):
        """Check if subscription is currently active"""
        if self.status not in ['active', 'trial']:
            return False
        return self.current_period_end > timezone.now()

    def days_remaining(self):
        """Get remaining days in current period"""
        if not self.is_active():
            return 0
        delta = self.current_period_end - timezone.now()
        return max(0, delta.days)

    def renew(self, order=None):
        """Renew subscription for another period"""
        period_days = self.plan.get_period_days()
        
        # Extend from current period end or now if expired
        start = self.current_period_end if self.is_active() else timezone.now()
        
        self.current_period_start = start
        self.current_period_end = start + timedelta(days=period_days)
        self.status = 'active'
        self.cancel_at_period_end = False
        
        if order:
            self.order = order
        
        self.save()

    def cancel(self, immediately=False, reason=''):
        """
        Cancel subscription.
        If immediately=True, expire now. Otherwise, cancel at period end.
        """
        self.cancelled_at = timezone.now()
        self.cancellation_reason = reason
        
        if immediately:
            self.status = 'cancelled'
            self.current_period_end = timezone.now()
        else:
            self.cancel_at_period_end = True
        
        self.save()
