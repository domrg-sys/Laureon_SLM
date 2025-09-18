"""
App configuration for the core Django app.

The 'core' app is intended to hold project-wide utilities, base classes,
and other code that doesn't belong to a specific functional app.
"""

# Django Imports
from django.apps import AppConfig


class CoreConfig(AppConfig):
    """
    Configuration class for the 'core' app.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = "Core Utilities"