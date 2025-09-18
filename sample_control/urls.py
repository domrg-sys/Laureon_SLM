"""
URL configuration for the sample_control app.
"""

# Django Imports
from django.urls import path

# Local Imports
from . import views

app_name = 'sample_control'

urlpatterns = [
    # --- Main & Search Views ---
    path(
        '',
        views.SampleControlListView.as_view(),
        name='sample_control'
    ),
    path(
        'search/',
        views.SampleSearchResultsView.as_view(),
        name='sample_search_results'
    ),

    # --- Sample Item CRUD Views ---
    path(
        'sample/<int:sample_pk>/',
        views.SampleItemDetailView.as_view(),
        name='sample_detail'
    ),
    path(
        'sample/<int:sample_pk>/edit/',
        views.SampleItemEditView.as_view(),
        name='sample_edit'
    ),
    path(
        'sample/<int:sample_pk>/delete/',
        views.SampleItemDeleteView.as_view(),
        name='sample_delete'
    ),

    # --- Location-Specific Views ---
    path(
        'location/<int:location_pk>/',
        views.SampleLocationDetailView.as_view(),
        name='sample_location_detail'
    ),
    path(
        'location/<int:location_pk>/add_sample/',
        views.sample_item_create_view,
        name='sample_add_to_location'
    ),
    path(
        'location/<int:location_pk>/<int:space_row>/<int:space_col>/add_sample/',
        views.sample_item_create_view,
        name='sample_add_to_space'
    ),

    # --- Bulk Operation Views ---
    path(
        'location/<int:location_pk>/bulk_add/',
        views.SampleItemBulkFormView.as_view(),
        name='sample_bulk_add_form'
    ),
    path(
        'location/<int:location_pk>/bulk_delete/',
        views.SampleItemBulkDeleteConfirmView.as_view(),
        name='sample_bulk_delete'
    ),
    path(
        'location/<int:location_pk>/bulk_delete/perform/',
        views.SampleItemBulkDeletePerformView.as_view(),
        name='sample_bulk_delete_perform'
    ),
]