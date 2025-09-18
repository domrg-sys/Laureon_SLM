from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

class LoginRequiredMiddlewareTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.main_menu_url = reverse('main_menu:main_menu')
        self.login_url = reverse('users:login')

    def test_unauthenticated_user_is_redirected(self):
        """Test that a user who is not logged in gets redirected."""
        response = self.client.get(self.main_menu_url)
        expected_redirect = f'{self.login_url}?next={self.main_menu_url}'
        self.assertRedirects(response, expected_redirect)

    def test_authenticated_user_can_access_page(self):
        """Test that a logged-in user is NOT redirected."""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.main_menu_url)
        self.assertEqual(response.status_code, 200)