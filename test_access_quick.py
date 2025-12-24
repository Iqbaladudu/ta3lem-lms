#!/usr/bin/env python
"""Quick test script to verify course access logic"""
import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ta3lem.settings.development')
django.setup()

from courses.models import Course, CourseEnrollment, Subject, User

# Test 1: Model-level can_access_course
print("=" * 60)
print("TEST 1: Model-level can_access_course")
print("=" * 60)

user = User.objects.first()
if not user:
    user = User.objects.create_user(username='testuser', password='testpass')

subject = Subject.objects.first()
if not subject:
    subject = Subject.objects.create(title='Test Subject', slug='test-subject')

course = Course.objects.filter(status='published').first()
if not course:
    course = Course.objects.create(
        owner=user,
        subject=subject,
        title='Test Course',
        slug='test-course-quick',
        overview='Test',
        status='published',
        is_free=True
    )

# Test valid access
enrollment = CourseEnrollment(
    student=user,
    course=course,
    status='enrolled',
    payment_status='free'
)
print(f"✓ Enrolled + Free: can_access = {enrollment.can_access_course()}")
assert enrollment.can_access_course() == True

# Test invalid status
enrollment.status = 'pending'
print(f"✗ Pending + Free: can_access = {enrollment.can_access_course()}")
assert enrollment.can_access_course() == False

# Test invalid payment
enrollment.status = 'enrolled'
enrollment.payment_status = 'pending'
print(f"✗ Enrolled + Pending Payment: can_access = {enrollment.can_access_course()}")
assert enrollment.can_access_course() == False

# Test paused but paid
enrollment.status = 'paused'
enrollment.payment_status = 'paid'
print(f"✓ Paused + Paid: can_access = {enrollment.can_access_course()}")
assert enrollment.can_access_course() == True

print("\n✅ All model tests passed!")

# Test 2: View-level access control
print("\n" + "=" * 60)
print("TEST 2: View-level access control")
print("=" * 60)

from django.test import Client

client = Client()
client.login(username='testuser', password='testpass')

# Clean up any existing enrollments for this test
CourseEnrollment.objects.filter(student=user, course=course).delete()

# Test 1: No enrollment - should create one with default 'enrolled' status
print(f"Test URL: /courses/student/{course.pk}/")
response = client.get(f'/courses/student/{course.pk}/')
print(f"Response status (no prior enrollment): {response.status_code}")

# Check if enrollment was created
enrollment = CourseEnrollment.objects.filter(student=user, course=course).first()
if enrollment:
    print(f"Enrollment created: status={enrollment.status}, payment_status={enrollment.payment_status}")
    print(f"Can access: {enrollment.can_access_course()}")

# Test 2: Existing enrollment with invalid status
if enrollment:
    enrollment.status = 'pending'
    enrollment.save()
    response = client.get(f'/courses/student/{course.pk}/')
    print(f"Response status (pending enrollment): {response.status_code}")

    # Test 3: Valid enrollment
    enrollment.status = 'enrolled'
    enrollment.save()
    response = client.get(f'/courses/student/{course.pk}/')
    print(f"Response status (enrolled): {response.status_code}")

print("\n✅ Script completed!")
