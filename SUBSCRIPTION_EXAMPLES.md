# Contoh Penggunaan Subscription Feature

## 1. Protect Course Access dengan Subscription

### Scenario: Hanya premium members yang bisa akses course detail

**File: `courses/views.py`**

```python
from django.views.generic import DetailView
from subscriptions.decorators import SubscriptionRequiredMixin
from .models import Course

class PremiumCourseDetailView(SubscriptionRequiredMixin, DetailView):
    """
    Course detail yang hanya bisa diakses oleh premium members.
    Non-premium users akan diarahkan ke halaman subscription plans.
    """
    model = Course
    template_name = 'courses/premium_course_detail.html'
    
    def get_queryset(self):
        # Only show published premium courses
        return Course.objects.filter(is_published=True, is_premium=True)
```

### Scenario: Premium content dalam course

**File: `courses/views.py`**

```python
from django.shortcuts import render, get_object_or_404
from subscriptions.decorators import subscription_required
from .models import Course

@subscription_required
def premium_course_content(request, course_id):
    """
    Function-based view untuk premium content.
    Akan redirect ke plans page jika tidak subscribe.
    """
    course = get_object_or_404(Course, id=course_id, is_premium=True)
    return render(request, 'courses/premium_content.html', {
        'course': course
    })
```

## 2. Conditional Content di Template

### Scenario: Show/hide features berdasarkan subscription

**File: `courses/templates/courses/detail.html`**

```html
{% extends 'base.html' %}

{% block content %}
<div class="course-detail">
    <h1>{{ course.title }}</h1>
    
    <!-- Basic content (available to all) -->
    <div class="course-overview">
        {{ course.description }}
    </div>
    
    <!-- Premium content (only for subscribers) -->
    {% if user_has_subscription %}
        <div class="premium-content">
            <h2>📚 Premium Materials</h2>
            <!-- Video lessons -->
            <div class="video-lessons">
                {% for lesson in course.lessons.all %}
                    <div class="lesson">
                        <video src="{{ lesson.video_url }}"></video>
                    </div>
                {% endfor %}
            </div>
            
            <!-- Downloadable resources -->
            <div class="resources">
                {% for resource in course.resources.all %}
                    <a href="{{ resource.file.url }}" download>
                        📥 Download {{ resource.name }}
                    </a>
                {% endfor %}
            </div>
        </div>
    {% else %}
        <!-- Upgrade prompt for non-subscribers -->
        <div class="upgrade-prompt">
            <div class="premium-lock">
                <i class="fas fa-lock"></i>
                <h3>Premium Content Locked</h3>
                <p>Upgrade to premium to access:</p>
                <ul>
                    <li>✨ All video lessons</li>
                    <li>📥 Downloadable resources</li>
                    <li>🎓 Certificates</li>
                    <li>💬 Priority support</li>
                </ul>
                <a href="{% url 'subscriptions:plans' %}" class="btn-upgrade">
                    Upgrade to Premium
                </a>
            </div>
        </div>
    {% endif %}
    
    <!-- Show subscription status -->
    {% if user_subscription %}
        <div class="subscription-status">
            <i class="fas fa-crown"></i>
            <span>Premium Member - {{ user_subscription.days_remaining }} days remaining</span>
        </div>
    {% endif %}
</div>
{% endblock %}
```

## 3. Programmatic Subscription Check

### Scenario: Check subscription in view logic

**File: `courses/views.py`**

```python
from django.shortcuts import render, redirect
from django.contrib import messages
from subscriptions.services import SubscriptionService
from .models import Course

def enroll_course(request, course_id):
    """
    Enroll user to course - check if course requires subscription.
    """
    course = Course.objects.get(id=course_id)
    user = request.user
    
    # Check if course requires subscription
    if course.requires_subscription:
        has_subscription = SubscriptionService.user_has_active_subscription(user)
        
        if not has_subscription:
            messages.warning(
                request,
                f'Course "{course.title}" requires an active subscription. '
                'Please upgrade to premium to access this course.'
            )
            return redirect('subscriptions:plans')
    
    # Enroll user
    course.students.add(user)
    messages.success(request, f'Successfully enrolled in {course.title}')
    return redirect('student_course_detail', pk=course.id)


def course_progress(request, course_id):
    """
    Track course progress - show different features for premium users.
    """
    course = Course.objects.get(id=course_id)
    user = request.user
    
    # Get subscription info
    subscription = SubscriptionService.get_user_subscription(user)
    stats = SubscriptionService.get_subscription_stats(user)
    
    context = {
        'course': course,
        'has_subscription': stats['has_subscription'],
        'subscription': subscription,
        'days_remaining': stats.get('days_remaining', 0),
    }
    
    # Premium features
    if stats['has_subscription']:
        context['can_download_certificate'] = True
        context['has_priority_support'] = subscription.plan.priority_support
        context['video_quality'] = 'HD'
    else:
        context['can_download_certificate'] = False
        context['has_priority_support'] = False
        context['video_quality'] = 'SD'
    
    return render(request, 'courses/progress.html', context)
```

