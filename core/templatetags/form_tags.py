"""
Custom template tags and filters for the core application.

This module provides reusable template utilities that can be used across
different templates in the project.
"""

# Django Imports
from django import template

register = template.Library()


@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    A custom template filter to allow accessing dictionary items with a
    variable key.

    This is useful in Django templates where you cannot use dynamic keys for
    dictionary access (e.g., `my_dict[my_var]`).

    Args:
        dictionary (dict): The dictionary to access.
        key: The key whose value needs to be retrieved.

    Returns:
        The value associated with the key, or None if the key is not found.

    Usage in a template:
        {{ my_dictionary|get_item:my_variable_key }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None