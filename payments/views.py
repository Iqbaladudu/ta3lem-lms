from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, ListView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import Order, PaymentProvider, BankAccount
from .services import PaymentService


class PaymentProviderListView(ListView):
    """List available payment providers for a given amount"""
    model = PaymentProvider
    template_name = 'payments/provider_list.html'
    context_object_name = 'providers'

    def get_queryset(self):
        amount = self.request.GET.get('amount', 0)
        currency = self.request.GET.get('currency', 'IDR')
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            amount = 0
        return PaymentService.get_available_providers(amount, currency)


class CheckoutView(LoginRequiredMixin, View):
    """
    Unified checkout view for courses, bundles, and subscriptions.
    Handles payment provider selection and payment initiation.
    """
    template_name = 'payments/checkout.html'

    def get(self, request, order_type, item_id):
        """Display checkout page with payment options"""
        from django.contrib.contenttypes.models import ContentType
        
        # Get the item being purchased based on order_type
        item = self._get_purchasable_item(order_type, item_id)
        if not item:
            raise Http404("Item not found")
        
        # VALIDATION: Check if course supports one-time purchase
        if order_type == 'course':
            from courses.models import Course
            if isinstance(item, Course):
                pricing_type = item.pricing_type
                
                # Block checkout for subscription-only courses
                if pricing_type == 'subscription_only':
                    messages.error(request, 
                        f'Kursus "{item.title}" hanya dapat diakses melalui subscription. '
                        'Silakan berlangganan terlebih dahulu.')
                    return redirect('subscriptions:plans')
                
                # Check if one-time purchase is enabled globally
                from core.utils import is_feature_enabled
                if not is_feature_enabled('one_time_purchase'):
                    if pricing_type == 'one_time' or pricing_type == 'both':
                        messages.error(request, 
                            'Pembelian kursus satuan tidak tersedia saat ini. '
                            'Silakan berlangganan untuk mengakses kursus.')
                        return redirect('subscriptions:plans')

        # Get price from item
        if hasattr(item, 'get_price'):
            amount = item.get_price()
        elif hasattr(item, 'price'):
            amount = item.price
        else:
            amount = 0

        currency = getattr(item, 'currency', 'IDR')

        # Get available providers
        providers = PaymentService.get_available_providers(amount, currency)
        
        # Separate by type for UI
        gateway_providers = [p for p in providers if p.provider_type != 'manual_transfer']
        manual_providers = [p for p in providers if p.provider_type == 'manual_transfer']

        # Get bank accounts for manual transfers
        bank_accounts = []
        for provider in manual_providers:
            bank_accounts.extend(PaymentService.get_bank_accounts(provider))

        context = {
            'item': item,
            'order_type': order_type,
            'amount': amount,
            'currency': currency,
            'gateway_providers': gateway_providers,
            'manual_providers': manual_providers,
            'bank_accounts': bank_accounts,
        }

        return render(request, self.template_name, context)

    def post(self, request, order_type, item_id):
        """Process checkout and initiate payment"""
        provider_id = request.POST.get('payment_provider')
        if not provider_id:
            messages.error(request, 'Silakan pilih metode pembayaran')
            return redirect(request.path)

        provider = get_object_or_404(PaymentProvider, id=provider_id, is_active=True)
        
        # Get the item
        item = self._get_purchasable_item(order_type, item_id)
        if not item:
            raise Http404("Item not found")

        # Create order
        order = PaymentService.create_order(
            user=request.user,
            item=item,
            order_type=order_type,
            provider=provider,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        # Build URLs
        return_url = request.build_absolute_uri(
            reverse('payments:payment_success', kwargs={'order_number': order.order_number})
        )
        cancel_url = request.build_absolute_uri(
            reverse('payments:payment_cancel', kwargs={'order_number': order.order_number})
        )

        # Initiate payment
        result = PaymentService.initiate_payment(order, provider, return_url, cancel_url)

        if result.get('type') == 'manual_transfer':
            # Redirect to transfer instructions
            return redirect('payments:transfer_instructions', order_number=order.order_number)
        elif result.get('redirect_url'):
            # Redirect to payment gateway
            return redirect(result['redirect_url'])
        else:
            messages.error(request, 'Terjadi kesalahan saat memproses pembayaran')
            return redirect(request.path)

    def _get_purchasable_item(self, order_type, item_id):
        """Get the purchasable item based on order type"""
        if order_type == 'course':
            from courses.models import Course
            return Course.objects.filter(pk=item_id, status='published').first()
        elif order_type == 'subscription':
            # Import when subscriptions app is ready
            try:
                from subscriptions.models import SubscriptionPlan
                return SubscriptionPlan.objects.filter(pk=item_id, is_active=True).first()
            except ImportError:
                return None
        elif order_type == 'bundle':
            # Import when pricing app is ready
            try:
                from pricing.models import CourseBundle
                return CourseBundle.objects.filter(pk=item_id, is_active=True).first()
            except ImportError:
                return None
        return None


class TransferInstructionsView(LoginRequiredMixin, DetailView):
    """Display bank transfer instructions for manual payment"""
    model = Order
    template_name = 'payments/transfer_instructions.html'
    context_object_name = 'order'
    slug_field = 'order_number'
    slug_url_kwarg = 'order_number'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object
        
        # Get bank accounts for the provider
        if order.payment_provider:
            context['bank_accounts'] = PaymentService.get_bank_accounts(order.payment_provider)
        else:
            context['bank_accounts'] = PaymentService.get_bank_accounts()
        
        return context


class UploadPaymentProofView(LoginRequiredMixin, View):
    """Handle payment proof upload for manual transfers"""
    
    def get(self, request, order_number):
        """Show upload form"""
        order = get_object_or_404(
            Order,
            order_number=order_number,
            user=request.user,
            status='awaiting_verification'
        )
        return render(request, 'payments/upload_proof.html', {'order': order})

    def post(self, request, order_number):
        """Process proof upload"""
        order = get_object_or_404(
            Order,
            order_number=order_number,
            user=request.user,
            status='awaiting_verification'
        )

        if 'payment_proof' not in request.FILES:
            messages.error(request, 'Silakan upload bukti transfer')
            return redirect('payments:upload_proof', order_number=order_number)

        # Update order with proof
        order.payment_proof = request.FILES['payment_proof']
        order.transfer_date = request.POST.get('transfer_date') or None
        order.transfer_amount = request.POST.get('transfer_amount') or None
        order.transfer_notes = request.POST.get('notes', '')
        
        # If bank account selected
        bank_id = request.POST.get('bank_account')
        if bank_id:
            order.bank_account = BankAccount.objects.filter(id=bank_id).first()
        
        order.save()

        messages.success(
            request,
            'Bukti transfer berhasil diupload. Tim kami akan memverifikasi '
            'pembayaran Anda dalam 1x24 jam kerja.'
        )

        return redirect('payments:payment_status', order_number=order_number)


class PaymentStatusView(LoginRequiredMixin, DetailView):
    """Display order/payment status"""
    model = Order
    template_name = 'payments/status.html'
    context_object_name = 'order'
    slug_field = 'order_number'
    slug_url_kwarg = 'order_number'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class PaymentSuccessView(LoginRequiredMixin, View):
    """Handle successful payment return from gateway"""
    
    def get(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
        
        # Try to verify payment
        verification_data = dict(request.GET)
        if PaymentService.verify_payment(order, verification_data):
            messages.success(request, 'Pembayaran berhasil! Terima kasih.')
        
        return redirect('payments:payment_status', order_number=order_number)


class PaymentCancelView(LoginRequiredMixin, View):
    """Handle cancelled payment from gateway"""
    
    def get(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
        
        if order.status == 'processing':
            order.status = 'cancelled'
            order.save(update_fields=['status', 'updated_at'])
        
        messages.info(request, 'Pembayaran dibatalkan.')
        return redirect('payments:payment_status', order_number=order_number)


@method_decorator(csrf_exempt, name='dispatch')
class WebhookView(View):
    """Handle webhooks from payment gateways"""
    
    def post(self, request, provider_type):
        try:
            provider = PaymentProvider.objects.get(
                provider_type=provider_type,
                is_active=True
            )
        except PaymentProvider.DoesNotExist:
            return HttpResponse(status=404)

        # Get headers as dict
        headers = {
            key.replace('HTTP_', '').replace('_', '-').lower(): value
            for key, value in request.META.items()
            if key.startswith('HTTP_')
        }
        headers['content-type'] = request.content_type

        result = PaymentService.handle_webhook(provider, request.body, headers)

        if result.get('success'):
            return HttpResponse(status=200)
        else:
            return HttpResponse(result.get('error', 'Error'), status=400)


# ========== Instructor Earnings Views ==========

class InstructorEarningsView(LoginRequiredMixin, View):
    """Dashboard for instructors to view their earnings and payouts"""
    template_name = 'payments/instructor/earnings.html'
    
    def get(self, request):
        from .earnings_service import EarningsService
        
        # Check if user is an instructor
        if not hasattr(request.user, 'role') or request.user.role != 'instructor':
            messages.error(request, 'Halaman ini hanya untuk instruktur')
            return redirect('landing')
        
        balance = EarningsService.get_instructor_balance(request.user)
        recent_earnings = EarningsService.get_instructor_earnings(request.user, limit=10)
        payouts = EarningsService.get_instructor_payouts(request.user, limit=5)
        
        context = {
            'balance': balance,
            'recent_earnings': recent_earnings,
            'payouts': payouts,
        }
        
        return render(request, self.template_name, context)


class RequestPayoutView(LoginRequiredMixin, View):
    """Handle payout requests from instructors"""
    template_name = 'payments/instructor/request_payout.html'
    
    def get(self, request):
        from .earnings_service import EarningsService
        
        if not hasattr(request.user, 'role') or request.user.role != 'instructor':
            messages.error(request, 'Halaman ini hanya untuk instruktur')
            return redirect('landing')
        
        balance = EarningsService.get_instructor_balance(request.user)
        
        if not balance['can_request_payout']:
            messages.warning(
                request,
                f"Saldo minimum untuk payout adalah {balance['minimum_payout']:,.0f}. "
                f"Saldo tersedia Anda: {balance['available_balance']:,.0f}"
            )
            return redirect('payments:instructor_earnings')
        
        context = {
            'balance': balance,
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request):
        from decimal import Decimal
        from .earnings_service import EarningsService
        
        if not hasattr(request.user, 'role') or request.user.role != 'instructor':
            return redirect('landing')
        
        bank_name = request.POST.get('bank_name', '').strip()
        account_number = request.POST.get('account_number', '').strip()
        account_holder = request.POST.get('account_holder', '').strip()
        
        if not all([bank_name, account_number, account_holder]):
            messages.error(request, 'Silakan lengkapi data rekening bank')
            return redirect('payments:request_payout')
        
        # Get amount (optional - defaults to full balance)
        amount = request.POST.get('amount')
        if amount:
            try:
                amount = Decimal(amount.replace(',', '').replace('.', ''))
            except (ValueError, TypeError):
                amount = None
        else:
            amount = None
        
        payout, error = EarningsService.request_payout(
            instructor=request.user,
            bank_name=bank_name,
            account_number=account_number,
            account_holder=account_holder,
            amount=amount
        )
        
        if error:
            messages.error(request, error)
            return redirect('payments:request_payout')
        
        messages.success(
            request,
            f'Permintaan payout sebesar {payout.get_formatted_amount()} berhasil dibuat. '
            'Menunggu verifikasi dari admin.'
        )
        
        return redirect('payments:payout_detail', payout_id=payout.pk)


class PayoutDetailView(LoginRequiredMixin, DetailView):
    """View payout details"""
    template_name = 'payments/instructor/payout_detail.html'
    context_object_name = 'payout'
    pk_url_kwarg = 'payout_id'
    
    def get_queryset(self):
        from .models import Payout
        return Payout.objects.filter(instructor=self.request.user)

