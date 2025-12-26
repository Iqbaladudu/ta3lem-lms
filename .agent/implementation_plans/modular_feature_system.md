# Implementation Plan: Modular Feature System untuk Ta3lem LMS

## Overview

Implementasi sistem Feature Flags yang memungkinkan admin untuk mengaktifkan/menonaktifkan fitur-fitur LMS secara dinamis tanpa perlu mengubah kode atau melakukan redeploy.

## Goals

1. **Flexibility** - Klien bisa memilih fitur yang diperlukan
2. **Simplicity** - Mudah di-manage via Django Admin
3. **Performance** - Caching untuk menghindari query berulang
4. **Developer Experience** - API yang mudah digunakan (mixins, template tags)
5. **Graceful Degradation** - UI menyesuaikan saat fitur dinonaktifkan

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Template Tags│  │Context Proc. │  │  Conditional URLs    │  │
│  │ {% feature %}│  │  features    │  │  urlpatterns         │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                          VIEW LAYER                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              FeatureRequiredMixin                         │   │
│  │  - Check feature before dispatch                          │   │
│  │  - Redirect or 404 if disabled                           │   │
│  └──────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                        SERVICE LAYER                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              FeatureService                               │   │
│  │  - is_enabled(feature_name)                              │   │
│  │  - get_all_features()                                    │   │
│  │  - Cache management                                       │   │
│  └──────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                         DATA LAYER                               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              PlatformConfig (Singleton Model)             │   │
│  │  - Feature flags                                          │   │
│  │  - Platform settings                                      │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Feature Modules

### Daftar Feature Flags

| Flag Name | Field | Default | Affects |
|-----------|-------|---------|---------|
| `payments` | `enable_payments` | `True` | Semua payment flow, checkout, orders |
| `subscriptions` | `enable_subscriptions` | `True` | Subscription plans, user subscriptions |
| `instructor_payouts` | `enable_instructor_payouts` | `True` | Earnings, payouts, revenue sharing |
| `waitlist` | `enable_waitlist` | `True` | Course waitlist functionality |
| `enrollment_approval` | `enable_enrollment_approval` | `True` | Manual approval workflow |
| `certificates` | `enable_certificates` | `True` | Certificate generation |
| `analytics` | `enable_analytics` | `True` | Instructor analytics dashboard |
| `video_progress` | `enable_video_progress` | `True` | Video completion tracking |
| `learning_sessions` | `enable_learning_sessions` | `True` | Session time tracking |
| `course_pricing` | `enable_course_pricing` | `True` | Paid courses (vs all free) |

### Feature Dependencies

```
subscriptions ──requires──► payments
instructor_payouts ──requires──► payments
course_pricing ──requires──► payments
enrollment_approval ──conflicts──► (open enrollment only if disabled)
```

---

## Implementation Steps

### Phase 1: Core Infrastructure (Estimated: 1-2 hours)

#### Step 1.1: Create `core` Django App
```bash
python manage.py startapp core
```

**Files to create:**
- `core/__init__.py`
- `core/apps.py`
- `core/models.py`
- `core/services.py`
- `core/mixins.py`
- `core/context_processors.py`
- `core/templatetags/__init__.py`
- `core/templatetags/features.py`
- `core/admin.py`

#### Step 1.2: PlatformConfig Model

