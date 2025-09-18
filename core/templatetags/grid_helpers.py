"""
Custom template tags and filters for grid-related display logic.
"""

from django import template

register = template.Library()

@register.filter(name='to_row_letter')
def to_row_letter(row_num):
    """
    Converts a 1-based row number into an Excel-style letter representation.
    (e.g., 1 -> A, 26 -> Z, 27 -> AA).
    """
    if not isinstance(row_num, int) or row_num < 1:
        return ""

    letters = ""
    while row_num > 0:
        row_num, remainder = divmod(row_num - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters