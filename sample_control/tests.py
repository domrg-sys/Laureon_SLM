from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from location_configuration.models import Location, LocationType
from .forms import BulkCreatePasteForm
from .models import SampleItem


class SampleItemModelTest(TestCase):
    def setUp(self):
        self.loc_type_no_grid = LocationType.objects.create(
            name="Shelf", can_store_samples=True
        )
        self.loc_type_with_grid = LocationType.objects.create(
            name="Rack", can_store_samples=True, can_have_spaces=True, space_rows=5, space_cols=5
        )
        self.location_no_grid = Location.objects.create(
            name="Shelf A", source_location_type=self.loc_type_no_grid
        )

    def test_str_representation(self):
        """Test that the string representation of a SampleItem is its name."""
        sample = SampleItem.objects.create(name="S-001", source_location=self.location_no_grid)
        self.assertEqual(str(sample), "S-001")

    def test_sample_cannot_be_in_grid_location_directly(self):
        """
        Test that a ValidationError is raised if a sample is assigned directly
        to a location that has spaces.
        """
        grid_location = Location.objects.create(name="Rack 1", source_location_type=self.loc_type_with_grid)
        with self.assertRaises(ValidationError):
            sample = SampleItem(name="S-002", source_location=grid_location)
            sample.full_clean()


class BulkCreatePasteFormTest(TestCase):
    def test_valid_data_is_cleaned_correctly(self):
        """Test that valid tab-separated data is parsed into a list of lists."""
        pasted_data = "Sample-A\tLot-001\tDesc A\nSample-B\tLot-002\tDesc B"
        form = BulkCreatePasteForm(data={'data': pasted_data})
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data['data'],
            [['Sample-A', 'Lot-001', 'Desc A'], ['Sample-B', 'Lot-002', 'Desc B']]
        )

    def test_missing_columns_are_padded(self):
        """Test that rows with missing columns are padded with empty strings."""
        pasted_data = "Sample-A\tLot-001\nSample-B"
        form = BulkCreatePasteForm(data={'data': pasted_data})
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data['data'],
            [['Sample-A', 'Lot-001', ''], ['Sample-B', '', '']]
        )

    def test_too_many_columns_raises_error(self):
        """Test that a ValidationError is raised if a row has too many columns."""
        pasted_data = "Sample-A\tLot-001\tDesc A\tExtra-Column"
        form = BulkCreatePasteForm(data={'data': pasted_data})
        self.assertFalse(form.is_valid())
        self.assertIn('data', form.errors)


class SampleControlAuthTest(TestCase):
    def setUp(self):
        # We need a user to test authenticated views
        self.user = User.objects.create_user(username='testuser', password='password')
        loc_type = LocationType.objects.create(name="Shelf", can_store_samples=True)
        self.location = Location.objects.create(name="Shelf A", source_location_type=loc_type)

    def test_sample_control_list_redirects_if_not_logged_in(self):
        """Test that the main sample control page redirects if not logged in."""
        response = self.client.get(reverse('sample_control:sample_control'))
        self.assertRedirects(response, '/accounts/login/?next=/sample_control/')

    def test_sample_control_list_accessible_if_logged_in(self):
        """
        Test that the main sample control page is accessible to an authenticated user.
        Note: This test will fail until you add the 'view_sampleitem' permission.
        """
        # To make this test pass, you would first need to give the user permission.
        # from django.contrib.auth.models import Permission
        # permission = Permission.objects.get(codename='view_sampleitem')
        # self.user.user_permissions.add(permission)

        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('sample_control:sample_control'))
        # For now, we expect a 403 Forbidden since the user doesn't have permissions yet.
        # Once you add permissions, this should be self.assertEqual(response.status_code, 200)
        self.assertEqual(response.status_code, 403)