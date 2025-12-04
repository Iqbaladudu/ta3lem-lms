# Data Model: Enhanced LMS Schema Design

**Feature**: Complete Learning Management System  
**Date**: 2025-12-03  
**Status**: Phase 1 Design  
**Prerequisites**: research.md complete

## Current Data Model Analysis

### Core Entity Relationships

```text
User (Custom AbstractUser)
├── StudentProfile (1:1, optional)
├── InstructorProfile (1:1, optional)
├── courses_created (1:Many → Course)
├── courses_joined (Many:Many → Course via CourseEnrollment)
└── owned_content (1:Many → ItemBase subclasses)

Subject
└── courses (1:Many → Course)

Course
├── owner (Many:1 → User)
├── subject (Many:1 → Subject)
├── students (Many:Many → User via CourseEnrollment)
├── modules (1:Many → Module)
└── enrollments (1:Many → CourseEnrollment)

Module
├── course (Many:1 → Course)
├── contents (1:Many → Content)
└── progress_records (1:Many → ModuleProgress)

Content
├── module (Many:1 → Module)
├── items (1:Many → ContentItem)
└── progress_records (1:Many → ContentProgress)

ContentItem (Generic Foreign Key)
├── content (Many:1 → Content)
└── item → {Text, Image, Video, File}

CourseEnrollment
├── student (Many:1 → User)
├── course (Many:1 → Course)
├── content_progress (1:Many → ContentProgress)
├── module_progress (1:Many → ModuleProgress)
└── learning_sessions (1:Many → LearningSession)
```

## Enhanced Data Model (Phase 1)

### 1. User Management Enhancements

```python
# users/models.py - Enhanced User Model

class User(AbstractUser):
    """Enhanced User model with additional fields for LMS functionality"""
    
    # Existing fields maintained
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=STUDENT)
    is_active = models.BooleanField(default=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    
    # Enhanced fields for API and mobile access
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    account_locked_until = models.DateTimeField(blank=True, null=True)
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    weekly_digest = models.BooleanField(default=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['role', 'is_active']),
            models.Index(fields=['email_verified']),
        ]

# New model for API access tokens
class APIToken(models.Model):
    """API access tokens for mobile and external integrations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_tokens')
    token = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)  # e.g., "Mobile App", "External Integration"
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'is_active']),
        ]
```

### 2. Course Management Enhancements

```python
# courses/models.py - Enhanced Course Models

class Course(models.Model):
    """Enhanced Course model with new enrollment and capacity features"""
    
    # Existing fields maintained
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_created')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='courses')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    overview = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    students = models.ManyToManyField(User, related_name='courses_joined', blank=True)
    
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
    max_capacity = models.PositiveIntegerField(blank=True, null=True, help_text='Optional enrollment limit')
    waitlist_enabled = models.BooleanField(default=True, help_text='Enable waitlist when capacity reached')
    
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
        ]
    
    def get_enrollment_count(self):
        """Get current enrollment count including active enrollments"""
        return self.course_enrollments.filter(
            status__in=['enrolled', 'completed']
        ).count()
    
    def is_full(self):
        """Check if course has reached capacity"""
        if not self.max_capacity:
            return False
        return self.get_enrollment_count() >= self.max_capacity
    
    def can_enroll(self, user):
        """Check if user can enroll in course"""
        # Check if user is already enrolled
        if self.course_enrollments.filter(student=user, status__in=['enrolled', 'completed']).exists():
            return False, "Already enrolled"
            
        # Check capacity
        if self.is_full():
            if self.waitlist_enabled:
                return False, "Course full - can join waitlist"
            else:
                return False, "Course full - no waitlist"
        
        # Check enrollment type
        if self.enrollment_type == 'restricted':
            return False, "Restricted course"
        
        return True, "Can enroll"

# New model for waitlist functionality
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

# Enhanced CourseEnrollment model
class CourseEnrollment(models.Model):
    """Enhanced enrollment model with approval workflow"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('enrolled', 'Enrolled'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('withdrawn', 'Withdrawn'),
        ('rejected', 'Rejected')  # New status for approval workflow
    ]
    
    # Existing fields maintained
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_enrollments')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='enrolled')
    enrolled_on = models.DateTimeField(auto_now_add=True)
    completed_on = models.DateTimeField(null=True, blank=True)
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    last_accessed = models.DateTimeField(null=True, blank=True)
    
    # Enhanced fields for approval workflow
    approval_requested_at = models.DateTimeField(blank=True, null=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_enrollments')
    approved_at = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True)
    
    # Learning analytics
    total_time_spent = models.DurationField(default=timedelta)
    last_activity = models.DateTimeField(auto_now=True)
    engagement_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)  # 0.0 to 1.0
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'course'], name='unique_enrollment')
        ]
        ordering = ['-enrolled_on']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['course', 'status']),
            models.Index(fields=['-last_accessed']),
            models.Index(fields=['status', 'approval_requested_at']),
        ]
```