## 4. Custom Subscription Check

### Scenario: Check specific plan features

**File: `courses/utils.py`**

```python
from subscriptions.services import SubscriptionService

def user_can_access_feature(user, feature_name):
    """
    Check if user's subscription plan includes a specific feature.
    
    Args:
        user: User object
        feature_name: String, e.g., "Priority Support", "HD Videos"
    
    Returns:
        Boolean
    """
    subscription = SubscriptionService.get_user_subscription(user)
    
    if not subscription:
        return False
    
    # Check if feature is in plan's features list
    return feature_name in subscription.plan.features


def get_user_video_quality(user):
    """
    Get video quality based on subscription.
    """
    subscription = SubscriptionService.get_user_subscription(user)
    
    if not subscription:
        return '480p'  # Free tier
    
    # Check plan's features
    if 'HD Videos' in subscription.plan.features:
        return '1080p'
    elif 'Standard Videos' in subscription.plan.features:
        return '720p'
    else:
        return '480p'


# Usage in view:
def course_video(request, video_id):
    video = Video.objects.get(id=video_id)
    quality = get_user_video_quality(request.user)
    
    return render(request, 'courses/video.html', {
        'video': video,
        'quality': quality,
        'can_download': user_can_access_feature(request.user, 'Video Downloads')
    })
```

## 5. API/AJAX Integration

### Scenario: Check subscription via AJAX

**File: `subscriptions/views.py`**

```python
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .services import SubscriptionService

@login_required
def subscription_status_api(request):
    """
    API endpoint to get user's subscription status.
    Used for dynamic UI updates.
    """
    stats = SubscriptionService.get_subscription_stats(request.user)
    
    return JsonResponse({
        'has_subscription': stats['has_subscription'],
        'plan_name': stats['plan'].name if stats['plan'] else None,
        'days_remaining': stats['days_remaining'],
        'expires_at': stats['expires_at'].isoformat() if stats['expires_at'] else None,
        'status': stats['status'],
    })
```

**File: `templates/base.html` (JavaScript)**

```javascript
// Check subscription status periodically
async function checkSubscriptionStatus() {
    const response = await fetch('/subscriptions/api/status/');
    const data = await response.json();
    
    if (data.has_subscription) {
        document.getElementById('premium-badge').style.display = 'block';
        
        // Show expiry warning if < 7 days
        if (data.days_remaining <= 7) {
            showExpiryWarning(data.days_remaining);
        }
    } else {
        document.getElementById('free-badge').style.display = 'block';
        showUpgradePrompt();
    }
}

// Call on page load
document.addEventListener('DOMContentLoaded', checkSubscriptionStatus);
```

## 6. Email Notifications (Bonus)

### Scenario: Send email before subscription expires

**File: `subscriptions/tasks.py`** (untuk Celery)

```python
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from .models import UserSubscription

def send_expiry_reminders():
    """
    Send email reminder to users whose subscription will expire soon.
    Run this daily via cron or Celery.
    """
    # Get subscriptions expiring in 7 days
    seven_days_later = timezone.now() + timedelta(days=7)
    expiring_soon = UserSubscription.objects.filter(
        status='active',
        current_period_end__lte=seven_days_later,
        current_period_end__gte=timezone.now()
    )
    
    for subscription in expiring_soon:
        send_mail(
            subject='Your subscription is expiring soon',
            message=f'Hi {subscription.user.username}, your {subscription.plan.name} subscription will expire in {subscription.days_remaining()} days.',
            from_email='noreply@ta3lem.com',
            recipient_list=[subscription.user.email],
            fail_silently=True,
        )
```

---

## Summary

Gunakan:
- `SubscriptionRequiredMixin` untuk class-based views
- `@subscription_required` untuk function-based views
- `user_has_subscription` & `user_subscription` di templates
- `SubscriptionService` untuk logic di Python
- Custom checks untuk fitur-fitur spesifik plan

Semua contoh di atas siap digunakan! 🚀
