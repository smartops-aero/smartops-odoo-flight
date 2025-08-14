from datetime import datetime, timedelta

from psycopg2 import IntegrityError

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'flight_event')
class TestFlightEvent(TransactionCase):
    """Test cases for flight event management"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        cls.company = cls.env.company
        
        # Create aircraft data
        aircraft_class = cls.env['flight.aircraft.class'].create({
            'name': 'Business Jet',
            'aircraft_category': 'airplane',
        })
        
        aircraft_make = cls.env['flight.aircraft.make'].create({
            'name': 'Cessna',
        })
        
        aircraft_model = cls.env['flight.aircraft.model'].create({
            'name': 'Citation X',
            'make_id': aircraft_make.id,
            'class_id': aircraft_class.id,
            'engine_type': 'turbofan',
            'gear_type': 'retractable_tricycle',
            'code': 'C750',
        })
        
        cls.aircraft = cls.env['flight.aircraft'].create({
            'registration': 'N750CX',
            'model_id': aircraft_model.id,
            'operator_id': cls.company.partner_id.id,
        })
        
        # Get countries for aerodrome creation
        cls.country_us = cls.env.ref('base.us')
        
        # Create aerodromes
        cls.aerodrome_origin = cls.env['flight.aerodrome'].create({
            'name': 'Miami International Airport',
            'icao': 'KEVM',  # Use unique ICAO to avoid conflicts
            'iata': 'EVM',
            'city': 'Miami',
            'country_id': cls.country_us.id,
        })
        
        cls.aerodrome_dest = cls.env['flight.aerodrome'].create({
            'name': 'Chicago O\'Hare International Airport',
            'icao': 'KEVT',  # Use unique ICAO to avoid conflicts
            'iata': 'EVT', 
            'city': 'Chicago',
            'country_id': cls.country_us.id,
        })
        
        # Create flight
        cls.flight = cls.env['flight.flight'].create({
            'date': datetime.now().date(),
            'aircraft_id': cls.aircraft.id,
            'departure_id': cls.aerodrome_origin.id,
            'arrival_id': cls.aerodrome_dest.id,
        })
        
        # Create event codes
        cls.event_code_pushback = cls.env['flight.event.code'].create({
            'name': 'Pushback',
            'code': 'OUT',
            'description': 'Aircraft pushback from gate',
            'sequence': 10,
        })
        
        cls.event_code_takeoff = cls.env['flight.event.code'].create({
            'name': 'Takeoff',
            'code': 'OFF',
            'description': 'Aircraft wheels off ground',
            'sequence': 20,
        })
        
        cls.event_code_landing = cls.env['flight.event.code'].create({
            'name': 'Landing',
            'code': 'ON',
            'description': 'Aircraft wheels on ground',
            'sequence': 30,
        })
        
        cls.event_code_arrival = cls.env['flight.event.code'].create({
            'name': 'Arrival at Gate',
            'code': 'IN',
            'description': 'Aircraft arrival at gate',
            'sequence': 40,
        })
        
    def test_01_event_code_creation(self):
        """Test event code creation and validation"""
        event_code = self.env['flight.event.code'].create({
            'name': 'Weather Diversion',
            'code': 'WX_DIV',
            'description': 'Weather related diversion',
            'sequence': 50,
        })
        
        self.assertTrue(event_code.id)
        self.assertEqual(event_code.code, 'WX_DIV')
        self.assertEqual(event_code.name, 'Weather Diversion')
        self.assertEqual(event_code.sequence, 50)
        
    def test_02_event_code_uniqueness(self):
        """Test event code uniqueness constraint"""
        # Try to create duplicate code
        with self.assertRaises(IntegrityError):
            self.env['flight.event.code'].create({
                'name': 'Duplicate Pushback',
                'code': 'OUT',  # Same code as existing
                'description': 'Duplicate code test',
            })
            
    def test_03_flight_event_time_creation(self):
        """Test flight event time creation"""
        event_time = self.env['flight.event.time'].create({
            'flight_id': self.flight.id,
            'code_id': self.event_code_pushback.id,
            'time_kind': 'S',  # Scheduled
            'time': datetime.now(),
        })
        
        self.assertTrue(event_time.id)
        self.assertEqual(event_time.flight_id, self.flight)
        self.assertEqual(event_time.code_id, self.event_code_pushback)
        self.assertEqual(event_time.time_kind, 'S')
        
    def test_04_flight_event_time_kinds(self):
        """Test different event time kinds"""
        time_kinds = ['A', 'S', 'R', 'T', 'E']  # Actual, Scheduled, Requested, Target, Estimated
        
        for i, kind in enumerate(time_kinds):
            event_time = self.env['flight.event.time'].create({
                'flight_id': self.flight.id,
                'code_id': self.event_code_pushback.id,
                'time_kind': kind,
                'time': datetime.now() + timedelta(minutes=i),  # Different times to avoid conflicts
            })
            
            self.assertEqual(event_time.time_kind, kind)
            
    def test_05_flight_phase_creation(self):
        """Test flight phase creation"""
        phase = self.env['flight.phase'].create({
            'name': 'Taxi Out',
            'start_event_code_id': self.event_code_pushback.id,
            'end_event_code_id': self.event_code_takeoff.id,
            'sequence': 10,
        })
        
        self.assertTrue(phase.id)
        self.assertEqual(phase.name, 'Taxi Out')
        self.assertEqual(phase.start_event_code_id, self.event_code_pushback)
        self.assertEqual(phase.end_event_code_id, self.event_code_takeoff)
        
    def test_06_flight_phase_duration_creation(self):
        """Test flight phase duration creation and calculation"""
        # Create a flight phase
        phase = self.env['flight.phase'].create({
            'name': 'Flight Time',
            'start_event_code_id': self.event_code_takeoff.id,
            'end_event_code_id': self.event_code_landing.id,
            'sequence': 20,
        })
        
        # Create start and end events - this should automatically create phase duration
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=2, minutes=30)
        
        self.env['flight.event.time'].create({
            'flight_id': self.flight.id,
            'code_id': self.event_code_takeoff.id,
            'time_kind': 'A',
            'time': start_time,
        })
        
        self.env['flight.event.time'].create({
            'flight_id': self.flight.id,
            'code_id': self.event_code_landing.id,
            'time_kind': 'A',
            'time': end_time,
        })
        
        # Check that phase duration was automatically created
        phase_durations = self.env['flight.phase.duration'].search([
            ('flight_id', '=', self.flight.id),
            ('phase_id', '=', phase.id),
            ('time_kind', '=', 'A'),
        ])
        
        self.assertEqual(len(phase_durations), 1)
        phase_duration = phase_durations[0]
        
        self.assertEqual(phase_duration.flight_id, self.flight)
        self.assertEqual(phase_duration.phase_id, phase)
        self.assertEqual(phase_duration.duration, 2.5)  # 2.5 hours
        
    def test_07_flight_phase_duration_uniqueness(self):
        """Test flight phase duration uniqueness constraint"""
        # Create a new flight to avoid conflicts with automatic durations
        test_flight = self.env['flight.flight'].create({
            'date': datetime.now().date(),
            'aircraft_id': self.aircraft.id,
            'departure_id': self.aerodrome_origin.id,
            'arrival_id': self.aerodrome_dest.id,
        })
        
        # Create a flight phase  
        phase = self.env['flight.phase'].create({
            'name': 'Test Phase Unique',
            'start_event_code_id': self.event_code_pushback.id,
            'end_event_code_id': self.event_code_takeoff.id,
            'sequence': 10,
        })
        
        # Create events - this will automatically create one phase duration
        start_event = self.env['flight.event.time'].create({
            'flight_id': test_flight.id,
            'code_id': self.event_code_pushback.id,
            'time_kind': 'A',
            'time': datetime.now(),
        })
        
        end_event = self.env['flight.event.time'].create({
            'flight_id': test_flight.id,
            'code_id': self.event_code_takeoff.id,
            'time_kind': 'A',
            'time': datetime.now() + timedelta(minutes=30),
        })
        
        # Verify the automatic duration was created
        existing_durations = self.env['flight.phase.duration'].search([
            ('flight_id', '=', test_flight.id),
            ('phase_id', '=', phase.id),
            ('time_kind', '=', 'A'),
        ])
        self.assertEqual(len(existing_durations), 1)
        
        # Try to manually create duplicate - should fail
        with self.assertRaises(IntegrityError):
            self.env['flight.phase.duration'].create({
                'flight_id': test_flight.id,
                'phase_id': phase.id,
                'start_event_id': start_event.id,
                'end_event_id': end_event.id,
                'time_kind': 'A',
            })
            
    def test_08_event_time_history(self):
        """Test event time history tracking"""
        # Create an event time
        event_time = self.env['flight.event.time'].create({
            'flight_id': self.flight.id,
            'code_id': self.event_code_pushback.id,
            'time_kind': 'S',
            'time': datetime.now(),
        })
        
        # Update the time - should create history record
        new_time = datetime.now() + timedelta(hours=1)
        event_time.write({'time': new_time})
        
        # Check history was created
        self.assertTrue(event_time.history_ids)
        self.assertTrue(event_time.has_history)
        
    def test_09_event_time_write_restrictions(self):
        """Test that only time field can be updated"""
        event_time = self.env['flight.event.time'].create({
            'flight_id': self.flight.id,
            'code_id': self.event_code_pushback.id,
            'time_kind': 'S',
            'time': datetime.now(),
        })
        
        # Should be able to update time
        event_time.write({'time': datetime.now() + timedelta(hours=1)})
        
        # Should not be able to update other fields
        from odoo.exceptions import UserError
        with self.assertRaises(UserError):
            event_time.write({'time_kind': 'A'})
            
    def test_10_display_time_calculation(self):
        """Test display time calculation with day offsets"""
        flight_date = datetime.now().date()
        
        # Create flight with specific date
        test_flight = self.env['flight.flight'].create({
            'date': flight_date,
            'aircraft_id': self.aircraft.id,
            'departure_id': self.aerodrome_origin.id,
            'arrival_id': self.aerodrome_dest.id,
        })
        
        # Event on same day
        same_day_time = datetime.combine(flight_date, datetime.min.time()) + timedelta(hours=10)
        event_same_day = self.env['flight.event.time'].create({
            'flight_id': test_flight.id,
            'code_id': self.event_code_pushback.id,
            'time_kind': 'S',
            'time': same_day_time,
        })
        
        # Event next day
        next_day_time = same_day_time + timedelta(days=1)
        event_next_day = self.env['flight.event.time'].create({
            'flight_id': test_flight.id,
            'code_id': self.event_code_landing.id,
            'time_kind': 'S',
            'time': next_day_time,
        })
        
        # Check display times
        self.assertEqual(event_same_day.display_time, '10:00')
        self.assertEqual(event_next_day.display_time, '10:00 (+1)')
        
    def test_11_event_code_phase_relationships(self):
        """Test event code relationships with phases"""
        # Create phases that use our event codes
        taxi_out_phase = self.env['flight.phase'].create({
            'name': 'Taxi Out',
            'start_event_code_id': self.event_code_pushback.id,
            'end_event_code_id': self.event_code_takeoff.id,
        })
        
        flight_phase = self.env['flight.phase'].create({
            'name': 'Flight',
            'start_event_code_id': self.event_code_takeoff.id,
            'end_event_code_id': self.event_code_landing.id,
        })
        
        # Check relationships
        self.assertIn(taxi_out_phase, self.event_code_pushback.start_phase_ids)
        self.assertIn(taxi_out_phase, self.event_code_takeoff.end_phase_ids)
        self.assertIn(flight_phase, self.event_code_takeoff.start_phase_ids)
        self.assertIn(flight_phase, self.event_code_landing.end_phase_ids)
        
    def test_12_automatic_phase_duration_creation(self):
        """Test automatic phase duration creation when events are created"""
        # Create a phase
        phase = self.env['flight.phase'].create({
            'name': 'Auto Test Phase',
            'start_event_code_id': self.event_code_pushback.id,
            'end_event_code_id': self.event_code_takeoff.id,
        })
        
        # Create start event
        start_event = self.env['flight.event.time'].create({
            'flight_id': self.flight.id,
            'code_id': self.event_code_pushback.id,
            'time_kind': 'A',
            'time': datetime.now(),
        })
        
        # Create end event - this should trigger automatic phase duration creation
        end_event = self.env['flight.event.time'].create({
            'flight_id': self.flight.id,
            'code_id': self.event_code_takeoff.id,
            'time_kind': 'A',
            'time': datetime.now() + timedelta(minutes=30),
        })
        
        # Check that phase duration was automatically created
        phase_durations = self.env['flight.phase.duration'].search([
            ('flight_id', '=', self.flight.id),
            ('phase_id', '=', phase.id),
            ('time_kind', '=', 'A'),
        ])
        
        self.assertEqual(len(phase_durations), 1)
        self.assertEqual(phase_durations.start_event_id, start_event)
        self.assertEqual(phase_durations.end_event_id, end_event)