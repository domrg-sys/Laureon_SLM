"""
Defines Django signal handlers for the location_configuration app.

These signals help automate certain database cleanup tasks, ensuring data
integrity and efficiency.
"""

# Django Imports
from django.db.models.signals import post_delete
from django.dispatch import receiver

# Local Imports
from sample_control.models import SampleItem

from .models import Location


@receiver(post_delete, sender=SampleItem)
@receiver(post_delete, sender=Location)
def delete_empty_location_space(sender, instance, **kwargs):
    """
    Listens for the deletion of a SampleItem or a Location.

    After a SampleItem or Location is deleted, this signal checks if it was
    occupying a LocationSpace. If so, the now-empty LocationSpace object
    is also deleted to keep the database clean.
    """
    # The 'occupied_space' is a OneToOneField, so if the deleted instance
    # had a related space, that space is now guaranteed to be empty.
    if hasattr(instance, 'occupied_space') and instance.occupied_space:
        instance.occupied_space.delete()