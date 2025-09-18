"""
App configuration for the main_menu Django app.

This app is responsible for displaying the main navigation menu of the project.
"""

# Django Imports
from django.apps import AppConfig


class MainMenuConfig(AppConfig):
    """
    Configuration class for the 'main_menu' app.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main_menu'
    verbose_name = "Main Menu"