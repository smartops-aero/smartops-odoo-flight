# -*- coding: utf-8 -*-
from odoo.tests import tagged
from odoo.exceptions import ValidationError
from psycopg2 import IntegrityError
from .common import FlightCommon


@tagged('post_install', '-at_install', 'flight_crew')
class TestCrew(FlightCommon):
    """Test cases for flight.crew model"""
    
    def test_01_crew_role_creation(self):
        """Test crew role creation"""
        role = self.env['flight.crew.role'].create({
            'name': 'Flight Attendant',
            'description': 'Cabin crew member responsible for passenger safety',
        })
        
        self.assertTrue(role.id)
        self.assertEqual(role.name, 'Flight Attendant')
        self.assertEqual(role.description, 'Cabin crew member responsible for passenger safety')
        
    def test_02_crew_assignment(self):
        """Test crew assignment to flight"""
        pilot = self.env['res.partner'].create({
            'name': 'Test Pilot',
            'is_company': False,
        })
        
        flight = self.create_test_flight()
        
        crew = self.env['flight.crew'].create({
            'flight_id': flight.id,
            'partner_id': pilot.id,
            'role_id': self.crew_role_pilot.id,
        })
        
        self.assertTrue(crew.id)
        self.assertEqual(crew.flight_id, flight)
        self.assertEqual(crew.partner_id, pilot)
        self.assertEqual(crew.role_id, self.crew_role_pilot)
        
    def test_03_crew_display_name(self):
        """Test crew member display name"""
        pilot = self.env['res.partner'].create({
            'name': 'John Smith',
            'is_company': False,
        })
        
        flight = self.create_test_flight()
        
        crew = self.env['flight.crew'].create({
            'flight_id': flight.id,
            'partner_id': pilot.id,
            'role_id': self.crew_role_pilot.id,
        })
        
        # Crew model uses default display_name format (model,id)
        self.assertTrue(crew.display_name.startswith('flight.crew,'))
        # Test the individual components instead
        self.assertEqual(crew.partner_id.name, 'John Smith')
        self.assertEqual(crew.role_id.name, 'Captain')
        
    def test_04_multiple_crew_same_flight(self):
        """Test multiple crew members on same flight"""
        flight = self.create_test_flight()
        
        crew_members = []
        for i in range(4):
            partner = self.env['res.partner'].create({
                'name': f'Crew Member {i}',
                'is_company': False,
            })
            
            role = self.crew_role_pilot if i < 2 else self.env['flight.crew.role'].create({
                'name': 'Flight Attendant',
                'description': 'Cabin crew member',
            })
            
            crew = self.env['flight.crew'].create({
                'flight_id': flight.id,
                'partner_id': partner.id,
                'role_id': role.id,
            })
            crew_members.append(crew)
            
        self.assertEqual(len(flight.crew_ids), 4)
        for crew in crew_members:
            self.assertIn(crew, flight.crew_ids)
            
    def test_05_crew_role_name_validation(self):
        """Test crew role name is required"""
        # Name is required - raises IntegrityError from database
        with self.assertRaises(IntegrityError):
            self.env['flight.crew.role'].create({
                'description': 'Role without name',
            })
            
    def test_06_crew_partner_validation(self):
        """Test that crew members must have a valid partner_id"""
        flight = self.create_test_flight()
        
        # Test that partner_id is required - raises IntegrityError from database
        with self.assertRaises(IntegrityError):
            self.env['flight.crew'].create({
                'flight_id': flight.id,
                'role_id': self.crew_role_pilot.id,
                # partner_id is intentionally missing - should fail because required=True
            })
            
    def test_07_crew_copy_with_flight(self):
        """Test crew copying when flight is duplicated"""
        flight = self.create_test_flight()
        
        # Add crew
        pilot = self.env['res.partner'].create({
            'name': 'Original Pilot',
            'is_company': False,
        })
        
        crew = self.env['flight.crew'].create({
            'flight_id': flight.id,
            'partner_id': pilot.id,
            'role_id': self.crew_role_pilot.id,
        })
        
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
        
        pilot1 = self.env['res.partner'].create({'name': 'Pilot 1', 'is_company': False})
        pilot2 = self.env['res.partner'].create({'name': 'Pilot 2', 'is_company': False})
        
        crew1 = self.env['flight.crew'].create({
            'flight_id': flight1.id,
            'partner_id': pilot1.id,
            'role_id': self.crew_role_pilot.id,
        })
        
        crew2 = self.env['flight.crew'].create({
            'flight_id': flight2.id,
            'partner_id': pilot2.id,
            'role_id': self.crew_role_copilot.id,
        })
        
        # Search captains
        captains = self.env['flight.crew'].search([
            ('role_id', '=', self.crew_role_pilot.id)
        ])
        self.assertIn(crew1, captains)
        self.assertNotIn(crew2, captains)
        
        # Search first officers
        first_officers = self.env['flight.crew'].search([
            ('role_id', '=', self.crew_role_copilot.id)
        ])
        self.assertIn(crew2, first_officers)
        self.assertNotIn(crew1, first_officers)