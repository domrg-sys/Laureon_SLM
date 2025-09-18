"""
Defines the data models for the Location Configuration application, establishing
the hierarchical structure for physical locations within the system.
"""

# Django Imports
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class LocationType(models.Model):
    """
    A blueprint for a physical location (e.g., "Freezer Rack", "96-Well Plate"),
    defining its properties and nesting rules.
    """
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Name",
        help_text="The unique name for this type of location."
    )
    allowed_parent_types = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        verbose_name="Allowed Parent Types",
        help_text="Defines which location types this type can be nested within."
    )
    can_store_samples = models.BooleanField(
        default=False,
        verbose_name="Can Store Samples",
        help_text="Indicates if locations of this type can directly store samples."
    )
    can_have_spaces = models.BooleanField(
        default=False,
        verbose_name="Can Have Spaces",
        help_text="If true, instances of this type are grid containers (e.g., a rack or plate)."
    )
    space_rows = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Grid Rows"
    )
    space_cols = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Grid Columns"
    )

    class Meta:
        verbose_name = "Location Type"
        verbose_name_plural = "Location Types"
        ordering = ['name']

    def __str__(self):
        return self.name

    def clean(self):
        """Custom model validation to enforce data integrity."""
        # Enforce case-insensitive name uniqueness
        if self.name:
            qs = LocationType.objects.filter(name__iexact=self.name)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({
                    'name': f"A Location Type with the name '{self.name}' already exists."
                })

        if self.can_have_spaces and (self.space_rows is None or self.space_cols is None):
            raise ValidationError("Grid dimensions (rows, cols) are required when 'can_have_spaces' is true.")

        if not self.can_have_spaces and (self.space_rows is not None or self.space_cols is not None):
            raise ValidationError("Grid dimensions must be null when 'can_have_spaces' is false.")

        # Prevent circular dependencies in parent-child relationships
        if self.pk:
            descendants = self.get_descendants()
            for parent in self.allowed_parent_types.all():
                if parent == self or parent in descendants:
                    raise ValidationError(
                        f"Circular dependency detected: '{parent.name}' cannot be a parent because it is a "
                        f"descendant of or the same as '{self.name}'."
                    )

    @property
    def is_in_use(self):
        """
        Checks if this LocationType is actively used.
        Note: For checking multiple objects, use the annotated queryset in the view
        to prevent N+1 queries.
        """
        return self.location_set.exists() or self.locationtype_set.exists()

    def get_descendants(self):
        """
        Efficiently finds all descendants of this LocationType using an
        iterative, non-recursive approach to prevent excessive database queries.
        """
        descendants = set()
        queue = list(self.locationtype_set.all())
        processed_ids = {self.pk} | {item.pk for item in queue}

        while queue:
            current_type = queue.pop(0)
            descendants.add(current_type)

            children = current_type.locationtype_set.exclude(pk__in=processed_ids)
            for child in children:
                if child.pk not in processed_ids:
                    queue.append(child)
                    processed_ids.add(child.pk)
        return descendants


