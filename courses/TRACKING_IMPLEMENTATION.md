# Course Tracking Implementation

## Overview
Implementasi course tracking ini menyediakan sistem lengkap untuk melacak progress siswa dalam mengikuti course, termasuk enrollment, progress content, progress module, dan learning sessions.

## Models yang Digunakan

### 1. CourseEnrollment
Model untuk melacak enrollment siswa dalam course.

**Fields:**
- `student`: Foreign key ke User (siswa yang enrolled)
- `course`: Foreign key ke Course
- `status`: Status enrollment (pending, enrolled, completed, paused)
- `enrolled_on`: Tanggal enrollment
- `completed_on`: Tanggal selesai (jika completed)
- `progress_percentage`: Persentase progress (0-100)
- `last_accessed`: Terakhir kali diakses

**Methods:**
- `calculate_progress()`: Menghitung persentase progress berdasarkan content yang diselesaikan
- `update_progress()`: Update progress dan status jika course selesai
- `get_current_module()`: Mendapatkan module yang sedang dikerjakan

### 2. ContentProgress
Model untuk melacak progress siswa dalam menyelesaikan content.

**Fields:**
- `enrollment`: Foreign key ke CourseEnrollment
- `content`: Foreign key ke Content
- `started_at`: Waktu mulai
- `completed_at`: Waktu selesai
- `is_completed`: Boolean status completion

**Methods:**
- `mark_completed()`: Menandai content sebagai selesai dan trigger update module progress

### 3. ModuleProgress
Model untuk melacak progress siswa dalam menyelesaikan module.

**Fields:**
- `enrollment`: Foreign key ke CourseEnrollment
- `module`: Foreign key ke Module
- `started_at`: Waktu mulai
- `completed_at`: Waktu selesai
- `is_completed`: Boolean status completion

**Methods:**
- `calculate_completion()`: Mengecek apakah semua content dalam module sudah selesai
- `mark_completed()`: Menandai module sebagai selesai dan trigger update course progress

### 4. LearningSession
Model untuk melacak session belajar siswa.

**Fields:**
- `enrollment`: Foreign key ke CourseEnrollment
- `content`: Foreign key ke Content (optional)
- `started_at`: Waktu mulai session
- `ended_at`: Waktu selesai session

**Methods:**
- `end_session()`: Mengakhiri session dan menghitung durasi

## Views Implementation

### Student Views

#### 1. StudentEnrollCourseView
**URL:** `/courses/student/<pk>/enroll/`
**Method:** POST
**Purpose:** Handle enrollment siswa ke course

**Flow:**
1. Get atau create CourseEnrollment
2. Tambahkan siswa ke course.students (M2M field)
3. Create ModuleProgress untuk module pertama
4. Redirect ke student_course_detail

#### 2. StudentCourseListView
**URL:** `/courses/student/courses/`
**Template:** `courses/student/course_list.html`
**Purpose:** Menampilkan daftar course yang sudah di-enroll siswa

**Context:**
- `enrollments`: QuerySet CourseEnrollment
- `total_courses`: Jumlah total course
- `active_courses`: Jumlah course aktif
- `completed_courses`: Jumlah course selesai
- `avg_progress`: Rata-rata progress

**Features:**
- Filter berdasarkan status (enrolled, completed, paused)
- Pagination (10 items per page)
- Statistics dashboard

#### 3. StudentCourseDetailView
**URL:** `/courses/student/<pk>/`
**Template:** `courses/student/course_detail.html`
**Purpose:** Menampilkan detail course dan progress siswa

**Context:**
- `course`: Course object
- `enrollment`: CourseEnrollment object
- `modules_data`: List of modules dengan progress info
- `current_module`: Module yang sedang dikerjakan

**Features:**
- Auto-create enrollment jika belum ada
- Update last_accessed timestamp
- Tampilkan progress per module
- Tampilkan completion percentage per module

