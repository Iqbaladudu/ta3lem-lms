from django.test import TestCase
from django.urls import reverse

from .models import Course, User, CourseEnrollment, Subject


# Create your tests here.

class CourseEnrollmentAccessTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='testuser')
        self.subject = Subject.objects.create(title='Test Subject', slug='test-subject')
        self.course = Course.objects.create(
            owner=self.user,
            subject=self.subject,
            title='Test Course',
            slug='test-course',
            overview='Test',
            is_free=True
        )

    def create_enrollment(self, status, payment_status):
        return CourseEnrollment(
            student=self.user,
            course=self.course,
            status=status,
            payment_status=payment_status
        )

    def test_accessible_status_and_payment(self):
        for status in ['enrolled', 'completed', 'paused']:
            for payment_status in ['paid', 'free']:
                enrollment = self.create_enrollment(status, payment_status)
                self.assertTrue(enrollment.can_access_course(), f"Should access: {status}, {payment_status}")

    def test_inaccessible_status(self):
        for status in ['pending', 'withdrawn', 'rejected']:
            for payment_status in ['paid', 'free']:
                enrollment = self.create_enrollment(status, payment_status)
                self.assertFalse(enrollment.can_access_course(), f"Should not access: {status}, {payment_status}")

    def test_inaccessible_payment(self):
        for status in ['enrolled', 'completed', 'paused']:
            for payment_status in ['pending', 'failed', 'refunded']:
                enrollment = self.create_enrollment(status, payment_status)
                self.assertFalse(enrollment.can_access_course(), f"Should not access: {status}, {payment_status}")


class CourseAccessViewTestCase(TestCase):
    """Test that views enforce can_access_course logic"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.subject = Subject.objects.create(title='Test Subject', slug='test-subject')
        self.course = Course.objects.create(
            owner=self.user,
            subject=self.subject,
            title='Test Course',
            slug='test-course',
            overview='Test',
            status='published',
            is_free=True
        )

    def test_accessible_course_can_be_viewed(self):
        """Course with valid status and payment can be accessed"""
        enrollment = CourseEnrollment.objects.create(
            student=self.user,
            course=self.course,
            status='enrolled',
            payment_status='free'
        )

        self.client.login(username='testuser', password='testpass')
        url = reverse('student_course_detail', args=[self.course.pk])
        response = self.client.get(url)

        # Should not raise 404 - accessible courses return 200 or redirect
        self.assertIn(response.status_code, [200, 302])

    def test_pending_enrollment_blocks_access(self):
        """Course with pending status cannot be accessed"""
        enrollment = CourseEnrollment.objects.create(
            student=self.user,
            course=self.course,
            status='pending',
            payment_status='free'
        )

        self.client.login(username='testuser', password='testpass')
        url = reverse('student_course_detail', args=[self.course.pk])
        response = self.client.get(url)

        # Should return 404 for inaccessible course
        self.assertEqual(response.status_code, 404)

    def test_unpaid_enrollment_blocks_access(self):
        """Course with unpaid payment status cannot be accessed"""
        enrollment = CourseEnrollment.objects.create(
            student=self.user,
            course=self.course,
            status='enrolled',
            payment_status='pending'
        )

        self.client.login(username='testuser', password='testpass')
        url = reverse('student_course_detail', args=[self.course.pk])
        response = self.client.get(url)

        # Should return 404 for inaccessible course
        self.assertEqual(response.status_code, 404)

    def test_paused_with_paid_can_access(self):
        """Course with paused status but paid can still be accessed"""
        enrollment = CourseEnrollment.objects.create(
            student=self.user,
            course=self.course,
            status='paused',
            payment_status='paid'
        )

        self.client.login(username='testuser', password='testpass')
        url = reverse('student_course_detail', args=[self.course.pk])
        response = self.client.get(url)

        # Should not raise 404
        self.assertIn(response.status_code, [200, 302])

    def test_completed_course_can_be_viewed(self):
        """Completed courses can still be accessed"""
        enrollment = CourseEnrollment.objects.create(
            student=self.user,
            course=self.course,
            status='completed',
            payment_status='free'
        )

        self.client.login(username='testuser', password='testpass')
        url = reverse('student_course_detail', args=[self.course.pk])
        response = self.client.get(url)

        # Should not raise 404
        self.assertIn(response.status_code, [200, 302])

