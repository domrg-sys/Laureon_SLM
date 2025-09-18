"""
App configuration for the sample_control Django app.
"""

# Django Imports
from django.apps import AppConfig


class SampleControlConfig(AppConfig):
    """
    Configuration class for the 'sample_control' app.

    This class is automatically discovered by Django and is used to manage
    app-specific settings and startup behavior.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sample_control'
    verbose_name = "Sample Control"