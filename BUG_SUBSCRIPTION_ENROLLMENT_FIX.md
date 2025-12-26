# Bug Fix: Subscription-Only Course Enrollment Bypass

## Problem
Kursus dengan `pricing_type='subscription_only'` atau `both` (saat user punya subscription) **mengabaikan enrollment_type** (approval/restricted) dan langsung mem-bypass approval flow.

### Behavior Sebelum Fix
```python
# subscription_only - LANGSUNG ENROLLED tanpa cek enrollment_type
if SubscriptionService.user_has_active_subscription(user):
    enrollment = CourseEnrollment.objects.create(
        status='enrolled',  # ❌ SELALU enrolled
        ...
    )
    course.students.add(user)  # ❌ LANGSUNG ditambahkan
```

Ini berarti:
- ✅ Kursus FREE dengan `enrollment_type='approval'` → perlu approval ✓
- ❌ Kursus SUBSCRIPTION_ONLY dengan `enrollment_type='approval'` → **BYPASS approval** ✗
- ❌ Kursus BOTH dengan subscription + `enrollment_type='approval'` → **BYPASS approval** ✗

## Root Cause
Di `courses/views.py` pada `StudentEnrollCourseView`, enrollment untuk subscription tidak mempertimbangkan `course.enrollment_type`.

## Solution
Implementasi logic yang sama dengan FREE course:

```python
# Determine enrollment status based on enrollment_type
enrollment_status = 'enrolled' if course.enrollment_type == 'open' else 'pending'

enrollment_data = {
    'status': enrollment_status,
    'payment_status': 'subscription',
    'access_type': 'subscription',
}

if course.enrollment_type in ['approval', 'restricted']:
    enrollment_data['approval_requested_at'] = timezone.now()

enrollment = CourseEnrollment.objects.create(**enrollment_data)

if course.enrollment_type == 'open':
    # Direct enrollment
    course.students.add(user)
    messages.success(...)
    return redirect('student_course_detail', ...)
else:
    # Requires approval
    messages.info(request, 'Permintaan pendaftaran telah dikirim.')
    return redirect('course_detail', ...)
```

## Changes Made

### File: `courses/views.py`

1. **SUBSCRIPTION_ONLY branch (line ~645)**
   - ✅ Menambahkan pengecekan `enrollment_type`
   - ✅ Set `status='pending'` jika bukan `open`
   - ✅ Set `approval_requested_at` jika perlu approval
   - ✅ Hanya `course.students.add()` jika `enrollment_type='open'`
   - ✅ Tampilkan pesan berbeda untuk pending vs enrolled

2. **BOTH branch (line ~694)**
   - ✅ Implementasi logic yang sama untuk consistency

## Testing Checklist

### Test Case 1: Subscription-Only + Open Enrollment
- [x] User dengan subscription aktif
- [x] Course: `pricing_type='subscription_only'`, `enrollment_type='open'`
- [x] Expected: Langsung enrolled, bisa akses konten
- [x] Result: ✅ PASS

### Test Case 2: Subscription-Only + Approval Required
- [x] User dengan subscription aktif
- [x] Course: `pricing_type='subscription_only'`, `enrollment_type='approval'`
- [x] Expected: Status `pending`, perlu approval instructor
- [x] Result: ✅ PASS (FIXED)

### Test Case 3: Subscription-Only + No Subscription
- [x] User tanpa subscription
- [x] Course: `pricing_type='subscription_only'`
- [x] Expected: Redirect ke subscription plans
- [x] Result: ✅ PASS

### Test Case 4: Both + Subscription + Approval
- [x] User dengan subscription aktif
- [x] Course: `pricing_type='both'`, `enrollment_type='approval'`
- [x] Expected: Status `pending`, perlu approval
- [x] Result: ✅ PASS (FIXED)

### Test Case 5: Both + No Subscription + Approval
- [x] User tanpa subscription
- [x] Course: `pricing_type='both'`, `enrollment_type='approval'`
- [x] Expected: Redirect ke payment checkout
- [x] Result: ✅ PASS

## Security Impact
✅ **POSITIVE** - Fix menutup security hole dimana subscription user bisa bypass approval requirements.

## Backward Compatibility
⚠️ **BREAKING CHANGE**: Existing subscription enrollments yang di-bypass approval flow akan tetap `enrolled`. New enrollments akan mengikuti approval flow yang benar.

## Related Files
- `courses/views.py` - StudentEnrollCourseView
- `courses/models.py` - Course.enrollment_type choices
- `courses/access_service.py` - CourseAccessService (tidak perlu diubah)

## Status
✅ **FIXED** - Subscription enrollment sekarang respect enrollment_type settings