class Location(models.Model):
    """
    A concrete instance of a physical location (e.g., "Lab A, Freezer 1"),
    based on a LocationType.
    """
    name = models.CharField(
        max_length=255,
        verbose_name="Name",
        help_text="The unique name for this specific location instance."
    )
    source_location_type = models.ForeignKey(
        LocationType,
        on_delete=models.PROTECT,
        verbose_name="Location Type"
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='child_locations',
        verbose_name="Parent Location",
        help_text="The parent location this location is directly nested inside."
    )

    class Meta:
        verbose_name = "Location"
        verbose_name_plural = "Locations"
        ordering = ['name']

    def __str__(self):
        return self.name

    def clean(self):
        """Custom validation to enforce physical nesting and storage rules."""
        # Enforce global case-insensitive name uniqueness
        if self.name:
            qs = Location.objects.filter(name__iexact=self.name)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({
                    'name': f"A Location with the name '{self.name}' already exists."
                })

        # If the foreign key isn't set yet, don't run validation.
        if not hasattr(self, 'source_location_type'):
            return

        has_direct_parent = self.parent is not None
        has_space_parent = hasattr(self, 'occupied_space') and self.occupied_space is not None

        if has_direct_parent and has_space_parent:
            raise ValidationError("A location can be assigned to a parent location OR a parent space, not both.")

        # Rule: A "root" type (no allowed parents) must not be nested.
        is_root_type = not self.source_location_type.allowed_parent_types.exists()
        if is_root_type and (has_direct_parent or has_space_parent):
            raise ValidationError(f"Location type '{self.source_location_type}' cannot be nested inside another location.")

        # Rule: Validate nesting within a direct parent.
        if has_direct_parent:
            parent_type = self.parent.source_location_type
            if parent_type not in self.source_location_type.allowed_parent_types.all():
                raise ValidationError("This location's type is not allowed inside the chosen parent's type.")
            if parent_type.can_have_spaces:
                raise ValidationError("The chosen parent is a grid container; you must assign this to a specific space within it.")

        # Rule: Validate nesting within a parent's space.
        if has_space_parent:
            space_parent_type = self.occupied_space.parent_location.source_location_type
            if space_parent_type not in self.source_location_type.allowed_parent_types.all():
                raise ValidationError("This location's type is not allowed inside the chosen parent space's location type.")

    @property
    def is_in_use(self):
        """
        Checks if the Location is in use, either directly or via its child spaces.
        Note: For checking multiple objects, use the annotated queryset in the view
        to prevent N+1 queries.
        """
        if self.child_locations.exists() or self.sampleitem_set.exists():
            return True

        return self.spaces.filter(
            Q(occupied_by_location__isnull=False) |
            Q(occupied_by_sample_item__isnull=False)
        ).exists()

    @property
    def effective_parent(self):
        """
        Returns the logical parent of this location, whether it's a direct parent
        or the parent of the space it occupies.
        """
        if self.parent:
            return self.parent
        if hasattr(self, 'occupied_space') and self.occupied_space:
            return self.occupied_space.parent_location
        return None

    @property
    def effective_children(self):
        """
        Returns a sorted list of all logical children, using data that should be
        pre-fetched by the view for efficiency.
        """
        # .all() will use the pre-fetched data from the view, avoiding a new query
        direct_children = list(self.child_locations.all())

        space_children = []
        # .all() here will also use the pre-fetched data
        for space in self.spaces.all():
            if space.occupied_by_location:
                space_children.append(space.occupied_by_location)

        # This sorting happens in Python on the already-retrieved objects
        return sorted(direct_children + space_children, key=lambda loc: loc.name)

    def get_path(self):
        """
        Traces the location hierarchy up to the root and returns a list of
        locations, from the top-level parent to the current location.
        """
        path = []
        current = self
        while current:
            path.append(current)
            current = current.effective_parent
        return reversed(path)


class LocationSpace(models.Model):
    """
    A single, addressable slot (e.g., a well or a position) within a
    grid-based Location.
    """
    parent_location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='spaces',
        verbose_name="Parent Location"
    )
    row = models.PositiveIntegerField()
    col = models.PositiveIntegerField()

    occupied_by_location = models.OneToOneField(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='occupied_space'
    )
    occupied_by_sample_item = models.OneToOneField(
        'sample_control.SampleItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='occupied_space'
    )

    class Meta:
        verbose_name = "Location Space"
        verbose_name_plural = "Location Spaces"
        unique_together = ('parent_location', 'row', 'col')
        ordering = ['parent_location', 'row', 'col']
        constraints = [
            # Guarantees that a space can have at most one occupant of any type.
            models.CheckConstraint(
                name="only_one_occupant",
                check=(
                    ~Q(occupied_by_location__isnull=False, occupied_by_sample_item__isnull=False)
                )
            )
        ]

    def __str__(self):
        return f"{self.parent_location.name} [R{self.row}, C{self.col}]"

    def clean(self):
        """Validates that the space's coordinates are within the parent's defined bounds."""
        if not hasattr(self.parent_location, 'source_location_type'):
            return

        max_rows = self.parent_location.source_location_type.space_rows
        max_cols = self.parent_location.source_location_type.space_cols

        if self.row > max_rows:
            raise ValidationError(f"Row {self.row} exceeds the maximum of {max_rows}.")
        if self.col > max_cols:
            raise ValidationError(f"Column {self.col} exceeds the maximum of {max_cols}.")