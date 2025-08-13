# -*- coding: utf-8 -*-
from odoo.tests import tagged
from odoo.exceptions import ValidationError, UserError
from datetime import date, timedelta
from .common import FlightCommon


@tagged('post_install', '-at_install', 'flight')
class TestFlight(FlightCommon):
    """Test cases for flight.flight model"""
    
    def test_01_flight_creation(self):
        """Test basic flight creation"""
        flight = self.create_test_flight()
        self.assertTrue(flight.id)
        self.assertEqual(flight.aircraft_id, self.aircraft)
        self.assertEqual(flight.departure_id, self.aerodrome_jfk)
        self.assertEqual(flight.arrival_id, self.aerodrome_lax)
        self.assertFalse(flight.locked)
        
    def test_02_flight_name_get(self):
        """Test flight display name generation"""
        flight = self.create_test_flight(date=date(2024, 1, 15))
        expected_name = f"2024-01-15 / N12345: KJFK - KLAX"
        self.assertEqual(flight.display_name, expected_name)
        
    def test_03_flight_lock_unlock(self):
        """Test flight locking mechanism"""
        flight = self.create_test_flight()
        
        # Test lock as manager
        flight.with_user(self.user_manager).toggle_locked()
        self.assertTrue(flight.locked)
        
        # Test unlock
        flight.with_user(self.user_manager).toggle_locked()
        self.assertFalse(flight.locked)
        
    def test_04_flight_crew_assignment(self):
        """Test crew assignment to flight"""
        pilot = self.env['res.partner'].create({
            'name': 'John Pilot',
            'is_company': False,
        })
        
        copilot = self.env['res.partner'].create({
            'name': 'Jane Copilot',
            'is_company': False,
        })
        
        flight = self.create_test_flight()
        
        # Add crew members
        self.env['flight.crew'].create({
            'flight_id': flight.id,
            'partner_id': pilot.id,
            'role_id': self.crew_role_pilot.id,
        })
        
        self.env['flight.crew'].create({
            'flight_id': flight.id,
            'partner_id': copilot.id,
            'role_id': self.crew_role_copilot.id,
        })
        
        self.assertEqual(len(flight.crew_ids), 2)
        self.assertIn(pilot, flight.crew_ids.mapped('partner_id'))
        self.assertIn(copilot, flight.crew_ids.mapped('partner_id'))
        
    def test_05_flight_auto_departure_from_last_arrival(self):
        """Test automatic departure setting from last aircraft arrival"""
        # Create first flight
        flight1 = self.create_test_flight(
            date=date.today() - timedelta(days=1),
            departure_id=self.aerodrome_jfk.id,
            arrival_id=self.aerodrome_lax.id,
        )
        
        # Create second flight for same aircraft
        flight2 = self.env['flight.flight'].create({
            'date': date.today(),
            'aircraft_id': self.aircraft.id,
            'arrival_id': self.aerodrome_jfk.id,
        })
        
        # Trigger onchange
        flight2._onchange_aircraft_id()
        
        # Departure should be set to last arrival
        self.assertEqual(flight2.departure_id, self.aerodrome_lax)
        
    def test_06_flight_multi_record_operations(self):
        """Test batch operations on multiple flights"""
        flights = self.env['flight.flight']
        for i in range(3):
            flights |= self.create_test_flight(
                date=date.today() + timedelta(days=i)
            )
        
        # Test batch lock
        flights.with_user(self.user_manager).write({'locked': True})
        self.assertTrue(all(f.locked for f in flights))
        
        # Test batch unlock
        flights.with_user(self.user_manager).write({'locked': False})
        self.assertFalse(any(f.locked for f in flights))
        
    def test_07_flight_search_filters(self):
        """Test search filters and grouping"""
        # Create test flights
        flight_locked = self.create_test_flight(locked=True)
        flight_unlocked = self.create_test_flight(locked=False)
        
        # Test locked filter
        locked_flights = self.env['flight.flight'].search([
            ('locked', '=', True)
        ])
        self.assertIn(flight_locked, locked_flights)
        self.assertNotIn(flight_unlocked, locked_flights)
        
        # Test grouping by aircraft
        grouped = self.env['flight.flight'].read_group(
            [('aircraft_id', '!=', False)],
            ['aircraft_id'],
            ['aircraft_id']
        )
        self.assertTrue(grouped)
        
    def test_08_flight_copy(self):
        """Test flight duplication"""
        original = self.create_test_flight(
            date=date(2024, 1, 1),
            locked=True
        )
        
        # Add crew
        self.env['flight.crew'].create({
            'flight_id': original.id,
            'partner_id': self.env.company.partner_id.id,
            'role_id': self.crew_role_pilot.id,
        })
        
        # Copy flight
        copy = original.copy()
        
        self.assertNotEqual(copy.id, original.id)
        self.assertEqual(copy.aircraft_id, original.aircraft_id)
        self.assertEqual(copy.departure_id, original.departure_id)
        self.assertEqual(copy.arrival_id, original.arrival_id)
        # Crew should be copied
        self.assertEqual(len(copy.crew_ids), len(original.crew_ids))
        # Lock status should not be copied (default value)
        self.assertFalse(copy.locked)
        
    def test_09_flight_unlink_locked(self):
        """Test that locked flights cannot be deleted by non-managers"""
        flight = self.create_test_flight(locked=True)
        
        # Try to delete as crew user (should fail)
        with self.assertRaises(UserError):
            flight.with_user(self.user_crew).unlink()
            
        # Manager should be able to delete
        flight.with_user(self.user_manager).unlink()
        self.assertFalse(flight.exists())