# Python Mixin Injection - Penjelasan Lengkap

## Konsep Dasar: Python Inheritance

Setiap class Python memiliki atribut `__bases__` yang berisi tuple dari parent classes:

```python
class Parent:
    pass

class Child(Parent):
    pass

print(Child.__bases__)  # Output: (<class 'Parent'>,)
```

---

## Method Resolution Order (MRO)

Ketika memanggil method, Python mencari di class hierarchy menggunakan MRO:

```python
class A:
    def greet(self):
        return "Hello from A"

class B(A):
    pass

class C(B):
    pass

# MRO untuk C:
print(C.__mro__)
# (<class 'C'>, <class 'B'>, <class 'A'>, <class 'object'>)

# Saat memanggil c.greet():
# 1. Cari di C → tidak ada
# 2. Cari di B → tidak ada  
# 3. Cari di A → ADA! → Return "Hello from A"
```

---

## Cara Kerja Mixin Injection

### Kode Injection:

```python
def ready(self):
    from courses.views import CourseDetailView
    from .mixins import AnalyticsViewMixin
    
    # Modifikasi __bases__ untuk menambah parent class baru
    CourseDetailView.__bases__ = (AnalyticsViewMixin,) + CourseDetailView.__bases__
```

### Step-by-Step:

**Step 1: Sebelum Injection**
```python
# CourseDetailView(DetailView):
#     ... course-specific methods ...

CourseDetailView.__bases__
# Output: (<class 'DetailView'>,)

CourseDetailView.__mro__
# (CourseDetailView, DetailView, TemplateResponseMixin, 
#  ContextMixin, View, object)
```

**Step 2: Operasi Tuple**
```python
# (AnalyticsViewMixin,) + CourseDetailView.__bases__
# = (AnalyticsViewMixin,) + (DetailView,)
# = (AnalyticsViewMixin, DetailView)
```

**Step 3: Sesudah Injection**
```python
CourseDetailView.__bases__
# Output: (<class 'AnalyticsViewMixin'>, <class 'DetailView'>)

CourseDetailView.__mro__
# (CourseDetailView, AnalyticsViewMixin, DetailView, 
#  TemplateResponseMixin, ContextMixin, View, object)
#                    ↑
#            MIXIN SEKARANG DI SINI!
```

### Visualisasi Hierarchy:

```
SEBELUM INJECTION:
==================

CourseDetailView
       │
       ▼
  DetailView
       │
       ▼
TemplateResponseMixin + ContextMixin
       │
       ▼
     View
       │
       ▼
    object


SESUDAH INJECTION:
==================

   CourseDetailView
          │
          ▼
┌─────────────────────┐
│ AnalyticsViewMixin  │  ← BARU DITAMBAHKAN!
└─────────────────────┘
          │
          ▼
     DetailView
          │
          ▼
TemplateResponseMixin + ContextMixin
          │
          ▼
        View
          │
          ▼
       object
```

---

## Bagaimana super() Bekerja

```python
class AnalyticsViewMixin:
    def get_context_data(self, **kwargs):
        # super() mengikuti MRO
        # Karena AnalyticsViewMixin sekarang sebelum DetailView di MRO,
        # super() akan memanggil DetailView.get_context_data()
        context = super().get_context_data(**kwargs)
        
        # Tambah data analytics
        context['page_views'] = self.get_page_views()
        
        return context
```

**Alur Eksekusi:**
```
1. Request masuk ke CourseDetailView
2. Django memanggil get_context_data()
3. MRO: Cek CourseDetailView → tidak ada
4. MRO: Cek AnalyticsViewMixin → ADA!
5. Execute AnalyticsViewMixin.get_context_data()
6. super().get_context_data() → DetailView.get_context_data()
7. Return context dengan data analytics ditambahkan
```

---

## ⚠️ Risiko Mixin Injection via __bases__

1. **Konflik dengan plugin lain** - Dua plugin bisa override method yang sama
2. **Sulit debug** - Stack trace tidak menunjukkan dengan jelas mana yang di-inject
3. **Timing issues** - Jika ready() dipanggil dalam urutan berbeda, hasil bisa berbeda
4. **Django upgrade** - Bisa break jika Django mengubah internal view classes

---

## ✅ Alternatif yang Lebih Aman

### 1. View Decorator Factory

