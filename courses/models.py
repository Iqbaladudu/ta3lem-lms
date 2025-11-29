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
    url = EmbedVideoField(blank=True, null=True)
    file = models.FileField(upload_to='videos', blank=True, null=True)


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

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.title


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


# Polymorphic content model
class Content(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='contents')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, limit_choices_to={
        'model__in': ('text', 'video', 'image', 'file')
    })
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey('content_type', 'object_id')
    order = OrderField(blank=True, for_fields=['module'])

    class Meta:
        ordering = ['order']

class CourseEnrollment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('enrolled', 'Enrolled'),
        ('completed', 'Completed'),
        ('paused', 'Paused')]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_enrollments')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='enrolled')
    enrolled_on = models.DateTimeField(auto_now_add=True)
    completed_on = models.DateTimeField(null=True, blank=True)
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    last_accessed = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'course'], name='unique_enrollment')
        ]
        ordering = ['-enrolled_on']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['course', 'status']),
            models.Index(fields=['-last_accessed']),
        ]

    def __str__(self):
        return f"{self.student.username} - {self.course.title} ({self.status})"

    def calculate_progress(self):
        total_contents = Content.objects.filter(module__course=self.course).count()

        if total_contents == 0:
            return 0.00

        completed_contents = ContentProgress.objects.filter(enrollment=self, is_completed=True).count()

        return round((completed_contents / total_contents) * 100, 2)

    def update_progress(self):
        self.progress_percentage = self.calculate_progress()

        if self.progress_percentage == 100 and self.status == 'active':
            self.status = 'completed'
            self.completed_on = timezone.now()

        self.save(update_fields=['progress_percentage', 'status', 'completed_on'])

    def get_current_module(self):
        incomplete_modules = ModuleProgress.objects.filter(enrollment=self, is_completed=False).order_by('module__order').first()

        if incomplete_modules:
            return  incomplete_modules.module

        # If all complete, return last module
        return self.course.modules.order_by('order').first()

class ContentProgress(models.Model):
    enrollment = models.ForeignKey(CourseEnrollment, on_delete=models.CASCADE, related_name='content_progress')
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='progress_records')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)

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
        return f"{self.enrollment.student.username} - {self.content.item.title} ({'Completed' if self.is_completed else 'In Progress'})"

    def mark_completed(self):
        if not self.is_completed:
            self.is_completed = True
            self.completed_at = timezone.now()
            self.save()

            # get or create module progress
            module_progress, created = ModuleProgress.objects.get_or_create(enrollment=self.enrollment, module=self.content.module)

            # Check if module is now completed
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

        completed_contents = ContentProgress.objects.filter(enrollment=self.enrollment, content__module=self.module, is_completed=True).count()

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
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='learning_sessions', null=True, blank=True)

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