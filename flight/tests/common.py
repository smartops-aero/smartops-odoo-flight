# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged
from datetime import date, datetime, timedelta


@tagged('post_install', '-at_install', 'flight_common')
class FlightCommon(TransactionCase):
    """Common test class for Flight module tests"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Create test users with different access levels
        # All users need base.group_user (Internal User) for mail access
        cls.user_manager = cls.env['res.users'].create({
            'name': 'Flight Manager',
            'login': 'flight_manager',
            'email': 'manager@flight.test',
            'groups_id': [(6, 0, [
                cls.env.ref('flight.group_flight_manager').id,
                cls.env.ref('base.group_user').id,  # Internal User
            ])]
        })
        
        cls.user_dispatcher = cls.env['res.users'].create({
            'name': 'Flight Dispatcher', 
            'login': 'flight_dispatcher',
            'email': 'dispatcher@flight.test',
            'groups_id': [(6, 0, [
                cls.env.ref('flight.group_flight_dispatcher').id,
                cls.env.ref('base.group_user').id,  # Internal User
            ])]
        })
        
        cls.user_crew = cls.env['res.users'].create({
            'name': 'Flight Crew',
            'login': 'flight_crew', 
            'email': 'crew@flight.test',
            'groups_id': [(6, 0, [
                cls.env.ref('flight.group_flight_crew').id,
                cls.env.ref('base.group_user').id,  # Internal User
            ])]
        })
        
        cls.user_basic = cls.env['res.users'].create({
            'name': 'Basic User',
            'login': 'basic_user',
            'email': 'basic@flight.test',
            'groups_id': [(6, 0, [
                cls.env.ref('flight.group_flight_user').id,
                cls.env.ref('base.group_user').id,  # Internal User
            ])]
        })
        
        # Create test data
        # Get or create US country
        cls.country_us = cls.env['res.country'].search([('code', '=', 'US')], limit=1)
        if not cls.country_us:
            cls.country_us = cls.env['res.country'].create({
                'name': 'United States',
                'code': 'US',
            })
        
        # Create test-specific airports that won't conflict with demo data
        cls.aerodrome_jfk = cls.env['flight.aerodrome'].create({
            'name': 'Test Airport East',
            'icao': 'KTES',  # Unique ICAO for testing
            'iata': 'TSE',
            'city': 'New York',
            'country_id': cls.country_us.id,
            'latitude': 40.6413,
            'longitude': -73.7781,
            'elevation': 13,
        })
        
        cls.aerodrome_lax = cls.env['flight.aerodrome'].create({
            'name': 'Test Airport West',
            'icao': 'KTSW',  # Unique ICAO for testing
            'iata': 'TSW',
            'city': 'Los Angeles',
            'country_id': cls.country_us.id,
            'latitude': 33.9425,
            'longitude': -118.4081,
            'elevation': 125,
        })
        
        cls.aircraft_class = cls.env['flight.aircraft.class'].create({
            'name': 'Large Jet',
            'aircraft_category': 'airplane',
        })
        
        cls.aircraft_make = cls.env['flight.aircraft.make'].create({
            'name': 'Boeing',
        })
        
        cls.aircraft_model = cls.env['flight.aircraft.model'].create({
            'name': '737-800',
            'make_id': cls.aircraft_make.id,
            'class_id': cls.aircraft_class.id,
            'engine_type': 'turbojet',
            'gear_type': 'retractable_tricycle',
            'code': 'B738',
        })
        
        cls.aircraft = cls.env['flight.aircraft'].create({
            'registration': 'TEST001',  # Unique test registration
            'model_id': cls.aircraft_model.id,
            'operator_id': cls.env.company.partner_id.id,
            'sn': 'SN123456',
            'dom': date(2020, 1, 1),
            'equipment_type': 'aircraft',
            'mtow': 79015,
            'weight_uom_id': cls.env.ref('uom.product_uom_lb').id,
        })
        
        cls.crew_role_pilot = cls.env['flight.crew.role'].create({
            'name': 'Captain',
            'description': 'Pilot in Command',
        })
        
        cls.crew_role_copilot = cls.env['flight.crew.role'].create({
            'name': 'First Officer',
            'description': 'Second in Command',
        })
        
    def create_test_flight(self, **kwargs):
        """Helper method to create a test flight"""
        vals = {
            'date': date.today(),
            'aircraft_id': self.aircraft.id,
            'departure_id': self.aerodrome_jfk.id,
            'arrival_id': self.aerodrome_lax.id,
        }
        vals.update(kwargs)
        return self.env['flight.flight'].create(vals)