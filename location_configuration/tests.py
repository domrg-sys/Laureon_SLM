from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from .forms import LocationTypeEditForm
from .models import Location, LocationType
from sample_control.models import SampleItem

class LocationTypeModelTest(TestCase):
    def test_str_representation(self):
        """Test that the string representation of a LocationType is its name."""
        location_type = LocationType.objects.create(name="Test Freezer")
        self.assertEqual(str(location_type), "Test Freezer")

    def test_spaces_require_dimensions(self):
        """
        Test that a ValidationError is raised if can_have_spaces is True
        but space_rows or space_cols is None.
        """
        with self.assertRaises(ValidationError):
            lt = LocationType(name="Test Rack", can_have_spaces=True, space_rows=None, space_cols=10)
            lt.full_clean()  # This is what triggers model validation

        with self.assertRaises(ValidationError):
            lt = LocationType(name="Test Rack 2", can_have_spaces=True, space_rows=10, space_cols=None)
            lt.full_clean()

class LocationTypeEditFormTest(TestCase):
    def setUp(self):
        # Create a basic setup for the tests
        self.location_type_in_use = LocationType.objects.create(name="Freezer", can_store_samples=True)
        self.location = Location.objects.create(name="F1", source_location_type=self.location_type_in_use)
        SampleItem.objects.create(name="S1", source_location=self.location)

    def test_can_store_samples_field_is_disabled_when_in_use(self):
        """
        Test that the 'can_store_samples' field is disabled if the
        location type has associated samples.
        """
        form = LocationTypeEditForm(instance=self.location_type_in_use)
        self.assertTrue(form.fields['can_store_samples'].disabled)

class LocationListViewAuthTest(TestCase):
    def test_redirect_if_not_logged_in(self):
        """
        Test that the user is redirected to the login page if they are not
        authenticated.
        """
        response = self.client.get(reverse('location_configuration:locations'))
        self.assertRedirects(response, '/accounts/login/?next=/location_configuration/locations/')