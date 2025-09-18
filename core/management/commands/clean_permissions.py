"""
Defines a custom management command to clean up orphaned permissions and
content types from the database.
"""

from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from django.apps import apps

class Command(BaseCommand):
    """
    A Django management command that finds and deletes stale content types
    and their associated permissions.
    """
    help = 'Removes stale content types and permissions for models that no longer exist.'

    def handle(self, *args, **options):
        self.stdout.write("Searching for stale content types...")

        # Find all content types that do NOT correspond to a current model
        stale_content_types = [
            ct for ct in ContentType.objects.all()
            if ct.model_class() is None
        ]

        if not stale_content_types:
            self.stdout.write(self.style.SUCCESS("No stale content types found. Your database is clean."))
            return

        self.stdout.write(f"Found {len(stale_content_types)} stale content type(s).")

        # Delete the permissions and content types associated with the stale models
        for ct in stale_content_types:
            self.stdout.write(f"  - Deleting permissions for {ct.app_label} | {ct.model}...")
            
            # First, delete the related permissions
            perm_delete_count, _ = Permission.objects.filter(content_type=ct).delete()
            self.stdout.write(f"    ...deleted {perm_delete_count} permissions.")

            # Then, delete the content type itself
            self.stdout.write(f"  - Deleting content type {ct.app_label} | {ct.model}...")
            ct.delete()

        self.stdout.write(self.style.SUCCESS("Successfully cleaned up all stale content types and permissions."))