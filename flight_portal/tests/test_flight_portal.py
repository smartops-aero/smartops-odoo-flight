from datetime import datetime, timedelta

from odoo.exceptions import AccessError
from odoo.tests import HttpCase, TransactionCase, tagged


@tagged("post_install", "-at_install", "flight_portal")
class TestFlightPortal(TransactionCase):
    """Test cases for flight portal functionality"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create portal user
        cls.portal_user = cls.env["res.users"].create(
            {
                "name": "Portal User",
                "login": "portal_user",
                "email": "portal@example.com",
                "groups_id": [(4, cls.env.ref("base.group_portal").id)],
            }
        )

        # Create internal user
        cls.internal_user = cls.env["res.users"].create(
            {
                "name": "Internal User",
                "login": "internal_user",
                "email": "internal@example.com",
                "groups_id": [(4, cls.env.ref("base.group_user").id)],
            }
        )

        # Create aircraft data
        aircraft_class = cls.env["flight.aircraft.class"].create(
            {
                "name": "Private Jet",
                "aircraft_category": "airplane",
            }
        )

        aircraft_make = cls.env["flight.aircraft.make"].create(
            {
                "name": "Gulfstream",
            }
        )

        aircraft_model = cls.env["flight.aircraft.model"].create(
            {
                "name": "G550",
                "make_id": aircraft_make.id,
                "class_id": aircraft_class.id,
                "engine_type": "turbofan",
                "gear_type": "retractable_tricycle",
                "code": "G550",
            }
        )

        cls.aircraft = cls.env["flight.aircraft"].create(
            {
                "registration": "N550GS",
                "model_id": aircraft_model.id,
                "operator_id": cls.portal_user.partner_id.id,
            }
        )

        # Get countries for aerodrome creation
        cls.country_us = cls.env.ref("base.us")

        # Create aerodromes
        cls.aerodrome_origin = cls.env["flight.aerodrome"].create(
            {
                "name": "Teterboro Airport",
                "icao": "KTEB",
                "iata": "TEB",
                "city": "Teterboro",
                "country_id": cls.country_us.id,
            }
        )

        cls.aerodrome_dest = cls.env["flight.aerodrome"].create(
            {
                "name": "Van Nuys Airport",
                "icao": "KVNY",
                "iata": "VNY",
                "city": "Van Nuys",
                "country_id": cls.country_us.id,
            }
        )

        # Create flight accessible to portal user
        cls.portal_flight = cls.env["flight.flight"].create(
            {
                "date": datetime.now().date(),
                "aircraft_id": cls.aircraft.id,
                "departure_id": cls.aerodrome_origin.id,
                "arrival_id": cls.aerodrome_dest.id,
            }
        )
        # Add portal user as follower to give access
        cls.portal_flight.message_subscribe([cls.portal_user.partner_id.id])

        # Create flight not accessible to portal user
        cls.private_flight = cls.env["flight.flight"].create(
            {
                "date": datetime.now().date() + timedelta(days=1),
                "aircraft_id": cls.aircraft.id,
                "departure_id": cls.aerodrome_dest.id,
                "arrival_id": cls.aerodrome_origin.id,
            }
        )

    def test_01_portal_user_access_own_flights(self):
        """Test portal user can access their own flights"""
        # Switch to portal user
        flight_sudo = self.portal_flight.with_user(self.portal_user)

        # Portal user should be able to read their flight
        flight_data = flight_sudo.read(["date", "departure_id", "arrival_id"])
        self.assertTrue(flight_data)
        self.assertEqual(flight_data[0]["id"], self.portal_flight.id)

    def test_02_portal_user_cannot_access_other_flights(self):
        """Test portal user cannot access flights they're not associated with"""
        # Switch to portal user
        with self.assertRaises(AccessError):
            self.private_flight.with_user(self.portal_user).read(["date"])

    def test_03_portal_flight_sharing(self):
        """Test flight sharing with portal users"""
        # Create another portal user
        portal_user2 = self.env["res.users"].create(
            {
                "name": "Portal User 2",
                "login": "portal_user2",
                "email": "portal2@example.com",
                "groups_id": [(4, self.env.ref("base.group_portal").id)],
            }
        )

        # Share flight with second portal user
        self.portal_flight.message_subscribe([portal_user2.partner_id.id])

        # Both users should now have access
        flight_sudo1 = self.portal_flight.with_user(self.portal_user)
        flight_sudo2 = self.portal_flight.with_user(portal_user2)

        self.assertTrue(flight_sudo1.read(["date"]))
        self.assertTrue(flight_sudo2.read(["date"]))

    def test_04_portal_flight_basic_fields(self):
        """Test portal access to basic flight fields"""
        # Portal user should be able to read flight through relationships
        flight_sudo = self.portal_flight.with_user(self.portal_user)

        # Test accessing related fields that portal templates use
        self.assertTrue(flight_sudo.date)
        self.assertTrue(flight_sudo.aircraft_id.registration)
        self.assertTrue(flight_sudo.departure_id.name)
        self.assertTrue(flight_sudo.arrival_id.name)

    def test_05_portal_flight_basic_data_visibility(self):
        """Test portal visibility of flight basic data"""
        # Update flight locked status
        self.portal_flight.write(
            {
                "locked": True,
            }
        )

        # Portal user should see basic flight data
        flight_sudo = self.portal_flight.with_user(self.portal_user)
        flight_data = flight_sudo.read(
            ["date", "aircraft_id", "departure_id", "arrival_id", "locked"]
        )

        self.assertEqual(flight_data[0]["locked"], True)
        self.assertTrue(flight_data[0]["date"])

    def test_06_portal_flight_template_fields(self):
        """Test portal access to fields used in portal templates"""
        # Portal templates access these specific fields - ensure they work
        flight_sudo = self.portal_flight.with_user(self.portal_user)

        # Fields used in portal_flight_page template
        self.assertTrue(flight_sudo.date)
        self.assertTrue(flight_sudo.aircraft_id.registration)
        self.assertTrue(flight_sudo.departure_id.name)
        self.assertTrue(flight_sudo.arrival_id.name)

        # Fields used in portal_my_flights template
        self.assertEqual(flight_sudo.aircraft_id.registration, "N550GS")
        self.assertEqual(flight_sudo.departure_id.icao, "KTEB")
        self.assertEqual(flight_sudo.arrival_id.icao, "KVNY")

    def test_07_portal_flight_search(self):
        """Test portal user flight search capabilities"""
        # Create multiple flights for portal user
        for i in range(3):
            flight = self.env["flight.flight"].create(
                {
                    "date": datetime.now().date() + timedelta(days=i + 2),
                    "aircraft_id": self.aircraft.id,
                    "departure_id": self.aerodrome_origin.id,
                    "arrival_id": self.aerodrome_dest.id,
                }
            )
            flight.message_subscribe([self.portal_user.partner_id.id])

        # Search flights as portal user
        flights = self.env["flight.flight"].with_user(self.portal_user).search([])

        # Should find at least 4 flights (1 original + 3 new)
        self.assertGreaterEqual(len(flights), 4)

    def test_08_portal_flight_readonly(self):
        """Test portal users cannot modify flights"""
        # Portal user should not be able to write
        with self.assertRaises(AccessError):
            self.portal_flight.with_user(self.portal_user).write(
                {"date": datetime.now().date() + timedelta(days=7)}
            )

        # Portal user should not be able to delete
        with self.assertRaises(AccessError):
            self.portal_flight.with_user(self.portal_user).unlink()

    def test_09_portal_flight_readonly_validation(self):
        """Test that portal users truly cannot modify flights"""
        # Additional validation that portal access is read-only
        flight_sudo = self.portal_flight.with_user(self.portal_user)

        # Should be able to read
        self.assertTrue(flight_sudo.read(["date", "aircraft_id"]))

        # But not modify core fields
        with self.assertRaises(AccessError):
            flight_sudo.write({"date": datetime.now().date() + timedelta(days=10)})

    def test_10_portal_flight_access_url_functionality(self):
        """Test portal access URL functionality"""
        # Test that access_url is computed correctly for portal access
        access_url = self.portal_flight.access_url
        expected_url = f"/my/flight/{self.portal_flight.id}"

        self.assertEqual(access_url, expected_url)

        # Portal user should be able to access this property
        flight_sudo = self.portal_flight.with_user(self.portal_user)
        self.assertEqual(flight_sudo.access_url, expected_url)

    def test_11_portal_flight_history(self):
        """Test portal access to flight history"""
        # Create past flights
        for i in range(5):
            flight = self.env["flight.flight"].create(
                {
                    "date": datetime.now().date() - timedelta(days=i + 1),
                    "aircraft_id": self.aircraft.id,
                    "departure_id": self.aerodrome_origin.id,
                    "arrival_id": self.aerodrome_dest.id,
                }
            )
            flight.message_subscribe([self.portal_user.partner_id.id])

        # Search past flights
        past_flights = (
            self.env["flight.flight"]
            .with_user(self.portal_user)
            .search(
                [
                    ("date", "<", datetime.now().date()),
                ]
            )
        )

        self.assertGreaterEqual(len(past_flights), 5)

    def test_12_portal_access_url(self):
        """Test portal access URL generation"""
        # Flight should have access URL from portal.mixin
        self.assertTrue(hasattr(self.portal_flight, "access_url"))

        # Access URL should be properly formatted
        expected_url = f"/my/flight/{self.portal_flight.id}"
        self.assertEqual(self.portal_flight.access_url, expected_url)


@tagged("post_install", "-at_install", "flight_portal", "at_install")
class TestFlightPortalHttp(HttpCase):
    """HTTP test cases for flight portal web interface"""

    def test_01_portal_flight_page(self):
        """Test accessing flight details page via portal"""
        # This would test the actual HTTP routes
        # Implementation depends on specific portal routes defined
        pass
