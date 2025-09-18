"""
Defines a base form class for the project to ensure consistent behavior
and styling for all forms.
"""

# Django Imports
from django import forms
from django.utils.safestring import mark_safe


class BaseForm(forms.ModelForm):
    """
    A base ModelForm that provides customized, user-friendly error messages.

    All other ModelForms in the project should inherit from this class to
    ensure a consistent user experience for form validation. It automatically
    overrides the default 'required' error message for all required fields.
    """
    def __init__(self, *args, **kwargs):
        """
        Overrides the default __init__ to iterate through the form's fields
        and set a custom, HTML-formatted error message for any field that is
        marked as required.
        """
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if field.required:
                # Use mark_safe to allow HTML (the <strong> tag) in the error
                # message, which will be rendered in the template.
                field.error_messages['required'] = mark_safe(
                    f"The <strong>{field.label}</strong> field is required."
                )