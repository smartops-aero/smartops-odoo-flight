# -*- coding: utf-8 -*-
from odoo.tests import tagged
from odoo.exceptions import ValidationError
from .common import FlightCommon


@tagged('post_install', '-at_install', 'flight_aerodrome')
class TestAerodrome(FlightCommon):
    """Test cases for flight.aerodrome model"""
    
    def test_01_aerodrome_creation(self):
        """Test aerodrome creation with all fields"""
        aerodrome = self.env['flight.aerodrome'].create({
            'name': 'Test Airport',
            'icao': 'KTST',
            'iata': 'TST',
            'city': 'Test City',
            'country_id': self.country_us.id,
            'latitude': 30.1234,
            'longitude': -95.5678,
            'elevation': 150,
            'tz': 'America/Chicago',
        })
        
        self.assertTrue(aerodrome.id)
        self.assertEqual(aerodrome.icao, 'KTST')
        self.assertEqual(aerodrome.iata, 'TST')
        self.assertEqual(aerodrome.latitude, 30.1234)
        self.assertEqual(aerodrome.longitude, -95.5678)
        
    def test_02_aerodrome_display_name(self):
        """Test aerodrome display name generation"""
        # With IATA code
        self.assertEqual(
            self.aerodrome_jfk.display_name,
            'KTES(TSE) - Test Airport East'
        )
        
        # Without IATA code
        aerodrome_no_iata = self.env['flight.aerodrome'].create({
            'name': 'Small Airport',
            'icao': 'KSML',
            'city': 'Small City',
            'country_id': self.country_us.id,
        })
        self.assertEqual(
            aerodrome_no_iata.display_name,
            'KSML - Small Airport'
        )
        
    def test_03_aerodrome_coordinates_handling(self):
        """Test latitude and longitude field handling"""
        # Test valid coordinates (no validation constraints in model currently)
        aerodrome = self.env['flight.aerodrome'].create({
            'name': 'Polar Airport',
            'icao': 'KPOL',
            'latitude': 89.9999,
            'longitude': -179.9999,
            'country_id': self.country_us.id,
        })
        
        self.assertTrue(aerodrome.id)
        self.assertEqual(aerodrome.latitude, 89.9999)
        self.assertEqual(aerodrome.longitude, -179.9999)
        
        # Test edge case coordinates (model accepts any float values)
        edge_aerodrome = self.env['flight.aerodrome'].create({
            'name': 'Edge Case Airport',
            'icao': 'KEDG',
            'latitude': 90.0,  # Max latitude
            'longitude': 180.0,  # Max longitude
            'country_id': self.country_us.id,
        })
        
        self.assertTrue(edge_aerodrome.id)
        self.assertEqual(edge_aerodrome.latitude, 90.0)
        self.assertEqual(edge_aerodrome.longitude, 180.0)
            
    def test_04_aerodrome_search_by_location(self):
        """Test searching aerodromes by city, state, country"""
        # Search by city
        found = self.env['flight.aerodrome'].search([
            ('city', '=', 'New York')
        ])
        self.assertIn(self.aerodrome_jfk, found)
        
        # Search by country
        found = self.env['flight.aerodrome'].search([
            ('country_id', '=', self.country_us.id)
        ])
        self.assertIn(self.aerodrome_jfk, found)
        self.assertIn(self.aerodrome_lax, found)
        
        # Search by ICAO
        found = self.env['flight.aerodrome'].search([
            ('icao', '=', 'KTES')
        ])
        self.assertEqual(len(found), 1)
        self.assertEqual(found, self.aerodrome_jfk)
        
    def test_05_aerodrome_unique_codes(self):
        """Test ICAO and IATA code uniqueness"""
        # Create a unique aerodrome for this test only
        unique_icao = 'KUQT'  # Unique Test ICAO code
        test_aerodrome = self.env['flight.aerodrome'].create({
            'name': 'Unique Test Airport',
            'icao': unique_icao,
            'iata': 'UQT',
            'country_id': self.country_us.id,
        })
        
        # ICAO should be unique - this should raise an exception
        from psycopg2 import IntegrityError
        with self.assertRaises(IntegrityError):
            self.env['flight.aerodrome'].create({
                'name': 'Duplicate ICAO Test',
                'icao': unique_icao,  # Same ICAO should fail
                'country_id': self.country_us.id,
            })
            
        # IATA can be empty and doesn't have unique constraint (based on model)
        aerodrome1 = self.env['flight.aerodrome'].create({
            'name': 'Airport 1',
            'icao': 'KAP1',
            'iata': 'AP1',
            'country_id': self.country_us.id,
        })
        
        # IATA duplicates are currently allowed (no constraint in model)
        aerodrome2 = self.env['flight.aerodrome'].create({
            'name': 'Airport 2', 
            'icao': 'KAP2',
            'iata': 'AP1',  # Same IATA is allowed
            'country_id': self.country_us.id,
        })
        
        self.assertTrue(aerodrome1.id)
        self.assertTrue(aerodrome2.id)
        self.assertEqual(aerodrome1.iata, aerodrome2.iata)  # Both have same IATA
            
    def test_06_aerodrome_timezone(self):
        """Test aerodrome timezone field"""
        import pytz
        
        valid_timezones = [
            'America/New_York',
            'Europe/London',
            'Asia/Tokyo',
            'Australia/Sydney',
            'UTC',
        ]
        
        for tz in valid_timezones:
            aerodrome = self.env['flight.aerodrome'].create({
                'name': f'Airport {tz}',
                'icao': f'K{tz[:3].upper()}',
                'tz': tz,
            })
            self.assertEqual(aerodrome.tz, tz)
            
    def test_07_aerodrome_elevation(self):
        """Test aerodrome elevation handling"""
        # Positive elevation
        high_airport = self.env['flight.aerodrome'].create({
            'name': 'Mountain Airport',
            'icao': 'KMTN',
            'elevation': 8500,  # feet
        })
        self.assertEqual(high_airport.elevation, 8500)
        
        # Negative elevation (below sea level)
        low_airport = self.env['flight.aerodrome'].create({
            'name': 'Dead Sea Airport',
            'icao': 'KDSA',
            'elevation': -1200,  # feet below sea level
        })
        self.assertEqual(low_airport.elevation, -1200)
        
        # Zero elevation (sea level)
        sea_airport = self.env['flight.aerodrome'].create({
            'name': 'Sea Level Airport',
            'icao': 'KSEA',
            'elevation': 0,
        })
        self.assertEqual(sea_airport.elevation, 0)
        
    def test_08_aerodrome_as_departure_arrival(self):
        """Test aerodrome usage in flights"""
        flights_from_jfk = self.env['flight.flight'].search([
            ('departure_id', '=', self.aerodrome_jfk.id)
        ])
        
        flights_to_lax = self.env['flight.flight'].search([
            ('arrival_id', '=', self.aerodrome_lax.id)
        ])
        
        # Create a flight and verify aerodrome references
        flight = self.create_test_flight()
        self.assertEqual(flight.departure_id, self.aerodrome_jfk)
        self.assertEqual(flight.arrival_id, self.aerodrome_lax)
        
    def test_09_aerodrome_copy(self):
        """Test aerodrome duplication"""
        copy = self.aerodrome_jfk.copy({
            'icao': 'KCPY',
            'iata': 'CPY',
        })
        
        self.assertNotEqual(copy.id, self.aerodrome_jfk.id)
        self.assertEqual(copy.icao, 'KCPY')
        self.assertEqual(copy.iata, 'CPY')
        self.assertEqual(copy.city, self.aerodrome_jfk.city)
        self.assertEqual(copy.country_id, self.aerodrome_jfk.country_id)