```python
# plugins_available/analytics/decorators.py

def with_analytics(view_class):
    """
    Decorator yang membuat subclass baru dengan mixin.
    Lebih aman karena tidak memodifikasi class original.
    """
    class AnalyticsEnabledView(AnalyticsViewMixin, view_class):
        pass
    
    # Preserve original class name for debugging
    AnalyticsEnabledView.__name__ = f"Analytics{view_class.__name__}"
    AnalyticsEnabledView.__qualname__ = f"Analytics{view_class.__qualname__}"
    
    return AnalyticsEnabledView
```

**Penggunaan di plugin:**
```python
# plugins_available/analytics/plugin.py

class AnalyticsPlugin(PluginBase):
    def ready(self):
        from courses import views
        from .decorators import with_analytics
        
        # Wrap the view class (tidak memodifikasi original)
        views.CourseDetailView = with_analytics(views.CourseDetailView)
```

---

### 2. Hook-Based Extension (RECOMMENDED)

**Tidak perlu modify class sama sekali:**

```python
# plugins_available/analytics/plugin.py

class AnalyticsPlugin(PluginBase):
    name = "analytics"
    
    @hook(CoreHooks.TEMPLATE_COURSE_DETAIL, priority=5)
    def inject_analytics_data(self, request=None, context=None, course=None, **kwargs):
        """
        Inject analytics data via hook.
        View original tidak perlu dimodifikasi.
        """
        if context is None:
            context = {}
        
        # Add analytics data
        context['page_views'] = self.get_page_views(course)
        context['analytics_enabled'] = True
        
        return context
    
    def get_page_views(self, course):
        from .models import PageView
        return PageView.objects.filter(course=course).count()
```

**Di view (sudah ada):**
```python
# courses/views.py

class CourseDetailView(DetailView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Plugin hooks inject data di sini
        extra_data = trigger_hook(
            CoreHooks.TEMPLATE_COURSE_DETAIL,
            request=self.request,
            course=self.object,
            context=context
        )
        
        # Merge data dari plugins
        for data in extra_data:
            if isinstance(data, dict):
                context.update(data)
        
        return context
```

---

### 3. Middleware-based Extension

```python
# plugins_available/analytics/middleware.py

class AnalyticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Track page view after response
        self.track_view(request)
        
        return response
    
    def track_view(self, request):
        # Track all page views
        pass
```

**Register di plugin ready():**
```python
def ready(self):
    from django.conf import settings
    if 'plugins_available.analytics.middleware.AnalyticsMiddleware' not in settings.MIDDLEWARE:
        # Note: Modifying MIDDLEWARE at runtime is tricky, 
        # better to add via settings
        pass
```

---

## Perbandingan Pendekatan

| Pendekatan | Safety | Flexibility | Complexity |
|------------|--------|-------------|------------|
| `__bases__` injection | ⚠️ Low | High | Medium |
| View decorator factory | ✅ High | High | Medium |
| Hook-based | ✅ High | Medium | Low |
| Middleware | ✅ High | Low | Low |

---

## Rekomendasi

1. **Hook-based** → Untuk inject data ke context
2. **View decorator** → Untuk modify view behavior
3. **Middleware** → Untuk tracking/logging semua requests
4. **`__bases__` injection** → Hanya jika tidak ada alternatif lain

---

## Contoh Lengkap: Analytics Plugin yang Aman

```python
# plugins_available/analytics/plugin.py

from plugins.base import PluginBase
from plugins.hooks import CoreHooks, hook

class AnalyticsPlugin(PluginBase):
    name = "analytics"
    version = "1.0.0"
    
    def ready(self):
        import logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("Analytics plugin ready")
    
    # === APPROACH 1: Hook untuk inject data ===
    @hook(CoreHooks.TEMPLATE_COURSE_DETAIL, priority=5)
    def add_course_analytics(self, request=None, course=None, context=None, **kwargs):
        """Inject analytics ke course detail context"""
        if not course:
            return {}
        
        return {
            'view_count': self.get_view_count(course),
            'unique_visitors': self.get_unique_visitors(course),
            'popular_times': self.get_popular_times(course),
        }
    
    # === APPROACH 2: Hook untuk tracking ===
    @hook(CoreHooks.COURSE_VIEWED, priority=1)
    def track_course_view(self, request=None, course=None, user=None, **kwargs):
        """Track page view via hook (triggered from view)"""
        from .models import PageView
        
        PageView.objects.create(
            course=course,
            user=user,
            ip_address=request.META.get('REMOTE_ADDR') if request else None,
        )
    
    # === Helper methods ===
    def get_view_count(self, course):
        from .models import PageView
        return PageView.objects.filter(course=course).count()
    
    def get_unique_visitors(self, course):
        from .models import PageView
        return PageView.objects.filter(course=course).values('ip_address').distinct().count()
    
    def get_popular_times(self, course):
        # Return popular viewing times
        return []
```

