from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from .models import PaymentProvider, BankAccount, Order


@admin.register(PaymentProvider)
class PaymentProviderAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'provider_type', 'display_name', 
        'is_active', 'supports_subscription', 'display_order'
    ]
    list_filter = ['is_active', 'provider_type', 'supports_subscription']
    list_editable = ['is_active', 'display_order']
    search_fields = ['name', 'display_name']
    ordering = ['display_order', 'name']

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'provider_type', 'display_name', 'description', 'icon')
        }),
        ('Configuration', {
            'fields': ('config', 'supported_currencies'),
            'classes': ('collapse',),
        }),
        ('Features', {
            'fields': ('supports_subscription', 'supports_refund')
        }),
        ('Limits', {
            'fields': ('min_amount', 'max_amount')
        }),
        ('Status', {
            'fields': ('is_active', 'display_order')
        }),
    )


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = [
        'bank_code', 'account_number', 'account_holder',
        'provider', 'is_active', 'display_order'
    ]
    list_filter = ['is_active', 'provider', 'bank_code']
    list_editable = ['is_active', 'display_order']
    search_fields = ['bank_name', 'bank_code', 'account_number', 'account_holder']
    ordering = ['display_order', 'bank_name']

    fieldsets = (
        ('Bank Details', {
            'fields': ('provider', 'bank_name', 'bank_code', 'account_number', 'account_holder', 'branch')
        }),
        ('Display', {
            'fields': ('logo', 'instructions')
        }),
        ('Status', {
            'fields': ('is_active', 'display_order')
        }),
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'user', 'order_type', 'total_amount_display',
        'status_badge', 'payment_provider', 'created_at'
    ]
    list_filter = [
        'status', 'order_type', 'payment_provider', 
        'created_at', 'paid_at'
    ]
    search_fields = ['order_number', 'user__username', 'user__email']
    readonly_fields = [
        'order_number', 'created_at', 'updated_at', 
        'paid_at', 'payment_proof_preview'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = (
        ('Order Info', {
            'fields': ('order_number', 'user', 'order_type', 'status')
        }),
        ('Purchased Item', {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',),
        }),
        ('Pricing', {
            'fields': ('subtotal', 'discount_amount', 'tax_amount', 'total_amount', 'currency')
        }),
        ('Payment', {
            'fields': ('payment_provider', 'gateway_order_id', 'gateway_payment_id')
        }),
        ('Manual Transfer', {
            'fields': (
                'bank_account', 'payment_proof', 'payment_proof_preview',
                'transfer_amount', 'transfer_date', 'transfer_notes'
            ),
        }),
        ('Verification', {
            'fields': ('verified_by', 'verified_at', 'verification_notes', 'rejection_reason'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'paid_at', 'expires_at'),
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'gateway_response'),
            'classes': ('collapse',),
        }),
    )

    actions = ['verify_payments', 'reject_payments', 'mark_as_expired']

    def total_amount_display(self, obj):
        return obj.get_formatted_total()
    total_amount_display.short_description = 'Amount'

    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'awaiting_verification': 'blue',
            'processing': 'purple',
            'completed': 'green',
            'failed': 'red',
            'cancelled': 'gray',
            'refunded': 'yellow',
            'expired': 'gray',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def payment_proof_preview(self, obj):
        if obj.payment_proof:
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" style="max-width: 300px; max-height: 200px;" />'
                '</a>',
                obj.payment_proof.url, obj.payment_proof.url
            )
        return '-'
    payment_proof_preview.short_description = 'Proof Preview'

    @admin.action(description='Verify selected payments')
    def verify_payments(self, request, queryset):
        from .services import PaymentService
        count = 0
        for order in queryset.filter(status='awaiting_verification'):
            if PaymentService.verify_manual_payment(order, request.user, 'Bulk verified via admin'):
                count += 1
        self.message_user(request, f'{count} payment(s) verified successfully.')

    @admin.action(description='Reject selected payments')
    def reject_payments(self, request, queryset):
        from .services import PaymentService
        count = 0
        for order in queryset.filter(status='awaiting_verification'):
            if PaymentService.reject_manual_payment(
                order, request.user, 'Bulk rejected via admin'
            ):
                count += 1
        self.message_user(request, f'{count} payment(s) rejected.')

    @admin.action(description='Mark selected as expired')
    def mark_as_expired(self, request, queryset):
        count = queryset.filter(
            status__in=['pending', 'awaiting_verification']
        ).update(status='expired', updated_at=timezone.now())
        self.message_user(request, f'{count} order(s) marked as expired.')


