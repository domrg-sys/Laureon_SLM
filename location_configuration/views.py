"""
Views for the Location Configuration app, handling the display, creation, and
modification of Location and LocationType objects.
"""

# Standard Library Imports
from collections import deque

# Django Imports
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Exists, OuterRef, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import (CreateView, DeleteView, ListView,
                                  UpdateView, View)
from django.utils.decorators import method_decorator


# Local Imports
from core.utils import generate_space_grid
from sample_control.models import SampleItem

from .forms import (LocationCreateForm, LocationEditForm,
                    LocationTypeCreateForm, LocationTypeEditForm)
from .models import Location, LocationSpace, LocationType

# ==========================================================================
#  Helper Functions
# ==========================================================================

def get_location_tabs():
    """Generates the context data for the tab navigator."""
    return [
        {'label': 'Locations', 'url': reverse('location_configuration:locations'), 'slug': 'locations'},
        {'label': 'Types', 'url': reverse('location_configuration:types'), 'slug': 'types'},
    ]

def _topologically_sort_location_types(qs):
    """
    Sorts a queryset of LocationType objects based on their parent-child
    relationships, ensuring parents appear before their children.
    """
    if not qs:
        return []

    type_map = {t.id: t for t in qs}
    in_degree = {t.id: t.allowed_parent_types.count() for t in qs}

    queue = deque(sorted(
        [t_id for t_id, degree in in_degree.items() if degree == 0],
        key=lambda t_id: type_map[t_id].name
    ))

    sorted_list = []
    while queue:
        current_id = queue.popleft()
        current_type = type_map[current_id]
        sorted_list.append(current_type)

        children = sorted(current_type.locationtype_set.all(), key=lambda t: t.name)
        for child in children:
            if child.id in in_degree:
                in_degree[child.id] -= 1
                if in_degree[child.id] == 0:
                    queue.append(child.id)

    if len(sorted_list) != len(qs):
        sorted_ids = {t.id for t in sorted_list}
        remaining = sorted([t for t in qs if t.id not in sorted_ids], key=lambda t: t.name)
        sorted_list.extend(remaining)

    return sorted_list

# ==========================================================================
#  LocationType Views (Class-Based)
# ==========================================================================

class LocationTypeListView(PermissionRequiredMixin, ListView):
    """Displays a list of all LocationType objects."""
    model = LocationType
    template_name = 'location_configuration/page.html'
    context_object_name = 'location_types'
    permission_required = 'location_configuration.view_locationtype'
    paginate_by = 25

    def get_queryset(self):
        """
        Returns a topologically sorted queryset of LocationTypes, annotated
        with an `in_use` flag to prevent N+1 queries.
        """
        qs = LocationType.objects.annotate(
            has_locations=Exists(Location.objects.filter(source_location_type=OuterRef('pk'))),
            is_parent_type=Exists(LocationType.objects.filter(allowed_parent_types=OuterRef('pk')))
        ).annotate(
            in_use=Q(has_locations=True) | Q(is_parent_type=True)
        )
        return _topologically_sort_location_types(qs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tabs'] = get_location_tabs()
        context['active_tab'] = 'types'
        return context


class LocationTypeCreateView(PermissionRequiredMixin, CreateView):
    """Handles the creation of a new LocationType instance."""
    model = LocationType
    form_class = LocationTypeCreateForm
    template_name = 'location_configuration/location_type_form.html'
    success_url = reverse_lazy('location_configuration:types')
    permission_required = 'location_configuration.add_locationtype'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Add New Location Type'
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Successfully created Location Type '{form.instance.name}'.")
        return super().form_valid(form)


class LocationTypeEditView(PermissionRequiredMixin, UpdateView):
    """Handles the updating of an existing LocationType instance."""
    model = LocationType
    form_class = LocationTypeEditForm
    template_name = 'location_configuration/location_type_form.html'
    success_url = reverse_lazy('location_configuration:types')
    permission_required = 'location_configuration.change_locationtype'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit {self.object.name}'
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Successfully saved Location Type '{form.instance.name}'.")
        return super().form_valid(form)


class LocationTypeDeleteView(PermissionRequiredMixin, DeleteView):
    """Handles the deletion of a LocationType instance after confirmation."""
    model = LocationType
    template_name = 'location_configuration/location_type_confirm_delete.html'
    success_url = reverse_lazy('location_configuration:types')
    permission_required = 'location_configuration.delete_locationtype'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'object_type': 'Location Type',
            'object_name': self.object.name,
            'cancel_url': self.success_url,
        })
        return context

    def post(self, request, *args, **kwargs):
        location_type = self.get_object()
        if location_type.is_in_use:
            messages.error(request, f"Cannot delete '{location_type.name}' because it is currently in use.")
            return redirect('location_configuration:types')
        
        location_type_name = location_type.name
        response = super().post(request, *args, **kwargs)
        messages.success(request, f"Successfully deleted Location Type '{location_type_name}'.")
        return response

