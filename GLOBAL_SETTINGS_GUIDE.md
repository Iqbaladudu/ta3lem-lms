# 🎛️ Global Settings System - Ta3lem LMS

**Date:** December 26, 2024  
**Status:** ✅ Implemented & Ready

---

## 📊 Overview

Global Settings system memungkinkan admin untuk mengkonfigurasi seluruh platform dari Django Admin tanpa perlu edit code. Sistem ini menggunakan **singleton pattern** untuk ensure hanya satu settings object yang ada.

---

## ✨ Features

### 🏢 Platform Information
- Site Name
- Tagline
- Description
- Contact Email

### 🎛️ Feature Toggles
- ✅ Enable/Disable Subscriptions
- ✅ Enable/Disable One-Time Purchase
- ✅ Enable/Disable Free Courses
- ✅ Enable/Disable Certificates
- ✅ Enable/Disable Course Reviews
- ✅ Enable/Disable Discussion Forums
- ✅ Enable/Disable Waitlist
- ✅ Enable/Disable Instructor Earnings

### 📚 Enrollment Settings
- Email verification requirement
- Auto-enroll for free courses
- Max enrollments per student

### 💳 Subscription Settings
- Trial enabled/disabled
- Trial period (days)
- Grace period (days)
- Auto-renewal

### 💰 Payment & Revenue
- Default currency (IDR/USD/EUR)
- Minimum payout amount
- Platform commission percentage

### 📖 Course Settings
- Default course capacity
- Require course approval
- Min/Max course price

### 📁 Content & Upload Settings
- Max video size (MB)
- Max file size (MB)
- Allowed video formats
- Allowed file formats

### 📧 Notifications
- Enrollment notifications
- Completion notifications
- Subscription notifications
- Payment notifications
- Expiry reminder days

### 🔍 SEO & Analytics
- Meta keywords
- Google Analytics ID
- Facebook Pixel ID

### 📱 Social Media
- Facebook URL
- Twitter URL
- Instagram URL
- LinkedIn URL
- YouTube URL

### 🎨 Landing Page
- Show/hide sections
- Featured courses count

### 🚧 Maintenance Mode
- Enable/disable
- Maintenance message

### ⚙️ Advanced Settings
- Session timeout
- Cache timeout
- Debug mode (⚠️ danger!)

---

## 🚀 How to Use

### 1. Access Django Admin

```
http://your-domain.com/admin/core/globalsettings/
```

Login with superuser credentials.

### 2. Edit Settings

All settings are organized in collapsible fieldsets:
- Click on a section to expand
- Edit values
- Click "Save" at the bottom

### 3. Settings are Applied Immediately!

Changes take effect immediately (cached for 1 hour).

---

## 💻 Usage in Code

### Method 1: Direct Access

```python
from core.models import GlobalSettings

settings = GlobalSettings.get_settings()

# Access any field
site_name = settings.site_name
is_subscriptions_enabled = settings.enable_subscriptions
commission = settings.platform_commission_percentage
```

### Method 2: Utility Functions

```python
from core.utils import get_setting, is_feature_enabled

# Get specific setting
site_name = get_setting('site_name')
currency = get_setting('payment_currency')

# Check if feature is enabled
if is_feature_enabled('subscriptions'):
    # Subscription code
    pass

if is_feature_enabled('certificates'):
    # Certificate generation code
    pass
```

### Method 3: Helper Functions

```python
from core.utils import (
    get_site_info,
    get_payment_settings,
    get_subscription_settings,
    is_maintenance_mode
)

# Get site information
site_info = get_site_info()
print(site_info['site_name'])
print(site_info['contact_email'])

# Get payment settings
payment = get_payment_settings()
currency = payment['currency']
commission = payment['commission_percentage']

# Get subscription settings
sub_settings = get_subscription_settings()
trial_days = sub_settings['trial_days']

# Check maintenance mode
if is_maintenance_mode():
    # Show maintenance page
    pass
```

---

## 🎨 Usage in Templates

Settings are automatically available in **all templates** via context processor:

