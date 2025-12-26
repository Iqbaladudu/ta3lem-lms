from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class PlatformSettings(models.Model):
    """Singleton model for platform-wide revenue settings"""
    
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('20.00'),
        help_text='Platform commission percentage (e.g., 20 for 20%)'
    )
    minimum_payout = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('500000'),
        help_text='Minimum balance required to request payout'
    )
    payout_requires_approval = models.BooleanField(
        default=True,
        help_text='Whether payouts need admin approval'
    )
    default_currency = models.CharField(max_length=3, default='IDR')
    
    class Meta:
        verbose_name = 'Platform Settings'
        verbose_name_plural = 'Platform Settings'

    def __str__(self):
        return f"Platform Settings (Commission: {self.commission_rate}%)"

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        """Get or create platform settings singleton"""
        settings, _ = cls.objects.get_or_create(pk=1)
        return settings


class InstructorEarning(models.Model):
    """Track earnings for each completed order"""
    
    order = models.OneToOneField(
        'payments.Order',
        on_delete=models.CASCADE,
        related_name='earning'
    )
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='earnings'
    )
    
    # Amounts
    order_amount = models.DecimalField(max_digits=10, decimal_places=2)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2)
    instructor_earning = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='IDR')
    
    # Status
    is_paid_out = models.BooleanField(default=False)
    payout = models.ForeignKey(
        'Payout',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='earnings'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['instructor', 'is_paid_out']),
            models.Index(fields=['instructor', 'created_at']),
        ]

    def __str__(self):
        return f"{self.instructor.username} - {self.get_formatted_earning()}"

    def get_formatted_earning(self):
        if self.currency == 'IDR':
            return f"Rp {self.instructor_earning:,.0f}".replace(',', '.')
        return f"{self.currency} {self.instructor_earning:,.2f}"


class Payout(models.Model):
    """Track payout requests from instructors"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]

    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payouts'
    )
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='IDR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Bank details for transfer
    bank_name = models.CharField(max_length=100)
    bank_account_number = models.CharField(max_length=50)
    bank_account_holder = models.CharField(max_length=100)
    
    # Processing info
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_payouts'
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    transfer_reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['instructor', 'status']),
            models.Index(fields=['status', 'requested_at']),
        ]

    def __str__(self):
        return f"Payout #{self.pk} - {self.instructor.username} - {self.get_formatted_amount()}"

    def get_formatted_amount(self):
        if self.currency == 'IDR':
            return f"Rp {self.amount:,.0f}".replace(',', '.')
        return f"{self.currency} {self.amount:,.2f}"

    def approve(self, admin_user):
        """Approve payout request"""
        self.status = 'approved'
        self.processed_by = admin_user
        self.processed_at = timezone.now()
        self.save()

    def complete(self, transfer_reference=''):
        """Mark payout as completed"""
        self.status = 'completed'
        self.transfer_reference = transfer_reference
        if not self.processed_at:
            self.processed_at = timezone.now()
        self.save()
        
        # Mark all associated earnings as paid out
        self.earnings.update(is_paid_out=True)

    def reject(self, reason=''):
        """Reject payout request"""
        self.status = 'rejected'
        self.rejection_reason = reason
        self.processed_at = timezone.now()
        self.save()
        
        # Unlink earnings so they can be included in future payouts
        self.earnings.update(payout=None)
