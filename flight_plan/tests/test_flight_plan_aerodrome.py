from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestFlightPlanAerodrome(TransactionCase):
    def setUp(self):
        super().setUp()
        
        # Create test aerodromes with unique ICAO codes
        self.aerodrome_jfk = self.env["flight.aerodrome"].create({
            "name": "Test JFK Airport",
            "icao": "TJFK",
            "iata": "TJK",
        })
        
        self.aerodrome_lax = self.env["flight.aerodrome"].create({
            "name": "Test LAX Airport", 
            "icao": "TLAX",
            "iata": "TLX",
        })
        
        self.aerodrome_ord = self.env["flight.aerodrome"].create({
            "name": "Test ORD Airport",
            "icao": "TORD", 
            "iata": "TRD",
        })
        
        # Create test flight plan
        self.flight_plan = self.env["flight.plan"].create({
            "flight_id": self.env["flight.flight"].create({
                "date": "2025-01-01",
                "aircraft_id": self.env["flight.aircraft"].create({
                    "registration": "N123TEST",
                    "model_id": self.env["flight.aircraft.model"].create({
                        "name": "Test Aircraft Model"
                    }).id,
                }).id,
                "departure_id": self.aerodrome_jfk.id,
                "arrival_id": self.aerodrome_lax.id,
            }).id,
        })

    def test_single_departure_allowed(self):
        """Test that a single departure aerodrome is allowed"""
        departure = self.env["flight.plan.aerodrome"].create({
            "plan_id": self.flight_plan.id,
            "aerodrome_id": self.aerodrome_jfk.id,
            "function": "departure",
        })
        self.assertEqual(departure.function, "departure")

    def test_single_arrival_allowed(self):
        """Test that a single arrival aerodrome is allowed"""
        arrival = self.env["flight.plan.aerodrome"].create({
            "plan_id": self.flight_plan.id,
            "aerodrome_id": self.aerodrome_lax.id,
            "function": "arrival",
        })
        self.assertEqual(arrival.function, "arrival")

    def test_multiple_departure_alternates_allowed(self):
        """Test that multiple departure alternates are allowed"""
        # Create first departure alternate
        dep_alt1 = self.env["flight.plan.aerodrome"].create({
            "plan_id": self.flight_plan.id,
            "aerodrome_id": self.aerodrome_lax.id,
            "function": "departure_alternate",
        })
        
        # Create second departure alternate - should succeed
        dep_alt2 = self.env["flight.plan.aerodrome"].create({
            "plan_id": self.flight_plan.id,
            "aerodrome_id": self.aerodrome_ord.id,
            "function": "departure_alternate",
        })
        
        self.assertEqual(dep_alt1.function, "departure_alternate")
        self.assertEqual(dep_alt2.function, "departure_alternate")

    def test_multiple_arrival_alternates_allowed(self):
        """Test that multiple arrival alternates are allowed"""
        # Create first arrival alternate
        arr_alt1 = self.env["flight.plan.aerodrome"].create({
            "plan_id": self.flight_plan.id,
            "aerodrome_id": self.aerodrome_jfk.id,
            "function": "arrival_alternate",
        })
        
        # Create second arrival alternate - should succeed
        arr_alt2 = self.env["flight.plan.aerodrome"].create({
            "plan_id": self.flight_plan.id,
            "aerodrome_id": self.aerodrome_ord.id,
            "function": "arrival_alternate",
        })
        
        self.assertEqual(arr_alt1.function, "arrival_alternate")
        self.assertEqual(arr_alt2.function, "arrival_alternate")

    def test_duplicate_departure_not_allowed(self):
        """Test that duplicate departure aerodromes are not allowed"""
        # Create first departure
        self.env["flight.plan.aerodrome"].create({
            "plan_id": self.flight_plan.id,
            "aerodrome_id": self.aerodrome_jfk.id,
            "function": "departure",
        })
        
        # Try to create second departure - should fail
        with self.assertRaises(ValidationError) as context:
            self.env["flight.plan.aerodrome"].create({
                "plan_id": self.flight_plan.id,
                "aerodrome_id": self.aerodrome_lax.id,
                "function": "departure",
            })
        self.assertIn("can only have one departure aerodrome", str(context.exception))

    def test_duplicate_arrival_not_allowed(self):
        """Test that duplicate arrival aerodromes are not allowed"""
        # Create first arrival
        self.env["flight.plan.aerodrome"].create({
            "plan_id": self.flight_plan.id,
            "aerodrome_id": self.aerodrome_lax.id,
            "function": "arrival",
        })
        
        # Try to create second arrival - should fail
        with self.assertRaises(ValidationError) as context:
            self.env["flight.plan.aerodrome"].create({
                "plan_id": self.flight_plan.id,
                "aerodrome_id": self.aerodrome_ord.id,
                "function": "arrival",
            })
        self.assertIn("can only have one arrival aerodrome", str(context.exception))

    def test_same_function_different_plans_allowed(self):
        """Test that same function is allowed in different flight plans"""
        # Create another flight plan
        flight_plan2 = self.env["flight.plan"].create({
            "flight_id": self.env["flight.flight"].create({
                "date": "2025-01-02",
                "aircraft_id": self.env["flight.aircraft"].create({
                    "registration": "N456TEST",
                    "model_id": self.env["flight.aircraft.model"].create({
                        "name": "Test Aircraft Model 2"
                    }).id,
                }).id,
                "departure_id": self.aerodrome_ord.id,
                "arrival_id": self.aerodrome_jfk.id,
            }).id,
        })
        
        # Create departure in both plans - should succeed
        dep1 = self.env["flight.plan.aerodrome"].create({
            "plan_id": self.flight_plan.id,
            "aerodrome_id": self.aerodrome_jfk.id,
            "function": "departure",
        })
        
        dep2 = self.env["flight.plan.aerodrome"].create({
            "plan_id": flight_plan2.id,
            "aerodrome_id": self.aerodrome_ord.id,
            "function": "departure",
        })
        
        self.assertEqual(dep1.function, "departure")
        self.assertEqual(dep2.function, "departure")
        self.assertNotEqual(dep1.plan_id, dep2.plan_id)

    def test_update_to_duplicate_function_not_allowed(self):
        """Test that updating to create duplicate function is not allowed"""
        # Create departure and departure alternate
        departure = self.env["flight.plan.aerodrome"].create({
            "plan_id": self.flight_plan.id,
            "aerodrome_id": self.aerodrome_jfk.id,
            "function": "departure",
        })
        
        departure_alt = self.env["flight.plan.aerodrome"].create({
            "plan_id": self.flight_plan.id,
            "aerodrome_id": self.aerodrome_lax.id,
            "function": "departure_alternate",
        })
        
        # Try to change departure_alternate to departure - should fail
        with self.assertRaises(ValidationError) as context:
            departure_alt.write({"function": "departure"})
        self.assertIn("can only have one departure aerodrome", str(context.exception))
        
        # Verify original function unchanged
        departure_alt.invalidate_recordset()
        self.assertEqual(departure_alt.function, "departure_alternate")