```python
# core/models.py
from django.db import models
from django.core.cache import cache


class PlatformConfig(models.Model):
    """
    Singleton model untuk platform-wide configuration.
    Hanya boleh ada 1 instance (pk=1).
    """
    
    CACHE_KEY = 'platform_config'
    CACHE_TIMEOUT = 60 * 60  # 1 hour
    
    # === PLATFORM BRANDING ===
    platform_name = models.CharField(
        max_length=100, 
        default="Ta3lem LMS",
        help_text="Nama platform yang ditampilkan di UI"
    )
    platform_tagline = models.CharField(
        max_length=200, 
        blank=True,
        help_text="Tagline untuk landing page"
    )
    
    # === PAYMENT FEATURES ===
    enable_payments = models.BooleanField(
        default=True,
        verbose_name="Enable Payments",
        help_text="Aktifkan sistem pembayaran. Jika OFF, semua course gratis."
    )
    enable_subscriptions = models.BooleanField(
        default=True,
        verbose_name="Enable Subscriptions",
        help_text="Aktifkan subscription plans. Requires: payments"
    )
    enable_instructor_payouts = models.BooleanField(
        default=True,
        verbose_name="Enable Instructor Payouts",
        help_text="Aktifkan revenue sharing dan payout untuk instructor. Requires: payments"
    )
    enable_course_pricing = models.BooleanField(
        default=True,
        verbose_name="Enable Course Pricing",
        help_text="Izinkan course berbayar. Jika OFF, semua course gratis. Requires: payments"
    )
    
    # === ENROLLMENT FEATURES ===
    enable_waitlist = models.BooleanField(
        default=True,
        verbose_name="Enable Waitlist",
        help_text="Aktifkan waitlist untuk course yang penuh"
    )
    enable_enrollment_approval = models.BooleanField(
        default=True,
        verbose_name="Enable Enrollment Approval",
        help_text="Izinkan instructor untuk require approval sebelum enrollment"
    )
    
    # === LEARNING FEATURES ===
    enable_certificates = models.BooleanField(
        default=True,
        verbose_name="Enable Certificates",
        help_text="Aktifkan certificate generation untuk course completion"
    )
    enable_analytics = models.BooleanField(
        default=True,
        verbose_name="Enable Analytics",
        help_text="Aktifkan analytics dashboard untuk instructor"
    )!
    enable_video_progress = models.BooleanField(
        default=True,
        verbose_name="Enable Video Progress Tracking",
        help_text="Track video watch progress dan completion"
    )
    enable_learning_sessions = models.BooleanField(
        default=True,
        verbose_name="Enable Learning Session Tracking",
        help_text="Track waktu belajar per session"
    )
    
    # === CONTENT FEATURES ===
    enable_multi_content_items = models.BooleanField(
        default=True,
        verbose_name="Enable Multi Content Items",
        help_text="Izinkan multiple items (text, video, file) dalam satu content"
    )
    
    # === UI FEATURES ===
    show_instructor_earnings_to_students = models.BooleanField(
        default=False,
        verbose_name="Show Earnings to Students",
        help_text="Tampilkan info penghasilan instructor di profile"
    )
    
    # === TIMESTAMPS ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Platform Configuration"
        verbose_name_plural = "Platform Configuration"
    
    def __str__(self):
        return f"Platform Config: {self.platform_name}"
    
    def save(self, *args, **kwargs):
        # Enforce singleton
        self.pk = 1
        super().save(*args, **kwargs)
        # Invalidate cache on save
        cache.delete(self.CACHE_KEY)
    
    def delete(self, *args, **kwargs):
        # Prevent deletion
        pass
    
    @classmethod
    def get_config(cls):
        """Get or create the singleton config with caching"""
        config = cache.get(cls.CACHE_KEY)
        if config is None:
            config, _ = cls.objects.get_or_create(pk=1)
            cache.set(cls.CACHE_KEY, config, cls.CACHE_TIMEOUT)
        return config
    
    @classmethod
    def invalidate_cache(cls):
        """Invalidate the config cache"""
        cache.delete(cls.CACHE_KEY)
```

#### Step 1.3: FeatureService

