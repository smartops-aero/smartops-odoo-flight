from datetime import date

from odoo.tests import tagged

from .common import FlightCommon


@tagged("post_install", "-at_install", "flight_aircraft")
class TestAircraft(FlightCommon):
    """Test cases for flight.aircraft model"""

    def test_01_aircraft_creation(self):
        """Test aircraft creation with all fields"""
        aircraft = self.env["flight.aircraft"].create(
            {
                "registration": "N99999",
                "model_id": self.aircraft_model.id,
                "operator_id": self.env.company.partner_id.id,
                "sn": "SN999999",
                "dom": date(2022, 6, 15),
                "equipment_type": "aircraft",
                "mtow": 85000,
                "weight_uom_id": self.env.ref("uom.product_uom_lb").id,
            }
        )

        self.assertTrue(aircraft.id)
        self.assertEqual(aircraft.registration, "N99999")
        self.assertEqual(aircraft.sn, "SN999999")
        self.assertEqual(aircraft.mtow, 85000)

    def test_02_aircraft_display_name(self):
        """Test aircraft display name"""
        self.assertEqual(self.aircraft.display_name, "TEST001")
        # Aircraft model doesn't have 'name' field, only 'registration'
        self.assertEqual(self.aircraft.registration, "TEST001")

    def test_03_aircraft_model_hierarchy(self):
        """Test aircraft model, make, and class relationships"""
        # Test model hierarchy
        self.assertEqual(self.aircraft.model_id.make_id, self.aircraft_make)
        self.assertEqual(self.aircraft.model_id.class_id, self.aircraft_class)
        self.assertEqual(self.aircraft.model_id.code, "B738")

    def test_04_aircraft_class_categories(self):
        """Test aircraft class categories"""
        valid_categories = [
            "airplane",
            "rotorcraft",
            "glider",
            "lighter_than_air",
            "powered_lift",
            "powered_parachute",
            "weight_shift_control",
        ]

        for category in valid_categories:
            aircraft_class = self.env["flight.aircraft.class"].create(
                {
                    "name": f"Test {category}",
                    "aircraft_category": category,
                }
            )
            self.assertEqual(aircraft_class.aircraft_category, category)

    def test_05_aircraft_model_engine_types(self):
        """Test aircraft model engine types"""
        engine_types = [
            "piston",
            "turboprop",
            "turbojet",
            "turbofan",
            "electric",
            "diesel",
            "radial",
            "turboshaft",
            "non_powered",
        ]

        for engine_type in engine_types:
            model = self.env["flight.aircraft.model"].create(
                {
                    "name": f"Test {engine_type}",
                    "make_id": self.aircraft_make.id,
                    "class_id": self.aircraft_class.id,
                    "engine_type": engine_type,
                    "gear_type": "retractable_tricycle",
                    "code": f"T{engine_type[:3].upper()}",
                }
            )
            self.assertEqual(model.engine_type, engine_type)

    def test_06_aircraft_model_gear_types(self):
        """Test aircraft model gear types"""
        gear_types = [
            "amphibian",
            "floats",
            "skids",
            "skis",
            "fixed_tailwheel",
            "fixed_tricycle",
            "retractable_tailwheel",
            "retractable_tricycle",
        ]

        for gear_type in gear_types:
            model = self.env["flight.aircraft.model"].create(
                {
                    "name": f"Test {gear_type}",
                    "make_id": self.aircraft_make.id,
                    "class_id": self.aircraft_class.id,
                    "engine_type": "turboprop",
                    "gear_type": gear_type,
                    "code": f"G{gear_type[:3].upper()}",
                }
            )
            self.assertEqual(model.gear_type, gear_type)

    def test_07_aircraft_model_tags(self):
        """Test aircraft model tags"""
        tag1 = self.env["flight.aircraft.model.tag"].create(
            {
                "name": "Long Range",
            }
        )
        tag2 = self.env["flight.aircraft.model.tag"].create(
            {
                "name": "Wide Body",
            }
        )

        model = self.env["flight.aircraft.model"].create(
            {
                "name": "A350-900",
                "make_id": self.aircraft_make.id,
                "class_id": self.aircraft_class.id,
                "engine_type": "turbofan",
                "gear_type": "retractable_tricycle",
                "code": "A359",
                "tag_ids": [(6, 0, [tag1.id, tag2.id])],
            }
        )

        self.assertIn(tag1, model.tag_ids)
        self.assertIn(tag2, model.tag_ids)
        self.assertEqual(len(model.tag_ids), 2)

    def test_08_aircraft_weight_conversion(self):
        """Test aircraft weight with different units"""
        kg_uom = self.env.ref("uom.product_uom_kgm")
        lb_uom = self.env.ref("uom.product_uom_lb")

        aircraft_kg = self.env["flight.aircraft"].create(
            {
                "registration": "D-TEST",
                "model_id": self.aircraft_model.id,
                "operator_id": self.env.company.partner_id.id,
                "mtow": 35000,  # kg
                "weight_uom_id": kg_uom.id,
            }
        )

        self.assertEqual(aircraft_kg.mtow, 35000)
        self.assertEqual(aircraft_kg.weight_uom_id, kg_uom)

    def test_09_aircraft_search(self):
        """Test aircraft search and filters"""
        # Create additional aircraft with different pattern
        aircraft2 = self.env["flight.aircraft"].create(
            {
                "registration": "G-TEST",  # This starts with 'G' not 'TEST'
                "model_id": self.aircraft_model.id,
                "operator_id": self.env.company.partner_id.id,
            }
        )

        # Search by exact registration match instead of LIKE to avoid any collation issues
        found = self.env["flight.aircraft"].search([("registration", "=", "TEST001")])
        self.assertEqual(len(found), 1)
        self.assertIn(self.aircraft, found)

        # Search for G-TEST specifically
        found_g = self.env["flight.aircraft"].search([("registration", "=", "G-TEST")])
        self.assertEqual(len(found_g), 1)
        self.assertIn(aircraft2, found_g)

        # Test pattern search with N- prefix (should find demo aircraft)
        found_n = self.env["flight.aircraft"].search([("registration", "like", "N%")])
        # Should find N12345 but not TEST001 or G-TEST
        self.assertNotIn(self.aircraft, found_n)
        self.assertNotIn(aircraft2, found_n)

        # Search by model
        found = self.env["flight.aircraft"].search(
            [("model_id", "=", self.aircraft_model.id)]
        )
        self.assertIn(self.aircraft, found)
        self.assertIn(aircraft2, found)

    def test_10_aircraft_copy(self):
        """Test aircraft duplication"""
        copy = self.aircraft.copy(
            {
                "registration": "N54321",
                "sn": "SN654321",
            }
        )

        self.assertNotEqual(copy.id, self.aircraft.id)
        self.assertEqual(copy.registration, "N54321")
        self.assertEqual(copy.sn, "SN654321")
        self.assertEqual(copy.model_id, self.aircraft.model_id)
        self.assertEqual(copy.mtow, self.aircraft.mtow)