#### 4. StudentModuleDetailView
**URL:** `/courses/student/<pk>/module/<module_pk>/`
**Template:** `courses/student/module_detail.html`
**Purpose:** Menampilkan detail module dan list content

**Context:**
- `module`: Module object
- `enrollment`: CourseEnrollment object
- `module_progress`: ModuleProgress object
- `contents_data`: List of contents dengan progress
- `previous_module`: Module sebelumnya
- `next_module`: Module selanjutnya

**Features:**
- Auto-create ModuleProgress jika belum ada
- Tampilkan status completion per content
- Navigation ke module sebelum/sesudah

#### 5. StudentContentView
**URL:** `/courses/student/<pk>/module/<module_pk>/content/<content_pk>/`
**Template:** `courses/student/content_detail.html`
**Purpose:** Menampilkan content dan track learning session

**Context:**
- `content`: Content object
- `enrollment`: CourseEnrollment object
- `content_progress`: ContentProgress object
- `learning_session`: LearningSession object
- `previous_content`: Content sebelumnya
- `next_content`: Content selanjutnya

**Features:**
- Auto-create ContentProgress jika belum ada
- Membuat LearningSession baru setiap kali content diakses
- Navigation ke content sebelum/sesudah

#### 6. MarkContentCompleteView
**URL:** `/courses/student/<pk>/module/<module_pk>/content/<content_pk>/complete/`
**Method:** POST
**Purpose:** Menandai content sebagai selesai

**Flow:**
1. Get atau create ContentProgress
2. Mark content as completed
3. End active learning sessions
4. Check dan update module completion
5. Return JSON response untuk AJAX atau redirect ke content selanjutnya

**Response (JSON):**
```json
{
    "success": true,
    "progress_percentage": 45.50,
    "module_completed": false,
    "course_completed": false
}
```

#### 7. StudentDashboardView
**URL:** `/courses/student/dashboard/`
**Template:** `courses/student/dashboard.html`
**Purpose:** Dashboard siswa dengan statistik lengkap

**Context:**
- `enrollments`: Recent enrollments
- `total_courses`: Total course enrolled
- `active_courses`: Jumlah course aktif
- `completed_courses`: Jumlah course selesai
- `avg_progress`: Rata-rata progress
- `recent_sessions`: 10 learning sessions terakhir
- `in_progress`: 5 course yang sedang dikerjakan
- `total_learning_time`: Total waktu belajar (dalam jam)
- `total_modules_completed`: Total module selesai
- `total_contents_completed`: Total content selesai

### Instructor Views

#### 8. InstructorCourseAnalyticsView
**URL:** `/courses/analytics/<pk>/`
**Template:** `courses/instructor/course_analytics.html`
**Purpose:** Analytics course untuk instructor

**Context:**
- `course`: Course object
- `enrollments`: Semua enrollment untuk course ini
- `total_students`: Total siswa enrolled
- `active_students`: Siswa aktif
- `completed_students`: Siswa yang selesai
- `avg_progress`: Rata-rata progress siswa
- `modules_data`: Statistik completion per module
- `recent_enrollments`: 10 enrollment terbaru
- `total_sessions`: Total learning sessions

**Features:**
- Hanya menampilkan course milik instructor
- Module completion rates
- Student progress overview

#### 9. StudentProgressDetailView
**URL:** `/courses/analytics/<pk>/student/<student_id>/`
**Template:** `courses/instructor/student_progress.html`
**Purpose:** Detail progress siswa tertentu dalam course (untuk instructor)

**Context:**
- `course`: Course object
- `enrollment`: CourseEnrollment object
- `student`: User object (siswa)
- `modules_progress`: Detail progress per module
- `learning_sessions`: 20 learning sessions terakhir

**Features:**
- Hanya accessible oleh owner course
- Detail progress per module dan content
- Learning session history

## URL Patterns