```python
# core/services.py
from typing import Dict, List, Optional
from django.core.cache import cache


class FeatureService:
    """
    Central service untuk feature flag management.
    Semua feature checks harus melalui service ini.
    """
    
    # Feature dependencies - key requires values to be enabled
    DEPENDENCIES = {
        'subscriptions': ['payments'],
        'instructor_payouts': ['payments'],
        'course_pricing': ['payments'],
    }
    
    # Feature conflicts - if key is enabled, values behavior changes
    CONFLICTS = {
        # No conflicts for now
    }
    
    @classmethod
    def get_config(cls):
        """Get platform config singleton"""
        from .models import PlatformConfig
        return PlatformConfig.get_config()
    
    @classmethod
    def is_enabled(cls, feature_name: str) -> bool:
        """
        Check if a feature is enabled.
        
        Args:
            feature_name: Feature name without 'enable_' prefix
                         e.g., 'payments', 'subscriptions'
        
        Returns:
            True if feature is enabled, False otherwise
        """
        config = cls.get_config()
        field_name = f'enable_{feature_name}'
        
        # Check if feature exists
        if not hasattr(config, field_name):
            return False
        
        # Check if feature is enabled
        is_enabled = getattr(config, field_name, False)
        
        # Check dependencies
        if is_enabled and feature_name in cls.DEPENDENCIES:
            for dep in cls.DEPENDENCIES[feature_name]:
                if not cls.is_enabled(dep):
                    return False
        
        return is_enabled
    
    @classmethod
    def get_all_features(cls) -> Dict[str, bool]:
        """Get all feature flags as a dictionary"""
        config = cls.get_config()
        features = {}
        
        for field in config._meta.get_fields():
            if field.name.startswith('enable_'):
                feature_name = field.name.replace('enable_', '')
                features[feature_name] = cls.is_enabled(feature_name)
        
        return features
    
    @classmethod
    def get_enabled_features(cls) -> List[str]:
        """Get list of enabled feature names"""
        return [name for name, enabled in cls.get_all_features().items() if enabled]
    
    @classmethod
    def get_disabled_features(cls) -> List[str]:
        """Get list of disabled feature names"""
        return [name for name, enabled in cls.get_all_features().items() if not enabled]
    
    @classmethod
    def require_feature(cls, feature_name: str) -> bool:
        """
        Check feature and raise exception if disabled.
        Use in views that absolutely require a feature.
        """
        if not cls.is_enabled(feature_name):
            from django.http import Http404
            raise Http404(f"Feature '{feature_name}' is not available")
        return True
    
    @classmethod
    def get_platform_name(cls) -> str:
        """Get platform name for branding"""
        return cls.get_config().platform_name
```

#### Step 1.4: View Mixin

```python
# core/mixins.py
from django.http import Http404
from django.shortcuts import redirect
from django.contrib import messages

from .services import FeatureService


class FeatureRequiredMixin:
    """
    Mixin untuk views yang memerlukan feature tertentu.
    
    Usage:
        class MyView(FeatureRequiredMixin, View):
            required_feature = 'subscriptions'
            feature_disabled_redirect = 'home'  # optional
    """
    
    required_feature: str = None
    required_features: list = None  # For multiple features (AND logic)
    feature_disabled_redirect: str = None  # URL name to redirect if disabled
    feature_disabled_message: str = None  # Flash message
    
    def dispatch(self, request, *args, **kwargs):
        # Check single feature
        if self.required_feature:
            if not FeatureService.is_enabled(self.required_feature):
                return self._handle_feature_disabled(request, self.required_feature)
        
        # Check multiple features (all must be enabled)
        if self.required_features:
            for feature in self.required_features:
                if not FeatureService.is_enabled(feature):
                    return self._handle_feature_disabled(request, feature)
        
        return super().dispatch(request, *args, **kwargs)
    
    def _handle_feature_disabled(self, request, feature_name):
        """Handle when a required feature is disabled"""
        if self.feature_disabled_redirect:
            if self.feature_disabled_message:
                messages.warning(request, self.feature_disabled_message)
            else:
                messages.warning(
                    request, 
                    f"Fitur ini sedang tidak tersedia."
                )
            return redirect(self.feature_disabled_redirect)
        
        raise Http404(f"Feature '{feature_name}' is not available")


class PaymentsRequiredMixin(FeatureRequiredMixin):
    """Shortcut mixin for payment-related views"""
    required_feature = 'payments'
    feature_disabled_redirect = 'course_list'
    feature_disabled_message = "Sistem pembayaran sedang tidak aktif."


class SubscriptionsRequiredMixin(FeatureRequiredMixin):
    """Shortcut mixin for subscription-related views"""
    required_feature = 'subscriptions'
    feature_disabled_redirect = 'course_list'
    feature_disabled_message = "Fitur subscription tidak tersedia."


class AnalyticsRequiredMixin(FeatureRequiredMixin):
    """Shortcut mixin for analytics-related views"""
    required_feature = 'analytics'
    feature_disabled_redirect = 'manage_course_list'
    feature_disabled_message = "Fitur analytics tidak tersedia."
```

