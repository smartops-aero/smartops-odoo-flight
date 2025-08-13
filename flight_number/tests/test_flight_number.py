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
        
        # Create airline
        cls.airline = cls.env['flight.airline'].create({
            'name': 'Test Airways',
            'iata_code': 'TX',
            'icao_code': 'TXA',
            'country': 'US',
            'active': True,
        })
        
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
            'gear_type': 'tricycle_retractable',
            'code': 'A320',
        })
        
        cls.aircraft = cls.env['flight.aircraft'].create({
            'registration': 'N320TX',
            'model_id': aircraft_model.id,
            'operator_id': cls.env.company.partner_id.id,
        })
        
        # Create aerodromes
        cls.aerodrome_nyc = cls.env['flight.aerodrome'].create({
            'name': 'New York JFK',
            'icao': 'KJFK',
            'iata': 'JFK',
            'city': 'New York',
            'country': 'US',
        })
        
        cls.aerodrome_lon = cls.env['flight.aerodrome'].create({
            'name': 'London Heathrow',
            'icao': 'EGLL',
            'iata': 'LHR',
            'city': 'London',
            'country': 'GB',
        })
        
    def test_01_airline_creation(self):
        """Test airline creation and validation"""
        airline = self.env['flight.airline'].create({
            'name': 'Global Airlines',
            'iata_code': 'GL',
            'icao_code': 'GLA',
            'country': 'US',
            'callsign': 'GLOBAL',
            'active': True,
        })
        
        self.assertTrue(airline.id)
        self.assertEqual(airline.iata_code, 'GL')
        self.assertEqual(airline.icao_code, 'GLA')
        self.assertEqual(airline.callsign, 'GLOBAL')
        
    def test_02_flight_number_format(self):
        """Test flight number format validation"""
        # Valid formats
        valid_numbers = ['TX001', 'TX1234', 'TXA567', 'TX9999']
        
        for number in valid_numbers:
            flight_num = self.env['flight.flight.number'].create({
                'airline_id': self.airline.id,
                'flight_number': number,
                'departure_id': self.aerodrome_nyc.id,
                'arrival_id': self.aerodrome_lon.id,
                'active': True,
            })
            self.assertTrue(flight_num.id)
            
    def test_03_flight_number_uniqueness(self):
        """Test flight number uniqueness per airline"""
        # Create first flight number
        flight_num1 = self.env['flight.flight.number'].create({
            'airline_id': self.airline.id,
            'flight_number': 'TX100',
            'departure_id': self.aerodrome_nyc.id,
            'arrival_id': self.aerodrome_lon.id,
        })
        
        # Try to create duplicate
        with self.assertRaises(ValidationError):
            self.env['flight.flight.number'].create({
                'airline_id': self.airline.id,
                'flight_number': 'TX100',  # Same number
                'departure_id': self.aerodrome_nyc.id,
                'arrival_id': self.aerodrome_lon.id,
            })
            
    def test_04_flight_number_schedule(self):
        """Test flight number scheduling"""
        flight_num = self.env['flight.flight.number'].create({
            'airline_id': self.airline.id,
            'flight_number': 'TX200',
            'departure_id': self.aerodrome_nyc.id,
            'arrival_id': self.aerodrome_lon.id,
            'departure_time': '14:30',
            'arrival_time': '22:30',
            'flight_duration': 8.0,
            'days_of_week': 'mon,wed,fri',
            'active': True,
        })
        
        self.assertEqual(flight_num.departure_time, '14:30')
        self.assertEqual(flight_num.arrival_time, '22:30')
        self.assertEqual(flight_num.flight_duration, 8.0)
        self.assertIn('mon', flight_num.days_of_week)
        
    def test_05_codeshare_flights(self):
        """Test codeshare flight numbers"""
        # Create partner airline
        partner_airline = self.env['flight.airline'].create({
            'name': 'Partner Air',
            'iata_code': 'PA',
            'icao_code': 'PAR',
            'country': 'US',
        })
        
        # Create main flight number
        main_flight = self.env['flight.flight.number'].create({
            'airline_id': self.airline.id,
            'flight_number': 'TX300',
            'departure_id': self.aerodrome_nyc.id,
            'arrival_id': self.aerodrome_lon.id,
        })
        
        # Create codeshare
        codeshare = self.env['flight.flight.number'].create({
            'airline_id': partner_airline.id,
            'flight_number': 'PA800',
            'departure_id': self.aerodrome_nyc.id,
            'arrival_id': self.aerodrome_lon.id,
            'codeshare_flight_id': main_flight.id,
        })
        
        self.assertEqual(codeshare.codeshare_flight_id, main_flight)
        
    def test_06_seasonal_flights(self):
        """Test seasonal flight schedules"""
        seasonal_flight = self.env['flight.flight.number'].create({
            'airline_id': self.airline.id,
            'flight_number': 'TX400',
            'departure_id': self.aerodrome_nyc.id,
            'arrival_id': self.aerodrome_lon.id,
            'seasonal': True,
            'season_start': '2024-06-01',
            'season_end': '2024-09-30',
            'active': True,
        })
        
        self.assertTrue(seasonal_flight.seasonal)
        self.assertEqual(str(seasonal_flight.season_start), '2024-06-01')
        self.assertEqual(str(seasonal_flight.season_end), '2024-09-30')
        
    def test_07_flight_number_to_flight_assignment(self):
        """Test assigning flight numbers to actual flights"""
        flight_num = self.env['flight.flight.number'].create({
            'airline_id': self.airline.id,
            'flight_number': 'TX500',
            'departure_id': self.aerodrome_nyc.id,
            'arrival_id': self.aerodrome_lon.id,
        })
        
        # Create actual flight
        flight = self.env['flight.flight'].create({
            'date': datetime.now().date(),
            'aircraft_id': self.aircraft.id,
            'departure_id': self.aerodrome_nyc.id,
            'arrival_id': self.aerodrome_lon.id,
            'flight_number_id': flight_num.id,
        })
        
        self.assertEqual(flight.flight_number_id, flight_num)
        self.assertEqual(flight.computed_flight_number, 'TX500')
        
    def test_08_flight_number_capacity(self):
        """Test flight number capacity allocation"""
        flight_num = self.env['flight.flight.number'].create({
            'airline_id': self.airline.id,
            'flight_number': 'TX600',
            'departure_id': self.aerodrome_nyc.id,
            'arrival_id': self.aerodrome_lon.id,
            'seats_first': 12,
            'seats_business': 30,
            'seats_economy': 150,
            'cargo_capacity': 5000.0,
        })
        
        self.assertEqual(flight_num.seats_first, 12)
        self.assertEqual(flight_num.seats_business, 30)
        self.assertEqual(flight_num.seats_economy, 150)
        
        # Calculate total seats
        total_seats = flight_num.seats_first + flight_num.seats_business + flight_num.seats_economy
        self.assertEqual(total_seats, 192)
        
    def test_09_international_domestic_classification(self):
        """Test flight classification as domestic or international"""
        # Domestic flight
        domestic_flight = self.env['flight.flight.number'].create({
            'airline_id': self.airline.id,
            'flight_number': 'TX700',
            'departure_id': self.aerodrome_nyc.id,
            'arrival_id': self.env['flight.aerodrome'].create({
                'name': 'Los Angeles',
                'icao': 'KLAX',
                'iata': 'LAX',
                'country': 'US',
            }).id,
            'flight_type': 'domestic',
        })
        
        self.assertEqual(domestic_flight.flight_type, 'domestic')
        
        # International flight
        intl_flight = self.env['flight.flight.number'].create({
            'airline_id': self.airline.id,
            'flight_number': 'TX701',
            'departure_id': self.aerodrome_nyc.id,
            'arrival_id': self.aerodrome_lon.id,
            'flight_type': 'international',
        })
        
        self.assertEqual(intl_flight.flight_type, 'international')
        
    def test_10_flight_number_status(self):
        """Test flight number status management"""
        flight_num = self.env['flight.flight.number'].create({
            'airline_id': self.airline.id,
            'flight_number': 'TX800',
            'departure_id': self.aerodrome_nyc.id,
            'arrival_id': self.aerodrome_lon.id,
            'status': 'scheduled',
            'active': True,
        })
        
        # Test status transitions
        statuses = ['scheduled', 'suspended', 'cancelled', 'completed']
        
        for status in statuses:
            flight_num.status = status
            self.assertEqual(flight_num.status, status)
            
    def test_11_flight_number_search(self):
        """Test searching flight numbers"""
        # Create multiple flight numbers
        for i in range(5):
            self.env['flight.flight.number'].create({
                'airline_id': self.airline.id,
                'flight_number': f'TX90{i}',
                'departure_id': self.aerodrome_nyc.id,
                'arrival_id': self.aerodrome_lon.id,
            })
        
        # Search by airline
        tx_flights = self.env['flight.flight.number'].search([
            ('airline_id', '=', self.airline.id)
        ])
        
        self.assertGreaterEqual(len(tx_flights), 5)
        
        # Search by route
        route_flights = self.env['flight.flight.number'].search([
            ('departure_id', '=', self.aerodrome_nyc.id),
            ('arrival_id', '=', self.aerodrome_lon.id),
        ])
        
        self.assertGreaterEqual(len(route_flights), 5)
        
    def test_12_flight_number_display_name(self):
        """Test flight number display name generation"""
        flight_num = self.env['flight.flight.number'].create({
            'airline_id': self.airline.id,
            'flight_number': 'TX999',
            'departure_id': self.aerodrome_nyc.id,
            'arrival_id': self.aerodrome_lon.id,
        })
        
        expected_name = f"TX999 (JFK → LHR)"
        self.assertEqual(flight_num.display_name, expected_name)