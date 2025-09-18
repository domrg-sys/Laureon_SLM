"""
Admin configurations for the sample_control app.

This module registers the SampleItem model with the Django admin site,
providing a customized interface for managing samples.
"""

# Django Imports
from django.contrib import admin

# Local Imports
from .models import SampleItem


@admin.register(SampleItem)
class SampleItemAdmin(admin.ModelAdmin):
    """
    Admin interface for the SampleItem model.
    """
    list_display = (
        'name',
        'catalog_number',
        'lot_number',
        'source_location',
        'occupied_space',
    )
    search_fields = (
        'name',
        'catalog_number',
        'lot_number',
        'description',
    )
    list_filter = (
        'source_location__source_location_type',
    )
    # Use raw_id_fields for foreign keys to improve performance, especially
    # if you have a large number of locations.
    raw_id_fields = (
        'source_location',
    )