#### Step 1.5: Template Tags

```python
# core/templatetags/features.py
from django import template
from django.utils.safestring import mark_safe

from core.services import FeatureService

register = template.Library()


@register.simple_tag
def feature_enabled(feature_name):
    """
    Check if a feature is enabled.
    
    Usage:
        {% feature_enabled 'payments' as has_payments %}
        {% if has_payments %}...{% endif %}
    """
    return FeatureService.is_enabled(feature_name)


@register.simple_tag(takes_context=True)
def if_feature(context, feature_name):
    """
    Returns True if feature is enabled, for use in conditionals.
    
    Usage:
        {% if_feature 'subscriptions' %}
    """
    return FeatureService.is_enabled(feature_name)


@register.inclusion_tag('core/feature_wrapper.html')
def feature_block(feature_name, fallback_template=None):
    """
    Render content only if feature is enabled.
    
    Usage:
        {% feature_block 'subscriptions' %}
    """
    return {
        'enabled': FeatureService.is_enabled(feature_name),
        'feature_name': feature_name,
        'fallback_template': fallback_template,
    }


@register.simple_tag
def platform_name():
    """Get platform name for branding"""
    return FeatureService.get_platform_name()


@register.simple_tag
def all_features():
    """Get all feature flags as dict"""
    return FeatureService.get_all_features()


# Block-style tags for cleaner templates
class FeatureNode(template.Node):
    def __init__(self, feature_name, nodelist_true, nodelist_false=None):
        self.feature_name = feature_name
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false or template.NodeList()
    
    def render(self, context):
        # Resolve feature name if it's a variable
        if isinstance(self.feature_name, template.Variable):
            feature_name = self.feature_name.resolve(context)
        else:
            feature_name = self.feature_name
        
        if FeatureService.is_enabled(feature_name):
            return self.nodelist_true.render(context)
        else:
            return self.nodelist_false.render(context)


@register.tag('iffeature')
def do_iffeature(parser, token):
    """
    Block tag for conditional feature rendering.
    
    Usage:
        {% iffeature "payments" %}
            <button>Buy Now</button>
        {% else %}
            <button>Enroll Free</button>
        {% endiffeature %}
    """
    bits = token.split_contents()
    if len(bits) != 2:
        raise template.TemplateSyntaxError(
            f"'{bits[0]}' tag requires exactly one argument (feature name)"
        )
    
    feature_name = bits[1]
    # Remove quotes if present
    if feature_name[0] in ('"', "'") and feature_name[-1] == feature_name[0]:
        feature_name = feature_name[1:-1]
    else:
        feature_name = template.Variable(feature_name)
    
    nodelist_true = parser.parse(('else', 'endiffeature'))
    token = parser.next_token()
    
    if token.contents == 'else':
        nodelist_false = parser.parse(('endiffeature',))
        parser.delete_first_token()
    else:
        nodelist_false = template.NodeList()
    
    return FeatureNode(feature_name, nodelist_true, nodelist_false)
```

#### Step 1.6: Context Processor

