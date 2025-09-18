"""
Defines the views for the main_menu app.
"""

# Django Imports
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def main_menu_page(request: HttpRequest) -> HttpResponse:
    """
    Renders the main menu page.

    This view renders the static main menu template, which contains the
    primary navigation links for the application.
    """
    return render(request, 'main_menu/page.html')