from django.contrib import admin
from django.utils.html import format_html

from .models import SubscriptionPlan, UserSubscription


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'billing_cycle', 'formatted_price', 
        'is_active', 'is_featured', 'display_order'
    ]
    list_filter = ['is_active', 'is_featured', 'billing_cycle']
    list_editable = ['is_active', 'is_featured', 'display_order']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['display_order', 'price']

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Pricing', {
            'fields': ('price', 'original_price', 'currency', 'billing_cycle')
        }),
        ('Features', {
            'fields': ('features', 'max_concurrent_courses', 'includes_certificate', 'priority_support')
        }),
        ('Trial', {
            'fields': ('trial_days',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured', 'display_order')
        }),
    )

    def formatted_price(self, obj):
        return obj.get_formatted_price()
    formatted_price.short_description = 'Price'


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'plan', 'status_badge', 'current_period_end', 
        'days_remaining', 'cancel_at_period_end'
    ]
    list_filter = ['status', 'plan', 'cancel_at_period_end', 'started_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['started_at', 'days_remaining_display']
    date_hierarchy = 'started_at'
    ordering = ['-started_at']

    fieldsets = (
        ('Subscription', {
            'fields': ('user', 'plan', 'status', 'order')
        }),
        ('Period', {
            'fields': ('current_period_start', 'current_period_end', 'days_remaining_display')
        }),
        ('Renewal', {
            'fields': ('auto_renew', 'gateway_subscription_id')
        }),
        ('Cancellation', {
            'fields': ('cancel_at_period_end', 'cancelled_at', 'cancellation_reason')
        }),
        ('Timestamps', {
            'fields': ('started_at',),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'trial': 'purple',
            'active': 'green',
            'past_due': 'orange',
            'cancelled': 'gray',
            'expired': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def days_remaining(self, obj):
        days = obj.days_remaining()
        if days <= 0:
            return format_html('<span style="color: red;">Expired</span>')
        elif days <= 7:
            return format_html('<span style="color: orange;">{} days</span>', days)
        return f"{days} days"
    days_remaining.short_description = 'Remaining'

    def days_remaining_display(self, obj):
        return f"{obj.days_remaining()} days"
    days_remaining_display.short_description = 'Days Remaining'

    @property
    def created_at(self):
        return self.started_at