### Student URLs
```python
# Dashboard
/courses/student/dashboard/

# Course list
/courses/student/courses/
/courses/student/courses/?status=enrolled

# Enrollment
/courses/student/<pk>/enroll/

# Course detail
/courses/student/<pk>/

# Module detail
/courses/student/<pk>/module/<module_pk>/

# Content detail
/courses/student/<pk>/module/<module_pk>/content/<content_pk>/

# Mark complete
/courses/student/<pk>/module/<module_pk>/content/<content_pk>/complete/
```

### Instructor URLs
```python
# Course analytics
/courses/analytics/<pk>/

# Student progress detail
/courses/analytics/<pk>/student/<student_id>/
```

## Usage Examples

### 1. Enrollment Flow
```python
# User mengakses course detail dan klik enroll
POST /courses/student/1/enroll/

# Sistem akan:
# - Create CourseEnrollment
# - Add student ke course.students
# - Create ModuleProgress untuk module pertama
# - Redirect ke /courses/student/1/
```

### 2. Learning Flow
```python
# 1. Student membuka course
GET /courses/student/1/

# 2. Student membuka module
GET /courses/student/1/module/1/

# 3. Student membuka content
GET /courses/student/1/module/1/content/1/
# Sistem create LearningSession

# 4. Student menyelesaikan content
POST /courses/student/1/module/1/content/1/complete/
# Sistem:
# - Mark ContentProgress as completed
# - End LearningSession
# - Check dan update ModuleProgress
# - Update CourseEnrollment progress
```

### 3. Tracking Query Examples
```python
# Get student's enrollments
enrollments = CourseEnrollment.objects.filter(student=user)

# Get active courses
active_courses = enrollments.filter(status='enrolled')

# Get completed contents in a course
completed_contents = ContentProgress.objects.filter(
    enrollment__student=user,
    enrollment__course=course,
    is_completed=True
)

# Get learning time for a course
sessions = LearningSession.objects.filter(
    enrollment__student=user,
    enrollment__course=course,
    ended_at__isnull=False
)
total_time = sum([
    (s.ended_at - s.started_at).total_seconds() 
    for s in sessions
])

# Get course completion rate for instructor
total_students = course.students.count()
completed = CourseEnrollment.objects.filter(
    course=course, 
    status='completed'
).count()
completion_rate = (completed / total_students * 100) if total_students > 0 else 0
```

## Template Requirements

Berikut adalah template yang perlu dibuat:

### Student Templates
1. `courses/student/course_list.html` - List enrollments
2. `courses/student/course_detail.html` - Course detail dengan module list
3. `courses/student/module_detail.html` - Module detail dengan content list
4. `courses/student/content_detail.html` - Content detail
5. `courses/student/dashboard.html` - Student dashboard

### Instructor Templates
6. `courses/instructor/course_analytics.html` - Course analytics
7. `courses/instructor/student_progress.html` - Student progress detail

## AJAX/HTMX Support

Views mendukung AJAX/HTMX requests:

### MarkContentCompleteView
```javascript
// AJAX request example
fetch('/courses/student/1/module/1/content/1/complete/', {
    method: 'POST',
    headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrfToken
    }
})
.then(response => response.json())
.then(data => {
    console.log('Progress:', data.progress_percentage);
    console.log('Module completed:', data.module_completed);
    console.log('Course completed:', data.course_completed);
});
```

### HTMX example
```html
<button 
    hx-post="/courses/student/1/module/1/content/1/complete/"
    hx-trigger="click"
    hx-swap="outerHTML">
    Mark as Complete
</button>
```

## Database Optimization

### Indexes
Models sudah dilengkapi dengan indexes untuk performa optimal:

