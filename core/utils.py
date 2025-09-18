"""
Provides core utility functions used across different apps in the project.
"""

# Standard Library Imports
from typing import Dict, List

# Local Imports
from location_configuration.models import Location, LocationSpace


def generate_space_grid(parent_location: Location) -> List[List[Dict]]:
    """
    Generates a 2D list representing a location's grid for template rendering.

    This function efficiently fetches all spaces and their occupants for a given
    parent location in a single query, then maps them to a grid structure. This
    prevents N+1 query problems in the template.

    Args:
        parent_location: The Location instance for which to generate the grid.
                         This location must have a type where `can_have_spaces`
                         is True.

    Returns:
        A 2D list (list of lists) where each inner element is a dictionary
        containing details about a single space, including its coordinates
        and any occupant information.
    """
    location_type = parent_location.source_location_type
    rows = location_type.space_rows or 0
    cols = location_type.space_cols or 0

    # Pre-fetch all related occupants in a single, efficient query.
    spaces_qs = LocationSpace.objects.filter(
        parent_location=parent_location
    ).select_related(
        'occupied_by_location',
        'occupied_by_sample_item'
    )

    # Create a dictionary mapping coordinates to space objects for O(1) lookups.
    space_map = {(space.row, space.col): space for space in spaces_qs}

    grid = []
    for r in range(1, rows + 1):
        row_list = []
        for c in range(1, cols + 1):
            space = space_map.get((r, c))
            cell_data = {
                'row': r,
                'col': c,
                'occupant_name': None,
                'occupant_type': None,
                'occupant_id': None,
            }

            if space:
                # Prioritize sample item, then location, to determine occupant.
                if space.occupied_by_sample_item:
                    cell_data.update({
                        'occupant_name': space.occupied_by_sample_item.name,
                        'occupant_type': 'sample',
                        'occupant_id': space.occupied_by_sample_item.pk,
                    })
                elif space.occupied_by_location:
                    cell_data.update({
                        'occupant_name': space.occupied_by_location.name,
                        'occupant_type': 'location',
                        'occupant_id': space.occupied_by_location.pk,
                    })

            row_list.append(cell_data)
        grid.append(row_list)

    return grid