Pendekatan ini **tidak memodifikasi** class view sama sekali, hanya menggunakan hooks yang sudah disediakan.

---

## ✅ Contoh-Contoh Hook-Based Lainnya

### Contoh 1: Menambah Data ke User Dashboard

**Skenario:** Plugin ingin menambahkan "streak" (berapa hari berturut-turut user belajar) ke dashboard.

```python
# plugins_available/gamification/plugin.py

class GamificationPlugin(PluginBase):
    name = "gamification"
    
    @hook(CoreHooks.TEMPLATE_USER_DASHBOARD)
    def add_streak_data(self, request=None, context=None, **kwargs):
        """Tambah streak ke dashboard context"""
        user = request.user if request and request.user.is_authenticated else None
        if not user:
            return {}
        
        streak = self.calculate_streak(user)
        return {
            'learning_streak': streak,
            'streak_message': f"🔥 {streak} hari berturut-turut belajar!"
        }
    
    def calculate_streak(self, user):
        from courses.models import LearningSession
        from django.utils import timezone
        from datetime import timedelta
        
        # Hitung hari berturut-turut dengan activity
        today = timezone.now().date()
        streak = 0
        
        for i in range(100):  # Max 100 days
            check_date = today - timedelta(days=i)
            has_activity = LearningSession.objects.filter(
                enrollment__student=user,
                started_at__date=check_date
            ).exists()
            
            if has_activity:
                streak += 1
            else:
                break
        
        return streak
```

**Di template:**
```html
{% if learning_streak %}
<div class="streak-badge">
    {{ streak_message }}
</div>
{% endif %}
```

---

### Contoh 2: Validasi Sebelum Enrollment

**Skenario:** Plugin memvalidasi apakah user boleh enroll (misal: cek prerequisite course).

```python
# plugins_available/prerequisites/plugin.py

class PrerequisitesPlugin(PluginBase):
    name = "prerequisites"
    
    @hook(CoreHooks.COURSE_ENROLLING, priority=1)  # Early priority
    def check_prerequisites(self, user=None, course=None, **kwargs):
        """
        Validasi prerequisite sebelum enrollment.
        Return dict dengan 'allowed' key.
        """
        if not user or not course:
            return {'allowed': True}
        
        # Check if course has prerequisites
        prerequisites = self.get_prerequisites(course)
        
        for prereq_course in prerequisites:
            # Cek apakah user sudah complete prerequisite
            completed = prereq_course.course_enrollments.filter(
                student=user,
                status='completed'
            ).exists()
            
            if not completed:
                return {
                    'allowed': False,
                    'reason': f'Harus menyelesaikan "{prereq_course.title}" terlebih dahulu',
                    'missing_prerequisite': prereq_course
                }
        
        return {'allowed': True}
    
    def get_prerequisites(self, course):
        from .models import CoursePrerequisite
        return [cp.prerequisite for cp in CoursePrerequisite.objects.filter(course=course)]
```

**Di view enrollment:**
```python
# courses/views.py

def enroll_course(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    
    # Trigger hook - semua plugin bisa validate
    validations = trigger_hook(
        CoreHooks.COURSE_ENROLLING,
        user=request.user,
        course=course
    )
    
    # Cek apakah ada yang tidak allow
    for result in validations:
        if isinstance(result, dict) and not result.get('allowed', True):
            messages.error(request, result.get('reason', 'Tidak dapat mendaftar'))
            return redirect('course_detail', slug=course.slug)
    
    # Proceed with enrollment...
```

---

### Contoh 3: Mengirim Notifikasi Setelah Event

**Skenario:** Plugin mengirim email/push notification saat course completed.

