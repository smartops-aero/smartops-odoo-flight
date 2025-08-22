from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestFlightRouteWaypoint(TransactionCase):
    def setUp(self):
        super().setUp()
        
        # Create a flight plan route for testing
        self.flight_plan_route = self.env["flight.plan.route"].create({
            "name": "Test Route",
            "route_type": "flight",
        })

    def test_valid_coordinates(self):
        """Test that valid coordinates are accepted"""
        # Test boundary values
        waypoint = self.env["flight.route.waypoint"].create({
            "route_id": self.flight_plan_route.id,
            "sequence": 10,
            "name": "North Pole",
            "latitude": 90.0,
            "longitude": 180.0,
        })
        self.assertEqual(waypoint.latitude, 90.0)
        self.assertEqual(waypoint.longitude, 180.0)

        # Test South Pole and opposite meridian
        waypoint2 = self.env["flight.route.waypoint"].create({
            "route_id": self.flight_plan_route.id,
            "sequence": 20,
            "name": "South Pole",
            "latitude": -90.0,
            "longitude": -180.0,
        })
        self.assertEqual(waypoint2.latitude, -90.0)
        self.assertEqual(waypoint2.longitude, -180.0)

        # Test zero coordinates (Gulf of Guinea)
        waypoint3 = self.env["flight.route.waypoint"].create({
            "route_id": self.flight_plan_route.id,
            "sequence": 30,
            "name": "Null Island",
            "latitude": 0.0,
            "longitude": 0.0,
        })
        self.assertEqual(waypoint3.latitude, 0.0)
        self.assertEqual(waypoint3.longitude, 0.0)

    def test_invalid_latitude_too_high(self):
        """Test that latitude > 90 raises ValidationError"""
        with self.assertRaises(ValidationError) as context:
            self.env["flight.route.waypoint"].create({
                "route_id": self.flight_plan_route.id,
                "sequence": 10,
                "name": "Invalid North",
                "latitude": 90.1,
                "longitude": 0.0,
            })
        self.assertIn("Latitude must be between -90.0 and +90.0 degrees", str(context.exception))

    def test_invalid_latitude_too_low(self):
        """Test that latitude < -90 raises ValidationError"""
        with self.assertRaises(ValidationError) as context:
            self.env["flight.route.waypoint"].create({
                "route_id": self.flight_plan_route.id,
                "sequence": 10,
                "name": "Invalid South",
                "latitude": -90.1,
                "longitude": 0.0,
            })
        self.assertIn("Latitude must be between -90.0 and +90.0 degrees", str(context.exception))

    def test_invalid_longitude_too_high(self):
        """Test that longitude > 180 raises ValidationError"""
        with self.assertRaises(ValidationError) as context:
            self.env["flight.route.waypoint"].create({
                "route_id": self.flight_plan_route.id,
                "sequence": 10,
                "name": "Invalid East",
                "latitude": 0.0,
                "longitude": 180.1,
            })
        self.assertIn("Longitude must be between -180.0 and +180.0 degrees", str(context.exception))

    def test_invalid_longitude_too_low(self):
        """Test that longitude < -180 raises ValidationError"""
        with self.assertRaises(ValidationError) as context:
            self.env["flight.route.waypoint"].create({
                "route_id": self.flight_plan_route.id,
                "sequence": 10,
                "name": "Invalid West",
                "latitude": 0.0,
                "longitude": -180.1,
            })
        self.assertIn("Longitude must be between -180.0 and +180.0 degrees", str(context.exception))

    def test_no_validation_for_false_coordinates(self):
        """Test that False/None coordinates skip validation"""
        # Should not raise validation error
        waypoint = self.env["flight.route.waypoint"].create({
            "route_id": self.flight_plan_route.id,
            "sequence": 10,
            "name": "No Coordinates",
            "latitude": False,
            "longitude": False,
        })
        self.assertFalse(waypoint.latitude)
        self.assertFalse(waypoint.longitude)

    def test_update_coordinates_validation(self):
        """Test that validation works on record updates"""
        waypoint = self.env["flight.route.waypoint"].create({
            "route_id": self.flight_plan_route.id,
            "sequence": 10,
            "name": "Test Waypoint",
            "latitude": 45.0,
            "longitude": 90.0,
        })
        
        # Test updating to invalid latitude
        with self.assertRaises(ValidationError):
            waypoint.write({"latitude": 95.0})
        
        # Test updating to invalid longitude
        with self.assertRaises(ValidationError):
            waypoint.write({"longitude": 185.0})
        
        # Verify original values unchanged
        self.assertEqual(waypoint.latitude, 45.0)
        self.assertEqual(waypoint.longitude, 90.0)

    def test_unique_sequence_per_route(self):
        """Test that sequence numbers must be unique within each route"""
        # Create first waypoint
        waypoint1 = self.env["flight.route.waypoint"].create({
            "route_id": self.flight_plan_route.id,
            "sequence": 10,
            "name": "Waypoint 1",
        })
        self.assertEqual(waypoint1.sequence, 10)

        # Try to create second waypoint with same sequence - should fail
        with self.assertRaises(Exception) as context:
            self.env["flight.route.waypoint"].create({
                "route_id": self.flight_plan_route.id,
                "sequence": 10,
                "name": "Waypoint 2",
            })
        # Check that it's a database constraint error
        self.assertIn("unique_sequence_per_route", str(context.exception))

    def test_unique_sequence_different_routes(self):
        """Test that same sequence numbers are allowed in different routes"""
        # Create another route
        route2 = self.env["flight.plan.route"].create({
            "name": "Test Route 2",
            "route_type": "alternate",
        })

        # Create waypoints with same sequence in different routes - should succeed
        waypoint1 = self.env["flight.route.waypoint"].create({
            "route_id": self.flight_plan_route.id,
            "sequence": 10,
            "name": "Route 1 Waypoint",
        })

        waypoint2 = self.env["flight.route.waypoint"].create({
            "route_id": route2.id,
            "sequence": 10,
            "name": "Route 2 Waypoint",
        })

        self.assertEqual(waypoint1.sequence, 10)
        self.assertEqual(waypoint2.sequence, 10)
        self.assertNotEqual(waypoint1.route_id, waypoint2.route_id)