```python
# core/context_processors.py
from .services import FeatureService


def features(request):
    """
    Add feature flags to template context.
    
    Usage in templates:
        {% if features.payments %}
        {{ platform_name }}
    """
    return {
        'features': FeatureService.get_all_features(),
        'platform_name': FeatureService.get_platform_name(),
    }
```

#### Step 1.7: Admin Interface

```python
# core/admin.py
from django.contrib import admin
from django.utils.html import format_html

from .models import PlatformConfig


@admin.register(PlatformConfig)
class PlatformConfigAdmin(admin.ModelAdmin):
    """Admin for platform configuration"""
    
    fieldsets = (
        ('Platform Branding', {
            'fields': ('platform_name', 'platform_tagline'),
        }),
        ('💳 Payment Features', {
            'fields': (
                'enable_payments',
                'enable_course_pricing',
                'enable_subscriptions',
                'enable_instructor_payouts',
            ),
            'description': 'Fitur terkait pembayaran dan monetisasi',
        }),
        ('📝 Enrollment Features', {
            'fields': (
                'enable_waitlist',
                'enable_enrollment_approval',
            ),
            'description': 'Fitur terkait proses enrollment',
        }),
        ('📊 Learning Features', {
            'fields': (
                'enable_certificates',
                'enable_analytics',
                'enable_video_progress',
                'enable_learning_sessions',
            ),
            'description': 'Fitur terkait pembelajaran dan tracking',
        }),
        ('📄 Content Features', {
            'fields': (
                'enable_multi_content_items',
            ),
            'description': 'Fitur terkait content management',
        }),
        ('🎨 UI Features', {
            'fields': (
                'show_instructor_earnings_to_students',
            ),
            'description': 'Pengaturan tampilan UI',
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not PlatformConfig.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion
        return False
    
    def changelist_view(self, request, extra_context=None):
        # Redirect to change view of singleton
        config = PlatformConfig.get_config()
        from django.shortcuts import redirect
        return redirect(f'/admin/core/platformconfig/{config.pk}/change/')
```

---

### Phase 2: Integration (Estimated: 2-3 hours)

#### Step 2.1: Update Django Settings

```python
# ta3lem/settings.py

INSTALLED_APPS = [
    # ... existing apps
    'core',  # Add core app
]

TEMPLATES = [
    {
        # ...
        'OPTIONS': {
            'context_processors': [
                # ... existing processors
                'core.context_processors.features',  # Add this
            ],
        },
    },
]
```

#### Step 2.2: Update Payment Views

```python
# payments/views.py
from core.mixins import PaymentsRequiredMixin, FeatureRequiredMixin

class CheckoutView(PaymentsRequiredMixin, LoginRequiredMixin, View):
    # ... existing code

class InstructorEarningsView(FeatureRequiredMixin, LoginRequiredMixin, View):
    required_feature = 'instructor_payouts'
    # ... existing code

class RequestPayoutView(FeatureRequiredMixin, LoginRequiredMixin, View):
    required_feature = 'instructor_payouts'
    # ... existing code
```

#### Step 2.3: Update Subscription Views

```python
# subscriptions/views.py
from core.mixins import SubscriptionsRequiredMixin

class PlanListView(SubscriptionsRequiredMixin, ListView):
    # ... existing code

class SubscribeView(SubscriptionsRequiredMixin, LoginRequiredMixin, View):
    # ... existing code
```

#### Step 2.4: Update Course Views

```python
# courses/views.py
from core.mixins import FeatureRequiredMixin, AnalyticsRequiredMixin
from core.services import FeatureService

class InstructorCourseAnalyticsView(AnalyticsRequiredMixin, LoginRequiredMixin, DetailView):
    # ... existing code

class CourseWaitlistManagementView(FeatureRequiredMixin, LoginRequiredMixin, View):
    required_feature = 'waitlist'
    # ... existing code

# In StudentEnrollCourseView.post():
def post(self, request, pk):
    # Check if waitlist is enabled
    if course.is_full():
        if FeatureService.is_enabled('waitlist') and course.waitlist_enabled:
            # Add to waitlist
            ...
        else:
            messages.error(request, "Course is full.")
            return redirect(...)
```

