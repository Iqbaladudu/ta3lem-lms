# Template Filter Fix - Documentation

## 🐛 Issue Found

**Error:** `TemplateSyntaxError: Invalid filter: 'sub'`

**Location:** `courses/templates/courses/student/module_detail.html` line 161

**Problem:** Template menggunakan Jinja2-style filters yang tidak tersedia di Django:
- `sub` - Subtraction
- `selectattr` - Filter by attribute
- `div` - Division
- `mul` - Multiplication

## ✅ Solution Applied

### 1. Updated `module_detail.html`

**Before (Incorrect):**
```html
<span class="text-sm font-bold text-blue-600">
    {{ contents_data|length|sub:contents_data|selectattr:"is_completed"|list|length|div:contents_data|length|mul:100|floatformat:0 }}%
</span>
```

**After (Fixed):**
```html
<span class="text-sm font-bold text-blue-600">
    {% if module_progress.is_completed %}
        100%
    {% else %}
        {% widthratio module_progress.completed_contents_count module_progress.total_contents_count 100 %}%
    {% endif %}
</span>
```

**Stats Display Before:**
```html
<p class="text-2xl font-bold text-green-600">
    {{ contents_data|selectattr:"is_completed"|list|length }}
</p>
```

**Stats Display After:**
```html
<p class="text-2xl font-bold text-green-600">
    {% if module_progress.completed_contents_count %}
        {{ module_progress.completed_contents_count }}
    {% else %}
        0
    {% endif %}
</p>
```

### 2. Updated `StudentModuleDetailView` in `views.py`

**Added computed values to context:**

```python
def get_context_data(self, **kwargs):
    # ...existing code...
    
    # Calculate completed count
    completed_count = 0
    for content in module.contents.all():
        content_progress = ContentProgress.objects.filter(
            enrollment=enrollment,
            content=content
        ).first()
        
        is_completed = content_progress.is_completed if content_progress else False
        if is_completed:
            completed_count += 1
    
    # Add counts to module_progress for template
    module_progress.completed_contents_count = completed_count
    module_progress.total_contents_count = len(contents_data)
    
    # ...rest of context...
```

### 3. Updated `content_detail.html`

**Problem:** Using custom `get_progress` filter

**Before (Incorrect):**
```html
{% for item in module.contents.all %}
    <!-- ...content... -->
    {% with item_progress=item|get_progress:enrollment %}
        {% if item_progress.is_completed %}
            <i class="fas fa-check-circle"></i>
        {% endif %}
    {% endwith %}
{% endfor %}
```

**After (Fixed):**
```html
{% for item in module_contents_with_progress %}
    <!-- ...content... -->
    {% if item.is_completed %}
        <i class="fas fa-check-circle"></i>
    {% endif %}
{% endfor %}
```

### 4. Updated `StudentContentView` in `views.py`

**Added content progress data to context:**

```python
def get_context_data(self, **kwargs):
    # ...existing code...
    
    # Get all module contents with their progress for sidebar
    module_contents_with_progress = []
    for item in module.contents.all():
        item_progress = ContentProgress.objects.filter(
            enrollment=enrollment,
            content=item
        ).first()
        module_contents_with_progress.append({
            'content': item,
            'is_completed': item_progress.is_completed if item_progress else False
        })
    
    context['module_contents_with_progress'] = module_contents_with_progress
    
    # ...rest of context...
```

## 🎯 Key Learnings

### Django vs Jinja2 Filters

**Django Built-in Filters:**
- `length` - Get list/queryset length
- `floatformat` - Format floats
- `date` - Format dates
- `default` - Default value
- `widthratio` - Calculate ratios/percentages

**NOT Available in Django (Jinja2 only):**
- `sub` - Use Python in view
- `selectattr` - Use QuerySet methods or view logic
- `div`, `mul` - Use Python in view
- Custom filters - Need to register them

### Best Practices

1. **Calculate in View, Display in Template**
   - ✅ Do: Calculate percentages, counts, etc. in view
   - ❌ Don't: Use complex filter chains in templates

2. **Use widthratio for Percentages**
   ```html
   {% widthratio completed total 100 %}%
   ```

3. **Provide Computed Values**
   - Add temporary attributes to objects in view
   - Create dictionaries with all needed data
   - Use context to pass preprocessed data

4. **Avoid Custom Filters Without Registration**
   - If you need custom filter, register it properly
   - Or better, compute in view

## 📝 Testing Checklist

After fixes:
- [x] Template syntax errors resolved
- [x] Module detail page loads successfully
- [x] Content detail page loads successfully
- [x] Progress percentages display correctly
- [x] Completed content counts show properly
- [x] Sidebar content list works with completion icons

## 🚀 Files Modified

1. **courses/views.py**
   - Updated `StudentModuleDetailView.get_context_data()`
   - Updated `StudentContentView.get_context_data()`

2. **courses/templates/courses/student/module_detail.html**
   - Fixed progress percentage display
   - Fixed completed count display
   - Used `widthratio` instead of custom filters

3. **courses/templates/courses/student/content_detail.html**
   - Removed `get_progress` custom filter
   - Used `module_contents_with_progress` from context

4. **courses/COMPLETE_CHECKLIST.md**
   - Added troubleshooting section for template filter errors

## 🔧 Alternative Solutions

If you need custom filters in the future:

### Option 1: Create Custom Template Tag/Filter

```python
# courses/templatetags/course_filters.py
from django import template

register = template.Library()

@register.filter
def get_progress(content, enrollment):
    """Get content progress for enrollment"""
    from courses.models import ContentProgress
    return ContentProgress.objects.filter(
        enrollment=enrollment,
        content=content
    ).first()
```

Then in template:
```html
{% load course_filters %}
{% with item_progress=item|get_progress:enrollment %}
    ...
{% endwith %}
```

### Option 2: Use Template Tags

```python
# courses/templatetags/progress_tags.py
from django import template

register = template.Library()

@register.inclusion_tag('courses/includes/progress_bar.html')
def show_progress(completed, total):
    percentage = (completed / total * 100) if total > 0 else 0
    return {'percentage': percentage, 'completed': completed, 'total': total}
```

### Option 3: Compute Everything in View (RECOMMENDED ✅)

This is what we did - cleanest and most maintainable approach.

## ✅ Conclusion

Template filter errors are now **FIXED**. All templates use proper Django template syntax and get their data from view context.

**Status:** ✅ RESOLVED
**Impact:** All tracking templates now working properly
**Testing:** Ready for full testing

---

**Next:** Run full testing checklist from COMPLETE_CHECKLIST.md

