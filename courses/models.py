from datetime import timedelta

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.template.loader import render_to_string
from django.utils import timezone
from embed_video.fields import EmbedVideoField

from users.models import User
from .fields import OrderField


class ItemBase(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_related')
    title = models.CharField(max_length=250)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.title

    @property
    def class_name(self):
        return self._meta.model_name

    @property
    def content_type(self):
        """Return the content type based on the model name"""
        return self._meta.model_name

    def render(self):
        return render_to_string(
            f'courses/content/{self._meta.model_name}.html',
            {'item': self}
        )


class Text(ItemBase):
    content = models.TextField()


class File(ItemBase):
    file = models.FileField(upload_to='files')


class Image(ItemBase):
    file = models.FileField(upload_to='images')


class Video(ItemBase):
    """Enhanced video model with multiple platform support and metadata"""
    url = EmbedVideoField(blank=True, null=True,
                          help_text='Video URL from YouTube, Vimeo, Dailymotion, or other platforms')
    file = models.FileField(upload_to='videos', blank=True, null=True, help_text='Upload video file directly')

    # Enhanced video metadata
    duration = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text='Video duration in seconds'
    )
    video_platform = models.CharField(
        max_length=20,
        choices=[
            ('youtube', 'YouTube'),
            ('vimeo', 'Vimeo'),
            ('dailymotion', 'Dailymotion'),
            ('uploaded', 'Uploaded File'),
            ('other', 'Other Platform')
        ],
        blank=True,
        help_text='Auto-detected from URL or set manually'
    )

    # Video quality and accessibility
    transcript = models.TextField(
        blank=True,
        help_text='Video transcript for accessibility'
    )
    captions_enabled = models.BooleanField(
        default=True,
        help_text='Whether captions/subtitles are available'
    )
    auto_play = models.BooleanField(
        default=False,
        help_text='Auto-play video when content is viewed'
    )

    # Learning analytics
    minimum_watch_percentage = models.PositiveIntegerField(
        default=80,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text='Minimum percentage to watch for completion (default: 80%)'
    )

    class Meta:
        indexes = [
            models.Index(fields=['video_platform']),
            models.Index(fields=['owner', 'created']),
        ]

    def save(self, *args, **kwargs):
        # Auto-detect video platform from URL
        if self.url and not self.video_platform:
            from .templatetags.course import extract_video_id
            platform, video_id = extract_video_id(str(self.url))
            if platform:
                self.video_platform = platform
        elif self.file and not self.video_platform:
            self.video_platform = 'uploaded'

        super().save(*args, **kwargs)

    def get_thumbnail_url(self):
        """Get video thumbnail URL"""
        if self.url and self.video_platform:
            from .templatetags.course import video_thumbnail
            return video_thumbnail(str(self.url))
        return None

    def get_embed_code(self, **kwargs):
        """Get video embed HTML"""
        if self.url:
            from .templatetags.course import video_player
            return video_player(
                str(self.url),
                autoplay=self.auto_play,
                **kwargs
            )
        return None

    def clean(self):
        from django.core.exceptions import ValidationError

        if not self.url and not self.file:
            raise ValidationError('Either URL or file must be provided.')

        if self.url and self.file:
            raise ValidationError('Provide either URL or file, not both.')

        super().clean()


