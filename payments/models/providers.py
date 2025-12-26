from django.conf import settings
from django.db import models


class PaymentProvider(models.Model):
    """Configuration for available payment gateways"""

    PROVIDER_TYPE_CHOICES = [
        ('stripe', 'Stripe'),
        ('midtrans', 'Midtrans'),
        ('xendit', 'Xendit'),
        ('manual_transfer', 'Transfer Manual'),
    ]

    name = models.CharField(max_length=100)
    provider_type = models.CharField(
        max_length=30,
        choices=PROVIDER_TYPE_CHOICES,
        unique=True
    )
    display_name = models.CharField(
        max_length=100,
        help_text='Name shown to users, e.g. "Transfer Bank BCA"'
    )
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text='CSS icon class, e.g. "fas fa-credit-card"'
    )

    # Configuration stored as JSON (should be encrypted in production)
    # Stripe: {"public_key": "pk_...", "secret_key": "sk_...", "webhook_secret": "whsec_..."}
    # Midtrans: {"server_key": "...", "client_key": "...", "is_production": false}
    # Manual: {} - uses related BankAccount instances
    config = models.JSONField(default=dict, blank=True)

    # Feature support
    supports_subscription = models.BooleanField(
        default=False,
        help_text='Whether this provider supports recurring payments'
    )
    supports_refund = models.BooleanField(default=False)

    # Status and ordering
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    # Currency support
    supported_currencies = models.JSONField(
        default=list,
        help_text='List of supported currencies, e.g. ["IDR", "USD"]'
    )

    # Amount limits
    min_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Minimum transaction amount'
    )
    max_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Maximum transaction amount (null for no limit)'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = 'Payment Provider'
        verbose_name_plural = 'Payment Providers'

    def __str__(self):
        return self.display_name

    def is_available_for_amount(self, amount, currency='IDR'):
        """Check if provider is available for given amount and currency"""
        if not self.is_active:
            return False
        if currency not in self.supported_currencies:
            return False
        if amount < self.min_amount:
            return False
        if self.max_amount and amount > self.max_amount:
            return False
        return True


class BankAccount(models.Model):
    """Bank accounts for manual transfer payments"""

    provider = models.ForeignKey(
        PaymentProvider,
        on_delete=models.CASCADE,
        related_name='bank_accounts',
        limit_choices_to={'provider_type': 'manual_transfer'}
    )

    bank_name = models.CharField(max_length=100)  # "Bank Central Asia"
    bank_code = models.CharField(max_length=20)   # "BCA"
    account_number = models.CharField(max_length=50)
    account_holder = models.CharField(max_length=200)
    branch = models.CharField(max_length=100, blank=True)

    # Display
    logo = models.ImageField(upload_to='bank_logos/', blank=True)
    instructions = models.TextField(
        blank=True,
        help_text='Transfer instructions to display to users'
    )

    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'bank_name']
        verbose_name = 'Bank Account'
        verbose_name_plural = 'Bank Accounts'

    def __str__(self):
        return f"{self.bank_code} - {self.account_number} ({self.account_holder})"
