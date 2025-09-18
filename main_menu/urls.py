"""
URL configuration for the main_menu app.
"""

# Django Imports
from django.urls import path

# Local Imports
from . import views

app_name = 'main_menu'

urlpatterns = [
    # Maps the root URL of the app ('/main_menu/') to the main menu page view.
    path('', views.main_menu_page, name='main_menu'),
]