class Subject(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class Course(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_created')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='courses')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    overview = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    students = models.ManyToManyField(User, related_name='courses_joined', blank=True)

    # Pricing information
    is_free = models.BooleanField(
        default=True,
        help_text='Whether this course is free or paid'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Course price (set only if not free)'
    )
    currency = models.CharField(
        max_length=3,
        default='IDR',
        choices=[
            ('IDR', 'Indonesian Rupiah'),
            ('USD', 'US Dollar'),
            ('EUR', 'Euro'),
        ],
        help_text='Currency for pricing'
    )

    # Enhanced fields from clarifications
    enrollment_type = models.CharField(
        max_length=20,
        choices=[
            ('open', 'Open Enrollment'),
            ('approval', 'Requires Approval'),
            ('restricted', 'Restricted Access')
        ],
        default='open'
    )
    max_capacity = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text='Optional enrollment limit'
    )
    waitlist_enabled = models.BooleanField(
        default=True,
        help_text='Enable waitlist when capacity reached'
    )

    # Course metadata
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced')
        ],
        blank=True
    )
    estimated_hours = models.PositiveIntegerField(blank=True, null=True)
    certificate_enabled = models.BooleanField(default=False)

    # Course status
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('published', 'Published'),
            ('archived', 'Archived')
        ],
        default='draft'
    )
    published_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['enrollment_type']),
            models.Index(fields=['subject', 'status']),
            models.Index(fields=['is_free', 'price']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(max_capacity__isnull=True) | models.Q(max_capacity__gt=0),
                name='positive_capacity'
            ),
            models.CheckConstraint(
                condition=(
                        models.Q(is_free=True, price__isnull=True) |
                        models.Q(is_free=False, price__isnull=False, price__gt=0)
                ),
                name='valid_pricing'
            ),
        ]

    def __str__(self):
        return self.title

    def get_enrollment_count(self):
        """Get current enrollment count including active enrollments"""
        return self.course_enrollments.filter(
            status__in=['enrolled', 'completed']
        ).count()

    def get_pending_approvals_count(self):
        """Get number of pending approval requests"""
        return self.course_enrollments.filter(status='pending').count()

    def get_available_spots(self):
        """Get number of available enrollment spots"""
        if not self.max_capacity:
            return None  # Unlimited
        return max(0, self.max_capacity - self.get_enrollment_count())

    def is_full(self):
        """Check if course has reached capacity"""
        if not self.max_capacity:
            return False
        return self.get_enrollment_count() >= self.max_capacity

    def get_formatted_price(self):
        """Get formatted price string"""
        if self.is_free:
            return "Gratis"

        if self.currency == 'IDR':
            return f"Rp {self.price:,.0f}".replace(',', '.')
        elif self.currency == 'USD':
            return f"${self.price:,.2f}"
        elif self.currency == 'EUR':
            return f"€{self.price:,.2f}"
        return f"{self.price} {self.currency}"

    def get_enrollment_button_text(self):
        """Get appropriate button text based on enrollment type and pricing"""
        if self.enrollment_type == 'approval':
            return "Request Pendaftaran"
        elif self.is_free:
            return "Daftar Kursus Gratis"
        else:
            return f"Beli Kursus - {self.get_formatted_price()}"

    def can_enroll(self, user):
        """Check if user can enroll in course"""
        # Check if user is already enrolled
        if self.course_enrollments.filter(
                student=user,
                status__in=['enrolled', 'completed', 'pending']
        ).exists():
            enrollment = self.course_enrollments.filter(student=user).first()
            if enrollment.status == 'pending':
                return False, "Approval request pending"
            elif enrollment.status in ['enrolled', 'completed']:
                return False, "Already enrolled"

        # Check capacity
        if self.is_full():
            if self.waitlist_enabled:
                return False, "Course full - can join waitlist"
            else:
                return False, "Course full - no waitlist"

        # Check enrollment type
        # For restricted courses: allow if it's a paid course (payment acts as access control)
        if self.enrollment_type == 'restricted':
            if not self.is_free:
                # Paid restricted courses can be purchased (approval after payment)
                return True, "Can purchase restricted course"
            else:
                # Free restricted courses require instructor invite
                return False, "Restricted course - contact instructor"

        return True, "Can enroll"

    def save(self, *args, **kwargs):
        # Auto-set published_at when status changes to published
        if self.status == 'published' and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()
        super().save(*args, **kwargs)


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = OrderField(blank=True, for_fields=['course'])

    def __str__(self):
        return f'{self.order}. {self.title}'

    class Meta:
        ordering = ['order']

    def get_previous_in_order(self):
        """Get the previous module in the course by order"""
        return self.course.modules.filter(order__lt=self.order).order_by('-order').first()

    def get_next_in_order(self):
        """Get the next module in the course by order"""
        return self.course.modules.filter(order__gt=self.order).order_by('order').first()

    def get_first_content(self):
        """Get the first content in this module"""
        return self.contents.order_by('order').first()


# Content model - can have multiple content items of different types
class Content(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='contents')
    title = models.CharField(max_length=250, blank=True)
    order = OrderField(blank=True, for_fields=['module'])

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class ContentItem(models.Model):
    """Each Content can have multiple ContentItems of different types"""
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='items')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, limit_choices_to={
        'model__in': ('text', 'video', 'image', 'file')
    })
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey('content_type', 'object_id')
    order = OrderField(blank=True, for_fields=['content'])

    class Meta:
        ordering = ['order']


