# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


@tagged('post_install', '-at_install', 'flight_number')
class TestFlightNumber(TransactionCase):
    """Test cases for flight number management"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Create flight prefixes for testing
        cls.prefix_aa = cls.env['flight.prefix'].create({
            'name': 'AA',
            'description': 'American Airlines',
        })
        
        cls.prefix_ua = cls.env['flight.prefix'].create({
            'name': 'UA', 
            'description': 'United Airlines',
        })
        
        # Note: flight.airline model doesn't exist in flight_number module
        # Tests need to be updated to work with available models
        
        # Create aircraft data
        aircraft_class = cls.env['flight.aircraft.class'].create({
            'name': 'Airliner',
            'aircraft_category': 'airplane',
        })
        
        aircraft_make = cls.env['flight.aircraft.make'].create({
            'name': 'Airbus',
        })
        
        aircraft_model = cls.env['flight.aircraft.model'].create({
            'name': 'A320',
            'make_id': aircraft_make.id,
            'class_id': aircraft_class.id,
            'engine_type': 'turbofan',
            'gear_type': 'retractable_tricycle',
            'code': 'A320',
        })
        
        cls.aircraft = cls.env['flight.aircraft'].create({
            'registration': 'N320TX',
            'model_id': aircraft_model.id,
            'operator_id': cls.env.company.partner_id.id,
        })
        
        # Get or create countries
        cls.country_us = cls.env.ref('base.us') 
        cls.country_gb = cls.env.ref('base.uk')
        
        # Create aerodromes
        cls.aerodrome_nyc = cls.env['flight.aerodrome'].create({
            'name': 'New York JFK',
            'icao': 'KNUM',  # Use unique ICAO to avoid conflicts  
            'iata': 'NUM',
            'city': 'New York',
            'country_id': cls.country_us.id,
        })
        
        cls.aerodrome_lon = cls.env['flight.aerodrome'].create({
            'name': 'London Heathrow',
            'icao': 'EGNUM',  # Use unique ICAO to avoid conflicts
            'iata': 'LNU',
            'city': 'London', 
            'country_id': cls.country_gb.id,
        })
        
    def test_01_flight_prefix_creation(self):
        """Test flight prefix creation and validation"""
        prefix = self.env['flight.prefix'].create({
            'name': 'TX',
            'description': 'Test Airline',
        })
        
        self.assertTrue(prefix.id)
        self.assertEqual(prefix.name, 'TX')
        self.assertEqual(prefix.description, 'Test Airline')
        
    def test_02_flight_number_creation(self):
        """Test flight number creation"""
        # Valid numbers
        valid_numbers = ['001', '1234', '567', '9999']
        
        for number in valid_numbers:
            flight_num = self.env['flight.number'].create({
                'prefix_id': self.prefix_aa.id,
                'number': number,
            })
            self.assertTrue(flight_num.id)
            self.assertEqual(flight_num.number, number)
            self.assertEqual(flight_num.prefix_id, self.prefix_aa)
            
    def test_03_flight_number_display_name(self):
        """Test flight number display name generation"""
        # Create flight number
        flight_num = self.env['flight.number'].create({
            'prefix_id': self.prefix_aa.id,
            'number': '100',
        })
        
        # Test display_name field
        self.assertEqual(flight_num.display_name, 'AA100')
        
        # Test with different prefix
        flight_num2 = self.env['flight.number'].create({
            'prefix_id': self.prefix_ua.id,
            'number': '200',
        })
        
        self.assertEqual(flight_num2.display_name, 'UA200')
            
    def test_04_flight_number_search(self):
        """Test flight number name search"""
        # Create flight numbers
        flight_num1 = self.env['flight.number'].create({
            'prefix_id': self.prefix_aa.id,
            'number': '300',
        })
        
        flight_num2 = self.env['flight.number'].create({
            'prefix_id': self.prefix_ua.id,
            'number': '400',
        })
        
        # Test search by prefix
        aa_results = self.env['flight.number']._name_search('AA')
        self.assertIn(flight_num1.id, aa_results)
        self.assertNotIn(flight_num2.id, aa_results)
        
        # Test search by number
        num_results = self.env['flight.number']._name_search('300')
        self.assertIn(flight_num1.id, num_results)
        
    def test_05_flight_number_with_flight(self):
        """Test flight number integration with flight.flight model"""
        # Create flight number
        flight_num = self.env['flight.number'].create({
            'prefix_id': self.prefix_aa.id,
            'number': '500',
        })
        
        # Create actual flight with flight number
        flight = self.env['flight.flight'].create({
            'date': datetime.now().date(),
            'aircraft_id': self.aircraft.id,
            'departure_id': self.aerodrome_nyc.id,
            'arrival_id': self.aerodrome_lon.id,
            'number_id': flight_num.id,
        })
        
        self.assertEqual(flight.number_id, flight_num)
        
        # Test flight display_name includes flight number
        flight_name = flight.display_name
        self.assertIn('AA500', flight_name)
        
    def test_06_multiple_prefixes(self):
        """Test multiple flight prefixes"""
        # Create additional prefixes
        prefix_ba = self.env['flight.prefix'].create({
            'name': 'BA',
            'description': 'British Airways',
        })
        
        prefix_lh = self.env['flight.prefix'].create({
            'name': 'LH',
            'description': 'Lufthansa',
        })
        
        # Create flight numbers with different prefixes
        flight_numbers = []
        for prefix in [self.prefix_aa, self.prefix_ua, prefix_ba, prefix_lh]:
            flight_num = self.env['flight.number'].create({
                'prefix_id': prefix.id,
                'number': '100',
            })
            flight_numbers.append(flight_num)
        
        # Test that all were created successfully
        self.assertEqual(len(flight_numbers), 4)
        
        # Test different display names
        expected_names = ['AA100', 'UA100', 'BA100', 'LH100']
        actual_names = [fn.display_name for fn in flight_numbers]
        self.assertEqual(actual_names, expected_names)
        
    def test_07_flight_number_empty_prefix(self):
        """Test flight number behavior with missing prefix"""
        # Create flight number without prefix
        flight_num = self.env['flight.number'].create({
            'number': '999',
        })
        
        # Should handle gracefully (though prefix might be required in real usage)
        self.assertTrue(flight_num.id)
        self.assertEqual(flight_num.number, '999')
        
    def test_08_flight_prefix_search(self):
        """Test flight prefix search functionality"""
        # Search for existing prefixes
        aa_prefix = self.env['flight.prefix'].search([('name', '=', 'AA')])
        self.assertEqual(len(aa_prefix), 1)
        self.assertEqual(aa_prefix.description, 'American Airlines')
        
        ua_prefix = self.env['flight.prefix'].search([('name', '=', 'UA')])  
        self.assertEqual(len(ua_prefix), 1)
        self.assertEqual(ua_prefix.description, 'United Airlines')
        
    def test_09_flight_number_domain_search(self):
        """Test complex domain searches on flight numbers"""
        # Create test data
        flight_nums = []
        for i, prefix in enumerate([self.prefix_aa, self.prefix_ua]):
            for j in range(3):
                flight_num = self.env['flight.number'].create({
                    'prefix_id': prefix.id,
                    'number': f'{i}{j}0',
                })
                flight_nums.append(flight_num)
        
        # Search by prefix
        aa_numbers = self.env['flight.number'].search([
            ('prefix_id', '=', self.prefix_aa.id)
        ])
        self.assertEqual(len(aa_numbers), 3)
        
        # Search by number pattern
        zero_numbers = self.env['flight.number'].search([
            ('number', 'like', '%0%')
        ])
        self.assertGreaterEqual(len(zero_numbers), 6)
        
    def test_10_flight_number_edge_cases(self):
        """Test edge cases for flight numbers"""
        # Test with special characters in number
        flight_num1 = self.env['flight.number'].create({
            'prefix_id': self.prefix_aa.id,
            'number': '123A',
        })
        
        self.assertEqual(flight_num1.display_name, 'AA123A')
        
        # Test with very long number
        flight_num2 = self.env['flight.number'].create({
            'prefix_id': self.prefix_ua.id,
            'number': '123456789',
        })
        
        self.assertEqual(flight_num2.display_name, 'UA123456789')
        
    def test_11_flight_prefix_validation(self):
        """Test flight prefix validation and constraints"""
        # Test creating prefix with empty name should work (no constraints defined)
        prefix = self.env['flight.prefix'].create({
            'name': '',
            'description': 'Empty Name Test',
        })
        
        self.assertTrue(prefix.id)
        
    def test_12_flight_number_performance(self):
        """Test flight number creation performance with bulk operations"""
        # Create multiple flight numbers at once
        flight_numbers_data = []
        for i in range(10):
            flight_numbers_data.append({
                'prefix_id': self.prefix_aa.id,
                'number': f'BULK{i:03d}',
            })
        
        # Bulk create
        flight_numbers = self.env['flight.number'].create(flight_numbers_data)
        
        self.assertEqual(len(flight_numbers), 10)
        
        # Test that all have correct prefix
        for flight_num in flight_numbers:
            self.assertEqual(flight_num.prefix_id, self.prefix_aa)