```python
# CourseEnrollment indexes
indexes = [
    models.Index(fields=['student', 'status']),
    models.Index(fields=['course', 'status']),
    models.Index(fields=['-last_accessed']),
]

# ContentProgress indexes
indexes = [
    models.Index(fields=['enrollment', 'is_completed']),
    models.Index(fields=['content', 'is_completed']),
]

# ModuleProgress indexes
indexes = [
    models.Index(fields=['enrollment', 'is_completed']),
    models.Index(fields=['module', 'is_completed']),
]

# LearningSession indexes
indexes = [
    models.Index(fields=['enrollment', 'started_at']),
    models.Index(fields=['content', '-started_at']),
]
```

### Query Optimization
Views menggunakan `select_related()` dan `prefetch_related()` untuk mengurangi database queries:

```python
# Example in StudentCourseListView
queryset = CourseEnrollment.objects.filter(
    student=self.request.user
).select_related('course', 'course__subject')

# Example in StudentCourseDetailView
modules = course.modules.prefetch_related('contents').all()
```

## Testing

### Unit Test Examples
```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from courses.models import Course, Module, Content, CourseEnrollment

User = get_user_model()

class CourseTrackingTestCase(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='password',
            role='student'
        )
        self.course = Course.objects.create(...)
        
    def test_enrollment_creation(self):
        enrollment = CourseEnrollment.objects.create(
            student=self.student,
            course=self.course
        )
        self.assertEqual(enrollment.status, 'enrolled')
        self.assertEqual(enrollment.progress_percentage, 0.00)
        
    def test_progress_calculation(self):
        enrollment = CourseEnrollment.objects.create(
            student=self.student,
            course=self.course
        )
        # Create and complete content
        # Assert progress calculation
```

## Security Considerations

1. **Authentication Required**: Semua views menggunakan `LoginRequiredMixin`
2. **Authorization**: 
   - Student hanya bisa akses course yang sudah di-enroll
   - Instructor hanya bisa akses analytics untuk course miliknya
3. **CSRF Protection**: POST requests dilindungi CSRF token
4. **Query Filtering**: Semua queries difilter berdasarkan user

## Performance Tips

1. **Caching**: Gunakan caching untuk data yang jarang berubah
2. **Pagination**: Semua list views menggunakan pagination
3. **Lazy Loading**: Load content on-demand
4. **Batch Updates**: Gunakan `bulk_create()` dan `bulk_update()` untuk operasi batch

## Future Enhancements

1. **Certificates**: Generate certificate saat course selesai
2. **Badges**: Award badges untuk achievements
3. **Leaderboards**: Ranking siswa berdasarkan progress
4. **Notifications**: Email/push notifications untuk milestones
5. **Export Reports**: Export progress reports ke PDF/Excel
6. **Time-based Analytics**: Learning patterns dan optimal learning times
7. **Recommendations**: Course recommendations berdasarkan history
8. **Gamification**: Points, levels, dan rewards system

## Troubleshooting

### Common Issues

1. **Progress tidak update**
   - Check apakah `mark_completed()` dipanggil
   - Verify ContentProgress created
   - Check module completion calculation

2. **Enrollment duplicate**
   - Gunakan `get_or_create()` untuk prevent duplicates
   - Check unique constraint di model

3. **Learning session tidak berakhir**
   - Call `end_session()` saat user meninggalkan content
   - Implement timeout mechanism

## Migration Commands

```bash
# Create migrations
python manage.py makemigrations courses

# Apply migrations
python manage.py migrate courses

# Load fixtures (jika ada)
python manage.py loaddata courses/fixtures/courses.json
```

## Conclusion

Implementasi course tracking ini menyediakan foundation lengkap untuk sistem LMS dengan fitur:
- ✅ Student enrollment dan progress tracking
- ✅ Content dan module completion tracking
- ✅ Learning session tracking
- ✅ Student dashboard dengan analytics
- ✅ Instructor analytics dan reporting
- ✅ AJAX/HTMX support
- ✅ Optimized queries dan indexes
- ✅ Security dan authorization

Template HTML perlu dibuat sesuai dengan struktur context yang sudah disediakan oleh views.