#### Step 2.5: Update Templates

```html
<!-- base.html or navigation -->
{% load features %}

<nav>
    {% iffeature "subscriptions" %}
        <a href="{% url 'subscriptions:plans' %}">Upgrade</a>
    {% endiffeature %}
    
    {% iffeature "analytics" %}
        <a href="{% url 'instructor_course_analytics' pk=course.pk %}">Analytics</a>
    {% endiffeature %}
</nav>

<!-- course detail -->
{% iffeature "payments" %}
    {% if course.is_free %}
        <button>Enroll Free</button>
    {% else %}
        <button>Buy for {{ course.get_formatted_price }}</button>
    {% endif %}
{% else %}
    <button>Enroll Free</button>
{% endiffeature %}

<!-- instructor dashboard -->
{% iffeature "instructor_payouts" %}
    <div class="earnings-widget">
        <h3>Your Earnings</h3>
        <p>{{ earnings.total_earned }}</p>
    </div>
{% endiffeature %}
```

#### Step 2.6: Update Course Form

```python
# courses/forms.py
from core.services import FeatureService

class CourseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Hide pricing fields if payments disabled
        if not FeatureService.is_enabled('payments'):
            if 'price' in self.fields:
                del self.fields['price']
            if 'is_free' in self.fields:
                del self.fields['is_free']
        
        # Hide waitlist if disabled
        if not FeatureService.is_enabled('waitlist'):
            if 'waitlist_enabled' in self.fields:
                del self.fields['waitlist_enabled']
        
        # Hide enrollment approval if disabled
        if not FeatureService.is_enabled('enrollment_approval'):
            if 'enrollment_type' in self.fields:
                # Remove approval_required option
                self.fields['enrollment_type'].choices = [
                    c for c in self.fields['enrollment_type'].choices
                    if c[0] != 'approval_required'
                ]
```

---

### Phase 3: URL Conditional Loading (Estimated: 1 hour)

#### Step 3.1: Conditional URL Patterns

```python
# ta3lem/urls.py
from core.services import FeatureService

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('courses.urls')),
    path('users/', include('users.urls')),
]

# Conditionally include payment URLs
# Note: This only works at server startup, not dynamically
# For dynamic behavior, use view mixins instead
try:
    from core.models import PlatformConfig
    config = PlatformConfig.get_config()
    
    if config.enable_payments:
        urlpatterns.append(path('payments/', include('payments.urls')))
    
    if config.enable_subscriptions:
        urlpatterns.append(path('subscriptions/', include('subscriptions.urls')))
except:
    # Include by default if core app not ready
    urlpatterns.extend([
        path('payments/', include('payments.urls')),
        path('subscriptions/', include('subscriptions.urls')),
    ])
```

**Note:** URL conditional loading hanya berlaku saat server start. Untuk dynamic behavior, gunakan view mixins.

---

### Phase 4: Model-Level Integration (Estimated: 1-2 hours)

#### Step 4.1: Course Model Updates

```python
# courses/models.py
from core.services import FeatureService

class Course(models.Model):
    # ... existing fields
    
    def get_effective_enrollment_type(self):
        """Get enrollment type considering feature flags"""
        if not FeatureService.is_enabled('enrollment_approval'):
            # If approval disabled, treat approval_required as open
            if self.enrollment_type == 'approval_required':
                return 'open'
        return self.enrollment_type
    
    def is_effectively_free(self):
        """Check if course is free considering feature flags"""
        if not FeatureService.is_enabled('payments'):
            return True  # All courses free if payments disabled
        if not FeatureService.is_enabled('course_pricing'):
            return True  # All courses free if pricing disabled
        return self.is_free
    
    def get_price(self):
        """Implement Purchasable protocol with feature check"""
        if self.is_effectively_free():
            return Decimal('0')
        return self.price or Decimal('0')
    
    @property
    def can_have_waitlist(self):
        """Check if waitlist is available for this course"""
        if not FeatureService.is_enabled('waitlist'):
            return False
        return self.waitlist_enabled and self.max_capacity
```