### 3. Enhanced Progress Tracking

```python
# Enhanced ContentProgress with learning time metrics
class ContentProgress(models.Model):
    """Enhanced content progress with detailed learning metrics"""
    
    enrollment = models.ForeignKey(CourseEnrollment, on_delete=models.CASCADE, related_name='content_progress')
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='progress_records')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    
    # Enhanced learning metrics (from clarifications)
    time_spent = models.DurationField(default=timedelta)
    view_count = models.PositiveIntegerField(default=0)
    last_viewed = models.DateTimeField(blank=True, null=True)
    completion_method = models.CharField(
        max_length=20,
        choices=[
            ('manual', 'Manual Mark Complete'),  # From clarification
            ('auto', 'Automatic'),
            ('time_based', 'Time Based'),
        ],
        default='manual'
    )
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['enrollment', 'content'], name='unique_content_progress')
        ]
        ordering = ['content__order']
        indexes = [
            models.Index(fields=['enrollment', 'is_completed']),
            models.Index(fields=['content', 'is_completed']),
            models.Index(fields=['last_viewed']),
        ]

# Enhanced LearningSession with detailed analytics
class LearningSession(models.Model):
    """Enhanced learning session tracking for analytics"""
    
    enrollment = models.ForeignKey(CourseEnrollment, on_delete=models.CASCADE, related_name='learning_sessions')
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='learning_sessions', null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    # Enhanced session analytics
    duration = models.DurationField(null=True, blank=True)
    device_type = models.CharField(
        max_length=20,
        choices=[
            ('desktop', 'Desktop'),
            ('tablet', 'Tablet'),
            ('mobile', 'Mobile'),
            ('unknown', 'Unknown')
        ],
        default='unknown'
    )
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    
    # Engagement metrics
    interactions_count = models.PositiveIntegerField(default=0)  # Clicks, scrolls, etc.
    focus_time = models.DurationField(default=timedelta)  # Time with page in focus
    idle_time = models.DurationField(default=timedelta)  # Time with page out of focus
    
    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['enrollment', 'started_at']),
            models.Index(fields=['content', '-started_at']),
            models.Index(fields=['device_type']),
        ]
```

## Database Schema Evolution

### Migration Strategy

1. **Phase 1A: Core Enhancements**
   ```python
   # Migration: Add enrollment type and capacity to Course
   # Migration: Create CourseWaitlist model
   # Migration: Add approval fields to CourseEnrollment
   ```

2. **Phase 1B: Analytics Enhancements**
   ```python
   # Migration: Add learning metrics to ContentProgress
   # Migration: Add engagement fields to LearningSession
   # Migration: Add analytics indexes
   ```

3. **Phase 1C: API Support**
   ```python
   # Migration: Create APIToken model
   # Migration: Add API-related user fields
   # Migration: Add performance indexes
   ```

### Database Indexes Strategy

```sql
-- Performance-critical indexes for 500+ concurrent users
CREATE INDEX CONCURRENTLY idx_course_enrollment_analytics 
    ON courses_courseenrollment (course_id, status, last_accessed);

CREATE INDEX CONCURRENTLY idx_content_progress_completion 
    ON courses_contentprogress (enrollment_id, is_completed, completed_at);

CREATE INDEX CONCURRENTLY idx_learning_sessions_analytics 
    ON courses_learningsession (enrollment_id, started_at, device_type);

CREATE INDEX CONCURRENTLY idx_course_capacity_lookup 
    ON courses_course (enrollment_type, status, max_capacity);
```

### Data Integrity Constraints