```django
<!-- Basic access -->
<h1>{{ settings.site_name }}</h1>
<p>{{ settings.site_tagline }}</p>

<!-- Feature checks -->
{% if settings.enable_subscriptions %}
    <div class="subscription-section">
        <!-- Subscription content -->
    </div>
{% endif %}

{% if settings.enable_course_certificates %}
    <a href="{% url 'certificate' %}">Download Certificate</a>
{% endif %}

<!-- Conditional rendering -->
{% if settings.show_testimonials %}
    {% include 'landing/testimonials.html' %}
{% endif %}

<!-- Social media links -->
{% if settings.facebook_url %}
    <a href="{{ settings.facebook_url }}">
        <i class="fab fa-facebook"></i>
    </a>
{% endif %}
```

---

## 🔧 Management Commands

### Initialize Settings

```bash
python manage.py init_settings
```

Creates default settings if they don't exist.

---

## 🎯 Common Use Cases

### 1. Disable a Feature Temporarily

**Admin Panel:**
1. Go to `/admin/core/globalsettings/`
2. Expand "Feature Toggles"
3. Uncheck "Enable subscriptions"
4. Save

**Code will automatically respect this:**
```python
if is_feature_enabled('subscriptions'):
    # This code won't run if disabled
    pass
```

### 2. Change Platform Name

```python
# No code changes needed!
# Just update in admin:
# Platform Information → Site Name
```

Templates will automatically show new name:
```django
<h1>{{ settings.site_name }}</h1>
<!-- Shows updated name immediately -->
```

### 3. Enable Maintenance Mode

**Admin Panel:**
1. Expand "Maintenance Mode"
2. Check "Maintenance mode"
3. Edit "Maintenance message"
4. Save

**In your middleware or view:**
```python
from core.utils import is_maintenance_mode

if is_maintenance_mode():
    return render(request, 'maintenance.html', {
        'message': get_setting('maintenance_message')
    })
```

### 4. Adjust Commission Rates

**Admin Panel:**
1. Expand "Payment & Revenue Settings"
2. Change "Platform commission percentage"
3. Save

**Code automatically uses new rate:**
```python
from core.utils import get_payment_settings

payment_info = get_payment_settings()
commission = payment_info['commission_percentage']
instructor_share = total * (100 - commission) / 100
```

### 5. Configure Trial Period

**Admin Panel:**
1. Expand "Subscription Settings"
2. Change "Subscription trial days"
3. Save

**Subscription service uses it:**
```python
from core.utils import get_subscription_settings

sub_settings = get_subscription_settings()
if sub_settings['trial_enabled']:
    trial_days = sub_settings['trial_days']
    # Create subscription with trial
```

---

## 📊 Settings Categories

### Critical Settings (⚠️ Be Careful)
- `maintenance_mode` - Disables site for users
- `enable_debug_mode` - Security risk in production
- `platform_commission_percentage` - Affects revenue

### Revenue Impact
- `enable_subscriptions` - Core monetization
- `enable_one_time_purchase` - Alternative monetization
- `min_course_price` / `max_course_price` - Price limits

### User Experience
- `auto_enroll_free_courses` - Enrollment friction
- `require_email_verification` - Signup friction
- `show_featured_courses` - Landing page design

### System Performance
- `cache_timeout_seconds` - Performance vs freshness
- `session_timeout_minutes` - Security vs convenience

---

## 🔒 Security Considerations

### 1. Only Superusers Should Access

Settings admin should be restricted to superusers only.

### 2. Never Enable Debug in Production

`enable_debug_mode` should ALWAYS be `False` in production.

### 3. Audit Trail

Settings track `updated_by` and `updated_at` for accountability.

```python
settings = GlobalSettings.get_settings()
print(f"Last updated by: {settings.updated_by}")
print(f"Last updated at: {settings.updated_at}")
```

---

## 🧪 Testing

### Test Settings Access

```python
from core.models import GlobalSettings

# Test 1: Singleton pattern
settings1 = GlobalSettings.get_settings()
settings2 = GlobalSettings.get_settings()
assert settings1.pk == settings2.pk  # Same instance

# Test 2: Caching
from django.core.cache import cache
cache.clear()
settings = GlobalSettings.get_settings()
# Second call should use cache
settings2 = GlobalSettings.get_settings()

# Test 3: Feature checks
assert settings.is_feature_enabled('subscriptions') in [True, False]
```

