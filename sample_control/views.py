"""
Defines the views for the Sample Control application, handling the display,
creation, modification, and deletion of SampleItem objects.
"""

# Django Imports
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import DeleteView, DetailView, ListView, UpdateView, View

# Local Imports
from core.utils import generate_space_grid
from location_configuration.models import Location, LocationSpace

from .forms import (BulkCreatePasteForm, BulkCreateSingleSampleForm,
                    SampleItemCreateForm, SampleItemEditForm)
from .models import SampleItem


class SampleControlListView(PermissionRequiredMixin, ListView):
    """
    Renders the main Sample Control explorer page, which contains the location
    tree and a search bar.
    """
    model = Location
    template_name = 'sample_control/page.html'
    context_object_name = 'all_locations'
    permission_required = 'sample_control.view_sampleitem'

    def get_queryset(self):
        """
        Return all locations, optimized for rendering the location tree.
        """
        return Location.objects.select_related(
            'source_location_type'
        ).prefetch_related(
            'child_locations__source_location_type',
            'spaces__occupied_by_location__source_location_type'
        )


class SampleLocationDetailView(PermissionRequiredMixin, DetailView):
    """
    Renders the detailed view of a specific location, showing either a grid of
    spaces or a table of samples.
    """
    model = Location
    template_name = 'sample_control/location_detail.html'
    context_object_name = 'selected_location'
    pk_url_kwarg = 'location_pk'
    permission_required = 'sample_control.view_sampleitem'

    def get_queryset(self):
        """
        Ensure that only locations that can store samples are accessible.
        """
        return Location.objects.select_related('source_location_type').filter(
            source_location_type__can_store_samples=True
        )

    def get_context_data(self, **kwargs):
        """
        Add the location's path and either a space grid or a list of samples
        to the context.
        """
        context = super().get_context_data(**kwargs)
        location = self.get_object()
        context['location_path'] = location.get_path()

        if location.source_location_type.can_have_spaces:
            context['grid'] = generate_space_grid(location)
        else:
            # Manually paginate the samples list
            sample_list = SampleItem.objects.filter(source_location=location)
            paginator = Paginator(sample_list, 25)  # Show 25 samples per page
            page_number = self.request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            context['samples'] = page_obj
            context['is_paginated'] = True
            context['page_obj'] = page_obj
        return context


class SampleSearchResultsView(PermissionRequiredMixin, ListView):
    """
    Renders the search results page for samples based on a query.
    """
    model = SampleItem
    template_name = 'sample_control/search_results.html'
    context_object_name = 'samples'
    permission_required = 'sample_control.view_sampleitem'
    paginate_by = 25

    def get_queryset(self):
        """
        Filter samples based on the 'q' GET parameter.
        """
        query = self.request.GET.get('q', '').strip()
        if query:
            return SampleItem.objects.filter(
                Q(name__icontains=query) |
                Q(catalog_number__icontains=query) |
                Q(lot_number__icontains=query) |
                Q(description__icontains=query)
            ).select_related(
                'source_location__source_location_type',
                'occupied_space__parent_location__source_location_type'
            )
        return SampleItem.objects.none()

    def get_context_data(self, **kwargs):
        """
        Add the search query back to the context to display it on the page.
        """
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context


@permission_required('sample_control.add_sampleitem')
def sample_item_create_view(request, location_pk, space_row=None, space_col=None):
    """Handles the creation of a new SampleItem."""
    parent_location = get_object_or_404(Location, pk=location_pk)
    space_coords = {'row': space_row, 'col': space_col} if space_row is not None else None

    form = SampleItemCreateForm(request.POST or None, parent_location=parent_location, space_coords=space_coords)

    if request.method == 'POST' and form.is_valid():
        sample = form.save(commit=False)
        with transaction.atomic():
            sample.save()  # Save sample first to get a PK
            if space_coords:
                space, _ = LocationSpace.objects.get_or_create(
                    parent_location=parent_location,
                    row=space_coords['row'], col=space_coords['col']
                )
                space.occupied_by_sample_item = sample
                space.save()
            else:
                sample.source_location = parent_location
                sample.save()

        messages.success(request, f"Successfully added sample '{sample.name}'.")
        return redirect('sample_control:sample_location_detail', location_pk=parent_location.pk)

    context = {
        'form': form,
        'parent_location': parent_location,
        'space_coords': space_coords,
    }
    return render(request, 'sample_control/sample_item_form.html', context)