class CourseWaitlist(models.Model):
    """Waitlist for courses that have reached capacity"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='waitlist_entries')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='waitlist_entries')
    joined_waitlist = models.DateTimeField(auto_now_add=True)
    notified_of_opening = models.BooleanField(default=False)
    priority = models.PositiveIntegerField(default=1)  # Lower numbers = higher priority

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['course', 'student'], name='unique_course_waitlist')
        ]
        ordering = ['priority', 'joined_waitlist']
        indexes = [
            models.Index(fields=['course', 'priority', 'joined_waitlist']),
        ]

    def __str__(self):
        return f"{self.student.username} waitlisted for {self.course.title}"

    def get_position(self):
        """Get position in waitlist (1-indexed)"""
        return self.course.waitlist_entries.filter(
            models.Q(priority__lt=self.priority) |
            (models.Q(priority=self.priority) & models.Q(joined_waitlist__lt=self.joined_waitlist))
        ).count() + 1


class CourseEnrollment(models.Model):
    """Enhanced enrollment model with approval workflow and payment tracking"""

    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('enrolled', 'Enrolled'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('withdrawn', 'Withdrawn'),
        ('rejected', 'Rejected')  # New status for approval workflow
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Payment Pending'),
        ('paid', 'Paid'),
        ('failed', 'Payment Failed'),
        ('refunded', 'Refunded'),
        ('free', 'Free Course'),
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_enrollments')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='enrolled')
    enrolled_on = models.DateTimeField(auto_now_add=True)
    completed_on = models.DateTimeField(null=True, blank=True)
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    last_accessed = models.DateTimeField(null=True, blank=True)

    # Payment tracking
    payment_status = models.CharField(
        max_length=15,
        choices=PAYMENT_STATUS_CHOICES,
        default='free'
    )
    payment_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    payment_date = models.DateTimeField(null=True, blank=True)
    payment_reference = models.CharField(
        max_length=100,
        blank=True,
        help_text='Payment gateway reference or transaction ID'
    )

    # Enhanced fields for approval workflow
    approval_requested_at = models.DateTimeField(blank=True, null=True)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_enrollments'
    )
    approved_at = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True)

    # Learning analytics
    total_time_spent = models.DurationField(default=timedelta)
    last_activity = models.DateTimeField(auto_now=True)
    engagement_score = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.0,
        help_text='Engagement score from 0.0 to 1.0'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'course'], name='unique_enrollment'),
            models.CheckConstraint(
                condition=models.Q(progress_percentage__gte=0) & models.Q(progress_percentage__lte=100),
                name='valid_progress_percentage'
            ),
            models.CheckConstraint(
                condition=models.Q(engagement_score__gte=0.0) & models.Q(engagement_score__lte=1.0),
                name='valid_engagement_score'
            ),
            models.CheckConstraint(
                condition=(
                        models.Q(payment_status='free', payment_amount__isnull=True) |
                        models.Q(payment_status__in=['pending', 'paid', 'failed', 'refunded'],
                                 payment_amount__isnull=False)
                ),
                name='valid_payment_data'
            ),
        ]
        ordering = ['-enrolled_on']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['course', 'status']),
            models.Index(fields=['-last_accessed']),
            models.Index(fields=['status', 'approval_requested_at']),
            models.Index(fields=['payment_status', 'payment_date']),
        ]

    def __str__(self):
        return f'{self.student.username} enrolled in {self.course.title} ({self.status})'

    def save(self, *args, **kwargs):
        # Auto-set completion date when status changes to completed
        if self.status == 'completed' and not self.completed_on:
            self.completed_on = timezone.now()

        # Set default payment status based on course pricing
        if not self.pk:
            if self.course.is_free:
                self.payment_status = 'free'
            else:
                self.payment_status = 'pending'
                self.payment_amount = self.course.price

        # Set default enrollment status based on course enrollment type
        if not self.pk and self.course.enrollment_type == 'approval':
            self.status = 'pending'
            self.approval_requested_at = timezone.now()

        super().save(*args, **kwargs)

    # Add helper methods used by views/tests for progress tracking
    def get_current_module(self):
        """Return the next module the student should work on.

        Strategy:
        - Iterate course modules in order.
        - If ModuleProgress exists and is not completed -> return that module.
        - If no ModuleProgress exists for a module -> return that module (first not started).
        - If all modules completed -> return None.
        """
        for module in self.course.modules.order_by('order'):
            mp = ModuleProgress.objects.filter(enrollment=self, module=module).first()
            if not mp or not mp.is_completed:
                return module
        return None

    def calculate_progress(self):
        """Compute progress percentage across all contents for this enrollment.

        Returns a float (0.0 - 100.0). Does not persist the value.
        """
        total_contents = Content.objects.filter(module__course=self.course).count()
        if total_contents == 0:
            return 0.0
        completed = ContentProgress.objects.filter(enrollment=self, is_completed=True).count()
        return round((completed / total_contents) * 100, 2)

    def update_progress(self):
        """Recalculate and persist progress_percentage and update enrollment status if complete."""
        pct = self.calculate_progress()
        # Update progress percentage
        self.progress_percentage = pct
        # If fully completed, set status and completed_on
        # Use epsilon for float comparison to handle potential rounding issues
        if pct >= 99.99 and self.status != 'completed':
            self.status = 'completed'
            self.completed_on = timezone.now()
            self.save(update_fields=['status', 'completed_on', 'progress_percentage'])
        else:
            # Persist only progress percentage
            self.save(update_fields=['progress_percentage'])

    def can_access_course(self):
        """
        Returns True if the course can be accessed/opened by the user according to:
        - status is 'enrolled', 'completed', or 'paused'
        - payment_status is 'paid' or 'free'
        """
        return (
                self.status in ['enrolled', 'completed', 'paused'] and
                self.payment_status in ['paid', 'free']
        )


class ContentProgress(models.Model):
    enrollment = models.ForeignKey(CourseEnrollment, on_delete=models.CASCADE, related_name='content_progress')
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='progress_records')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)
    time_spent = models.DurationField(default=timedelta)
    last_viewed = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['enrollment', 'content'], name='unique_content_progress')
        ]
        ordering = ['content__order']
        indexes = [
            models.Index(fields=['enrollment', 'is_completed']),
            models.Index(fields=['content', 'is_completed']),
        ]
        verbose_name_plural = 'Content Progresses'

    def __str__(self):
        # Use content.title as a safe fallback; some codebases previously stored an `item` relation
        content_title = getattr(self.content, 'title', None) or getattr(getattr(self.content, 'item', None), 'title',
                                                                        'Content')
        return f"{self.enrollment.student.username} - {content_title} ({'Completed' if self.is_completed else 'In Progress'})"

    def mark_completed(self):
        if not self.is_completed:
            self.is_completed = True
            self.completed_at = timezone.now()
            self.save()

            # get or create module progress
            module_progress, created = ModuleProgress.objects.get_or_create(enrollment=self.enrollment,
                                                                            module=self.content.module)

            # Check if module is now completed
            if module_progress.calculate_completion():
                module_progress.mark_completed()


class ModuleProgress(models.Model):
    enrollment = models.ForeignKey(CourseEnrollment, on_delete=models.CASCADE, related_name='module_progress')
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='progress_records')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['enrollment', 'module'], name='unique_module_progress')
        ]
        ordering = ['module__order']
        indexes = [
            models.Index(fields=['enrollment', 'is_completed']),
            models.Index(fields=['module', 'is_completed']),
        ]
        verbose_name_plural = 'Module Progresses'

    def __str__(self):
        return f"{self.enrollment.student.username} - {self.module.title} ({'Completed' if self.is_completed else 'In Progress'})"

    def calculate_completion(self):
        total_contents = self.module.contents.count()

        if total_contents == 0:
            return False

        completed_contents = ContentProgress.objects.filter(enrollment=self.enrollment, content__module=self.module,
                                                            is_completed=True).count()

        return total_contents == completed_contents

    def mark_completed(self):
        if not self.is_completed:
            self.is_completed = True
            self.completed_at = timezone.now()
            self.save()

            # Update overall courseprogress
            self.enrollment.update_progress()


class LearningSession(models.Model):
    """ Track individual learning sessions for students """
    enrollment = models.ForeignKey(CourseEnrollment, on_delete=models.CASCADE, related_name='learning_sessions')
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='learning_sessions', null=True,
                                blank=True)

    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['enrollment', 'started_at']),
            models.Index(fields=['content', '-started_at']),
        ]

    def __str__(self):
        return f"Session for {self.enrollment.student.username} on {self.enrollment.course.title} started at {self.started_at}"

    def end_session(self):
        """ End session and calculate duration """
        if not self.ended_at:
            self.ended_at = timezone.now()
            self.duration = self.ended_at - self.started_at
            self.save()