#### Step 4.2: Enrollment Model Updates

```python
# courses/models.py

class CourseEnrollment(models.Model):
    # ... existing code
    
    def can_access_course(self):
        """Check access with feature flags"""
        # Status check
        valid_statuses = ['enrolled', 'completed', 'paused']
        if self.status not in valid_statuses:
            return False
        
        # Payment check - skip if payments disabled
        if FeatureService.is_enabled('payments'):
            valid_payment = ['paid', 'free']
            if self.payment_status not in valid_payment:
                # Check subscription if enabled
                if FeatureService.is_enabled('subscriptions'):
                    if self.course.subscription_enabled and self.student.has_active_subscription():
                        return True
                return False
        
        return True
```

---

### Phase 5: Testing & Documentation (Estimated: 1-2 hours)

#### Step 5.1: Unit Tests

```python
# core/tests.py
from django.test import TestCase, override_settings
from .models import PlatformConfig
from .services import FeatureService


class FeatureServiceTests(TestCase):
    def setUp(self):
        self.config = PlatformConfig.get_config()
    
    def test_feature_enabled_by_default(self):
        self.assertTrue(FeatureService.is_enabled('payments'))
    
    def test_feature_can_be_disabled(self):
        self.config.enable_payments = False
        self.config.save()
        self.assertFalse(FeatureService.is_enabled('payments'))
    
    def test_dependent_feature_disabled_when_parent_disabled(self):
        """Subscriptions should be disabled if payments is disabled"""
        self.config.enable_payments = False
        self.config.save()
        self.assertFalse(FeatureService.is_enabled('subscriptions'))
    
    def test_cache_invalidation(self):
        # Enable feature
        self.config.enable_payments = True
        self.config.save()
        self.assertTrue(FeatureService.is_enabled('payments'))
        
        # Disable and check cache is invalidated
        self.config.enable_payments = False
        self.config.save()
        self.assertFalse(FeatureService.is_enabled('payments'))


class FeatureMixinTests(TestCase):
    def test_feature_required_mixin_allows_when_enabled(self):
        # Test that view works when feature is enabled
        pass
    
    def test_feature_required_mixin_blocks_when_disabled(self):
        # Test that view returns 404 when feature is disabled
        pass
```

#### Step 5.2: Create Documentation

```markdown
# Feature Flags Documentation

## Overview
Ta3lem LMS menggunakan sistem feature flags untuk mengontrol fitur yang tersedia.

## Admin Interface
Akses `/admin/core/platformconfig/` untuk mengatur feature flags.

## Available Features
- payments: Sistem pembayaran
- subscriptions: Subscription plans
- ...

## Usage in Views
```python
from core.mixins import FeatureRequiredMixin

class MyView(FeatureRequiredMixin, View):
    required_feature = 'payments'
```

## Usage in Templates
```html
{% load features %}
{% iffeature "payments" %}
    ...
{% endiffeature %}
```
```

---

## Migration Script

