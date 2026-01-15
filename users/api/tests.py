"""
API Tests for Users app.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

User = get_user_model()


class AuthenticationAPITests(APITestCase):
    """Tests for authentication endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='student'
        )
    
    def test_login_success(self):
        """Test successful login returns tokens."""
        url = '/api/v1/auth/login/'
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'testuser')
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials fails."""
        url = '/api/v1/auth/login/'
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_register_success(self):
        """Test successful user registration."""
        url = '/api/v1/auth/register/'
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123!',
            'password_confirm': 'newpass123!',
            'role': 'student'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('data', response.data)
        self.assertIn('tokens', response.data['data'])
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_register_password_mismatch(self):
        """Test registration with mismatched passwords fails."""
        url = '/api/v1/auth/register/'
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123!',
            'password_confirm': 'differentpass!',
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_token_refresh(self):
        """Test token refresh works correctly."""
        # First login to get tokens
        login_url = '/api/v1/auth/login/'
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        refresh_token = login_response.data['refresh']
        
        # Use refresh token to get new access token
        refresh_url = '/api/v1/auth/refresh/'
        refresh_data = {'refresh': refresh_token}
        response = self.client.post(refresh_url, refresh_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)


class CurrentUserAPITests(APITestCase):
    """Tests for current user endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='student',
            first_name='Test',
            last_name='User'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_get_current_user(self):
        """Test getting current user profile."""
        url = '/api/v1/me/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['username'], 'testuser')
        self.assertEqual(response.data['data']['email'], 'test@example.com')
    
    def test_update_current_user(self):
        """Test updating current user profile."""
        url = '/api/v1/me/'
        data = {
            'first_name': 'Updated',
            'bio': 'This is my bio'
        }
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.bio, 'This is my bio')
    
    def test_change_password(self):
        """Test password change."""
        url = '/api/v1/me/password/'
        data = {
            'old_password': 'testpass123',
            'new_password': 'newpass456!',
            'new_password_confirm': 'newpass456!'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify new password works
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass456!'))
    
    def test_unauthenticated_access_denied(self):
        """Test unauthenticated access is denied."""
        self.client.logout()
        url = '/api/v1/me/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserListAPITests(APITestCase):
    """Tests for user listing endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.student = User.objects.create_user(
            username='student1',
            email='student@example.com',
            password='testpass123',
            role='student'
        )
        self.instructor = User.objects.create_user(
            username='instructor1',
            email='instructor@example.com',
            password='testpass123',
            role='instructor'
        )
        self.client.force_authenticate(user=self.student)
    
    def test_list_instructors_public(self):
        """Test listing instructors is public."""
        self.client.logout()
        url = '/api/v1/users/instructors/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should contain instructor
        usernames = [u['username'] for u in response.data['results']]
        self.assertIn('instructor1', usernames)
