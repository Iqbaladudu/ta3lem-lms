from django.contrib.auth.models import AbstractUser, Group
from django.db import models


class User(AbstractUser):
    """ BASE USER MODEL"""

    STUDENT = 'student'
    INSTRUCTOR = 'instructor'
    STAFF = 'staff'

    ROLE_CHOICES = [
        (STUDENT, 'Student'),
        (INSTRUCTOR, 'Instructor'),
        (STAFF, 'Staff'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=STUDENT,
        help_text='User role in the LMS'
    )

    is_active = models.BooleanField(default=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)

    # Address
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    # Preferences
    timezone = models.CharField(max_length=50, default='UTC')
    language = models.CharField(max_length=10, default='en')
    email_notifications = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = [
            ('view_dashboard', 'Can view dashboard'),
        ]

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


    def is_student(self):
        return self.role == self.STUDENT

    def is_instructor(self):
        return self.role == self.INSTRUCTOR

    def has_active_subscription(self):
        """Check if user has an active subscription"""
        try:
            from subscriptions.services import SubscriptionService
            return SubscriptionService.user_has_active_subscription(self)
        except ImportError:
            return False

    def is_staff_member(self):
        return self.is_staff

    def save(self, *args, **kwargs):
        # Only set is_staff based on role if not a superuser
        if not self.is_superuser:
            self.is_staff = (self.role == self.STAFF)
        return super().save(*args, **kwargs)

    def get_profile(self):
        """Get role-specific profile"""
        if self.role == self.STUDENT:
            return getattr(self, 'student_profile', None)
        elif self.role == self.INSTRUCTOR:
            return getattr(self, 'instructor_profile', None)
        return None


class StudentProfile(models.Model):
    """Student-specific data"""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_profile',
        limit_choices_to={'role': 'student'}
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Student Profile'
        verbose_name_plural = 'Student Profiles'

    def __str__(self):
        return f"{self.user.username} - {self.user.get_full_name()}"


class InstructorProfile(models.Model):
    """Instructor-specific data"""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='instructor_profile',
        limit_choices_to={'role': 'instructor'}
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Instructor Profile'
        verbose_name_plural = 'Instructor Profiles'

    def __str__(self):
        return f"{self.user.username} - {self.user.get_full_name()}"
