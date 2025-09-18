"""
URL configuration for the location_configuration app.
"""

# Django Imports
from django.urls import path

# Local Imports
from . import views

app_name = 'location_configuration'

urlpatterns = [
    # --- Main Redirect ---
    path(
        '',
        views.location_configuration_page,
        name='location_configuration'
    ),

    # --- LocationType URLs ---
    path(
        'types/',
        views.LocationTypeListView.as_view(),
        name='types'
    ),
    path(
        'types/add/',
        views.LocationTypeCreateView.as_view(),
        name='location_type_add'
    ),
    path(
        'types/<int:pk>/edit/',
        views.LocationTypeEditView.as_view(),
        name='location_type_edit'
    ),
    path(
        'types/<int:pk>/delete/',
        views.LocationTypeDeleteView.as_view(),
        name='location_type_delete'
    ),

    # --- Location URLs ---
    path(
        'locations/',
        views.LocationListView.as_view(),
        name='locations'
    ),
    path(
        'locations/add/',
        views.location_create_view,
        name='location_add_toplevel'
    ),
    path(
        'locations/<int:pk>/edit/',
        views.LocationEditView.as_view(),
        name='location_edit'
    ),
    path(
        'locations/<int:pk>/delete/',
        views.LocationDeleteView.as_view(),
        name='location_delete'
    ),

    # --- URLs for Adding Child Locations ---
    path(
        'locations/<int:parent_pk>/add_child/',
        views.location_create_view,
        name='location_add_child'
    ),
    path(
        'locations/<int:parent_pk>/select_space/',
        views.SelectSpaceView.as_view(),
        name='location_select_space'
    ),
    path(
        'locations/<int:parent_pk>/<int:space_row>/<int:space_col>/add_child/',
        views.location_create_view,
        name='location_add_child_in_space'
    ),
]