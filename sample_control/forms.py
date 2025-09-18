"""
Defines the forms used for creating and managing SampleItem objects in the
sample_control application.
"""

# Django Imports
from django import forms
from django.core.exceptions import ValidationError

# Local Imports
from core.forms import BaseForm
from core.templatetags.grid_helpers import to_row_letter

from .models import SampleItem


class SampleItemCreateForm(BaseForm):
    """
    A form for creating a new SampleItem, including display-only fields for its
    intended parent location and space.
    """
    location_display = forms.CharField(label="Parent Location", required=False, disabled=True)
    space_display = forms.CharField(label="Space", required=False, disabled=True)

    class Meta:
        model = SampleItem
        fields = ['name', 'catalog_number', 'lot_number', 'description']

    def __init__(self, *args, **kwargs):
        parent_location = kwargs.pop('parent_location', None)
        space_coords = kwargs.pop('space_coords', None)
        super().__init__(*args, **kwargs)

        if not parent_location:
            # This case should not happen in the current workflow, but as a
            # safeguard, we remove the fields if there's no parent.
            del self.fields['location_display']
            if 'space_display' in self.fields:
                del self.fields['space_display']
            return

        self.fields['location_display'].initial = parent_location.name

        if space_coords:
            row_letter = to_row_letter(space_coords['row'])
            self.fields['space_display'].initial = f"{row_letter}{space_coords['col']}"
        else:
            if 'space_display' in self.fields:
                del self.fields['space_display']


class SampleItemEditForm(BaseForm):
    """A straightforward form for editing an existing SampleItem."""
    class Meta:
        model = SampleItem
        fields = ['name', 'catalog_number', 'lot_number', 'description']


class BulkCreateSingleSampleForm(BaseForm):
    """
    A form for defining the details of a single sample that will be created
    multiple times in a bulk operation.
    """
    class Meta:
        model = SampleItem
        fields = ['name', 'catalog_number', 'lot_number', 'description']


class BulkCreatePasteForm(forms.Form):
    """
    A form for creating multiple samples from pasted spreadsheet data.

    This form includes a textarea for raw data and custom validation to parse
    and clean the input.
    """
    data = forms.CharField(
        label="Pasted Data",
        widget=forms.Textarea(attrs={
            'rows': 10,
            'placeholder': 'Example:\nSample-A\tCat-001\tLot-001\tDescription for A\nSample-B\tCat-002\tLot-002\tDescription for B'
        }),
        help_text=(
            "Paste tab-separated data. Each line will create a new sample. "
            "Columns must be in the order: Name, Catalog Number, Lot Number, Description."
        )
    )

    def clean_data(self):
        """
        Parses the pasted text data into a list of lists.

        Raises:
            ValidationError: If a row contains more than the expected number
                             of columns.
        """
        raw_data = self.cleaned_data.get('data', '')
        lines = [line.strip() for line in raw_data.strip().split('\n')]
        parsed_data = []

        for i, line in enumerate(lines, 1):
            if not line:
                continue  # Skip empty lines

            columns = line.split('\t')
            if len(columns) > 4:
                raise ValidationError(
                    f"Line {i} has too many columns. Expected 3 (Name, Lot, "
                    f"Description), but found {len(columns)}."
                )

            # Pad with empty strings if columns are missing
            while len(columns) < 4:
                columns.append('')
            parsed_data.append(columns)

        return parsed_data