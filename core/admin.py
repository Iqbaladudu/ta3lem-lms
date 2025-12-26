"""
Django Admin configuration for Global Settings
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import GlobalSettings


@admin.register(GlobalSettings)
class GlobalSettingsAdmin(admin.ModelAdmin):
    """
    Custom admin for Global Settings with organized fieldsets
    """
    
    # Prevent adding/deleting (singleton model)
    def has_add_permission(self, request):
        # Only allow add if no settings exist
        return not GlobalSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Never allow deletion
        return False
    
    # Custom change list to show single "Edit Settings" button
    def changelist_view(self, request, extra_context=None):
        # Redirect to edit page if settings exist
        if GlobalSettings.objects.exists():
            settings = GlobalSettings.objects.first()
            from django.shortcuts import redirect
            from django.urls import reverse
            return redirect(reverse('admin:core_globalsettings_change', args=[settings.pk]))
        return super().changelist_view(request, extra_context)
    
    fieldsets = (
        ('🏢 Platform Information', {
            'fields': ('site_name', 'site_tagline', 'site_description', 'contact_email'),
            'description': 'Basic information about your LMS platform'
        }),
        ('🎛️ Feature Toggles', {
            'fields': (
                'enable_subscriptions',
                'enable_one_time_purchase', 
                'enable_free_courses',
                'enable_course_certificates',
                'enable_course_reviews',
                'enable_discussion_forums',
                'enable_waitlist',
                'enable_instructor_earnings',
            ),
            'description': 'Enable or disable major platform features',
            'classes': ('collapse',),
        }),
        ('📚 Enrollment Settings', {
            'fields': (
                'require_email_verification',
                'auto_enroll_free_courses',
                'max_enrollments_per_student',
            ),
            'classes': ('collapse',),
        }),
        ('💳 Subscription Settings', {
            'fields': (
                'subscription_trial_enabled',
                'subscription_trial_days',
                'subscription_grace_period_days',
                'subscription_auto_renew',
            ),
            'classes': ('collapse',),
        }),
        ('💰 Payment & Revenue Settings', {
            'fields': (
                'payment_currency',
                'minimum_payout_amount',
                'platform_commission_percentage',
            ),
            'classes': ('collapse',),
        }),
        ('📖 Course Settings', {
            'fields': (
                'default_course_capacity',
                'require_course_approval',
                'min_course_price',
                'max_course_price',
            ),
            'classes': ('collapse',),
        }),
        ('📁 Content & Upload Settings', {
            'fields': (
                'max_video_size_mb',
                'max_file_size_mb',
                'allowed_video_formats',
                'allowed_file_formats',
            ),
            'classes': ('collapse',),
        }),
        ('📧 Notification Settings', {
            'fields': (
                'send_enrollment_notifications',
                'send_completion_notifications',
                'send_subscription_notifications',
                'send_payment_notifications',
                'subscription_expiry_reminder_days',
            ),
            'classes': ('collapse',),
        }),
        ('🔍 SEO & Analytics', {
            'fields': (
                'meta_keywords',
                'google_analytics_id',
                'facebook_pixel_id',
            ),
            'classes': ('collapse',),
        }),
        ('📱 Social Media Links', {
            'fields': (
                'facebook_url',
                'twitter_url',
                'instagram_url',
                'linkedin_url',
                'youtube_url',
            ),
            'classes': ('collapse',),
        }),
        ('🎨 Landing Page Settings', {
            'fields': (
                'show_stats_section',
                'show_featured_courses',
                'show_testimonials',
                'show_pricing',
                'featured_courses_count',
            ),
            'classes': ('collapse',),
        }),
        ('🚧 Maintenance Mode', {
            'fields': (
                'maintenance_mode',
                'maintenance_message',
            ),
            'description': '⚠️ Warning: Enabling maintenance mode will make the site inaccessible to regular users',
            'classes': ('collapse',),
        }),
        ('⚙️ Advanced Settings', {
            'fields': (
                'session_timeout_minutes',
                'cache_timeout_seconds',
                'enable_debug_mode',
            ),
            'description': '⚠️ Caution: These settings affect system performance and security',
            'classes': ('collapse',),
        }),
        ('ℹ️ System Information', {
            'fields': ('created_at', 'updated_at', 'updated_by'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'updated_by')
    
    def save_model(self, request, obj, form, change):
        """Track who updated the settings"""
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    # Custom admin title
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        # Add help text styling
        for field_name, field in form.base_fields.items():
            if field.help_text:
                field.help_text = format_html(
                    '<span style="color: #666; font-size: 0.9em;">{}</span>',
                    field.help_text
                )
        
        return form
    
    class Media:
        css = {
            'all': ('admin/css/global-settings.css',)
        }

