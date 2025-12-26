import random
import string

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

from .providers import PaymentProvider, BankAccount


class Order(models.Model):
    """Central order/transaction model for all payment types"""

    ORDER_TYPE_CHOICES = [
        ('course', 'Single Course'),
        ('bundle', 'Course Bundle'),
        ('subscription', 'Subscription'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('awaiting_verification', 'Awaiting Verification'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
        ('expired', 'Expired'),
    ]

    # Order identification
    order_number = models.CharField(max_length=50, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )

    # Order type and generic reference to purchased item
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey('content_type', 'object_id')

    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='IDR')

    # Payment provider reference
    payment_provider = models.ForeignKey(
        PaymentProvider,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='pending')

    # Gateway references (for Stripe, Midtrans, etc.)
    gateway_order_id = models.CharField(max_length=100, blank=True)
    gateway_payment_id = models.CharField(max_length=100, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)

    # Manual transfer specific fields
    bank_account = models.ForeignKey(
        BankAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    payment_proof = models.ImageField(upload_to='payment_proofs/%Y/%m/', blank=True)
    transfer_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Amount user claims to have transferred'
    )
    transfer_date = models.DateField(null=True, blank=True)
    transfer_notes = models.TextField(blank=True)

    # Verification (for manual payments)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_orders'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Payment deadline for pending orders'
    )

    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['order_number']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['payment_provider', 'status']),
        ]
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'

    def __str__(self):
        return f"{self.order_number} - {self.user.username} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        # Track if this is a status change to 'completed'
        is_new = self.pk is None
        old_status = None
        
        if not is_new:
            try:
                old_status = Order.objects.filter(pk=self.pk).values_list('status', flat=True).first()
            except Order.DoesNotExist:
                pass
        
        if not self.order_number:
            self.order_number = self.generate_order_number()
        
        # Set paid_at if completing
        if self.status == 'completed' and not self.paid_at:
            self.paid_at = timezone.now()
        
        super().save(*args, **kwargs)
        
        # Emit signal if status just changed to 'completed'
        if old_status and old_status != 'completed' and self.status == 'completed':
            from payments.signals import payment_completed
            payment_completed.send(sender=self.__class__, order=self, user=self.user)

    @staticmethod
    def generate_order_number():
        """Generate unique order number: TA3-YYYYMMDD-XXXXX"""
        date_str = timezone.now().strftime('%Y%m%d')
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        return f"TA3-{date_str}-{random_str}"

    def get_formatted_total(self):
        """Get formatted total amount with currency"""
        if self.currency == 'IDR':
            return f"Rp {self.total_amount:,.0f}".replace(',', '.')
        elif self.currency == 'USD':
            return f"${self.total_amount:,.2f}"
        elif self.currency == 'EUR':
            return f"€{self.total_amount:,.2f}"
        return f"{self.total_amount} {self.currency}"

    def is_expired(self):
        """Check if payment deadline has passed"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    def mark_completed(self, gateway_payment_id=''):
        """Mark order as completed - signal is emitted by save()"""
        self.status = 'completed'
        self.paid_at = timezone.now()
        if gateway_payment_id:
            self.gateway_payment_id = gateway_payment_id
        self.save()  # Signal will be emitted by save() if status changed

    def mark_failed(self, reason=''):
        """Mark order as failed and trigger signals"""
        from payments.signals import payment_failed
        
        self.status = 'failed'
        self.rejection_reason = reason
        self.save(update_fields=['status', 'rejection_reason', 'updated_at'])
        
        # Emit signal
        payment_failed.send(sender=self.__class__, order=self, reason=reason)
