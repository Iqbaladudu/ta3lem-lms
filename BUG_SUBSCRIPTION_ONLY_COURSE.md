# Bug Fix: Subscription-Only Course Access

## Masalah
Course dengan `pricing_type='subscription_only'` bisa dienroll oleh user yang belum berlangganan, sehingga mendapat akses gratis.

## Root Cause
1. `StudentEnrollCourseView` menggunakan logika lama yang langsung menambahkan user ke `course.students` tanpa validasi subscription
2. Template `course/detail.html` tidak membedakan tampilan untuk subscription-only courses
3. Tidak ada validasi akses subscription saat user mencoba masuk ke course content

## Solusi Implementasi

### 1. Update `StudentEnrollCourseView` (users/views.py)
```python
def form_valid(self, form):
    # Cek pricing_type dan handle sesuai jenisnya:
    
    if pricing_type == 'subscription_only':
        # Harus punya subscription aktif
        subscription = SubscriptionService.get_active_subscription(user)
        if subscription:
            EnrollmentService.enroll_with_subscription(user, course, subscription)
        else:
            # Redirect ke halaman subscription
            return redirect('subscription_plans')
    
    elif pricing_type == 'free':
        EnrollmentService.enroll_free(user, course)
    
    elif pricing_type == 'one_time':
        # Redirect ke payment
        return redirect('course_detail', pk=course.id)
    
    elif pricing_type == 'both':
        # User harus pilih: beli atau subscribe
        return redirect('course_detail', pk=course.id)
```

### 2. Update Template `course/detail.html`
Tambahkan conditional rendering untuk subscription-only courses:

```html
{% if course.pricing_type == 'subscription_only' %}
    <!-- Tampilkan badge "Khusus Pelanggan" -->
    <!-- Button redirect ke subscription_plans -->
    <a href="{% url 'subscription_plans' %}">
        Lihat Paket Langganan
    </a>

{% elif course.pricing_type == 'both' %}
    <!-- Tampilkan 2 opsi: Beli Sekali atau Berlangganan -->
    <button>Beli Sekali - Rp X</button>
    <a href="{% url 'subscription_plans' %}">Atau Berlangganan</a>

{% else %}
    <!-- Free atau one_time: tampilan normal -->
{% endif %}
```

### 3. Update `StudentCourseDetailView` (users/views.py)
Tambahkan validasi akses di `dispatch()`:

```python
def dispatch(self, request, *args, **kwargs):
    # Check access menggunakan CourseAccessService
    can_access, reason = CourseAccessService.can_access_course(user, course)
    
    if not can_access:
        if reason == 'subscription_expired':
            # Redirect ke subscription plans
            return redirect('subscription_plans')
        elif reason == 'not_enrolled':
            return redirect('course_detail', pk=course.id)
    
    return super().dispatch(request, *args, **kwargs)
```

## Testing
1. ✅ User tanpa subscription tidak bisa enroll ke subscription-only course
2. ✅ User diarahkan ke halaman subscription plans
3. ✅ User dengan subscription aktif bisa enroll dan akses course
4. ✅ User yang subscription-nya expired kehilangan akses
5. ✅ Template menampilkan UI yang sesuai untuk setiap pricing_type

## File yang Diubah
1. `/users/views.py` - StudentEnrollCourseView dan StudentCourseDetailView
2. `/courses/templates/courses/course/detail.html` - UI untuk enrollment

## Dampak
- ✅ Subscription-only courses sekarang benar-benar memerlukan subscription aktif
- ✅ User experience lebih jelas dengan arahan ke subscription plans
- ✅ Tidak ada lagi akses gratis yang tidak sengaja
