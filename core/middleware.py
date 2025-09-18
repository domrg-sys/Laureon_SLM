"""
Provides custom middleware for the project.
"""
from django.shortcuts import redirect
from django.urls import reverse


class LoginRequiredMiddleware:
    """
    Middleware that requires a user to be authenticated to view any page.

    Exemptions to this requirement can be specified in the EXEMPT_URLS tuple.
    """
    EXEMPT_URL_NAMES = ('users:login',)  # Add other URL names like 'password_reset' if needed

    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_urls = [reverse(name) for name in self.EXEMPT_URL_NAMES]

    def __call__(self, request):
        # Allow access to the admin site without this middleware's intervention
        if request.path.startswith(reverse('admin:index')):
            return self.get_response(request)

        if not request.user.is_authenticated:
            if request.path not in self.exempt_urls:
                login_url = reverse('users:login')
                # Append the 'next' parameter to redirect after login
                return redirect(f'{login_url}?next={request.path}')

        return self.get_response(request)