---

## 🎨 Customization

### Add New Settings

1. **Update Model:**
```python
# core/models.py

class GlobalSettings(models.Model):
    # ... existing fields ...
    
    # Add your new setting
    my_new_setting = models.BooleanField(
        default=True,
        help_text='Description of my setting'
    )
```

2. **Create Migration:**
```bash
python manage.py makemigrations core
python manage.py migrate
```

3. **Update Admin (Optional):**
```python
# core/admin.py

fieldsets = (
    # ... existing fieldsets ...
    ('My New Section', {
        'fields': ('my_new_setting',),
    }),
)
```

4. **Use in Code:**
```python
from core.utils import get_setting

if get_setting('my_new_setting'):
    # Your code
    pass
```

---

## 📝 Best Practices

### 1. Always Use Utility Functions

❌ **Bad:**
```python
from core.models import GlobalSettings
settings = GlobalSettings.objects.first()
value = settings.some_field
```

✅ **Good:**
```python
from core.utils import get_setting
value = get_setting('some_field')
```

**Why?** Utility functions handle caching, errors, and defaults.

### 2. Check Features Before Use

```python
from core.utils import is_feature_enabled

if is_feature_enabled('subscriptions'):
    # Subscription code
    from subscriptions.services import SubscriptionService
    # ...
```

### 3. Provide Fallbacks

```python
site_name = get_setting('site_name', 'Ta3lem LMS')
# If settings fail, still have a default
```

### 4. Cache Template Fragments

```django
{% load cache %}

{% cache 3600 site_info %}
    <h1>{{ settings.site_name }}</h1>
    <p>{{ settings.site_tagline }}</p>
{% endcache %}
```

---

## 🚨 Troubleshooting

### Settings Not Updating

**Problem:** Changed settings but not reflected  
**Solution:** Clear cache
```bash
python manage.py shell
>>> from django.core.cache import cache
>>> cache.delete('global_settings')
>>> exit()
```

### Multiple Settings Objects

**Problem:** Somehow created multiple settings  
**Solution:** Delete extras (keep pk=1)
```python
from core.models import GlobalSettings

# Keep only the first one
GlobalSettings.objects.exclude(pk=1).delete()
```

### Settings Not in Templates

**Problem:** `{{ settings.site_name }}` shows nothing  
**Solution:** Check context processor is registered
```python
# ta3lem/settings/base.py
TEMPLATES = [{
    'OPTIONS': {
        'context_processors': [
            # ...
            'core.context_processors.global_settings',  # ← This
        ],
    },
}]
```

---

## 📚 API Reference

### Model Methods

```python
GlobalSettings.get_settings()
# Returns: GlobalSettings instance (singleton, cached)

settings.is_feature_enabled(feature_name)
# Args: feature_name (str)
# Returns: bool

settings.get_allowed_video_formats_list()
# Returns: list of allowed video formats

settings.get_allowed_file_formats_list()
# Returns: list of allowed file formats
```

### Utility Functions

```python
from core.utils import (
    get_setting,           # Get single setting by key
    is_feature_enabled,    # Check if feature is enabled
    is_maintenance_mode,   # Check maintenance mode
    get_site_info,         # Get site information dict
    get_payment_settings,  # Get payment settings dict
    get_subscription_settings,  # Get subscription settings dict
)
```

---

## ✅ Summary

Global Settings system provides:
- ✅ **Centralized Configuration** - One place for all settings
- ✅ **Admin Interface** - Easy to use, no code changes
- ✅ **Singleton Pattern** - Only one settings object
- ✅ **Cached** - Performance optimized
- ✅ **Template Access** - Available in all templates
- ✅ **Feature Toggles** - Enable/disable features easily
- ✅ **Audit Trail** - Track who changed what
- ✅ **Type Safe** - Proper validation
- ✅ **Documented** - Complete guide

**Access:** http://localhost:8000/admin/core/globalsettings/

**Status:** ✅ Production Ready!

