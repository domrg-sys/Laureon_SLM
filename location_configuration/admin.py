"""
Admin configurations for the location_configuration app.

This module registers the LocationType, Location, and LocationSpace models
with the Django admin site, providing customized interfaces for each to
improve usability and data management.
"""

# Django Imports
from django.contrib import admin

# Local Imports
from .models import Location, LocationSpace, LocationType


@admin.register(LocationType)
class LocationTypeAdmin(admin.ModelAdmin):
    """
    Admin interface for the LocationType model.
    """
    list_display = (
        'name',
        'can_store_samples',
        'can_have_spaces',
    )
    search_fields = ('name',)
    list_filter = ('can_store_samples', 'can_have_spaces')


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    """
    Admin interface for the Location model.
    """
    list_display = ('name', 'source_location_type', 'parent')
    search_fields = ('name',)
    list_filter = ('source_location_type',)
    # Use raw_id_fields for better performance and UI when dealing with
    # potentially thousands of locations.
    raw_id_fields = ('parent',)


@admin.register(LocationSpace)
class LocationSpaceAdmin(admin.ModelAdmin):
    """
    Admin interface for the LocationSpace model.
    """
    list_display = (
        '__str__',
        'parent_location',
        'occupied_by_location',
        'occupied_by_sample_item',
    )
    search_fields = ('parent_location__name',)
    list_filter = ('parent_location',)
    # Use raw_id_fields for foreign keys to improve performance.
    raw_id_fields = (
        'parent_location',
        'occupied_by_location',
        'occupied_by_sample_item',
    )