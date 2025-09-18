"""
Defines the data models for the Sample Control application, which handles the
tracking of individual physical samples.
"""

# Django Imports
from django.core.exceptions import ValidationError
from django.db import models


class SampleItem(models.Model):
    """
    Represents a unique, individually tracked physical object, such as a
    patient sample or a chemical compound.
    """
    name = models.CharField(
        max_length=255,
        verbose_name="Sample Name",
        help_text="The unique name or identifier for this sample."
    )
    catalog_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Catalog Number",
        help_text="The catalog number for the sample, if applicable."
    )
    lot_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Lot Number",
        help_text="The production lot number, if applicable."
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description",
        help_text="Any additional notes or description for this sample."
    )
    source_location = models.ForeignKey(
        'location_configuration.Location',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Source Location",
        help_text="The location where this sample is stored, if not in a specific space."
    )
    # Note: The 'occupied_space' field is a reverse OneToOne relation from
    # the LocationSpace model in the 'location_configuration' app.

    class Meta:
        verbose_name = "Sample Item"
        verbose_name_plural = "Sample Items"
        ordering = ['name']

    def __str__(self):
        return self.name

    def clean(self):
        """
        Custom model validation to enforce storage rules and prevent data
        inconsistencies.
        """
        # Determine the storage state of the sample.
        is_in_direct_location = self.source_location is not None
        # The 'occupied_space' reverse relation can only exist if the instance is saved.
        is_in_space = self.pk is not None and hasattr(self, 'occupied_space') and self.occupied_space is not None

        # On initial creation, if no location is set, validation can be skipped.
        if not self.pk and not is_in_direct_location:
            return

        # --- Rule: A sample must be in one and only one place. ---
        if not (is_in_direct_location or is_in_space):
            raise ValidationError("A sample must be stored in either a location or a location space.")
        if is_in_direct_location and is_in_space:
            raise ValidationError("A sample cannot be in both a direct location and a location space simultaneously.")

        # --- Rules for storage in a direct location. ---
        if is_in_direct_location:
            location_type = self.source_location.source_location_type
            if location_type.can_have_spaces:
                raise ValidationError("This sample must be assigned to a specific space within the chosen location, not the location itself.")
            if not location_type.can_store_samples:
                raise ValidationError("The selected location's type is not designated for storing samples.")

        # --- Rules for storage in a location space. ---
        if is_in_space:
            parent_location_type = self.occupied_space.parent_location.source_location_type
            if not parent_location_type.can_have_spaces:
                raise ValidationError("The chosen space belongs to a location that does not have spaces.")
            if not parent_location_type.can_store_samples:
                raise ValidationError("The selected space's parent location is not designated for storing samples.")

    def get_location_path(self):
        """
        Traces the location hierarchy up to the root and returns a list of
        locations, from the top-level parent to the immediate location.
        """
        path = []
        # First, determine the immediate location of the sample.
        current_location = self.source_location
        if not current_location and hasattr(self, 'occupied_space') and self.occupied_space:
            current_location = self.occupied_space.parent_location

        # Then, traverse up the hierarchy using the 'effective_parent' property.
        while current_location:
            path.append(current_location)
            current_location = current_location.effective_parent

        # The path is built from child to parent, so it must be reversed for display.
        return reversed(path)