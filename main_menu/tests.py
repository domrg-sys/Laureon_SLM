from django.test import TestCase
from django.urls import reverse

class MainMenuViewTest(TestCase):
    def test_main_menu_view_status_code(self):
        """Test that the main menu page returns a 200 status code."""
        response = self.client.get(reverse('main_menu:main_menu'))
        self.assertEqual(response.status_code, 200)

    def test_main_menu_view_uses_correct_template(self):
        """Test that the main menu page uses the correct template."""
        response = self.client.get(reverse('main_menu:main_menu'))
        self.assertTemplateUsed(response, 'main_menu/page.html')