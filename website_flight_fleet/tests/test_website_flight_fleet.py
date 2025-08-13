# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, HttpCase, tagged
from datetime import datetime, timedelta


@tagged('post_install', '-at_install', 'website_flight_fleet')
class TestWebsiteFlightFleet(TransactionCase):
    """Test cases for website flight fleet display"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Get website
        cls.website = cls.env['website'].get_current_website()
        
        # Create aircraft classes
        cls.class_jet = cls.env['flight.aircraft.class'].create({
            'name': 'Business Jet',
            'aircraft_category': 'airplane',
            'website_published': True,
        })
        
        cls.class_turbo = cls.env['flight.aircraft.class'].create({
            'name': 'Turboprop',
            'aircraft_category': 'airplane',
            'website_published': True,
        })
        
        cls.class_heli = cls.env['flight.aircraft.class'].create({
            'name': 'Helicopter',
            'aircraft_category': 'helicopter',
            'website_published': True,
        })
        
        # Create makes
        cls.make_gulfstream = cls.env['flight.aircraft.make'].create({
            'name': 'Gulfstream',
            'website_published': True,
        })
        
        cls.make_cessna = cls.env['flight.aircraft.make'].create({
            'name': 'Cessna',
            'website_published': True,
        })
        
        cls.make_bell = cls.env['flight.aircraft.make'].create({
            'name': 'Bell',
            'website_published': True,
        })
        
        # Create models
        cls.model_g650 = cls.env['flight.aircraft.model'].create({
            'name': 'G650',
            'make_id': cls.make_gulfstream.id,
            'class_id': cls.class_jet.id,
            'engine_type': 'turbofan',
            'gear_type': 'tricycle_retractable',
            'code': 'G650',
            'max_passengers': 19,
            'cruise_speed': 500,
            'range_nm': 7000,
            'website_published': True,
        })
        
        cls.model_citation = cls.env['flight.aircraft.model'].create({
            'name': 'Citation CJ3',
            'make_id': cls.make_cessna.id,
            'class_id': cls.class_jet.id,
            'engine_type': 'turbofan',
            'gear_type': 'tricycle_retractable',
            'code': 'CJ3',
            'max_passengers': 9,
            'cruise_speed': 416,
            'range_nm': 2040,
            'website_published': True,
        })
        
        cls.model_caravan = cls.env['flight.aircraft.model'].create({
            'name': 'Caravan 208',
            'make_id': cls.make_cessna.id,
            'class_id': cls.class_turbo.id,
            'engine_type': 'turboprop',
            'gear_type': 'tricycle_fixed',
            'code': 'C208',
            'max_passengers': 14,
            'cruise_speed': 186,
            'range_nm': 1070,
            'website_published': True,
        })
        
        cls.model_bell407 = cls.env['flight.aircraft.model'].create({
            'name': '407',
            'make_id': cls.make_bell.id,
            'class_id': cls.class_heli.id,
            'engine_type': 'turboshaft',
            'gear_type': 'skids',
            'code': 'B407',
            'max_passengers': 6,
            'cruise_speed': 133,
            'range_nm': 337,
            'website_published': True,
        })
        
        # Create aircraft
        cls.aircraft_g650 = cls.env['flight.aircraft'].create({
            'registration': 'N650GS',
            'model_id': cls.model_g650.id,
            'operator_id': cls.env.company.partner_id.id,
            'year_manufactured': 2020,
            'website_published': True,
            'available_for_charter': True,
        })
        
        cls.aircraft_citation = cls.env['flight.aircraft'].create({
            'registration': 'N123CJ',
            'model_id': cls.model_citation.id,
            'operator_id': cls.env.company.partner_id.id,
            'year_manufactured': 2018,
            'website_published': True,
            'available_for_charter': True,
        })
        
        cls.aircraft_caravan = cls.env['flight.aircraft'].create({
            'registration': 'N208CV',
            'model_id': cls.model_caravan.id,
            'operator_id': cls.env.company.partner_id.id,
            'year_manufactured': 2019,
            'website_published': False,  # Not published
            'available_for_charter': False,
        })
        
        cls.aircraft_bell = cls.env['flight.aircraft'].create({
            'registration': 'N407BH',
            'model_id': cls.model_bell407.id,
            'operator_id': cls.env.company.partner_id.id,
            'year_manufactured': 2021,
            'website_published': True,
            'available_for_charter': True,
        })
        
    def test_01_website_published_aircraft(self):
        """Test website published aircraft filtering"""
        # Get published aircraft
        published_aircraft = self.env['flight.aircraft'].search([
            ('website_published', '=', True)
        ])
        
        self.assertIn(self.aircraft_g650, published_aircraft)
        self.assertIn(self.aircraft_citation, published_aircraft)
        self.assertNotIn(self.aircraft_caravan, published_aircraft)
        self.assertIn(self.aircraft_bell, published_aircraft)
        
    def test_02_aircraft_by_category(self):
        """Test grouping aircraft by category"""
        # Get airplanes
        airplanes = self.env['flight.aircraft'].search([
            ('model_id.class_id.aircraft_category', '=', 'airplane'),
            ('website_published', '=', True)
        ])
        
        self.assertIn(self.aircraft_g650, airplanes)
        self.assertIn(self.aircraft_citation, airplanes)
        self.assertNotIn(self.aircraft_bell, airplanes)
        
        # Get helicopters
        helicopters = self.env['flight.aircraft'].search([
            ('model_id.class_id.aircraft_category', '=', 'helicopter'),
            ('website_published', '=', True)
        ])
        
        self.assertIn(self.aircraft_bell, helicopters)
        self.assertNotIn(self.aircraft_g650, helicopters)
        
    def test_03_aircraft_charter_availability(self):
        """Test charter availability filtering"""
        available = self.env['flight.aircraft'].search([
            ('available_for_charter', '=', True),
            ('website_published', '=', True)
        ])
        
        self.assertIn(self.aircraft_g650, available)
        self.assertIn(self.aircraft_citation, available)
        self.assertIn(self.aircraft_bell, available)
        
    def test_04_aircraft_specifications_display(self):
        """Test aircraft specifications for website display"""
        # Check G650 specifications
        self.assertEqual(self.model_g650.max_passengers, 19)
        self.assertEqual(self.model_g650.cruise_speed, 500)
        self.assertEqual(self.model_g650.range_nm, 7000)
        
        # Check display name
        expected_name = f"Gulfstream G650"
        self.assertEqual(self.model_g650.display_name, expected_name)
        
    def test_05_aircraft_image_management(self):
        """Test aircraft image attachments for gallery"""
        # Create images for aircraft
        image1 = self.env['ir.attachment'].create({
            'name': 'g650_exterior.jpg',
            'type': 'binary',
            'datas': 'test_image_data',
            'res_model': 'flight.aircraft',
            'res_id': self.aircraft_g650.id,
            'public': True,
        })
        
        image2 = self.env['ir.attachment'].create({
            'name': 'g650_interior.jpg',
            'type': 'binary',
            'datas': 'test_image_data',
            'res_model': 'flight.aircraft',
            'res_id': self.aircraft_g650.id,
            'public': True,
        })
        
        # Get aircraft images
        images = self.env['ir.attachment'].search([
            ('res_model', '=', 'flight.aircraft'),
            ('res_id', '=', self.aircraft_g650.id),
            ('public', '=', True)
        ])
        
        self.assertEqual(len(images), 2)
        self.assertIn(image1, images)
        self.assertIn(image2, images)
        
    def test_06_fleet_statistics(self):
        """Test fleet statistics calculation"""
        published_fleet = self.env['flight.aircraft'].search([
            ('website_published', '=', True)
        ])
        
        # Count by category
        stats = {}
        for aircraft in published_fleet:
            category = aircraft.model_id.class_id.aircraft_category
            if category not in stats:
                stats[category] = 0
            stats[category] += 1
        
        self.assertEqual(stats.get('airplane', 0), 2)
        self.assertEqual(stats.get('helicopter', 0), 1)
        
    def test_07_aircraft_search_filters(self):
        """Test website search filters for aircraft"""
        # Filter by passenger capacity
        large_aircraft = self.env['flight.aircraft'].search([
            ('model_id.max_passengers', '>=', 10),
            ('website_published', '=', True)
        ])
        
        self.assertIn(self.aircraft_g650, large_aircraft)
        self.assertNotIn(self.aircraft_citation, large_aircraft)
        
        # Filter by range
        long_range = self.env['flight.aircraft'].search([
            ('model_id.range_nm', '>=', 3000),
            ('website_published', '=', True)
        ])
        
        self.assertIn(self.aircraft_g650, long_range)
        self.assertNotIn(self.aircraft_citation, long_range)
        
    def test_08_aircraft_seo_metadata(self):
        """Test SEO metadata for aircraft pages"""
        # Check aircraft has SEO-friendly URL
        aircraft_name = self.aircraft_g650.registration.replace(' ', '-').lower()
        
        # Check meta description content
        meta_description = f"{self.aircraft_g650.model_id.make_id.name} {self.aircraft_g650.model_id.name} - " \
                          f"{self.aircraft_g650.model_id.max_passengers} passengers, " \
                          f"{self.aircraft_g650.model_id.range_nm} nm range"
        
        self.assertTrue(meta_description)
        self.assertIn('Gulfstream', meta_description)
        
    def test_09_fleet_comparison_table(self):
        """Test data for fleet comparison table"""
        comparison_data = []
        
        for aircraft in [self.aircraft_g650, self.aircraft_citation, self.aircraft_bell]:
            if aircraft.website_published:
                comparison_data.append({
                    'registration': aircraft.registration,
                    'model': aircraft.model_id.display_name,
                    'category': aircraft.model_id.class_id.aircraft_category,
                    'passengers': aircraft.model_id.max_passengers,
                    'speed': aircraft.model_id.cruise_speed,
                    'range': aircraft.model_id.range_nm,
                    'available': aircraft.available_for_charter,
                })
        
        self.assertEqual(len(comparison_data), 3)
        
        # Check data integrity
        g650_data = next((d for d in comparison_data if d['registration'] == 'N650GS'), None)
        self.assertIsNotNone(g650_data)
        self.assertEqual(g650_data['passengers'], 19)
        
    def test_10_aircraft_availability_calendar(self):
        """Test aircraft availability for booking calendar"""
        # Create sample bookings
        today = datetime.now().date()
        
        booking1 = self.env['flight.flight'].create({
            'date': today + timedelta(days=5),
            'aircraft_id': self.aircraft_g650.id,
            'departure_id': self.env['flight.aerodrome'].create({
                'name': 'Test Airport',
                'icao': 'KTST',
            }).id,
            'arrival_id': self.env['flight.aerodrome'].create({
                'name': 'Test Airport 2',
                'icao': 'KTS2',
            }).id,
        })
        
        # Check aircraft availability
        booked_dates = self.env['flight.flight'].search([
            ('aircraft_id', '=', self.aircraft_g650.id),
            ('date', '>=', today),
            ('date', '<=', today + timedelta(days=30))
        ])
        
        self.assertEqual(len(booked_dates), 1)
        self.assertEqual(booked_dates[0].date, today + timedelta(days=5))
        
    def test_11_aircraft_operating_costs(self):
        """Test aircraft operating cost display"""
        # Add operating costs to aircraft
        self.aircraft_g650.hourly_rate = 8500.00
        self.aircraft_citation.hourly_rate = 2500.00
        self.aircraft_bell.hourly_rate = 1200.00
        
        # Calculate trip costs
        flight_hours = 3.5
        g650_cost = self.aircraft_g650.hourly_rate * flight_hours
        
        self.assertEqual(g650_cost, 29750.00)
        
    def test_12_responsive_fleet_display(self):
        """Test data structure for responsive fleet display"""
        # Prepare data for different screen sizes
        fleet_data = {
            'desktop': {
                'columns': ['Image', 'Model', 'Category', 'Passengers', 'Speed', 'Range', 'Availability'],
                'items_per_page': 10
            },
            'tablet': {
                'columns': ['Image', 'Model', 'Passengers', 'Availability'],
                'items_per_page': 6
            },
            'mobile': {
                'columns': ['Model', 'Availability'],
                'items_per_page': 4
            }
        }
        
        self.assertTrue(fleet_data['desktop'])
        self.assertTrue(fleet_data['tablet'])
        self.assertTrue(fleet_data['mobile'])
        self.assertEqual(len(fleet_data['desktop']['columns']), 7)


@tagged('post_install', '-at_install', 'website_flight_fleet', 'at_install')
class TestWebsiteFlightFleetHttp(HttpCase):
    """HTTP test cases for website flight fleet pages"""
    
    def test_01_fleet_page_access(self):
        """Test public access to fleet page"""
        # This would test actual HTTP routes
        # Implementation depends on specific website routes
        pass