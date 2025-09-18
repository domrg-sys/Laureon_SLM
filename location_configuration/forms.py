"""
Defines the forms used for creating and updating LocationType and Location
objects in the location_configuration app.
"""

# Django Imports
from django import forms
from django.db.models import Exists, OuterRef, Q

# Local Imports
from core.forms import BaseForm
from core.templatetags.grid_helpers import to_row_letter
from sample_control.models import SampleItem

from .models import Location, LocationSpace, LocationType


class LockableCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    """
    A custom CheckboxSelectMultiple widget that can disable specific choices.

    This is used to prevent users from unselecting parent types that are
    currently in use by a LocationType.
    """
    def __init__(self, *args, **kwargs):
        self.locked_choices = kwargs.pop('locked_choices', set())
        super().__init__(*args, **kwargs)

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if value in self.locked_choices:
            option['attrs']['disabled'] = True
        return option

    def value_from_datadict(self, data, files, name):
        """
        Override to ensure locked choices are always included.
        """
        value = super().value_from_datadict(data, files, name)
        if value is None:
            return None
        # When the form is submitted, disabled values are not included in the POST
        # data. We need to add them back in to ensure they remain checked visually
        # if the form has errors and is re-rendered.
        return list(set(value) | set(map(str, self.locked_choices)))


class LocationTypeCreateForm(BaseForm):
    """A form for creating a new LocationType instance."""
    class Meta:
        model = LocationType
        fields = [
            'name', 'can_store_samples', 'can_have_spaces',
            'space_rows', 'space_cols', 'allowed_parent_types'
        ]
        widgets = {
            'allowed_parent_types': forms.CheckboxSelectMultiple,
        }


