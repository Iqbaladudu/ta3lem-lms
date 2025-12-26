# 🎯 Dual Pricing System Strategy
## Subscription vs One-Time Payment

**Date:** December 26, 2024  
**Status:** Implementation Plan

---

## 📊 Overview

Sistem ini akan mengelola **dua model pricing** yang berbeda:

### 1. **Subscription Model** 
- Akses **unlimited** ke semua kursus
- Berlaku selama periode aktif
- **Akses hilang** ketika subscription berakhir
- Renewal otomatis atau manual

### 2. **One-Time Payment Model**
- Pembelian **per kursus**
- Akses **selamanya** (lifetime access)
- Tidak ada renewal
- Bisa dibeli individual atau bundle

---

## 🔑 Key Business Rules

### Access Management Rules:

| Pricing Model | Access Duration | After Expiry | Renewal |
|---------------|-----------------|--------------|---------|
| **Subscription** | While active | ❌ Access Lost | Required |
| **One-Time** | Lifetime | ✅ Keep Access | Not needed |
| **Free** | Lifetime | ✅ Keep Access | N/A |

### Course Pricing Types:
```python
pricing_type = models.CharField(
    max_length=20,
    choices=[
        ('free', 'Gratis'),                    # Free forever
        ('one_time', 'Beli Satuan'),          # Buy once, own forever
        ('subscription_only', 'Hanya Langganan'), # Subscription required
        ('both', 'Beli/Langganan'),           # Can buy OR subscribe
    ],
    default='free'
)
```

---

## 🏗️ Architecture Changes Needed

### 1. CourseEnrollment Enhancement

Add field to track access type:

```python
# Add to CourseEnrollment model
ACCESS_TYPE_CHOICES = [
    ('free', 'Free Access'),
    ('purchased', 'One-Time Purchase'),
    ('subscription', 'Subscription Access'),
]

access_type = models.CharField(
    max_length=20,
    choices=ACCESS_TYPE_CHOICES,
    default='free'
)

# For subscription-based enrollments
subscription = models.ForeignKey(
    'subscriptions.UserSubscription',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='course_enrollments'
)

# Link to order (for one-time purchases)
order = models.ForeignKey(
    'payments.Order',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='course_enrollments'
)
```

### 2. Access Validation Service

Create service to check access rights:

```python
# courses/services.py

class CourseAccessService:
    """Service to validate and manage course access"""
    
    @staticmethod
    def can_access_course(user, course):
        """
        Check if user can access a course.
        
        Returns: (bool, str) - (can_access, reason)
        """
        # 1. Check if course is free
        if course.pricing_type == 'free':
            return True, 'free'
        
        # 2. Check if user has active enrollment
        enrollment = CourseEnrollment.objects.filter(
            student=user,
            course=course,
            status='enrolled'
        ).first()
        
        if not enrollment:
            return False, 'not_enrolled'
        
        # 3. Check access type
        if enrollment.access_type == 'purchased':
            # One-time purchase - lifetime access
            return True, 'purchased'
        
        elif enrollment.access_type == 'subscription':
            # Check if subscription is still active
            from subscriptions.services import SubscriptionService
            
            if enrollment.subscription:
                if enrollment.subscription.is_active():
                    return True, 'subscription_active'
                else:
                    # Subscription expired - revoke access
                    return False, 'subscription_expired'
            else:
                # Check if user has any active subscription
                has_active = SubscriptionService.user_has_active_subscription(user)
                if has_active:
                    return True, 'subscription_active'
                else:
                    return False, 'subscription_expired'
        
        elif enrollment.access_type == 'free':
            return True, 'free'
        
        return False, 'unknown'
    
    @staticmethod
    def get_enrollment_options(user, course):
        """
        Get available enrollment options for a course.
        
        Returns: dict with available options
        """
        options = {
            'can_enroll_free': False,
            'can_purchase': False,
            'can_use_subscription': False,
            'requires_subscription': False,
        }
        
        if course.pricing_type == 'free':
            options['can_enroll_free'] = True
        
        elif course.pricing_type == 'one_time':
            options['can_purchase'] = True
        
        elif course.pricing_type == 'subscription_only':
            options['requires_subscription'] = True
            options['can_use_subscription'] = True
        
        elif course.pricing_type == 'both':
            options['can_purchase'] = True
            options['can_use_subscription'] = True
        
        return options
```

