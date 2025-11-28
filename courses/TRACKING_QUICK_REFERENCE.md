# Quick Reference Guide - Course Tracking System

## URL Routes Summary

### Student Routes
| Route | View | Method | Purpose |
|-------|------|--------|---------|
| `/courses/student/dashboard/` | StudentDashboardView | GET | Student dashboard |
| `/courses/student/courses/` | StudentCourseListView | GET | List enrolled courses |
| `/courses/student/<pk>/enroll/` | StudentEnrollCourseView | POST | Enroll to course |
| `/courses/student/<pk>/` | StudentCourseDetailView | GET | Course detail & progress |
| `/courses/student/<pk>/module/<module_pk>/` | StudentModuleDetailView | GET | Module detail |
| `/courses/student/<pk>/module/<module_pk>/content/<content_pk>/` | StudentContentView | GET | Content view |
| `/courses/student/<pk>/module/<module_pk>/content/<content_pk>/complete/` | MarkContentCompleteView | POST | Mark content complete |

### Instructor Routes
| Route | View | Method | Purpose |
|-------|------|--------|---------|
| `/courses/analytics/<pk>/` | InstructorCourseAnalyticsView | GET | Course analytics |
| `/courses/analytics/<pk>/student/<student_id>/` | StudentProgressDetailView | GET | Student progress detail |

## Context Variables by View

### StudentCourseListView
```python
context = {
    'enrollments': QuerySet[CourseEnrollment],
    'total_courses': int,
    'active_courses': int,
    'completed_courses': int,
    'avg_progress': Decimal,
    'status_filter': str
}
```

### StudentCourseDetailView
```python
context = {
    'course': Course,
    'enrollment': CourseEnrollment,
    'modules_data': [
        {
            'module': Module,
            'progress': ModuleProgress,
            'total_contents': int,
            'completed_contents': int,
            'completion_percentage': float
        }
    ],
    'current_module': Module
}
```

### StudentModuleDetailView
```python
context = {
    'module': Module,
    'enrollment': CourseEnrollment,
    'module_progress': ModuleProgress,
    'contents_data': [
        {
            'content': Content,
            'progress': ContentProgress,
            'is_completed': bool
        }
    ],
    'course': Course,
    'previous_module': Module,
    'next_module': Module
}
```

### StudentContentView
```python
context = {
    'content': Content,
    'enrollment': CourseEnrollment,
    'content_progress': ContentProgress,
    'learning_session': LearningSession,
    'module': Module,
    'course': Course,
    'previous_content': Content,
    'next_content': Content
}
```

### StudentDashboardView
```python
context = {
    'enrollments': QuerySet[CourseEnrollment],
    'total_courses': int,
    'active_courses': int,
    'completed_courses': int,
    'avg_progress': float,
    'recent_sessions': QuerySet[LearningSession],
    'in_progress': QuerySet[CourseEnrollment],
    'total_learning_time': float,  # hours
    'total_modules_completed': int,
    'total_contents_completed': int
}
```

### InstructorCourseAnalyticsView
```python
context = {
    'course': Course,
    'enrollments': QuerySet[CourseEnrollment],
    'total_students': int,
    'active_students': int,
    'completed_students': int,
    'avg_progress': float,
    'modules_data': [
        {
            'module': Module,
            'total_contents': int,
            'completed_count': int,
            'completion_rate': float
        }
    ],
    'recent_enrollments': QuerySet[CourseEnrollment],
    'total_sessions': int
}
```

### StudentProgressDetailView
```python
context = {
    'course': Course,
    'enrollment': CourseEnrollment,
    'student': User,
    'modules_progress': [
        {
            'module': Module,
            'progress': ModuleProgress,
            'contents_progress': [
                {
                    'content': Content,
                    'progress': ContentProgress
                }
            ]
        }
    ],
    'learning_sessions': QuerySet[LearningSession]
}
```

## Common Template Patterns

### Display Progress Bar
```html
<!-- Student progress bar -->
<div class="progress">
    <div class="progress-bar" 
         style="width: {{ enrollment.progress_percentage }}%">
        {{ enrollment.progress_percentage }}%
    </div>
</div>
```