class LocationTypeEditForm(BaseForm):
    """
    A form for updating an existing LocationType, with complex logic to lock
    fields that cannot be changed once the type is in use.
    """
    class Meta:
        model = LocationType
        fields = [
            'name', 'can_store_samples', 'can_have_spaces',
            'space_rows', 'space_cols', 'allowed_parent_types'
        ]
        widgets = {
            'allowed_parent_types': LockableCheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = self.instance

        if not (instance and instance.pk):
            return

        # Step 1: Prevent circular dependencies for 'allowed_parent_types'.
        self._prevent_circular_dependencies()

        # Step 2: Lock parent types that are already in use.
        self._lock_in_use_parent_types()

        # Step 3: Lock space-related fields if any location of this type is in use.
        self._lock_space_fields_if_in_use()

        # Step 4: Lock sample storage field if samples are stored in this type.
        self._lock_sample_storage_field_if_in_use()

    def _prevent_circular_dependencies(self):
        """Exclude the instance itself and its descendants from the parent choices."""
        descendants = self.instance.get_descendants()
        excluded_ids = {self.instance.pk} | {d.pk for d in descendants}
        self.fields['allowed_parent_types'].queryset = LocationType.objects.exclude(pk__in=excluded_ids)

    def _lock_in_use_parent_types(self):
        """Find and lock any parent types that are actively being used."""
        # Find parents from direct relationships (Location -> Location)
        direct_parents = set(Location.objects.filter(
            source_location_type=self.instance, parent__isnull=False
        ).values_list('parent__source_location_type_id', flat=True).distinct())

        # Find parents from space relationships (Location -> LocationSpace -> Location)
        space_parents = set(Location.objects.filter(
            source_location_type=self.instance, occupied_space__isnull=False
        ).values_list('occupied_space__parent_location__source_location_type_id', flat=True).distinct())

        self.locked_parent_type_ids = direct_parents.union(space_parents)
        self.fields['allowed_parent_types'].widget.locked_choices = self.locked_parent_type_ids

    def _lock_space_fields_if_in_use(self):
        """Disable space-related fields if any location of this type is in use."""
        space_occupied_subquery = LocationSpace.objects.filter(
            Q(occupied_by_location__isnull=False) | Q(occupied_by_sample_item__isnull=False),
            parent_location=OuterRef('pk')
        )
        is_any_location_in_use = self.instance.location_set.annotate(
            has_children=Exists(Location.objects.filter(parent=OuterRef('pk'))),
            has_items=Exists(self.instance.location_set.filter(sampleitem__source_location=OuterRef('pk'))),
            has_occupied_spaces=Exists(space_occupied_subquery)
        ).filter(
            Q(has_children=True) | Q(has_items=True) | Q(has_occupied_spaces=True)
        ).exists()

        if is_any_location_in_use:
            for field_name in ['can_have_spaces', 'space_rows', 'space_cols']:
                self.fields[field_name].disabled = True
            self.fields['can_have_spaces'].help_text = "This setting is locked because locations of this type are in use."

    def _lock_sample_storage_field_if_in_use(self):
        """Disable sample storage field if samples are stored in this type."""
        has_associated_samples = SampleItem.objects.filter(
            Q(source_location__source_location_type=self.instance) |
            Q(occupied_space__parent_location__source_location_type=self.instance)
        ).exists()

        if has_associated_samples:
            self.fields['can_store_samples'].disabled = True
            self.fields['can_store_samples'].help_text = "This setting is locked because samples are stored in locations of this type."

    def clean(self):
        """
        Restore original values for disabled fields to prevent data loss upon saving.
        """
        cleaned_data = super().clean()
        for field_name, field in self.fields.items():
            if field.disabled:
                cleaned_data[field_name] = getattr(self.instance, field_name)
        return cleaned_data

    def clean_allowed_parent_types(self):
        """
        Ensure that locked (disabled) parent types are not removed from the
        ManyToMany relationship when the form is saved.
        """
        submitted_parents = self.cleaned_data.get('allowed_parent_types', LocationType.objects.none())
        submitted_parent_ids = {p.id for p in submitted_parents}
        all_parent_ids = submitted_parent_ids.union(self.locked_parent_type_ids)
        return LocationType.objects.filter(pk__in=all_parent_ids)


class LocationCreateForm(BaseForm):
    """A form for creating a new Location, with display-only parent/space fields."""
    parent_display = forms.CharField(label="Parent Location", required=False, disabled=True)
    space_display = forms.CharField(label="Space", required=False, disabled=True)

    class Meta:
        model = Location
        fields = ['name', 'source_location_type']
        labels = {'source_location_type': 'Location Type'}

    def __init__(self, *args, **kwargs):
        parent_location = kwargs.pop('parent_location', None)
        space_coords = kwargs.pop('space_coords', None)
        super().__init__(*args, **kwargs)

        # Configure fields based on whether the location is a child or top-level.
        if parent_location:
            self.fields['parent_display'].initial = parent_location.name
            self.fields['source_location_type'].queryset = LocationType.objects.filter(
                allowed_parent_types=parent_location.source_location_type
            )
            # Display space info if applicable.
            if space_coords:
                row_letter = to_row_letter(space_coords['row'])
                self.fields['space_display'].initial = f"{row_letter}{space_coords['col']}"
            else:
                del self.fields['space_display']
        else:
            # Hide parent-related fields for top-level locations.
            del self.fields['parent_display']
            del self.fields['space_display']
            self.fields['source_location_type'].queryset = LocationType.objects.filter(
                allowed_parent_types__isnull=True
            )


class LocationEditForm(BaseForm):
    """A form for updating a Location, with display-only parent/space fields."""
    parent_display = forms.CharField(label="Parent Location", required=False, disabled=True)
    space_display = forms.CharField(label="Space", required=False, disabled=True)
    source_location_type_display = forms.CharField(label="Location Type", required=False, disabled=True)

    class Meta:
        model = Location
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = self.instance
        parent = instance.effective_parent

        self.fields['source_location_type_display'].initial = instance.source_location_type.name

        if parent:
            self.fields['parent_display'].initial = parent.name
        else:
            del self.fields['parent_display']
            del self.fields['space_display']

        if hasattr(instance, 'occupied_space') and instance.occupied_space:
            space = instance.occupied_space
            row_letter = to_row_letter(space.row)
            self.fields['space_display'].initial = f"{row_letter}{space.col}"
        else:
            if 'space_display' in self.fields:
                del self.fields['space_display']