```python
# Additional model constraints for data integrity
class CourseEnrollment(models.Model):
    class Meta:
        constraints = [
            # Existing unique constraint
            models.UniqueConstraint(fields=['student', 'course'], name='unique_enrollment'),
            
            # New business logic constraints
            models.CheckConstraint(
                check=models.Q(progress_percentage__gte=0) & models.Q(progress_percentage__lte=100),
                name='valid_progress_percentage'
            ),
            models.CheckConstraint(
                check=models.Q(engagement_score__gte=0.0) & models.Q(engagement_score__lte=1.0),
                name='valid_engagement_score'
            ),
        ]

class Course(models.Model):
    class Meta:
        constraints = [
            # Ensure capacity is positive when set
            models.CheckConstraint(
                check=models.Q(max_capacity__isnull=True) | models.Q(max_capacity__gt=0),
                name='positive_capacity'
            ),
        ]
```

## API Data Transfer Objects (DTOs)

### REST API Serialization Strategy

```python
# api/serializers.py - Data transfer objects for API

class UserProfileSerializer(serializers.ModelSerializer):
    """User profile data for mobile apps"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'role', 'avatar', 'bio', 'date_of_birth']
        read_only_fields = ['id', 'username', 'role']

class CourseListSerializer(serializers.ModelSerializer):
    """Optimized course list for mobile/API"""
    enrollment_count = serializers.IntegerField(read_only=True)
    can_enroll = serializers.SerializerMethodField()
    instructor_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    
    class Meta:
        model = Course
        fields = ['id', 'title', 'slug', 'overview', 'difficulty_level', 
                 'estimated_hours', 'enrollment_count', 'can_enroll', 'instructor_name']
    
    def get_can_enroll(self, obj):
        user = self.context['request'].user
        can_enroll, message = obj.can_enroll(user)
        return {'allowed': can_enroll, 'message': message}

class StudentProgressSerializer(serializers.ModelSerializer):
    """Student progress data with learning analytics"""
    course_title = serializers.CharField(source='course.title', read_only=True)
    total_modules = serializers.IntegerField(read_only=True)
    completed_modules = serializers.IntegerField(read_only=True)
    learning_time_hours = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseEnrollment
        fields = ['id', 'course_title', 'status', 'progress_percentage', 
                 'total_modules', 'completed_modules', 'learning_time_hours', 
                 'last_accessed', 'engagement_score']
    
    def get_learning_time_hours(self, obj):
        total_seconds = obj.total_time_spent.total_seconds()
        return round(total_seconds / 3600, 2)
```

## Data Validation Rules

### Business Logic Validation

```python
# Enhanced model validation methods

class Course(models.Model):
    def clean(self):
        super().clean()
        
        # Validate enrollment type and capacity relationship
        if self.enrollment_type == 'open' and not self.max_capacity:
            # Open courses should have capacity to enable waitlist
            pass  # Optional capacity for open courses
        
        # Validate published courses have content
        if self.status == 'published' and not self.modules.exists():
            raise ValidationError("Published courses must have at least one module")
    
    def save(self, *args, **kwargs):
        # Auto-set published_at when status changes to published
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

class CourseEnrollment(models.Model):
    def clean(self):
        super().clean()
        
        # Validate enrollment business rules
        if self.status == 'completed' and not self.completed_on:
            self.completed_on = timezone.now()
        
        # Validate approval workflow
        if self.status == 'enrolled' and self.course.enrollment_type == 'approval':
            if not self.approved_by or not self.approved_at:
                raise ValidationError("Approved enrollments must have approver and approval date")
```

## Performance Optimization Strategy

### Query Optimization Points

1. **Course List Queries**
   ```python
   # Optimized course queryset with enrollment counts
   courses = Course.objects.select_related('subject', 'owner').prefetch_related('course_enrollments').annotate(
       enrollment_count=Count('course_enrollments', filter=Q(course_enrollments__status='enrolled'))
   )
   ```

2. **Student Dashboard Queries**
   ```python
   # Optimized student enrollment queries with progress
   enrollments = CourseEnrollment.objects.select_related('course', 'course__subject').prefetch_related(
       'content_progress', 'module_progress'
   ).filter(student=user, status__in=['enrolled', 'completed'])
   ```

3. **Analytics Queries**
   ```python
   # Optimized instructor analytics with aggregation
   analytics = CourseEnrollment.objects.filter(course__owner=instructor).aggregate(
       total_students=Count('id'),
       completed_courses=Count('id', filter=Q(status='completed')),
       avg_progress=Avg('progress_percentage'),
       total_learning_time=Sum('total_time_spent')
   )
   ```

**Status**: Data model design complete. Ready for Phase 1 contract generation and API design.