### List Modules with Progress
```html
{% for module_data in modules_data %}
<div class="module-item">
    <h3>{{ module_data.module.title }}</h3>
    <p>{{ module_data.completed_contents }} / {{ module_data.total_contents }} completed</p>
    <div class="progress">
        <div class="progress-bar" 
             style="width: {{ module_data.completion_percentage }}%">
        </div>
    </div>
    {% if module_data.progress.is_completed %}
        <span class="badge bg-success">Completed</span>
    {% endif %}
</div>
{% endfor %}
```

### List Contents with Status
```html
{% for content_data in contents_data %}
<div class="content-item">
    <a href="{% url 'student_content_view' pk=course.pk module_pk=module.pk content_pk=content_data.content.pk %}">
        {{ content_data.content.item.title }}
    </a>
    {% if content_data.is_completed %}
        <span class="badge bg-success">✓</span>
    {% else %}
        <span class="badge bg-secondary">○</span>
    {% endif %}
</div>
{% endfor %}
```

### Mark Complete Button
```html
<form method="post" 
      action="{% url 'mark_content_complete' pk=course.pk module_pk=module.pk content_pk=content.pk %}">
    {% csrf_token %}
    <button type="submit" class="btn btn-primary">
        Mark as Complete
    </button>
</form>
```

### Mark Complete with HTMX
```html
<button 
    hx-post="{% url 'mark_content_complete' pk=course.pk module_pk=module.pk content_pk=content.pk %}"
    hx-trigger="click"
    hx-swap="outerHTML"
    class="btn btn-primary">
    Mark as Complete
</button>
```

### Navigation Buttons
```html
<!-- Previous/Next Content -->
{% if previous_content %}
<a href="{% url 'student_content_view' pk=course.pk module_pk=module.pk content_pk=previous_content.pk %}" 
   class="btn btn-secondary">
    ← Previous
</a>
{% endif %}

{% if next_content %}
<a href="{% url 'student_content_view' pk=course.pk module_pk=module.pk content_pk=next_content.pk %}" 
   class="btn btn-primary">
    Next →
</a>
{% endif %}

<!-- Previous/Next Module -->
{% if previous_module %}
<a href="{% url 'student_module_detail' pk=course.pk module_pk=previous_module.pk %}" 
   class="btn btn-secondary">
    ← {{ previous_module.title }}
</a>
{% endif %}

{% if next_module %}
<a href="{% url 'student_module_detail' pk=course.pk module_pk=next_module.pk %}" 
   class="btn btn-primary">
    {{ next_module.title }} →
</a>
{% endif %}
```

### Enrollment Status Badge
```html
{% if enrollment.status == 'enrolled' %}
    <span class="badge bg-primary">Active</span>
{% elif enrollment.status == 'completed' %}
    <span class="badge bg-success">Completed</span>
{% elif enrollment.status == 'paused' %}
    <span class="badge bg-warning">Paused</span>
{% elif enrollment.status == 'pending' %}
    <span class="badge bg-secondary">Pending</span>
{% endif %}
```

## JavaScript/HTMX Examples

### Mark Complete with Progress Update
```javascript
// Using fetch API
document.getElementById('complete-btn').addEventListener('click', async function() {
    const response = await fetch(this.dataset.url, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken')
        }
    });
    
    const data = await response.json();
    
    if (data.success) {
        // Update progress bar
        document.querySelector('.progress-bar').style.width = data.progress_percentage + '%';
        document.querySelector('.progress-bar').textContent = data.progress_percentage + '%';
        
        // Show completion message
        if (data.course_completed) {
            alert('Congratulations! You completed the course!');
        } else if (data.module_completed) {
            alert('Module completed!');
        }
        
        // Redirect to next content
        window.location.href = this.dataset.nextUrl;
    }
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
```

### HTMX with Progress Update
```html
<button 
    hx-post="{% url 'mark_content_complete' pk=course.pk module_pk=module.pk content_pk=content.pk %}"
    hx-trigger="click"
    hx-target="#progress-container"
    hx-swap="outerHTML"
    class="btn btn-primary">
    Mark as Complete
</button>

<script>
document.body.addEventListener('htmx:afterRequest', function(evt) {
    if (evt.detail.successful) {
        const response = JSON.parse(evt.detail.xhr.responseText);
        if (response.course_completed) {
            alert('Congratulations! You completed the course!');
        }
    }
});
</script>
```

