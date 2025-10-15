from psycopg2 import IntegrityError

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "flight_aircraft_spec")
class TestAircraftSpec(TransactionCase):
    """Test cases for aircraft specifications"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create test aircraft
        cls.aircraft_class = cls.env["flight.aircraft.class"].create(
            {
                "name": "Business Jet",
                "aircraft_category": "airplane",
            }
        )

        cls.aircraft_make = cls.env["flight.aircraft.make"].create(
            {
                "name": "Gulfstream",
            }
        )

        cls.aircraft_model = cls.env["flight.aircraft.model"].create(
            {
                "name": "G650",
                "make_id": cls.aircraft_make.id,
                "class_id": cls.aircraft_class.id,
                "engine_type": "turbofan",
                "gear_type": "retractable_tricycle",
                "code": "G650",
            }
        )

        cls.aircraft = cls.env["flight.aircraft"].create(
            {
                "registration": "N650GS",
                "model_id": cls.aircraft_model.id,
                "operator_id": cls.env.company.partner_id.id,
            }
        )

        # Create spec categories with unique codes for testing
        cls.category_amenity = cls.env["flight.aircraft.spec.category"].create(
            {
                "name": "Test Amenities",
                "code": "test_amenity",
                "sequence": 10,
            }
        )

        cls.category_performance = cls.env["flight.aircraft.spec.category"].create(
            {
                "name": "Test Performance",
                "code": "test_performance",
                "sequence": 20,
            }
        )

        # Create spec codes with unique identifiers for testing
        cls.spec_wifi = cls.env["flight.aircraft.spec.code"].create(
            {
                "category_id": cls.category_amenity.id,
                "code": "test_amenity.wifi",
                "name": "WiFi Available",
                "code_type": "bool",
                "sequence": 10,
            }
        )

        cls.spec_range = cls.env["flight.aircraft.spec.code"].create(
            {
                "category_id": cls.category_performance.id,
                "code": "test_performance.range",
                "name": "Maximum Range",
                "code_type": "float",
                "default_uom_id": cls.env.ref("flight_uom.product_uom_nm").id,
                "sequence": 10,
            }
        )

        cls.spec_notes = cls.env["flight.aircraft.spec.code"].create(
            {
                "category_id": cls.category_amenity.id,
                "code": "test_amenity.notes",
                "name": "Special Notes",
                "code_type": "text",
                "sequence": 20,
            }
        )

    def test_01_spec_category_creation(self):
        """Test specification category creation"""
        category = self.env["flight.aircraft.spec.category"].create(
            {
                "name": "Test Safety",
                "code": "test_safety",
                "description": "Safety equipment and features",
                "sequence": 30,
            }
        )

        self.assertTrue(category.id)
        self.assertEqual(category.name, "Test Safety")
        self.assertEqual(category.code, "test_safety")

    def test_02_spec_code_types(self):
        """Test different specification code types"""
        # Boolean type
        self.assertEqual(self.spec_wifi.code_type, "bool")

        # Float type with UOM
        self.assertEqual(self.spec_range.code_type, "float")
        self.assertTrue(self.spec_range.default_uom_id)

        # Text type
        self.assertEqual(self.spec_notes.code_type, "text")

    def test_03_aircraft_spec_assignment(self):
        """Test assigning specifications to aircraft"""
        # Boolean spec
        spec_wifi = self.env["flight.aircraft.spec"].create(
            {
                "aircraft_id": self.aircraft.id,
                "code_id": self.spec_wifi.id,
                "value_bool": True,
            }
        )

        self.assertTrue(spec_wifi.id)
        self.assertTrue(spec_wifi.value_bool)
        self.assertEqual(spec_wifi.display_name, "WiFi Available: Yes")

        # Float spec with UOM
        spec_range = self.env["flight.aircraft.spec"].create(
            {
                "aircraft_id": self.aircraft.id,
                "code_id": self.spec_range.id,
                "value_float": 7500.0,
                "uom_id": self.env.ref("flight_uom.product_uom_nm").id,
            }
        )

        self.assertEqual(spec_range.value_float, 7500.0)
        self.assertTrue(spec_range.uom_id)

        # Text spec
        spec_notes = self.env["flight.aircraft.spec"].create(
            {
                "aircraft_id": self.aircraft.id,
                "code_id": self.spec_notes.id,
                "value_text": "Custom interior design with sleeping quarters",
            }
        )

        self.assertEqual(
            spec_notes.value_text, "Custom interior design with sleeping quarters"
        )

    def test_04_spec_value_validation(self):
        """Test that only appropriate value field is used based on code type"""
        # Boolean spec should use value_bool
        spec_bool = self.env["flight.aircraft.spec"].create(
            {
                "aircraft_id": self.aircraft.id,
                "code_id": self.spec_wifi.id,
                "value_bool": True,
            }
        )
        self.assertTrue(spec_bool.value_bool)

        # Float spec should use value_float
        spec_float = self.env["flight.aircraft.spec"].create(
            {
                "aircraft_id": self.aircraft.id,
                "code_id": self.spec_range.id,
                "value_float": 5000.0,
            }
        )
        self.assertEqual(spec_float.value_float, 5000.0)

        # Text spec should use value_text
        spec_text = self.env["flight.aircraft.spec"].create(
            {
                "aircraft_id": self.aircraft.id,
                "code_id": self.spec_notes.id,
                "value_text": "Test note",
            }
        )
        self.assertEqual(spec_text.value_text, "Test note")

    def test_05_spec_sequence_ordering(self):
        """Test specification ordering by sequence"""
        specs = []

        for i in range(3):
            spec_code = self.env["flight.aircraft.spec.code"].create(
                {
                    "category_id": self.category_amenity.id,
                    "code": f"test.spec{i}",
                    "name": f"Test Spec {i}",
                    "code_type": "bool",
                    "sequence": (3 - i) * 10,  # Reverse sequence
                }
            )

            spec = self.env["flight.aircraft.spec"].create(
                {
                    "aircraft_id": self.aircraft.id,
                    "code_id": spec_code.id,
                    "value_bool": True,
                    "sequence": (3 - i) * 10,
                }
            )
            specs.append(spec)

        # Specs should be ordered by sequence
        ordered_specs = self.aircraft.spec_ids.sorted("sequence")
        self.assertEqual(ordered_specs[0].sequence, 10)
        self.assertEqual(ordered_specs[-1].sequence, 30)

    def test_06_spec_category_grouping(self):
        """Test grouping specifications by category"""
        # Create specs in different categories
        spec1 = self.env["flight.aircraft.spec"].create(
            {
                "aircraft_id": self.aircraft.id,
                "code_id": self.spec_wifi.id,
                "value_bool": True,
            }
        )

        spec2 = self.env["flight.aircraft.spec"].create(
            {
                "aircraft_id": self.aircraft.id,
                "code_id": self.spec_range.id,
                "value_float": 6000.0,
            }
        )

        # Group by category
        amenity_specs = self.aircraft.spec_ids.filtered(
            lambda s: s.code_id.category_id == self.category_amenity
        )
        performance_specs = self.aircraft.spec_ids.filtered(
            lambda s: s.code_id.category_id == self.category_performance
        )

        self.assertIn(spec1, amenity_specs)
        self.assertNotIn(spec1, performance_specs)
        self.assertIn(spec2, performance_specs)
        self.assertNotIn(spec2, amenity_specs)

    def test_07_spec_assignment_to_different_aircraft(self):
        """Test specification assignment to different aircraft"""
        # Create a second aircraft for testing
        aircraft2 = self.env["flight.aircraft"].create(
            {
                "registration": "N651GS",
                "model_id": self.aircraft_model.id,
                "operator_id": self.env.company.partner_id.id,
            }
        )

        # Add specs to first aircraft
        self.env["flight.aircraft.spec"].create(
            {
                "aircraft_id": self.aircraft.id,
                "code_id": self.spec_wifi.id,
                "value_bool": True,
            }
        )

        self.env["flight.aircraft.spec"].create(
            {
                "aircraft_id": self.aircraft.id,
                "code_id": self.spec_range.id,
                "value_float": 7000.0,
            }
        )

        # Add different specs to second aircraft
        self.env["flight.aircraft.spec"].create(
            {
                "aircraft_id": aircraft2.id,
                "code_id": self.spec_wifi.id,
                "value_bool": False,  # Different value
            }
        )

        # Test that specs are properly assigned to their respective aircraft
        self.assertEqual(len(self.aircraft.spec_ids), 2)
        self.assertEqual(len(aircraft2.spec_ids), 1)

        # Test that each aircraft has the correct spec values
        aircraft1_wifi = self.aircraft.spec_ids.filtered(
            lambda s: s.code_id == self.spec_wifi
        )
        aircraft2_wifi = aircraft2.spec_ids.filtered(
            lambda s: s.code_id == self.spec_wifi
        )

        self.assertTrue(aircraft1_wifi.value_bool)
        self.assertFalse(aircraft2_wifi.value_bool)

    def test_08_spec_unique_per_aircraft(self):
        """Test that each spec code can only be assigned once per aircraft"""
        # Create first spec
        self.env["flight.aircraft.spec"].create(
            {
                "aircraft_id": self.aircraft.id,
                "code_id": self.spec_wifi.id,
                "value_bool": True,
            }
        )

        # Try to create duplicate spec for same aircraft
        with self.assertRaises(IntegrityError):
            self.env["flight.aircraft.spec"].create(
                {
                    "aircraft_id": self.aircraft.id,
                    "code_id": self.spec_wifi.id,  # Same code
                    "value_bool": False,
                }
            )

    def test_09_spec_uom_conversion(self):
        """Test unit of measure handling for float specs"""
        # Create spec with nautical miles
        spec_nm = self.env["flight.aircraft.spec"].create(
            {
                "aircraft_id": self.aircraft.id,
                "code_id": self.spec_range.id,
                "value_float": 7500.0,
                "uom_id": self.env.ref("flight_uom.product_uom_nm").id,
            }
        )

        self.assertEqual(spec_nm.value_float, 7500.0)
        self.assertEqual(spec_nm.uom_id.name, "nm")

        # Could test conversion to other units if needed
        # km = spec_nm.value_float * 1.852  # 1 nm = 1.852 km
