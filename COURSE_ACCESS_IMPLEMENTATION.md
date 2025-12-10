# Implementasi Course Access Control

## Ringkasan

Course hanya bisa diakses/dibuka oleh student jika memenuhi kondisi:

1. **Status enrollment**: `enrolled`, `completed`, atau `paused`
2. **Status pembayaran**: `paid` atau `free`

## Perubahan yang Dilakukan

### 1. Model - CourseEnrollment.can_access_course()

**File**: `courses/models.py`

Menambahkan method `can_access_course()` pada model `CourseEnrollment`:

```python
def can_access_course(self):
    """
    Returns True if the course can be accessed/opened by the user according to:
    - status is 'enrolled', 'completed', or 'paused'
    - payment_status is 'paid' or 'free'
    """
    return (
            self.status in ['enrolled', 'completed', 'paused'] and
            self.payment_status in ['paid', 'free']
    )
```

### 2. Views - Enforcement di StudentCourseDetailView

**File**: `courses/views.py`

Memperbarui `StudentCourseDetailView.get_context_data()` untuk memeriksa akses setelah enrollment didapat/dibuat:

```python
def get_context_data(self, **kwargs):
    # ... existing code ...

    # Get or create enrollment
    enrollment, created = CourseEnrollment.objects.get_or_create(
        student=self.request.user,
        course=course,
        defaults={'status': 'enrolled'}
    )

    # Check if user can access this course
    if not enrollment.can_access_course():
        raise Http404("You do not have access to this course. Please check your enrollment and payment status.")

    # ... rest of code ...
```

### 3. Views - Enforcement di StudentModuleDetailView

**File**: `courses/views.py`

Menambahkan pengecekan yang sama di `StudentModuleDetailView.get_context_data()`:

```python
def get_context_data(self, **kwargs):
    # ... existing code ...

    enrollment = get_object_or_404(
        CourseEnrollment,
        student=self.request.user,
        course=course
    )

    # Check if user can access this course
    if not enrollment.can_access_course():
        raise Http404("You do not have access to this course. Please check your enrollment and payment status.")

    # ... rest of code ...
```

### 4. Views - Enforcement di StudentContentView

**File**: `courses/views.py`

Menambahkan pengecekan yang sama di `StudentContentView.get_context_data()`:

```python
def get_context_data(self, **kwargs):
    # ... existing code ...

    enrollment = get_object_or_404(
        CourseEnrollment,
        student=self.request.user,
        course=course
    )

    # Check if user can access this course content
    if not enrollment.can_access_course():
        raise Http404("You do not have access to this course content. Please check your enrollment and payment status.")

    # ... rest of code ...
```

### 5. Template - Visual Indicator di Course List

**File**: `courses/templates/courses/student/course_list.html`

Menambahkan:

- Badge status untuk semua status enrollment (pending, withdrawn, rejected, dll)
- Warning box untuk course yang tidak bisa diakses
- Tombol disabled untuk course yang tidak bisa diakses

```html
<!-- Access Warning -->
{% if not enrollment.can_access_course %}
<div class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
    <div class="flex items-start">
        <i class="fas fa-exclamation-triangle text-red-500 mt-0.5 mr-2"></i>
        <div class="text-xs text-red-700">
            <strong>Akses Ditolak:</strong>
            {% if enrollment.status not in 'enrolled,completed,paused' %}
            Status enrollment tidak valid.
            {% elif enrollment.payment_status not in 'paid,free' %}
            Pembayaran belum lunas ({{ enrollment.get_payment_status_display }}).
            {% endif %}
        </div>
    </div>
</div>
{% endif %}

<!-- Action Button -->
{% if enrollment.can_access_course %}
<a href="{% url 'student_course_detail' enrollment.course.pk %}" ...>
    Lanjutkan Belajar
</a>
{% else %}
<button disabled ...>
    <i class="fas fa-lock mr-2"></i>Tidak Dapat Diakses
</button>
{% endif %}
```

### 6. Tests

**File**: `courses/tests.py`

Menambahkan comprehensive tests:

- `CourseEnrollmentAccessTestCase`: Test model-level logic
- `CourseAccessViewTestCase`: Test view-level enforcement

## Validasi

### Model Tests (✅ PASSED)

```bash
$ python test_access_quick.py
✓ Enrolled + Free: can_access = True
✗ Pending + Free: can_access = False  
✗ Enrolled + Pending Payment: can_access = False
✓ Paused + Paid: can_access = True
✅ All model tests passed!
```

### Skenario yang Ditest

| Status Enrollment | Payment Status | Can Access? |
|-------------------|----------------|-------------|
| enrolled          | free           | ✅ Yes       |
| enrolled          | paid           | ✅ Yes       |
| completed         | free           | ✅ Yes       |
| completed         | paid           | ✅ Yes       |
| paused            | free           | ✅ Yes       |
| paused            | paid           | ✅ Yes       |
| pending           | free           | ❌ No        |
| pending           | paid           | ❌ No        |
| withdrawn         | free           | ❌ No        |
| rejected          | free           | ❌ No        |
| enrolled          | pending        | ❌ No        |
| enrolled          | failed         | ❌ No        |
| enrolled          | refunded       | ❌ No        |

## User Experience

### Dashboard Student

- Course yang tidak bisa diakses akan ditampilkan dengan:
    - Warning box berwarna merah dengan penjelasan
    - Button disabled dengan icon lock
    - Badge status yang sesuai

### Akses Course

- Jika user mencoba mengakses course yang tidak valid:
    - Akan mendapat HTTP 404 error
    - Pesan error yang informatif

## Next Steps (Optional)

1. Tambahkan logging untuk tracking akses yang ditolak
2. Tambahkan notification kepada user ketika status berubah
3. Tambahkan admin action untuk bulk update status enrollment
4. Tambahkan payment gateway integration untuk update payment_status otomatis

