from decimal import Decimal
from typing import Optional

from django.db import transaction
from django.db.models import Sum

from .models import PlatformSettings, InstructorEarning, Payout, Order


class EarningsService:
    """Service layer for managing instructor earnings and payouts"""

    @classmethod
    def get_platform_settings(cls) -> PlatformSettings:
        """Get platform settings singleton"""
        return PlatformSettings.get_settings()
    
    @classmethod
    def get_commission_rate(cls) -> Decimal:
        """
        Get commission rate from global settings if available,
        otherwise fallback to PlatformSettings model.
        """
        from core.utils import get_payment_settings
        payment_settings = get_payment_settings()
        return Decimal(str(payment_settings['commission_percentage']))

    @classmethod
    @transaction.atomic
    def create_earning_from_order(cls, order: Order) -> Optional[InstructorEarning]:
        """
        Create instructor earning record when an order is completed.
        Called automatically via signal when payment_completed is fired.
        Uses commission rate from global settings.
        """
        # Only process course orders (not subscriptions which go to platform)
        if order.order_type != 'course':
            return None

        # Get the course owner (instructor)
        course = order.item
        if not course or not hasattr(course, 'owner'):
            return None

        instructor = course.owner

        # Calculate earnings using global settings commission
        order_amount = order.total_amount
        commission_rate = cls.get_commission_rate()  # From global settings!
        platform_fee = (order_amount * commission_rate / Decimal('100')).quantize(Decimal('0.01'))
        instructor_earning = order_amount - platform_fee

        # Create earning record
        earning = InstructorEarning.objects.create(
            order=order,
            instructor=instructor,
            order_amount=order_amount,
            commission_rate=commission_rate,
            platform_fee=platform_fee,
            instructor_earning=instructor_earning,
            currency=order.currency,
        )

        return earning

    @classmethod
    def get_instructor_balance(cls, instructor) -> dict:
        """Get instructor's current balance and earnings summary"""
        earnings = InstructorEarning.objects.filter(instructor=instructor)
        
        total_earned = earnings.aggregate(total=Sum('instructor_earning'))['total'] or Decimal('0')
        pending_balance = earnings.filter(is_paid_out=False).aggregate(
            total=Sum('instructor_earning')
        )['total'] or Decimal('0')
        paid_out = earnings.filter(is_paid_out=True).aggregate(
            total=Sum('instructor_earning')
        )['total'] or Decimal('0')

        # Get pending payouts
        pending_payouts = Payout.objects.filter(
            instructor=instructor,
            status__in=['pending', 'approved', 'processing']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # Available balance = pending balance - pending payouts
        available_balance = pending_balance - pending_payouts

        settings = cls.get_platform_settings()

        return {
            'total_earned': total_earned,
            'pending_balance': pending_balance,
            'available_balance': available_balance,
            'paid_out': paid_out,
            'pending_payouts': pending_payouts,
            'currency': settings.default_currency,
            'minimum_payout': settings.minimum_payout,
            'can_request_payout': available_balance >= settings.minimum_payout,
        }

    @classmethod
    def get_instructor_earnings(cls, instructor, limit=None):
        """Get instructor's earning history"""
        qs = InstructorEarning.objects.filter(
            instructor=instructor
        ).select_related('order').order_by('-created_at')
        
        if limit:
            qs = qs[:limit]
        return qs

    @classmethod
    @transaction.atomic
    def request_payout(
        cls,
        instructor,
        bank_name: str,
        account_number: str,
        account_holder: str,
        amount: Optional[Decimal] = None
    ) -> tuple[Payout, str]:
        """
        Request a payout for instructor.
        If amount is None, request full available balance.
        Returns (Payout, error_message) - error_message is empty on success.
        """
        balance = cls.get_instructor_balance(instructor)
        settings = cls.get_platform_settings()

        # Determine amount
        if amount is None:
            amount = balance['available_balance']

        # Validate amount
        if amount <= 0:
            return None, "Jumlah payout harus lebih dari 0"

        if amount > balance['available_balance']:
            return None, f"Saldo tidak mencukupi. Tersedia: {balance['available_balance']}"

        if amount < settings.minimum_payout:
            return None, f"Minimum payout adalah {settings.minimum_payout}"

        # Create payout request
        payout = Payout.objects.create(
            instructor=instructor,
            amount=amount,
            currency=settings.default_currency,
            bank_name=bank_name,
            bank_account_number=account_number,
            bank_account_holder=account_holder,
            status='pending' if settings.payout_requires_approval else 'approved'
        )

        # Link unpaid earnings to this payout (up to payout amount)
        unpaid_earnings = InstructorEarning.objects.filter(
            instructor=instructor,
            is_paid_out=False,
            payout__isnull=True
        ).order_by('created_at')

        running_total = Decimal('0')
        for earning in unpaid_earnings:
            if running_total >= amount:
                break
            earning.payout = payout
            earning.save(update_fields=['payout'])
            running_total += earning.instructor_earning

        return payout, ""

    @classmethod
    def get_instructor_payouts(cls, instructor, limit=None):
        """Get instructor's payout history"""
        qs = Payout.objects.filter(instructor=instructor).order_by('-requested_at')
        if limit:
            qs = qs[:limit]
        return qs

    @classmethod
    def get_platform_revenue_summary(cls) -> dict:
        """Get platform revenue summary for admin dashboard"""
        earnings = InstructorEarning.objects.all()
        
        total_revenue = earnings.aggregate(total=Sum('order_amount'))['total'] or Decimal('0')
        total_platform_fees = earnings.aggregate(total=Sum('platform_fee'))['total'] or Decimal('0')
        total_instructor_earnings = earnings.aggregate(
            total=Sum('instructor_earning')
        )['total'] or Decimal('0')
        
        pending_payouts = Payout.objects.filter(
            status__in=['pending', 'approved', 'processing']
        )
        pending_payout_amount = pending_payouts.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        pending_payout_count = pending_payouts.count()

        return {
            'total_revenue': total_revenue,
            'total_platform_fees': total_platform_fees,
            'total_instructor_earnings': total_instructor_earnings,
            'pending_payout_amount': pending_payout_amount,
            'pending_payout_count': pending_payout_count,
        }