### 3. Enrollment Service Update

```python
# courses/services.py

class EnrollmentService:
    """Handle course enrollment logic"""
    
    @classmethod
    def enroll_with_subscription(cls, user, course, subscription):
        """Enroll user via subscription"""
        enrollment, created = CourseEnrollment.objects.get_or_create(
            student=user,
            course=course,
            defaults={
                'access_type': 'subscription',
                'subscription': subscription,
                'status': 'enrolled',
                'payment_status': 'paid',
            }
        )
        
        if not created and enrollment.access_type != 'subscription':
            # Update existing enrollment to subscription
            enrollment.access_type = 'subscription'
            enrollment.subscription = subscription
            enrollment.status = 'enrolled'
            enrollment.save()
        
        return enrollment
    
    @classmethod
    def enroll_with_purchase(cls, user, course, order):
        """Enroll user via one-time purchase"""
        enrollment, created = CourseEnrollment.objects.get_or_create(
            student=user,
            course=course,
            defaults={
                'access_type': 'purchased',
                'order': order,
                'status': 'enrolled',
                'payment_status': 'paid',
                'payment_amount': order.total_amount,
                'payment_date': order.completed_at,
            }
        )
        
        return enrollment
    
    @classmethod
    def revoke_subscription_access(cls, user, subscription):
        """
        Revoke access to courses when subscription expires.
        Only affects subscription-based enrollments.
        """
        # Get all subscription-based enrollments
        enrollments = CourseEnrollment.objects.filter(
            student=user,
            access_type='subscription',
            subscription=subscription,
            status='enrolled'
        )
        
        # Mark as paused (not withdrawn, so progress is kept)
        enrollments.update(status='paused')
        
        return enrollments.count()
    
    @classmethod
    def restore_subscription_access(cls, user, subscription):
        """
        Restore access when subscription is renewed.
        """
        enrollments = CourseEnrollment.objects.filter(
            student=user,
            access_type='subscription',
            subscription=subscription,
            status='paused'
        )
        
        enrollments.update(status='enrolled')
        
        return enrollments.count()
```

---

## 🔄 Subscription Expiry Workflow

### When Subscription Expires:

```python
# subscriptions/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserSubscription

@receiver(post_save, sender=UserSubscription)
def handle_subscription_status_change(sender, instance, **kwargs):
    """Handle subscription expiry and renewal"""
    
    if instance.status in ['expired', 'cancelled']:
        # Revoke access to subscription-based enrollments
        from courses.services import EnrollmentService
        
        count = EnrollmentService.revoke_subscription_access(
            user=instance.user,
            subscription=instance
        )
        
        # Optional: Send email notification
        from subscriptions.emails import send_subscription_expired_email
        send_subscription_expired_email(instance.user, count)
    
    elif instance.status == 'active':
        # Restore access if subscription was renewed
        from courses.services import EnrollmentService
        
        count = EnrollmentService.restore_subscription_access(
            user=instance.user,
            subscription=instance
        )
```

### Cron Job for Auto-Expiry:

```python
# subscriptions/management/commands/expire_subscriptions.py
# (Already exists - update to include access revocation)

from django.core.management.base import BaseCommand
from subscriptions.services import SubscriptionService
from courses.services import EnrollmentService

class Command(BaseCommand):
    help = 'Expire subscriptions and revoke course access'

    def handle(self, *args, **options):
        # Expire subscriptions
        expired_count = SubscriptionService.check_and_expire_subscriptions()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Expired {expired_count} subscription(s)'
            )
        )
        
        # Revoke access for expired subscriptions
        # (This happens via signal, but we can do explicit check here too)
```

---

## 🎨 UI/UX Implementation

### Course Card Display