## Model Methods Quick Reference

### CourseEnrollment
```python
enrollment = CourseEnrollment.objects.get(student=user, course=course)

# Calculate and update progress
enrollment.update_progress()

# Get current module
current_module = enrollment.get_current_module()

# Manual progress calculation
progress = enrollment.calculate_progress()
```

### ContentProgress
```python
content_progress = ContentProgress.objects.get(enrollment=enrollment, content=content)

# Mark as completed
content_progress.mark_completed()
# This automatically:
# - Sets is_completed = True
# - Sets completed_at timestamp
# - Updates module progress
# - Updates course progress
```

### ModuleProgress
```python
module_progress = ModuleProgress.objects.get(enrollment=enrollment, module=module)

# Check if all contents are completed
is_complete = module_progress.calculate_completion()

# Mark as completed
module_progress.mark_completed()
# This automatically:
# - Sets is_completed = True
# - Sets completed_at timestamp
# - Updates course progress
```

### LearningSession
```python
session = LearningSession.objects.create(
    enrollment=enrollment,
    content=content
)

# End session
session.end_session()
# This sets ended_at and calculates duration
```

## Query Examples

### Get student enrollments with status
```python
# Active courses
active = CourseEnrollment.objects.filter(
    student=request.user,
    status='enrolled'
)

# Completed courses
completed = CourseEnrollment.objects.filter(
    student=request.user,
    status='completed'
)

# With course data
enrollments = CourseEnrollment.objects.filter(
    student=request.user
).select_related('course', 'course__subject')
```

### Get progress statistics
```python
# Total completed contents
total_completed = ContentProgress.objects.filter(
    enrollment__student=request.user,
    is_completed=True
).count()

# Completed contents for a course
course_completed = ContentProgress.objects.filter(
    enrollment__student=request.user,
    enrollment__course=course,
    is_completed=True
).count()

# Average progress across all courses
from django.db.models import Avg
avg_progress = CourseEnrollment.objects.filter(
    student=request.user
).aggregate(avg=Avg('progress_percentage'))['avg']
```

### Get learning time
```python
# Total learning time for all courses
sessions = LearningSession.objects.filter(
    enrollment__student=request.user,
    ended_at__isnull=False
)
total_hours = sum([
    (s.ended_at - s.started_at).total_seconds() 
    for s in sessions
]) / 3600

# Learning time for specific course
course_sessions = LearningSession.objects.filter(
    enrollment__student=request.user,
    enrollment__course=course,
    ended_at__isnull=False
)
```

### Instructor queries
```python
# All students in a course
students = CourseEnrollment.objects.filter(
    course=course
).select_related('student')

# Course completion rate
total_students = CourseEnrollment.objects.filter(course=course).count()
completed_students = CourseEnrollment.objects.filter(
    course=course, 
    status='completed'
).count()
completion_rate = (completed_students / total_students * 100) if total_students > 0 else 0

# Module completion rates
module_completions = ModuleProgress.objects.filter(
    module=module,
    is_completed=True
).count()
module_students = CourseEnrollment.objects.filter(
    course=module.course
).count()
module_rate = (module_completions / module_students * 100) if module_students > 0 else 0
```

## Status Choices

### CourseEnrollment.STATUS_CHOICES
- `'pending'`: Pending approval
- `'enrolled'`: Currently enrolled and active
- `'completed'`: Course completed
- `'paused'`: Temporarily paused

## Tips & Best Practices

1. **Always use get_or_create()** for enrollment and progress objects
2. **Call update_progress()** after marking content complete
3. **Use select_related()** for foreign keys to reduce queries
4. **Use prefetch_related()** for reverse foreign keys and M2M
5. **End learning sessions** when user navigates away
6. **Check permissions** before showing instructor analytics
7. **Cache expensive queries** for dashboard statistics
8. **Use pagination** for large lists
9. **Validate enrollment** before showing course content
10. **Handle edge cases** (empty modules, no contents, etc.)

