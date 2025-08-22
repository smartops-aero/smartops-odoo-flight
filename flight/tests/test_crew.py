from psycopg2 import IntegrityError

from odoo.tests import tagged

from .common import FlightCommon


@tagged("post_install", "-at_install", "flight_crew")
class TestCrew(FlightCommon):
    """Test cases for flight.crew model"""

    def test_01_crew_role_creation(self):
        """Test crew role creation"""
        role = self.env["flight.crew.role"].create(
            {
                "name": "Flight Attendant",
                "description": "Cabin crew member responsible for passenger safety",
            }
        )

        self.assertTrue(role.id)
        self.assertEqual(role.name, "Flight Attendant")
        self.assertEqual(
            role.description, "Cabin crew member responsible for passenger safety"
        )

    def test_02_crew_assignment(self):
        """Test crew assignment to flight"""
        pilot = self.env["res.partner"].create(
            {
                "name": "Test Pilot",
                "is_company": False,
            }
        )

        flight = self.create_test_flight()

        crew = self.env["flight.crew"].create(
            {
                "flight_id": flight.id,
                "partner_id": pilot.id,
                "role_id": self.crew_role_pilot.id,
            }
        )

        self.assertTrue(crew.id)
        self.assertEqual(crew.flight_id, flight)
        self.assertEqual(crew.partner_id, pilot)
        self.assertEqual(crew.role_id, self.crew_role_pilot)

    def test_03_crew_display_name(self):
        """Test crew member display name"""
        pilot = self.env["res.partner"].create(
            {
                "name": "John Smith",
                "is_company": False,
            }
        )

        flight = self.create_test_flight()

        crew = self.env["flight.crew"].create(
            {
                "flight_id": flight.id,
                "partner_id": pilot.id,
                "role_id": self.crew_role_pilot.id,
            }
        )

        # Crew model uses custom display_name format (partner name and role)
        expected_display_name = "John Smith (Captain)"
        self.assertEqual(crew.display_name, expected_display_name)
        # Test the individual components
        self.assertEqual(crew.partner_id.name, "John Smith")
        self.assertEqual(crew.role_id.name, "Captain")

    def test_04_multiple_crew_same_flight(self):
        """Test multiple crew members on same flight"""
        flight = self.create_test_flight()

        crew_members = []
        for i in range(4):
            partner = self.env["res.partner"].create(
                {
                    "name": f"Crew Member {i}",
                    "is_company": False,
                }
            )

            role = (
                self.crew_role_pilot
                if i < 2
                else self.env["flight.crew.role"].create(
                    {
                        "name": "Flight Attendant",
                        "description": "Cabin crew member",
                    }
                )
            )

            crew = self.env["flight.crew"].create(
                {
                    "flight_id": flight.id,
                    "partner_id": partner.id,
                    "role_id": role.id,
                }
            )
            crew_members.append(crew)

        self.assertEqual(len(flight.crew_ids), 4)
        for crew in crew_members:
            self.assertIn(crew, flight.crew_ids)

    def test_05_crew_role_name_validation(self):
        """Test crew role name is required"""
        # Name is required - raises IntegrityError from database
        with self.assertRaises(IntegrityError):
            self.env["flight.crew.role"].create(
                {
                    "description": "Role without name",
                }
            )

    def test_06_crew_partner_validation(self):
        """Test that crew members must have a valid partner_id"""
        flight = self.create_test_flight()

        # Test that partner_id is required - raises IntegrityError from database
        with self.assertRaises(IntegrityError):
            self.env["flight.crew"].create(
                {
                    "flight_id": flight.id,
                    "role_id": self.crew_role_pilot.id,
                    # partner_id is intentionally missing - should fail because required=True
                }
            )

    def test_07_crew_copy_with_flight(self):
        """Test crew copying when flight is duplicated"""
        flight = self.create_test_flight()

        # Add crew
        pilot = self.env["res.partner"].create(
            {
                "name": "Original Pilot",
                "is_company": False,
            }
        )

        crew = self.env["flight.crew"].create(
            {
                "flight_id": flight.id,
                "partner_id": pilot.id,
                "role_id": self.crew_role_pilot.id,
            }
        )

        # Copy flight
        flight_copy = flight.copy()

        # Crew should be copied
        self.assertEqual(len(flight_copy.crew_ids), 1)
        crew_copy = flight_copy.crew_ids[0]
        self.assertEqual(crew_copy.partner_id, pilot)
        self.assertEqual(crew_copy.role_id, self.crew_role_pilot)
        self.assertNotEqual(crew_copy.id, crew.id)

    def test_08_crew_search_by_role(self):
        """Test searching crew by role"""
        flight1 = self.create_test_flight()
        flight2 = self.create_test_flight()

        pilot1 = self.env["res.partner"].create(
            {"name": "Pilot 1", "is_company": False}
        )
        pilot2 = self.env["res.partner"].create(
            {"name": "Pilot 2", "is_company": False}
        )

        crew1 = self.env["flight.crew"].create(
            {
                "flight_id": flight1.id,
                "partner_id": pilot1.id,
                "role_id": self.crew_role_pilot.id,
            }
        )

        crew2 = self.env["flight.crew"].create(
            {
                "flight_id": flight2.id,
                "partner_id": pilot2.id,
                "role_id": self.crew_role_copilot.id,
            }
        )

        # Search captains
        captains = self.env["flight.crew"].search(
            [("role_id", "=", self.crew_role_pilot.id)]
        )
        self.assertIn(crew1, captains)
        self.assertNotIn(crew2, captains)

        # Search first officers
        first_officers = self.env["flight.crew"].search(
            [("role_id", "=", self.crew_role_copilot.id)]
        )
        self.assertIn(crew2, first_officers)
        self.assertNotIn(crew1, first_officers)

    def test_09_crew_display_name_edge_cases(self):
        """Test crew display name with missing role"""
        pilot = self.env["res.partner"].create({
            "name": "Jane Doe",
            "is_company": False,
        })
        
        flight = self.create_test_flight()
        
        # Test crew without role (role_id is not required)
        crew_no_role = self.env["flight.crew"].create({
            "flight_id": flight.id,
            "partner_id": pilot.id,
            # No role_id specified
        })
        
        # Should show just the partner name when no role
        self.assertEqual(crew_no_role.display_name, "Jane Doe")
        
        # Test fallback when partner has empty name (edge case)
        empty_partner = self.env["res.partner"].create({
            "name": "",  # Empty name
            "is_company": False,
        })
        
        crew_empty_name = self.env["flight.crew"].create({
            "flight_id": flight.id,
            "partner_id": empty_partner.id,
            "role_id": self.crew_role_pilot.id,
        })
        
        # When partner name is empty, should show just the role
        self.assertEqual(crew_empty_name.display_name, "(Captain)")

    def test_10_multiple_roles_same_person_same_flight(self):
        """Test that one person can have multiple roles on same flight"""
        pilot = self.env["res.partner"].create({
            "name": "Multi Role Pilot",
            "is_company": False,
        })
        
        flight = self.create_test_flight()
        
        # Create safety officer role
        safety_role = self.env["flight.crew.role"].create({
            "name": "Safety Officer",
            "description": "Safety oversight"
        })
        
        # Same person as pilot
        crew_pilot = self.env["flight.crew"].create({
            "flight_id": flight.id,
            "partner_id": pilot.id,
            "role_id": self.crew_role_pilot.id,
        })
        
        # Same person as safety officer
        crew_safety = self.env["flight.crew"].create({
            "flight_id": flight.id,
            "partner_id": pilot.id,
            "role_id": safety_role.id,
        })
        
        # Both should be valid and different records
        self.assertNotEqual(crew_pilot.id, crew_safety.id)
        self.assertEqual(crew_pilot.partner_id, crew_safety.partner_id)
        self.assertEqual(crew_pilot.flight_id, crew_safety.flight_id)
        self.assertNotEqual(crew_pilot.role_id, crew_safety.role_id)
        
        # Check display names
        self.assertEqual(crew_pilot.display_name, "Multi Role Pilot (Captain)")
        self.assertEqual(crew_safety.display_name, "Multi Role Pilot (Safety Officer)")
        
        # Flight should have 2 crew records
        self.assertEqual(len(flight.crew_ids), 2)
