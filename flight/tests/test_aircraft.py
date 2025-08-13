# -*- coding: utf-8 -*-
from odoo.tests import tagged
from odoo.exceptions import ValidationError
from datetime import date
from .common import FlightCommon


@tagged('post_install', '-at_install', 'flight_aircraft')
class TestAircraft(FlightCommon):
    """Test cases for flight.aircraft model"""
    
    def test_01_aircraft_creation(self):
        """Test aircraft creation with all fields"""
        aircraft = self.env['flight.aircraft'].create({
            'registration': 'N99999',
            'model_id': self.aircraft_model.id,
            'operator_id': self.env.company.partner_id.id,
            'sn': 'SN999999',
            'dom': date(2022, 6, 15),
            'equipment_type': 'standard',
            'mtow': 85000,
            'weight_uom_id': self.env.ref('uom.product_uom_lb').id,
        })
        
        self.assertTrue(aircraft.id)
        self.assertEqual(aircraft.registration, 'N99999')
        self.assertEqual(aircraft.sn, 'SN999999')
        self.assertEqual(aircraft.mtow, 85000)
        
    def test_02_aircraft_display_name(self):
        """Test aircraft display name"""
        self.assertEqual(self.aircraft.display_name, 'N12345')
        self.assertEqual(self.aircraft.name, 'N12345')
        
    def test_03_aircraft_model_hierarchy(self):
        """Test aircraft model, make, and class relationships"""
        # Test model hierarchy
        self.assertEqual(self.aircraft.model_id.make_id, self.aircraft_make)
        self.assertEqual(self.aircraft.model_id.class_id, self.aircraft_class)
        self.assertEqual(self.aircraft.model_id.code, 'B738')
        
    def test_04_aircraft_class_categories(self):
        """Test aircraft class categories"""
        valid_categories = [
            'airplane', 'helicopter', 'glider', 'lighter_than_air',
            'powered_lift', 'powered_parachute', 'weight_shift_control'
        ]
        
        for category in valid_categories:
            aircraft_class = self.env['flight.aircraft.class'].create({
                'name': f'Test {category}',
                'aircraft_category': category,
            })
            self.assertEqual(aircraft_class.aircraft_category, category)
            
    def test_05_aircraft_model_engine_types(self):
        """Test aircraft model engine types"""
        engine_types = [
            'piston', 'turboprop', 'turbojet', 'turbofan', 
            'ramjet', 'electric', '2_cycle', '4_cycle', 
            'rotary', 'turboshaft'
        ]
        
        for engine_type in engine_types:
            model = self.env['flight.aircraft.model'].create({
                'name': f'Test {engine_type}',
                'make_id': self.aircraft_make.id,
                'class_id': self.aircraft_class.id,
                'engine_type': engine_type,
                'gear_type': 'tricycle_retractable',
                'code': f'T{engine_type[:3].upper()}',
            })
            self.assertEqual(model.engine_type, engine_type)
            
    def test_06_aircraft_model_gear_types(self):
        """Test aircraft model gear types"""
        gear_types = [
            'amphibian', 'floats', 'retractable_floats', 'skids',
            'skis', 'tailwheel', 'tricycle_fixed', 'tricycle_retractable'
        ]
        
        for gear_type in gear_types:
            model = self.env['flight.aircraft.model'].create({
                'name': f'Test {gear_type}',
                'make_id': self.aircraft_make.id,
                'class_id': self.aircraft_class.id,
                'engine_type': 'turboprop',
                'gear_type': gear_type,
                'code': f'G{gear_type[:3].upper()}',
            })
            self.assertEqual(model.gear_type, gear_type)
            
    def test_07_aircraft_model_tags(self):
        """Test aircraft model tags"""
        tag1 = self.env['flight.aircraft.model.tag'].create({
            'name': 'Long Range',
        })
        tag2 = self.env['flight.aircraft.model.tag'].create({
            'name': 'Wide Body',
        })
        
        model = self.env['flight.aircraft.model'].create({
            'name': 'A350-900',
            'make_id': self.aircraft_make.id,
            'class_id': self.aircraft_class.id,
            'engine_type': 'turbofan',
            'gear_type': 'tricycle_retractable',
            'code': 'A359',
            'tag_ids': [(6, 0, [tag1.id, tag2.id])],
        })
        
        self.assertIn(tag1, model.tag_ids)
        self.assertIn(tag2, model.tag_ids)
        self.assertEqual(len(model.tag_ids), 2)
        
    def test_08_aircraft_weight_conversion(self):
        """Test aircraft weight with different units"""
        kg_uom = self.env.ref('uom.product_uom_kgm')
        lb_uom = self.env.ref('uom.product_uom_lb')
        
        aircraft_kg = self.env['flight.aircraft'].create({
            'registration': 'D-TEST',
            'model_id': self.aircraft_model.id,
            'operator_id': self.env.company.partner_id.id,
            'mtow': 35000,  # kg
            'weight_uom_id': kg_uom.id,
        })
        
        self.assertEqual(aircraft_kg.mtow, 35000)
        self.assertEqual(aircraft_kg.weight_uom_id, kg_uom)
        
    def test_09_aircraft_search(self):
        """Test aircraft search and filters"""
        # Create additional aircraft
        aircraft2 = self.env['flight.aircraft'].create({
            'registration': 'G-TEST',
            'model_id': self.aircraft_model.id,
            'operator_id': self.env.company.partner_id.id,
        })
        
        # Search by registration
        found = self.env['flight.aircraft'].search([
            ('registration', 'like', 'N%')
        ])
        self.assertIn(self.aircraft, found)
        self.assertNotIn(aircraft2, found)
        
        # Search by model
        found = self.env['flight.aircraft'].search([
            ('model_id', '=', self.aircraft_model.id)
        ])
        self.assertIn(self.aircraft, found)
        self.assertIn(aircraft2, found)
        
    def test_10_aircraft_copy(self):
        """Test aircraft duplication"""
        copy = self.aircraft.copy({
            'registration': 'N54321',
            'sn': 'SN654321',
        })
        
        self.assertNotEqual(copy.id, self.aircraft.id)
        self.assertEqual(copy.registration, 'N54321')
        self.assertEqual(copy.sn, 'SN654321')
        self.assertEqual(copy.model_id, self.aircraft.model_id)
        self.assertEqual(copy.mtow, self.aircraft.mtow)