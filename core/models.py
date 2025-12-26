"""
Global Settings Model for Ta3lem LMS
Allows admin to configure platform-wide settings from Django Admin
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.cache import cache


class GlobalSettings(models.Model):
    """
    Singleton model for global LMS settings.
    Only one instance should exist at a time.
    """
    
    # Platform Information
    site_name = models.CharField(
        max_length=200,
        default='Ta3lem LMS',
        help_text='Name of your LMS platform'
    )
    site_tagline = models.CharField(
        max_length=500,
        blank=True,
        default='Platform Belajar Online Terdepan',
        help_text='Tagline shown on landing page'
    )
    site_description = models.TextField(
        blank=True,
        default='Tingkatkan keahlian masa depanmu dengan kursus berkualitas',
        help_text='Site description for SEO'
    )
    contact_email = models.EmailField(
        default='support@ta3lem.com',
        help_text='Main contact email for support'
    )
    
    # Feature Toggles
    enable_subscriptions = models.BooleanField(
        default=True,
        help_text='Enable subscription-based access to courses'
    )
    enable_one_time_purchase = models.BooleanField(
        default=True,
        help_text='Enable one-time course purchases'
    )
    enable_free_courses = models.BooleanField(
        default=True,
        help_text='Allow free courses on the platform'
    )
    enable_course_certificates = models.BooleanField(
        default=True,
        help_text='Enable certificate generation for completed courses'
    )
    enable_course_reviews = models.BooleanField(
        default=True,
        help_text='Allow students to review courses'
    )
    enable_discussion_forums = models.BooleanField(
        default=True,
        help_text='Enable discussion forums for courses'
    )
    enable_waitlist = models.BooleanField(
        default=True,
        help_text='Enable course waitlist when capacity is reached'
    )
    enable_instructor_earnings = models.BooleanField(
        default=True,
        help_text='Enable earnings system for instructors'
    )
    
    # Enrollment Settings
    require_email_verification = models.BooleanField(
        default=True,
        help_text='Require email verification before enrollment'
    )
    auto_enroll_free_courses = models.BooleanField(
        default=True,
        help_text='Automatically enroll students in free courses (no approval)'
    )
    max_enrollments_per_student = models.PositiveIntegerField(
        default=0,
        help_text='Maximum courses a student can enroll in (0 = unlimited)'
    )
    
    # Subscription Settings
    subscription_trial_enabled = models.BooleanField(
        default=True,
        help_text='Allow trial periods for subscriptions'
    )
    subscription_trial_days = models.PositiveIntegerField(
        default=7,
        validators=[MinValueValidator(1), MaxValueValidator(90)],
        help_text='Default trial period in days'
    )
    subscription_grace_period_days = models.PositiveIntegerField(
        default=3,
        validators=[MinValueValidator(0), MaxValueValidator(30)],
        help_text='Grace period after subscription expires before revoking access'
    )
    subscription_auto_renew = models.BooleanField(
        default=True,
        help_text='Enable auto-renewal for subscriptions'
    )
    
    # Payment Settings
    payment_currency = models.CharField(
        max_length=3,
        default='IDR',
        choices=[
            ('IDR', 'Indonesian Rupiah'),
            ('USD', 'US Dollar'),
            ('EUR', 'Euro'),
        ],
        help_text='Default currency for payments'
    )
    minimum_payout_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=100000,
        help_text='Minimum amount for instructor payout requests (in default currency)'
    )
    platform_commission_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Platform commission percentage on course sales'
    )
    
    # Course Settings
    default_course_capacity = models.PositiveIntegerField(
        default=0,
        help_text='Default maximum enrollment capacity for courses (0 = unlimited)'
    )
    require_course_approval = models.BooleanField(
        default=False,
        help_text='Require admin approval before courses are published'
    )
    min_course_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Minimum price for paid courses'
    )
    max_course_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=10000000,
        help_text='Maximum price for paid courses'
    )
    
    # Content Settings
    max_video_size_mb = models.PositiveIntegerField(
        default=500,
        help_text='Maximum video upload size in MB'
    )
    max_file_size_mb = models.PositiveIntegerField(
        default=50,
        help_text='Maximum file upload size in MB'
    )
    allowed_video_formats = models.CharField(
        max_length=200,
        default='mp4,webm,avi,mov',
        help_text='Allowed video formats (comma-separated)'
    )
    allowed_file_formats = models.CharField(
        max_length=200,
        default='pdf,doc,docx,ppt,pptx,xls,xlsx,zip',
        help_text='Allowed file formats for downloads (comma-separated)'
    )
    
    # Notification Settings
    send_enrollment_notifications = models.BooleanField(
        default=True,
        help_text='Send email notifications on enrollment'
    )
    send_completion_notifications = models.BooleanField(
        default=True,
        help_text='Send email notifications on course completion'
    )
    send_subscription_notifications = models.BooleanField(
        default=True,
        help_text='Send email notifications for subscription events'
    )
    send_payment_notifications = models.BooleanField(
        default=True,
        help_text='Send email notifications for payment events'
    )
    subscription_expiry_reminder_days = models.PositiveIntegerField(
        default=7,
        help_text='Days before expiry to send reminder email'
    )
    
    # SEO Settings
    meta_keywords = models.CharField(
        max_length=500,
        blank=True,
        default='online learning, courses, education, skills',
        help_text='Meta keywords for SEO (comma-separated)'
    )
    google_analytics_id = models.CharField(
        max_length=50,
        blank=True,
        help_text='Google Analytics tracking ID (e.g., G-XXXXXXXXXX)'
    )
    facebook_pixel_id = models.CharField(
        max_length=50,
        blank=True,
        help_text='Facebook Pixel ID for tracking'
    )
    
    # Social Media Links
    facebook_url = models.URLField(blank=True, help_text='Facebook page URL')
    twitter_url = models.URLField(blank=True, help_text='Twitter profile URL')
    instagram_url = models.URLField(blank=True, help_text='Instagram profile URL')
    linkedin_url = models.URLField(blank=True, help_text='LinkedIn page URL')
    youtube_url = models.URLField(blank=True, help_text='YouTube channel URL')
    
    # Maintenance Mode
    maintenance_mode = models.BooleanField(
        default=False,
        help_text='Enable maintenance mode (site inaccessible except for admins)'
    )
    maintenance_message = models.TextField(
        blank=True,
        default='We are currently performing maintenance. Please check back soon.',
        help_text='Message shown during maintenance mode'
    )
    
    # Landing Page Settings
    show_stats_section = models.BooleanField(
        default=True,
        help_text='Show statistics section on landing page'
    )
    show_featured_courses = models.BooleanField(
        default=True,
        help_text='Show featured courses section on landing page'
    )
    show_testimonials = models.BooleanField(
        default=True,
        help_text='Show testimonials section on landing page'
    )
    show_pricing = models.BooleanField(
        default=True,
        help_text='Show pricing section on landing page'
    )
    featured_courses_count = models.PositiveIntegerField(
        default=6,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        help_text='Number of featured courses to show on landing page'
    )
    
    # Advanced Settings
    session_timeout_minutes = models.PositiveIntegerField(
        default=60,
        help_text='User session timeout in minutes'
    )
    cache_timeout_seconds = models.PositiveIntegerField(
        default=300,
        help_text='Default cache timeout in seconds'
    )
    enable_debug_mode = models.BooleanField(
        default=False,
        help_text='⚠️ Enable debug mode (DO NOT use in production!)'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='settings_updates'
    )
    
    class Meta:
        verbose_name = 'Global Settings'
        verbose_name_plural = 'Global Settings'
    
    def __str__(self):
        return f"Global Settings - {self.site_name}"
    
    def save(self, *args, **kwargs):
        """Override save to ensure only one instance exists (singleton)"""
        # Ensure only one settings object exists
        if not self.pk and GlobalSettings.objects.exists():
            # If creating new but one already exists, update existing instead
            existing = GlobalSettings.objects.first()
            self.pk = existing.pk
        
        super().save(*args, **kwargs)
        
        # Clear cache when settings are updated
        cache.delete('global_settings')
    
    @classmethod
    def get_settings(cls):
        """
        Get global settings instance (singleton).
        Uses caching to avoid repeated database queries.
        """
        settings = cache.get('global_settings')
        
        if settings is None:
            settings, created = cls.objects.get_or_create(
                pk=1,
                defaults={'site_name': 'Ta3lem LMS'}
            )
            cache.set('global_settings', settings, timeout=3600)  # Cache for 1 hour
        
        return settings
    
    def get_allowed_video_formats_list(self):
        """Get list of allowed video formats"""
        return [fmt.strip() for fmt in self.allowed_video_formats.split(',')]
    
    def get_allowed_file_formats_list(self):
        """Get list of allowed file formats"""
        return [fmt.strip() for fmt in self.allowed_file_formats.split(',')]
    
    def is_feature_enabled(self, feature_name):
        """Check if a specific feature is enabled"""
        feature_map = {
            'subscriptions': self.enable_subscriptions,
            'one_time_purchase': self.enable_one_time_purchase,
            'free_courses': self.enable_free_courses,
            'certificates': self.enable_course_certificates,
            'reviews': self.enable_course_reviews,
            'forums': self.enable_discussion_forums,
            'waitlist': self.enable_waitlist,
            'earnings': self.enable_instructor_earnings,
        }
        return feature_map.get(feature_name, False)
