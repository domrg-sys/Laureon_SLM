"""
Main URL configuration for the Laureon_MRP project.

This file routes URLs from the root of the project to the appropriate app's
URL configuration. It also includes the URL for the Django admin site.

For more information, see:
https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""

# Django Imports
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView

# --- Group all application-specific URLs together ---
# These will all be prefixed with /slm/
slm_patterns = [
    path('', RedirectView.as_view(url='main_menu/', permanent=False)),
    path('main_menu/', include('main_menu.urls')),
    path('location_configuration/', include('location_configuration.urls')),
    path('sample_control/', include('sample_control.urls')),
    path('accounts/', include('users.urls')),
]

urlpatterns = [
    # --- Admin Site (remains at the root) ---
    path('admin/', admin.site.urls),

    # --- Main Application URLs ---
    # All URLs from slm_patterns will now start with /slm/
    path('slm/', include(slm_patterns)),

    # --- Root URL Redirect ---
    # Redirect the root URL ('/') to the new, prefixed main menu.
    path('', RedirectView.as_view(url='/slm/main_menu/', permanent=True)),
]