```python
# plugins_available/notifications/plugin.py

class NotificationsPlugin(PluginBase):
    name = "notifications"
    
    @hook(CoreHooks.COURSE_COMPLETED, priority=50)  # After main processing
    def send_completion_notification(self, user=None, course=None, enrollment=None, **kwargs):
        """Kirim notifikasi setelah course selesai"""
        if not user or not course:
            return
        
        # Send email
        self.send_email_notification(user, course)
        
        # Send push notification (jika enabled)
        self.send_push_notification(user, course)
        
        return {'notification_sent': True}
    
    def send_email_notification(self, user, course):
        from django.core.mail import send_mail
        
        send_mail(
            subject=f'🎉 Selamat! Anda telah menyelesaikan {course.title}',
            message=f'Halo {user.first_name},\n\n'
                    f'Selamat! Anda telah berhasil menyelesaikan kursus "{course.title}".\n'
                    f'Sertifikat Anda sudah tersedia di dashboard.',
            from_email='noreply@ta3lem.com',
            recipient_list=[user.email],
            fail_silently=True
        )
    
    def send_push_notification(self, user, course):
        # Integration dengan service push notification
        pass
```

---

### Contoh 4: Inject Script/CSS ke Template

**Skenario:** Plugin menambahkan chat widget di semua halaman.

```python
# plugins_available/live_chat/plugin.py

class LiveChatPlugin(PluginBase):
    name = "live_chat"
    
    default_settings = {
        'widget_position': 'bottom-right',
        'primary_color': '#4F46E5',
        'welcome_message': 'Halo! Ada yang bisa kami bantu?',
    }
    
    @hook(CoreHooks.TEMPLATE_BODY_END)
    def inject_chat_widget(self, request=None, **kwargs):
        """Inject chat widget script di akhir body"""
        settings = self.get_settings()
        
        return f'''
        <div id="live-chat-widget" 
             data-position="{settings['widget_position']}"
             data-color="{settings['primary_color']}">
        </div>
        <script>
            window.LiveChatConfig = {{
                welcomeMessage: "{settings['welcome_message']}",
                userEmail: "{request.user.email if request and request.user.is_authenticated else ''}",
                userName: "{request.user.get_full_name() if request and request.user.is_authenticated else 'Guest'}"
            }};
        </script>
        <script src="/static/live_chat/widget.js" defer></script>
        '''
    
    @hook(CoreHooks.TEMPLATE_HEAD)
    def inject_chat_css(self, **kwargs):
        """Inject CSS untuk chat widget"""
        return '<link rel="stylesheet" href="/static/live_chat/widget.css">'
```

---

### Contoh 5: Modifikasi Data Sebelum Save

**Skenario:** Plugin auto-generate slug atau auto-tag content.

```python
# plugins_available/auto_tags/plugin.py

class AutoTagsPlugin(PluginBase):
    name = "auto_tags"
    
    @hook(CoreHooks.COURSE_CREATING, priority=5)
    def auto_generate_tags(self, course=None, **kwargs):
        """
        Auto-generate tags berdasarkan title dan overview.
        Hook dipanggil sebelum course.save()
        """
        if not course:
            return
        
        # Extract keywords dari title dan overview
        text = f"{course.title} {course.overview}"
        tags = self.extract_keywords(text)
        
        return {'suggested_tags': tags}
    
    def extract_keywords(self, text):
        """Simple keyword extraction"""
        # Bisa pakai NLP library untuk lebih canggih
        stopwords = {'dan', 'atau', 'yang', 'untuk', 'dengan', 'di', 'ke', 'dari'}
        words = text.lower().split()
        keywords = [w for w in words if len(w) > 3 and w not in stopwords]
        return list(set(keywords))[:5]  # Max 5 tags
```

---

## Quick Reference: Hook Pattern

```python
# PATTERN STANDAR:

@hook(CoreHooks.HOOK_NAME, priority=10)
def handler_method(self, **kwargs):
    """
    1. Ekstrak data dari kwargs
    2. Proses data
    3. Return hasil (dict, string, atau None)
    """
    # 1. Extract
    user = kwargs.get('user')
    course = kwargs.get('course')
    
    if not user or not course:
        return None  # Early return jika data tidak lengkap
    
    # 2. Process
    result = self.do_something(user, course)
    
    # 3. Return
    return {
        'key': result,
        'another_key': 'value'
    }
```

**Priority Guidelines:**
- `1-10`: Validasi/blocking (bisa cancel action)
- `10-30`: Main processing
- `30-50`: Side effects (notifications, logging)
- `50+`: Cleanup/analytics