```html
<!-- courses/templates/courses/course_card.html -->
<div class="course-card">
    <h3>{{ course.title }}</h3>
    
    <!-- Pricing Badge -->
    {% if course.pricing_type == 'free' %}
        <span class="badge badge-success">GRATIS</span>
    
    {% elif course.pricing_type == 'one_time' %}
        <span class="badge badge-primary">
            {{ course.get_formatted_price }}
        </span>
    
    {% elif course.pricing_type == 'subscription_only' %}
        <span class="badge badge-premium">
            <i class="fas fa-crown"></i> Premium Only
        </span>
    
    {% elif course.pricing_type == 'both' %}
        <span class="badge badge-info">
            Beli: {{ course.get_formatted_price }}
        </span>
        <span class="badge badge-premium">
            atau Langganan
        </span>
    {% endif %}
    
    <!-- Enrollment CTA -->
    {% if user_has_access %}
        <a href="{% url 'student_course_detail' course.id %}" class="btn btn-success">
            Lanjutkan Belajar
        </a>
    {% else %}
        <!-- Show enrollment options based on pricing_type -->
        {% include 'courses/enrollment_options.html' %}
    {% endif %}
</div>
```

### Enrollment Options Modal

```html
<!-- courses/templates/courses/enrollment_options.html -->
{% if course.pricing_type == 'free' %}
    <button class="btn btn-primary" onclick="enrollFree('{{ course.id }}')">
        Daftar Gratis
    </button>

{% elif course.pricing_type == 'one_time' %}
    <button class="btn btn-primary" onclick="purchaseCourse('{{ course.id }}')">
        Beli Kursus - {{ course.get_formatted_price }}
    </button>

{% elif course.pricing_type == 'subscription_only' %}
    {% if user_has_subscription %}
        <button class="btn btn-primary" onclick="enrollWithSubscription('{{ course.id }}')">
            Akses dengan Subscription
        </button>
    {% else %}
        <a href="{% url 'subscriptions:plans' %}" class="btn btn-premium">
            <i class="fas fa-crown"></i> Langganan untuk Akses
        </a>
    {% endif %}

{% elif course.pricing_type == 'both' %}
    <div class="enrollment-options">
        <button class="btn btn-primary" onclick="purchaseCourse('{{ course.id }}')">
            Beli Selamanya - {{ course.get_formatted_price }}
        </button>
        
        <div class="divider">ATAU</div>
        
        {% if user_has_subscription %}
            <button class="btn btn-outline-primary" onclick="enrollWithSubscription('{{ course.id }}')">
                Akses dengan Subscription
            </button>
        {% else %}
            <a href="{% url 'subscriptions:plans' %}" class="btn btn-outline-premium">
                <i class="fas fa-crown"></i> Langganan
            </a>
        {% endif %}
    </div>
{% endif %}
```

---

## 🚨 Important: Access Check Middleware/Decorator

```python
# courses/decorators.py

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .services import CourseAccessService

def course_access_required(view_func):
    """
    Decorator to check if user has access to course.
    Course must be passed as 'course_id' or 'pk' in URL kwargs.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        course_id = kwargs.get('pk') or kwargs.get('course_id')
        
        if not course_id:
            messages.error(request, 'Course not found')
            return redirect('course_list')
        
        from courses.models import Course
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            messages.error(request, 'Course not found')
            return redirect('course_list')
        
        # Check access
        can_access, reason = CourseAccessService.can_access_course(
            request.user, course
        )
        
        if not can_access:
            if reason == 'subscription_expired':
                messages.warning(
                    request,
                    f'Subscription Anda telah berakhir. '
                    f'Perpanjang untuk melanjutkan akses ke {course.title}'
                )
                return redirect('subscriptions:manage')
            
            elif reason == 'not_enrolled':
                messages.info(
                    request,
                    f'Anda belum terdaftar di kursus ini.'
                )
                return redirect('course_detail', slug=course.slug)
            
            else:
                messages.error(request, 'Anda tidak memiliki akses ke kursus ini')
                return redirect('course_list')
        
        # Pass course to view
        kwargs['course'] = course
        return view_func(request, *args, **kwargs)
    
    return wrapper
```