class SampleItemEditView(PermissionRequiredMixin, UpdateView):
    """Handles the editing of an existing SampleItem."""
    model = SampleItem
    form_class = SampleItemEditForm
    template_name = 'sample_control/sample_item_edit_form.html'
    pk_url_kwarg = 'sample_pk'
    permission_required = 'sample_control.change_sampleitem'

    def get_success_url(self):
        return reverse('sample_control:sample_detail', kwargs={'sample_pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, f"Successfully updated sample '{form.instance.name}'.")
        return super().form_valid(form)


class SampleItemDeleteView(PermissionRequiredMixin, DeleteView):
    """Handles the deletion of a single SampleItem."""
    model = SampleItem
    template_name = 'sample_control/sample_item_confirm_delete.html'
    pk_url_kwarg = 'sample_pk'
    permission_required = 'sample_control.delete_sampleitem'

    def get_success_url(self):
        parent_location = self.object.source_location or self.object.occupied_space.parent_location
        return reverse('sample_control:sample_location_detail', kwargs={'location_pk': parent_location.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'object_type': 'Sample',
            'object_name': self.object.name,
            'cancel_url': reverse('sample_control:sample_detail', kwargs={'sample_pk': self.object.pk})
        })
        return context

    def form_valid(self, form):
        sample_name = self.object.name
        messages.success(self.request, f"Successfully deleted sample '{sample_name}'.")
        return super().form_valid(form)


class SampleItemDetailView(PermissionRequiredMixin, DetailView):
    """Displays the details of a single SampleItem."""
    model = SampleItem
    template_name = 'sample_control/sample_item_detail.html'
    pk_url_kwarg = 'sample_pk'
    permission_required = 'sample_control.view_sampleitem'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sample = self.get_object()
        parent_location = sample.source_location or (
            sample.occupied_space.parent_location if hasattr(sample, 'occupied_space') and sample.occupied_space else None
        )
        context.update({
            'parent_location': parent_location,
            'location_path': sample.get_location_path(),
            'from_search': self.request.GET.get('from_search') == 'true',
            'search_query': self.request.GET.get('q', ''),
        })
        return context


@method_decorator(permission_required('sample_control.add_sampleitem'), name='dispatch')
class SampleItemBulkFormView(View):
    """Displays and processes the form for bulk-adding samples."""
    def get(self, request, *args, **kwargs):
        # GET requests are not appropriate for this view, redirect to detail page.
        return redirect('sample_control:sample_location_detail', location_pk=kwargs.get('location_pk'))

    def post(self, request, *args, **kwargs):
        parent_location = get_object_or_404(Location, pk=kwargs.get('location_pk'))
        selected_spaces_str = request.POST.getlist('selected_spaces')
        count = int(request.POST.get('count', 0))

        if not selected_spaces_str and count <= 0:
            messages.error(request, "No spaces were selected or a valid count was not provided.")
            return redirect('sample_control:sample_location_detail', location_pk=parent_location.pk)

        # Handle different form submissions
        form_type = request.POST.get('form_type')
        if form_type == 'single':
            return self._handle_single_form(request, parent_location, selected_spaces_str, count)
        elif form_type == 'paste':
            return self._handle_paste_form(request, parent_location, selected_spaces_str, count)

        # Fallback for initial POST to this view from the detail page
        context = {
            'parent_location': parent_location,
            'selected_spaces': selected_spaces_str,
            'count': count,
            'single_form': BulkCreateSingleSampleForm(),
            'paste_form': BulkCreatePasteForm(),
        }
        return render(request, 'sample_control/sample_item_bulk_form.html', context)

    def _handle_single_form(self, request, parent_location, spaces, count):
        form = BulkCreateSingleSampleForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    if spaces:
                        for space_coord in spaces:
                            row, col = space_coord.split(',')
                            sample = SampleItem.objects.create(**form.cleaned_data)
                            space, _ = LocationSpace.objects.get_or_create(parent_location=parent_location, row=row, col=col)
                            space.occupied_by_sample_item = sample
                            space.save()
                        num_created = len(spaces)
                    elif count > 0:
                        for _ in range(count):
                            SampleItem.objects.create(source_location=parent_location, **form.cleaned_data)
                        num_created = count

                messages.success(request, f"Successfully created {num_created} samples.")
                return redirect('sample_control:sample_location_detail', location_pk=parent_location.pk)
            except Exception as e:
                messages.error(request, f"An error occurred: {e}")

        context = {'parent_location': parent_location, 'selected_spaces': spaces, 'count': count,
                   'single_form': form, 'paste_form': BulkCreatePasteForm()}
        return render(request, 'sample_control/sample_item_bulk_form.html', context)

    def _handle_paste_form(self, request, parent_location, spaces, count):
        form = BulkCreatePasteForm(request.POST)
        if form.is_valid():
            pasted_data = form.cleaned_data['data']
            num_targets = len(spaces) if spaces else count

            if len(pasted_data) != num_targets:
                messages.error(request, f"The number of rows in your data ({len(pasted_data)}) does not match the number of targets ({num_targets}).")
            else:
                try:
                    with transaction.atomic():
                        if spaces:
                            for space_coord, data in zip(spaces, pasted_data):
                                row, col = space_coord.split(',')
                                sample = SampleItem.objects.create(name=data[0], catalog_number=data[1], lot_number=data[2], description=data[3])
                                space, _ = LocationSpace.objects.get_or_create(parent_location=parent_location, row=row, col=col)
                                space.occupied_by_sample_item = sample
                                space.save()
                        elif count > 0:
                            for data in pasted_data:
                                SampleItem.objects.create(source_location=parent_location, name=data[0], catalog_number=data[1], lot_number=data[2], description=data[3])
                        messages.success(request, f"Successfully created {num_targets} samples.")
                        return redirect('sample_control:sample_location_detail', location_pk=parent_location.pk)
                except Exception as e:
                    messages.error(request, f"An error occurred: {e}")

        context = {'parent_location': parent_location, 'selected_spaces': spaces, 'count': count,
                   'single_form': BulkCreateSingleSampleForm(), 'paste_form': form}
        return render(request, 'sample_control/sample_item_bulk_form.html', context)


@method_decorator(permission_required('sample_control.delete_sampleitem'), name='dispatch')
class SampleItemBulkDeleteConfirmView(View):
    """
    Displays a confirmation page listing all samples selected for bulk deletion.
    """
    def post(self, request, *args, **kwargs):
        sample_pks = request.POST.getlist('selected_samples')
        if not sample_pks:
            messages.error(request, "You did not select any samples to delete.")
            return redirect('sample_control:sample_location_detail', location_pk=kwargs.get('location_pk'))

        context = {
            'samples_to_delete': SampleItem.objects.filter(pk__in=sample_pks),
            'location_pk': kwargs.get('location_pk'),
        }
        return render(request, 'sample_control/sample_item_bulk_confirm_delete.html', context)


@method_decorator(permission_required('sample_control.delete_sampleitem'), name='dispatch')
class SampleItemBulkDeletePerformView(View):
    """
    Handles the actual bulk deletion of selected SampleItems.
    """
    def post(self, request, *args, **kwargs):
        sample_pks = request.POST.getlist('selected_samples')
        if sample_pks:
            try:
                with transaction.atomic():
                    count, _ = SampleItem.objects.filter(pk__in=sample_pks).delete()
                    messages.success(request, f"Successfully deleted {count} samples.")
            except Exception as e:
                messages.error(request, f"An error occurred while deleting samples: {e}")
        
        return redirect('sample_control:sample_location_detail', location_pk=kwargs.get('location_pk'))