# ========== Revenue Sharing Admin ==========
from .models import PlatformSettings, InstructorEarning, Payout


@admin.register(PlatformSettings)
class PlatformSettingsAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'commission_rate', 'minimum_payout', 'payout_requires_approval']
    
    def has_add_permission(self, request):
        # Only allow one settings instance
        return not PlatformSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(InstructorEarning)
class InstructorEarningAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'instructor', 'order', 'order_amount_display', 
        'commission_rate', 'platform_fee_display', 'earning_display',
        'is_paid_out', 'created_at'
    ]
    list_filter = ['is_paid_out', 'created_at', 'currency']
    search_fields = ['instructor__username', 'instructor__email', 'order__order_number']
    readonly_fields = [
        'order', 'instructor', 'order_amount', 'commission_rate',
        'platform_fee', 'instructor_earning', 'currency', 'created_at'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def order_amount_display(self, obj):
        if obj.currency == 'IDR':
            return f"Rp {obj.order_amount:,.0f}".replace(',', '.')
        return f"{obj.currency} {obj.order_amount:,.2f}"
    order_amount_display.short_description = 'Order Amount'
    
    def platform_fee_display(self, obj):
        if obj.currency == 'IDR':
            return f"Rp {obj.platform_fee:,.0f}".replace(',', '.')
        return f"{obj.currency} {obj.platform_fee:,.2f}"
    platform_fee_display.short_description = 'Platform Fee'
    
    def earning_display(self, obj):
        if obj.currency == 'IDR':
            return f"Rp {obj.instructor_earning:,.0f}".replace(',', '.')
        return f"{obj.currency} {obj.instructor_earning:,.2f}"
    earning_display.short_description = 'Instructor Earning'


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'instructor', 'amount_display', 'status_badge',
        'bank_name', 'requested_at', 'processed_at'
    ]
    list_filter = ['status', 'requested_at', 'bank_name']
    search_fields = [
        'instructor__username', 'instructor__email',
        'bank_account_number', 'bank_account_holder'
    ]
    readonly_fields = ['requested_at', 'earnings_list']
    date_hierarchy = 'requested_at'
    ordering = ['-requested_at']
    
    fieldsets = (
        ('Payout Info', {
            'fields': ('instructor', 'amount', 'currency', 'status')
        }),
        ('Bank Details', {
            'fields': ('bank_name', 'bank_account_number', 'bank_account_holder')
        }),
        ('Processing', {
            'fields': ('processed_by', 'processed_at', 'transfer_reference', 'notes')
        }),
        ('Rejection', {
            'fields': ('rejection_reason',),
            'classes': ('collapse',),
        }),
        ('Related Earnings', {
            'fields': ('earnings_list',),
        }),
        ('Timestamps', {
            'fields': ('requested_at',)
        }),
    )
    
    actions = ['approve_payouts', 'complete_payouts', 'reject_payouts']
    
    def amount_display(self, obj):
        return obj.get_formatted_amount()
    amount_display.short_description = 'Amount'
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'approved': 'blue',
            'processing': 'purple',
            'completed': 'green',
            'rejected': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def earnings_list(self, obj):
        earnings = obj.earnings.all()[:10]
        if not earnings:
            return '-'
        items = [f"Order {e.order.order_number}: {e.get_formatted_earning()}" for e in earnings]
        return format_html('<br>'.join(items))
    earnings_list.short_description = 'Related Earnings'
    
    @admin.action(description='Approve selected payouts')
    def approve_payouts(self, request, queryset):
        count = 0
        for payout in queryset.filter(status='pending'):
            payout.approve(request.user)
            count += 1
        self.message_user(request, f'{count} payout(s) approved.')
    
    @admin.action(description='Mark selected as completed')
    def complete_payouts(self, request, queryset):
        count = 0
        for payout in queryset.filter(status__in=['pending', 'approved', 'processing']):
            payout.complete()
            count += 1
        self.message_user(request, f'{count} payout(s) completed.')
    
    @admin.action(description='Reject selected payouts')
    def reject_payouts(self, request, queryset):
        count = 0
        for payout in queryset.filter(status__in=['pending', 'approved']):
            payout.reject('Rejected via admin bulk action')
            count += 1
        self.message_user(request, f'{count} payout(s) rejected.')