---

## 📋 Migration Plan

### Step 1: Add Fields to CourseEnrollment

```python
# courses/migrations/XXXX_add_access_type_fields.py

from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('courses', 'XXXX_previous_migration'),
        ('subscriptions', 'XXXX_initial'),
        ('payments', 'XXXX_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseenrollment',
            name='access_type',
            field=models.CharField(
                choices=[
                    ('free', 'Free Access'),
                    ('purchased', 'One-Time Purchase'),
                    ('subscription', 'Subscription Access')
                ],
                default='free',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='courseenrollment',
            name='subscription',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                related_name='course_enrollments',
                to='subscriptions.usersubscription'
            ),
        ),
        migrations.AddField(
            model_name='courseenrollment',
            name='order',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                related_name='course_enrollments',
                to='payments.order'
            ),
        ),
    ]
```

### Step 2: Data Migration (Backfill)

```python
# courses/migrations/XXXX_backfill_access_types.py

def backfill_access_types(apps, schema_editor):
    """Set access_type for existing enrollments"""
    CourseEnrollment = apps.get_model('courses', 'CourseEnrollment')
    Course = apps.get_model('courses', 'Course')
    
    for enrollment in CourseEnrollment.objects.all():
        course = enrollment.course
        
        # Determine access type based on course pricing
        if course.is_free or course.pricing_type == 'free':
            enrollment.access_type = 'free'
        elif enrollment.payment_status == 'paid':
            enrollment.access_type = 'purchased'
        else:
            enrollment.access_type = 'free'
        
        enrollment.save()

class Migration(migrations.Migration):
    dependencies = [
        ('courses', 'XXXX_add_access_type_fields'),
    ]

    operations = [
        migrations.RunPython(backfill_access_types),
    ]
```

---

## 📊 Admin Interface Updates

```python
# courses/admin.py

@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'course', 'access_type', 'status',
        'payment_status', 'enrolled_on'
    ]
    list_filter = ['access_type', 'status', 'payment_status']
    search_fields = ['student__username', 'course__title']
    readonly_fields = ['subscription', 'order']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('student', 'course', 'status')
        }),
        ('Access Control', {
            'fields': ('access_type', 'subscription', 'order')
        }),
        ('Payment Info', {
            'fields': ('payment_status', 'payment_amount', 'payment_date')
        }),
        ('Progress', {
            'fields': ('progress_percentage', 'last_accessed')
        }),
    )
```

---

## ✅ Testing Checklist

### Subscription-Based Access:
- [ ] User with active subscription can enroll in subscription_only courses
- [ ] User can access course while subscription is active
- [ ] Access is revoked when subscription expires
- [ ] Access is restored when subscription is renewed
- [ ] Proper messages shown when access is denied

### One-Time Purchase:
- [ ] User can purchase course with one-time payment
- [ ] Access is granted after payment completion
- [ ] Access remains even after subscription expires
- [ ] User keeps progress and certificates

### Mixed Access:
- [ ] User with purchased access can still use subscription for other courses
- [ ] User can have both subscription and purchased courses
- [ ] Proper access type is recorded in enrollment

### Edge Cases:
- [ ] User tries to access expired subscription course
- [ ] User tries to purchase already-purchased course
- [ ] User downgrades from purchased to subscription
- [ ] Subscription expires but user has purchased courses

---

## 🎯 Summary

### Key Points:
1. **Subscription = Temporary Access** - Hilang saat berakhir
2. **One-Time = Lifetime Access** - Beli sekali, milik selamanya
3. **CourseEnrollment.access_type** - Tracks how access was granted
4. **Automatic Revocation** - Via signals when subscription expires
5. **Flexible Pricing** - Courses can offer both options

### Implementation Priority:
1. ✅ Add fields to CourseEnrollment (migration)
2. ✅ Create CourseAccessService
3. ✅ Update EnrollmentService
4. ✅ Add subscription expiry signals
5. ✅ Update course access decorator
6. ✅ Update UI/templates
7. ✅ Test all scenarios

**Status:** Ready for implementation 🚀
