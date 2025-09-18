from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

class UserAuthTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')

    def test_user_can_log_in(self):
        """Test that a user can successfully log in."""
        response = self.client.post(reverse('users:login'), {
            'username': 'testuser',
            'password': 'password123',
        })
        # A successful login should redirect to the main menu
        self.assertRedirects(response, reverse('main_menu:main_menu'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_user_can_log_out(self):
        """Test that a logged-in user can successfully log out."""
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('users:logout'))
        # A logout should redirect back to the login page
        self.assertRedirects(response, reverse('users:login'))
        self.assertFalse(response.wsgi_request.user.is_authenticated)