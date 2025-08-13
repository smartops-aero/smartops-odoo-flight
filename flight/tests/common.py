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
        cls.user_manager = cls.env['res.users'].create({
            'name': 'Flight Manager',
            'login': 'flight_manager',
            'email': 'manager@flight.test',
            'groups_id': [(6, 0, [cls.env.ref('flight.group_flight_manager').id])]
        })
        
        cls.user_dispatcher = cls.env['res.users'].create({
            'name': 'Flight Dispatcher', 
            'login': 'flight_dispatcher',
            'email': 'dispatcher@flight.test',
            'groups_id': [(6, 0, [cls.env.ref('flight.group_flight_dispatcher').id])]
        })
        
        cls.user_crew = cls.env['res.users'].create({
            'name': 'Flight Crew',
            'login': 'flight_crew', 
            'email': 'crew@flight.test',
            'groups_id': [(6, 0, [cls.env.ref('flight.group_flight_crew').id])]
        })
        
        cls.user_basic = cls.env['res.users'].create({
            'name': 'Basic User',
            'login': 'basic_user',
            'email': 'basic@flight.test',
            'groups_id': [(6, 0, [cls.env.ref('flight.group_flight_user').id])]
        })
        
        # Create test data
        cls.aerodrome_jfk = cls.env['flight.aerodrome'].create({
            'name': 'John F Kennedy International Airport',
            'icao': 'KJFK',
            'iata': 'JFK',
            'city': 'New York',
            'country': 'US',
            'latitude': 40.6413,
            'longitude': -73.7781,
            'elevation': 13,
        })
        
        cls.aerodrome_lax = cls.env['flight.aerodrome'].create({
            'name': 'Los Angeles International Airport',
            'icao': 'KLAX',
            'iata': 'LAX',
            'city': 'Los Angeles',
            'country': 'US',
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
            'gear_type': 'tricycle_retractable',
            'code': 'B738',
        })
        
        cls.aircraft = cls.env['flight.aircraft'].create({
            'registration': 'N12345',
            'model_id': cls.aircraft_model.id,
            'operator_id': cls.env.company.partner_id.id,
            'sn': 'SN123456',
            'dom': date(2020, 1, 1),
            'equipment_type': 'standard',
            'mtow': 79015,
            'weight_uom_id': cls.env.ref('uom.product_uom_lb').id,
        })
        
        cls.crew_role_pilot = cls.env['flight.crew.role'].create({
            'name': 'Captain',
            'code': 'CPT',
        })
        
        cls.crew_role_copilot = cls.env['flight.crew.role'].create({
            'name': 'First Officer',
            'code': 'FO',
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