```python
# core/migrations/0001_initial.py
# (Auto-generated by Django)

# After migration, create initial data:
# core/management/commands/setup_platform_config.py

from django.core.management.base import BaseCommand
from core.models import PlatformConfig


class Command(BaseCommand):
    help = 'Setup initial platform configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--simple',
            action='store_true',
            help='Setup for simple LMS (disable advanced features)',
        )
        parser.add_argument(
            '--full',
            action='store_true',
            help='Setup for full-featured LMS (enable all features)',
        )

    def handle(self, *args, **options):
        config = PlatformConfig.get_config()
        
        if options['simple']:
            # Simple LMS configuration
            config.enable_payments = False
            config.enable_subscriptions = False
            config.enable_instructor_payouts = False
            config.enable_course_pricing = False
            config.enable_waitlist = False
            config.enable_enrollment_approval = False
            config.enable_certificates = False
            config.enable_analytics = True  # Keep basic analytics
            config.enable_video_progress = True
            config.enable_learning_sessions = False
            config.enable_multi_content_items = False
            self.stdout.write(self.style.SUCCESS('Configured for Simple LMS'))
        
        elif options['full']:
            # Full-featured LMS configuration
            config.enable_payments = True
            config.enable_subscriptions = True
            config.enable_instructor_payouts = True
            config.enable_course_pricing = True
            config.enable_waitlist = True
            config.enable_enrollment_approval = True
            config.enable_certificates = True
            config.enable_analytics = True
            config.enable_video_progress = True
            config.enable_learning_sessions = True
            config.enable_multi_content_items = True
            self.stdout.write(self.style.SUCCESS('Configured for Full LMS'))
        
        config.save()
        self.stdout.write(self.style.SUCCESS(f'Platform config saved'))
```

---

## Preset Configurations

### Simple LMS (Free courses only)
```
enable_payments = False
enable_subscriptions = False
enable_instructor_payouts = False
enable_course_pricing = False
enable_waitlist = False
enable_enrollment_approval = False
enable_certificates = False
enable_analytics = True
enable_video_progress = True
enable_learning_sessions = False
enable_multi_content_items = False
```

### Standard LMS (Paid courses, no revenue sharing)
```
enable_payments = True
enable_subscriptions = False
enable_instructor_payouts = False
enable_course_pricing = True
enable_waitlist = True
enable_enrollment_approval = True
enable_certificates = True
enable_analytics = True
enable_video_progress = True
enable_learning_sessions = True
enable_multi_content_items = True
```

### Marketplace LMS (Full features)
```
All features = True
```

---

## Timeline Summary

| Phase | Task | Estimated Time |
|-------|------|----------------|
| **Phase 1** | Core Infrastructure | 1-2 hours |
| **Phase 2** | View Integration | 2-3 hours |
| **Phase 3** | URL Conditionals | 1 hour |
| **Phase 4** | Model Integration | 1-2 hours |
| **Phase 5** | Testing & Docs | 1-2 hours |
| **Total** | | **6-10 hours** |

---

## Checklist

### Phase 1: Core Infrastructure
- [ ] Create `core` Django app
- [ ] Implement `PlatformConfig` model
- [ ] Implement `FeatureService`
- [ ] Create view mixins
- [ ] Create template tags
- [ ] Create context processor
- [ ] Setup admin interface
- [ ] Create migrations
- [ ] Register app in settings

### Phase 2: Integration
- [ ] Update payment views with mixins
- [ ] Update subscription views with mixins
- [ ] Update course views with mixins
- [ ] Update templates with feature tags
- [ ] Update forms with feature checks

### Phase 3: URL Conditionals
- [ ] Setup conditional URL loading
- [ ] Handle edge cases

### Phase 4: Model Integration
- [ ] Update Course model methods
- [ ] Update Enrollment model methods
- [ ] Update other affected models

### Phase 5: Testing & Documentation
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Create user documentation
- [ ] Create developer documentation
- [ ] Create preset configurations

---

## Notes

1. **Caching**: Config di-cache selama 1 jam untuk performance. Cache di-invalidate otomatis saat save.

2. **Dependencies**: Beberapa feature memiliki dependency. Jika parent disabled, child otomatis disabled.

3. **Graceful Degradation**: UI harus menyesuaikan dengan baik saat fitur dinonaktifkan.

4. **Testing**: Test semua kombinasi feature flags untuk memastikan tidak ada error.

5. **Migration**: Untuk existing installation, semua features default ke `True` (no breaking changes).
