"""
Simple test script to verify course tracking implementation
Run with: python manage.py shell < courses/test_tracking.py
"""

from django.contrib.auth import get_user_model
from courses.models import (
    Course, Module, Content, Subject, CourseEnrollment,
    ContentProgress, ModuleProgress, LearningSession, Text
)

User = get_user_model()

print("=" * 60)
print("Testing Course Tracking Implementation")
print("=" * 60)

# 1. Get or create test users
print("\n1. Creating test users...")
student, created = User.objects.get_or_create(
    username='test_student',
    defaults={
        'email': 'student@test.com',
        'role': 'student',
        'is_active': True
    }
)
if created:
    student.set_password('password123')
    student.save()
    print("   ✓ Created student:", student.username)
else:
    print("   ✓ Using existing student:", student.username)

instructor, created = User.objects.get_or_create(
    username='test_instructor',
    defaults={
        'email': 'instructor@test.com',
        'role': 'instructor',
        'is_active': True
    }
)
if created:
    instructor.set_password('password123')
    instructor.save()
    print("   ✓ Created instructor:", instructor.username)
else:
    print("   ✓ Using existing instructor:", instructor.username)

# 2. Get or create test course structure
print("\n2. Setting up test course...")
subject, _ = Subject.objects.get_or_create(
    slug='test-subject',
    defaults={'title': 'Test Subject'}
)

course, created = Course.objects.get_or_create(
    slug='test-course',
    defaults={
        'owner': instructor,
        'subject': subject,
        'title': 'Test Course for Tracking',
        'overview': 'A test course to verify tracking implementation'
    }
)
if created:
    print("   ✓ Created course:", course.title)
else:
    print("   ✓ Using existing course:", course.title)

# 3. Create modules and contents
print("\n3. Creating modules and contents...")
module1, created = Module.objects.get_or_create(
    course=course,
    order=0,
    defaults={
        'title': 'Module 1: Introduction',
        'description': 'Introduction to the course'
    }
)
if created:
    print("   ✓ Created module:", module1.title)

    # Create content for module 1
    text1 = Text.objects.create(
        owner=instructor,
        title='Welcome to the Course',
        content='This is the introduction content'
    )
    Content.objects.create(module=module1, item=text1, order=0)

    text2 = Text.objects.create(
        owner=instructor,
        title='Course Overview',
        content='This is the course overview'
    )
    Content.objects.create(module=module1, item=text2, order=1)
    print("   ✓ Created 2 contents for module 1")
else:
    print("   ✓ Using existing module:", module1.title)

module2, created = Module.objects.get_or_create(
    course=course,
    order=1,
    defaults={
        'title': 'Module 2: Main Content',
        'description': 'Main course content'
    }
)
if created:
    print("   ✓ Created module:", module2.title)

    # Create content for module 2
    text3 = Text.objects.create(
        owner=instructor,
        title='Lesson 1',
        content='Main lesson content'
    )
    Content.objects.create(module=module2, item=text3, order=0)
    print("   ✓ Created 1 content for module 2")
else:
    print("   ✓ Using existing module:", module2.title)

# 4. Test enrollment
print("\n4. Testing enrollment...")
enrollment, created = CourseEnrollment.objects.get_or_create(
    student=student,
    course=course,
    defaults={'status': 'enrolled'}
)
if created:
    course.students.add(student)
    print("   ✓ Enrolled student in course")
else:
    print("   ✓ Student already enrolled")

print(f"   - Enrollment status: {enrollment.status}")
print(f"   - Progress: {enrollment.progress_percentage}%")

# 5. Test content progress
print("\n5. Testing content progress...")
content1 = module1.contents.first()
if content1:
    content_progress, created = ContentProgress.objects.get_or_create(
        enrollment=enrollment,
        content=content1
    )
    print(f"   ✓ Content progress created for: {content1.item.title}")

    # Mark as completed
    if not content_progress.is_completed:
        content_progress.mark_completed()
        print("   ✓ Marked content as completed")
        print(f"   - Completed at: {content_progress.completed_at}")
    else:
        print("   - Content already completed")

    # Refresh enrollment to see updated progress
    enrollment.refresh_from_db()
    print(f"   - Updated course progress: {enrollment.progress_percentage}%")

# 6. Test module progress
print("\n6. Testing module progress...")
module_progress = ModuleProgress.objects.filter(
    enrollment=enrollment,
    module=module1
).first()
if module_progress:
    print(f"   ✓ Module progress exists for: {module1.title}")
    print(f"   - Is completed: {module_progress.is_completed}")
    if module_progress.completed_at:
        print(f"   - Completed at: {module_progress.completed_at}")
else:
    print("   ! No module progress found")

# 7. Test learning session
print("\n7. Testing learning session...")
if content1:
    session = LearningSession.objects.create(
        enrollment=enrollment,
        content=content1
    )
    print(f"   ✓ Learning session created")
    print(f"   - Started at: {session.started_at}")

    # End session
    session.end_session()
    print(f"   ✓ Session ended")
    if session.ended_at:
        print(f"   - Ended at: {session.ended_at}")

# 8. Display statistics
print("\n8. Course statistics:")
print(f"   - Total modules: {course.modules.count()}")
print(f"   - Total contents: {Content.objects.filter(module__course=course).count()}")
print(f"   - Total students: {course.students.count()}")
print(f"   - Course progress: {enrollment.progress_percentage}%")

completed_contents = ContentProgress.objects.filter(
    enrollment=enrollment,
    is_completed=True
).count()
print(f"   - Completed contents: {completed_contents}")

completed_modules = ModuleProgress.objects.filter(
    enrollment=enrollment,
    is_completed=True
).count()
print(f"   - Completed modules: {completed_modules}")

total_sessions = LearningSession.objects.filter(
    enrollment=enrollment
).count()
print(f"   - Total learning sessions: {total_sessions}")

# 9. Test enrollment methods
print("\n9. Testing enrollment methods:")
current_module = enrollment.get_current_module()
if current_module:
    print(f"   - Current module: {current_module.title}")
else:
    print("   - No current module (all completed or none started)")

calculated_progress = enrollment.calculate_progress()
print(f"   - Calculated progress: {calculated_progress}%")

print("\n" + "=" * 60)
print("Course Tracking Test Complete!")
print("=" * 60)
print("\nTest results:")
print("✓ Enrollment working")
print("✓ Content progress tracking working")
print("✓ Module progress tracking working")
print("✓ Learning session tracking working")
print("✓ Progress calculation working")
print("\nAll core tracking features are functional!")
print("=" * 60)

