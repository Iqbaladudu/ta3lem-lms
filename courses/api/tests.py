"""
API Tests for Courses app.
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from courses.models import Subject, Course, Module, Content, CourseEnrollment

User = get_user_model()


class SubjectAPITests(APITestCase):
    """Tests for Subject API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.subject = Subject.objects.create(
            title='Programming',
            slug='programming'
        )
    
    def test_list_subjects(self):
        """Test listing subjects."""
        url = '/api/v1/subjects/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Programming')
    
    def test_get_subject_detail(self):
        """Test getting subject detail by slug."""
        url = f'/api/v1/subjects/{self.subject.slug}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Programming')


class CourseAPITests(APITestCase):
    """Tests for Course API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.instructor = User.objects.create_user(
            username='instructor',
            email='instructor@example.com',
            password='testpass123',
            role='instructor'
        )
        self.student = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='testpass123',
            role='student'
        )
        self.subject = Subject.objects.create(
            title='Programming',
            slug='programming'
        )
        self.course = Course.objects.create(
            owner=self.instructor,
            subject=self.subject,
            title='Python Basics',
            slug='python-basics',
            overview='Learn Python programming',
            status='published',
            pricing_type='free',
            is_free=True
        )
    
    def test_list_courses_public(self):
        """Test listing courses is public."""
        url = '/api/v1/courses/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_get_course_detail(self):
        """Test getting course detail by slug."""
        url = f'/api/v1/courses/{self.course.slug}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Python Basics')
        self.assertEqual(response.data['status'], 'published')
    
    def test_filter_courses_by_subject(self):
        """Test filtering courses by subject."""
        url = '/api/v1/courses/'
        response = self.client.get(url, {'subject': 'programming'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_filter_free_courses(self):
        """Test filtering free courses."""
        url = '/api/v1/courses/'
        response = self.client.get(url, {'is_free': True})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_search_courses(self):
        """Test searching courses."""
        url = '/api/v1/courses/'
        response = self.client.get(url, {'search': 'Python'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [c['title'] for c in response.data['results']]
        self.assertIn('Python Basics', titles)
    
    def test_create_course_instructor_only(self):
        """Test only instructors can create courses."""
        self.client.force_authenticate(user=self.instructor)
        url = '/api/v1/courses/'
        data = {
            'subject': self.subject.id,
            'title': 'New Course',
            'slug': 'new-course',
            'overview': 'A new course',
            'pricing_type': 'free',
            'is_free': True
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_create_course_student_denied(self):
        """Test students cannot create courses."""
        self.client.force_authenticate(user=self.student)
        url = '/api/v1/courses/'
        data = {
            'subject': self.subject.id,
            'title': 'New Course',
            'slug': 'new-course',
            'overview': 'A new course'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_course_owner_only(self):
        """Test only owner can update course."""
        self.client.force_authenticate(user=self.instructor)
        url = f'/api/v1/courses/{self.course.slug}/'
        data = {'title': 'Updated Python Basics'}
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.course.refresh_from_db()
        self.assertEqual(self.course.title, 'Updated Python Basics')
    
    def test_my_courses_instructor(self):
        """Test instructor can view their courses."""
        self.client.force_authenticate(user=self.instructor)
        url = '/api/v1/courses/my_courses/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class EnrollmentAPITests(APITestCase):
    """Tests for Enrollment API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.instructor = User.objects.create_user(
            username='instructor',
            email='instructor@example.com',
            password='testpass123',
            role='instructor'
        )
        self.student = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='testpass123',
            role='student'
        )
        self.subject = Subject.objects.create(
            title='Programming',
            slug='programming'
        )
        self.course = Course.objects.create(
            owner=self.instructor,
            subject=self.subject,
            title='Python Basics',
            slug='python-basics',
            overview='Learn Python programming',
            status='published',
            pricing_type='free',
            is_free=True
        )
    
    def test_enroll_free_course(self):
        """Test enrolling in a free course."""
        self.client.force_authenticate(user=self.student)
        url = '/api/v1/enrollments/enroll/'
        data = {'course_id': self.course.id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            CourseEnrollment.objects.filter(
                student=self.student,
                course=self.course
            ).exists()
        )
    
    def test_list_my_enrollments(self):
        """Test listing user's enrollments."""
        # Create enrollment
        CourseEnrollment.objects.create(
            student=self.student,
            course=self.course,
            status='enrolled',
            payment_status='free'
        )
        
        self.client.force_authenticate(user=self.student)
        url = '/api/v1/enrollments/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_withdraw_from_course(self):
        """Test withdrawing from a course."""
        enrollment = CourseEnrollment.objects.create(
            student=self.student,
            course=self.course,
            status='enrolled',
            payment_status='free'
        )
        
        self.client.force_authenticate(user=self.student)
        url = f'/api/v1/enrollments/{enrollment.id}/withdraw/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.status, 'withdrawn')


class ProgressAPITests(APITestCase):
    """Tests for Progress API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.instructor = User.objects.create_user(
            username='instructor',
            email='instructor@example.com',
            password='testpass123',
            role='instructor'
        )
        self.student = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='testpass123',
            role='student'
        )
        self.subject = Subject.objects.create(
            title='Programming',
            slug='programming'
        )
        self.course = Course.objects.create(
            owner=self.instructor,
            subject=self.subject,
            title='Python Basics',
            slug='python-basics',
            overview='Learn Python programming',
            status='published',
            pricing_type='free',
            is_free=True
        )
        self.module = Module.objects.create(
            course=self.course,
            title='Introduction',
            description='Getting started'
        )
        self.content = Content.objects.create(
            module=self.module,
            title='Lesson 1'
        )
        self.enrollment = CourseEnrollment.objects.create(
            student=self.student,
            course=self.course,
            status='enrolled',
            payment_status='free'
        )
    
    def test_get_course_progress(self):
        """Test getting course progress."""
        self.client.force_authenticate(user=self.student)
        url = f'/api/v1/courses/{self.course.slug}/progress/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('progress_percentage', response.data['data'])
    
    def test_mark_content_complete(self):
        """Test marking content as complete."""
        self.client.force_authenticate(user=self.student)
        url = f'/api/v1/courses/{self.course.slug}/complete/'
        data = {'content_id': self.content.id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['data']['content_completed'])
    
    def test_get_module_progress(self):
        """Test getting module progress."""
        self.client.force_authenticate(user=self.student)
        url = f'/api/v1/courses/{self.course.slug}/modules/progress/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