# ==========================================================================
#  Location Views (Class-Based and Function-Based)
# ==========================================================================

class LocationListView(PermissionRequiredMixin, ListView):
    """Displays a hierarchical list of Location objects."""
    model = Location
    template_name = 'location_configuration/page.html'
    context_object_name = 'locations'
    permission_required = 'location_configuration.view_location'

    def get_queryset(self):
        """
        Returns a queryset of Locations, annotated with an `in_use` flag and
        optimized with select_related and prefetch_related.
        """
        space_is_occupied = LocationSpace.objects.filter(
            Q(occupied_by_location__isnull=False) | Q(occupied_by_sample_item__isnull=False),
            parent_location=OuterRef('pk')
        )
        return Location.objects.select_related('source_location_type').prefetch_related(
            'child_locations__source_location_type',
            'spaces__occupied_by_location__source_location_type'
        ).annotate(
            has_child_locations=Exists(Location.objects.filter(parent=OuterRef('pk'))),
            has_sample_items=Exists(SampleItem.objects.filter(source_location=OuterRef('pk'))),
            child_space_is_used=Exists(space_is_occupied)
        ).annotate(
            in_use=(
                Q(has_child_locations=True) |
                Q(has_sample_items=True) |
                Q(child_space_is_used=True)
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tabs'] = get_location_tabs()
        context['active_tab'] = 'locations'
        context['show_actions'] = True
        return context

@permission_required('location_configuration.add_location')
def location_create_view(request, parent_pk=None, space_row=None, space_col=None):
    """Handles the creation of a new Location instance."""
    parent_location = get_object_or_404(Location, pk=parent_pk) if parent_pk else None
    space_coords = {'row': space_row, 'col': space_col} if space_row is not None else None

    form_kwargs = {'parent_location': parent_location, 'space_coords': space_coords}
    form = LocationCreateForm(request.POST or None, **form_kwargs)

    if request.method == 'POST' and form.is_valid():
        location = form.save(commit=False)
        if parent_location and not space_coords:
            location.parent = parent_location
        location.save()

        if space_coords and parent_location:
            space, _ = LocationSpace.objects.get_or_create(
                parent_location=parent_location,
                row=space_coords['row'], col=space_coords['col']
            )
            space.occupied_by_location = location
            space.save()
        messages.success(request, f"Successfully created location '{location.name}'.")
        return redirect('location_configuration:locations')

    context = {'form': form, 'parent_location': parent_location}
    return render(request, 'location_configuration/location_form.html', context)


class LocationEditView(PermissionRequiredMixin, UpdateView):
    """Handles the updating of an existing Location instance."""
    model = Location
    form_class = LocationEditForm
    template_name = 'location_configuration/location_form.html'
    success_url = reverse_lazy('location_configuration:locations')
    permission_required = 'location_configuration.change_location'

    def get_queryset(self):
        return Location.objects.select_related('occupied_space__parent_location', 'parent')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['parent_location'] = self.object.effective_parent
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Successfully updated location '{form.instance.name}'.")
        return super().form_valid(form)


class LocationDeleteView(PermissionRequiredMixin, DeleteView):
    """Handles the deletion of a Location instance after confirmation."""
    model = Location
    template_name = 'location_configuration/location_confirm_delete.html'
    success_url = reverse_lazy('location_configuration:locations')
    permission_required = 'location_configuration.delete_location'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'object_type': 'Location',
            'object_name': self.object.name,
            'cancel_url': self.success_url,
        })
        return context

    def post(self, request, *args, **kwargs):
        location = self.get_object()
        if location.is_in_use:
            messages.error(request, f"Cannot delete '{location.name}' because it is in use.")
            return redirect('location_configuration:locations')
        
        location_name = location.name
        response = super().post(request, *args, **kwargs)
        messages.success(request, f"Successfully deleted Location '{location_name}'.")
        return response


@method_decorator(permission_required('location_configuration.add_location'), name='dispatch')
class SelectSpaceView(View):
    """Displays a visual grid of a location's spaces for selection."""
    def get(self, request, parent_pk):
        parent_location = get_object_or_404(Location, pk=parent_pk)
        context = {
            'parent_location': parent_location,
            'grid': generate_space_grid(parent_location),
            'page_title': f'Select a Space in {parent_location.name}',
        }
        return render(request, 'location_configuration/select_space.html', context)

# ==========================================================================
#  Redirect View
# ==========================================================================

def location_configuration_page(request):
    """Redirects the base URL to the default 'locations' tab."""
    return redirect('location_configuration:locations')