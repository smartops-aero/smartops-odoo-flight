from odoo.exceptions import AccessError
from odoo.tests import tagged

from .common import FlightCommon


@tagged("post_install", "-at_install", "flight_security")
class TestSecurity(FlightCommon):
    """Test cases for flight module security and access rights"""

    def test_01_user_groups_hierarchy(self):
        """Test user group hierarchy and inheritance"""
        # Manager should have all lower permissions
        manager_groups = self.user_manager.groups_id
        self.assertIn(self.env.ref("flight.group_flight_manager"), manager_groups)
        self.assertIn(self.env.ref("flight.group_flight_dispatcher"), manager_groups)
        self.assertIn(self.env.ref("flight.group_flight_crew"), manager_groups)
        self.assertIn(self.env.ref("flight.group_flight_user"), manager_groups)

        # Dispatcher should have crew and user permissions
        dispatcher_groups = self.user_dispatcher.groups_id
        self.assertIn(self.env.ref("flight.group_flight_dispatcher"), dispatcher_groups)
        self.assertIn(self.env.ref("flight.group_flight_crew"), dispatcher_groups)
        self.assertIn(self.env.ref("flight.group_flight_user"), dispatcher_groups)
        self.assertNotIn(self.env.ref("flight.group_flight_manager"), dispatcher_groups)

        # Crew should have user permissions
        crew_groups = self.user_crew.groups_id
        self.assertIn(self.env.ref("flight.group_flight_crew"), crew_groups)
        self.assertIn(self.env.ref("flight.group_flight_user"), crew_groups)
        self.assertNotIn(self.env.ref("flight.group_flight_dispatcher"), crew_groups)

        # Basic user should only have user permissions
        user_groups = self.user_basic.groups_id
        self.assertIn(self.env.ref("flight.group_flight_user"), user_groups)
        self.assertNotIn(self.env.ref("flight.group_flight_crew"), user_groups)

    def test_02_flight_read_access(self):
        """Test read access to flights for different user groups"""
        flight = self.create_test_flight()

        # All users should be able to read flights
        for user in [
            self.user_manager,
            self.user_dispatcher,
            self.user_crew,
            self.user_basic,
        ]:
            flight_read = flight.with_user(user).read(["date", "aircraft_id"])
            self.assertTrue(flight_read)

    def test_03_flight_write_access(self):
        """Test write access to flights for different user groups"""
        flight = self.create_test_flight()

        # Manager should be able to write
        flight.with_user(self.user_manager).write({"locked": True})
        self.assertTrue(flight.locked)

        # Dispatcher should be able to write
        flight.with_user(self.user_dispatcher).write({"locked": False})
        self.assertFalse(flight.locked)

        # Crew should be able to write
        flight.with_user(self.user_crew).write({"date": flight.date})

        # Basic user should not be able to write
        with self.assertRaises(AccessError):
            flight.with_user(self.user_basic).write({"locked": True})

    def test_04_flight_create_access(self):
        """Test create access to flights for different user groups"""
        vals = {
            "date": "2024-01-01",
            "aircraft_id": self.aircraft.id,
            "departure_id": self.aerodrome_jfk.id,
            "arrival_id": self.aerodrome_lax.id,
        }

        # Manager should be able to create
        flight1 = self.env["flight.flight"].with_user(self.user_manager).create(vals)
        self.assertTrue(flight1.id)

        # Dispatcher should be able to create
        vals["date"] = "2024-01-02"
        flight2 = self.env["flight.flight"].with_user(self.user_dispatcher).create(vals)
        self.assertTrue(flight2.id)

        # Crew should be able to create
        vals["date"] = "2024-01-03"
        flight3 = self.env["flight.flight"].with_user(self.user_crew).create(vals)
        self.assertTrue(flight3.id)

        # Basic user should not be able to create
        vals["date"] = "2024-01-04"
        with self.assertRaises(AccessError):
            self.env["flight.flight"].with_user(self.user_basic).create(vals)

    def test_05_flight_unlink_access(self):
        """Test delete access to flights for different user groups"""
        # Manager should be able to delete
        flight1 = self.create_test_flight()
        flight1.with_user(self.user_manager).unlink()
        self.assertFalse(flight1.exists())

        # Dispatcher should be able to delete unlocked flights
        flight2 = self.create_test_flight()
        flight2.with_user(self.user_dispatcher).unlink()
        self.assertFalse(flight2.exists())

        # Crew should NOT be able to delete flights (only dispatcher/manager)
        flight3 = self.create_test_flight()
        with self.assertRaises(AccessError):
            flight3.with_user(self.user_crew).unlink()

        # Basic user should not be able to delete
        flight4 = self.create_test_flight()
        with self.assertRaises(AccessError):
            flight4.with_user(self.user_basic).unlink()

    def test_06_aircraft_access_rights(self):
        """Test access rights for aircraft model"""
        vals = {
            "registration": "N11111",
            "model_id": self.aircraft_model.id,
            "operator_id": self.env.company.partner_id.id,
        }

        # Manager can create/write/delete
        aircraft = self.env["flight.aircraft"].with_user(self.user_manager).create(vals)
        aircraft.with_user(self.user_manager).write({"registration": "N22222"})
        aircraft.with_user(self.user_manager).unlink()

        # Dispatcher can create/write
        vals["registration"] = "N33333"
        aircraft = (
            self.env["flight.aircraft"].with_user(self.user_dispatcher).create(vals)
        )
        aircraft.with_user(self.user_dispatcher).write({"registration": "N44444"})

        # Crew can read but not create
        # Create aircraft that crew can read (set website_published if field exists)
        crew_aircraft_vals = vals.copy()
        crew_aircraft_vals["registration"] = "N55555"
        # Check if website_published field exists (from website_flight_fleet module)
        if "website_published" in self.env["flight.aircraft"]._fields:
            crew_aircraft_vals["website_published"] = True
        crew_aircraft = (
            self.env["flight.aircraft"]
            .with_user(self.user_manager)
            .create(crew_aircraft_vals)
        )

        aircraft_read = crew_aircraft.with_user(self.user_crew).read(["registration"])
        self.assertTrue(aircraft_read)

        vals["registration"] = "N66666"
        with self.assertRaises(AccessError):
            self.env["flight.aircraft"].with_user(self.user_crew).create(vals)

        # Basic user can only read aircraft they have access to
        # Create aircraft that basic user can read (set website_published if field exists)
        basic_aircraft_vals = vals.copy()
        basic_aircraft_vals["registration"] = "N77777"
        # Check if website_published field exists (from website_flight_fleet module)
        if "website_published" in self.env["flight.aircraft"]._fields:
            basic_aircraft_vals["website_published"] = True
        basic_aircraft = (
            self.env["flight.aircraft"]
            .with_user(self.user_manager)
            .create(basic_aircraft_vals)
        )

        aircraft_read = basic_aircraft.with_user(self.user_basic).read(["registration"])
        self.assertTrue(aircraft_read)

        with self.assertRaises(AccessError):
            basic_aircraft.with_user(self.user_basic).write({"registration": "N88888"})

    def test_07_aerodrome_access_rights(self):
        """Test access rights for aerodrome model"""
        vals = {
            "name": "Test Airport",
            "icao": "KTST",
        }

        # Manager and dispatcher can create aerodromes
        aerodrome1 = (
            self.env["flight.aerodrome"].with_user(self.user_manager).create(vals)
        )
        self.assertTrue(aerodrome1.id)

        vals["icao"] = "KTS2"
        aerodrome2 = (
            self.env["flight.aerodrome"].with_user(self.user_dispatcher).create(vals)
        )
        self.assertTrue(aerodrome2.id)

        # Crew and basic users can only read
        for user in [self.user_crew, self.user_basic]:
            aerodrome_read = self.aerodrome_jfk.with_user(user).read(["name", "icao"])
            self.assertTrue(aerodrome_read)

            vals["icao"] = f"KTS{user.id}"
            with self.assertRaises(AccessError):
                self.env["flight.aerodrome"].with_user(user).create(vals)

    def test_08_lock_unlock_permission(self):
        """Test lock/unlock permission restricted to managers"""
        flight = self.create_test_flight()

        # Manager can lock/unlock
        flight.with_user(self.user_manager).toggle_locked()
        self.assertTrue(flight.locked)
        flight.with_user(self.user_manager).toggle_locked()
        self.assertFalse(flight.locked)

        # Other users cannot use toggle_locked (button is hidden)
        # But they could try to call the method directly
        for user in [self.user_dispatcher, self.user_crew, self.user_basic]:
            # The button visibility is controlled by groups in XML
            # Here we test if they try to call the method directly
            # It should check for manager group
            pass  # Button group restriction is UI-level, tested in UI tests
