# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


@tagged('post_install', '-at_install', 'flight_event')
class TestFlightEvent(TransactionCase):
    """Test cases for flight event management"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Create base data
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
            'gear_type': 'tricycle_retractable',
            'code': 'C750',
        })
        
        cls.aircraft = cls.env['flight.aircraft'].create({
            'registration': 'N750CX',
            'model_id': aircraft_model.id,
            'operator_id': cls.company.partner_id.id,
        })
        
        # Create aerodromes
        cls.aerodrome_origin = cls.env['flight.aerodrome'].create({
            'name': 'Miami International Airport',
            'icao': 'KMIA',
            'iata': 'MIA',
            'city': 'Miami',
            'state': 'FL',
            'country': 'US',
        })
        
        cls.aerodrome_dest = cls.env['flight.aerodrome'].create({
            'name': 'Chicago O\'Hare International Airport',
            'icao': 'KORD',
            'iata': 'ORD',
            'city': 'Chicago',
            'state': 'IL',
            'country': 'US',
        })
        
        # Create flight
        cls.flight = cls.env['flight.flight'].create({
            'date': datetime.now().date(),
            'aircraft_id': cls.aircraft.id,
            'departure_id': cls.aerodrome_origin.id,
            'arrival_id': cls.aerodrome_dest.id,
            'scheduled_departure': datetime.now(),
            'scheduled_arrival': datetime.now() + timedelta(hours=3),
        })
        
        # Create event types
        cls.event_type_delay = cls.env['flight.event.type'].create({
            'name': 'Delay',
            'code': 'DELAY',
            'category': 'operational',
            'severity': 'medium',
            'active': True,
        })
        
        cls.event_type_emergency = cls.env['flight.event.type'].create({
            'name': 'Emergency',
            'code': 'EMERG',
            'category': 'safety',
            'severity': 'high',
            'active': True,
        })
        
        cls.event_type_maintenance = cls.env['flight.event.type'].create({
            'name': 'Maintenance',
            'code': 'MAINT',
            'category': 'technical',
            'severity': 'low',
            'active': True,
        })
        
    def test_01_event_type_creation(self):
        """Test event type creation and validation"""
        event_type = self.env['flight.event.type'].create({
            'name': 'Weather Diversion',
            'code': 'WX_DIV',
            'category': 'operational',
            'severity': 'medium',
            'description': 'Flight diverted due to weather conditions',
            'active': True,
        })
        
        self.assertTrue(event_type.id)
        self.assertEqual(event_type.code, 'WX_DIV')
        self.assertEqual(event_type.severity, 'medium')
        
    def test_02_flight_event_creation(self):
        """Test flight event creation"""
        event = self.env['flight.event'].create({
            'flight_id': self.flight.id,
            'event_type_id': self.event_type_delay.id,
            'event_date': datetime.now(),
            'description': 'Flight delayed due to weather',
            'duration_minutes': 45,
            'status': 'active',
        })
        
        self.assertTrue(event.id)
        self.assertEqual(event.flight_id, self.flight)
        self.assertEqual(event.event_type_id, self.event_type_delay)
        self.assertEqual(event.duration_minutes, 45)
        
    def test_03_event_severity_levels(self):
        """Test different event severity levels"""
        severities = ['low', 'medium', 'high', 'critical']
        
        for severity in severities:
            event_type = self.env['flight.event.type'].create({
                'name': f'{severity.capitalize()} Event',
                'code': f'EVT_{severity.upper()}',
                'category': 'operational',
                'severity': severity,
            })
            
            self.assertEqual(event_type.severity, severity)
            
            # Create event with this type
            event = self.env['flight.event'].create({
                'flight_id': self.flight.id,
                'event_type_id': event_type.id,
                'event_date': datetime.now(),
                'description': f'Test {severity} severity event',
            })
            
            self.assertEqual(event.event_type_id.severity, severity)
            
    def test_04_event_categories(self):
        """Test event categorization"""
        categories = {
            'operational': 'Flight Operations',
            'technical': 'Aircraft Technical',
            'safety': 'Safety Related',
            'regulatory': 'Regulatory Compliance',
            'commercial': 'Commercial Operations',
        }
        
        for code, name in categories.items():
            event_type = self.env['flight.event.type'].create({
                'name': name,
                'code': f'CAT_{code.upper()}',
                'category': code,
                'severity': 'low',
            })
            
            self.assertEqual(event_type.category, code)
            
    def test_05_event_status_workflow(self):
        """Test event status workflow"""
        event = self.env['flight.event'].create({
            'flight_id': self.flight.id,
            'event_type_id': self.event_type_emergency.id,
            'event_date': datetime.now(),
            'description': 'Medical emergency on board',
            'status': 'active',
        })
        
        # Active status
        self.assertEqual(event.status, 'active')
        
        # Resolve event
        event.status = 'resolved'
        self.assertEqual(event.status, 'resolved')
        
        # Close event
        event.status = 'closed'
        self.assertEqual(event.status, 'closed')
        
    def test_06_event_timeline(self):
        """Test event timeline and ordering"""
        events = []
        base_time = datetime.now()
        
        # Create events at different times
        for i in range(5):
            event = self.env['flight.event'].create({
                'flight_id': self.flight.id,
                'event_type_id': self.event_type_delay.id,
                'event_date': base_time + timedelta(minutes=i*10),
                'description': f'Event {i}',
                'sequence': i,
            })
            events.append(event)
        
        # Check ordering
        sorted_events = self.flight.event_ids.sorted('event_date')
        for i, event in enumerate(sorted_events):
            self.assertEqual(event.description, f'Event {i}')
            
    def test_07_event_attachments(self):
        """Test event documentation and attachments"""
        event = self.env['flight.event'].create({
            'flight_id': self.flight.id,
            'event_type_id': self.event_type_maintenance.id,
            'event_date': datetime.now(),
            'description': 'Routine maintenance check',
        })
        
        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': 'maintenance_report.pdf',
            'type': 'binary',
            'datas': 'test_data',
            'res_model': 'flight.event',
            'res_id': event.id,
        })
        
        self.assertTrue(attachment.id)
        self.assertEqual(attachment.res_id, event.id)
        
        # Check attachment is linked to event
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'flight.event'),
            ('res_id', '=', event.id),
        ])
        
        self.assertIn(attachment, attachments)
        
    def test_08_event_impact_assessment(self):
        """Test event impact on flight operations"""
        # Create delay event
        delay_event = self.env['flight.event'].create({
            'flight_id': self.flight.id,
            'event_type_id': self.event_type_delay.id,
            'event_date': self.flight.scheduled_departure,
            'description': 'ATC delay',
            'duration_minutes': 90,
            'impact': 'high',
        })
        
        self.assertEqual(delay_event.impact, 'high')
        self.assertEqual(delay_event.duration_minutes, 90)
        
        # Calculate new departure time
        original_departure = self.flight.scheduled_departure
        delayed_departure = original_departure + timedelta(minutes=90)
        
        # Update flight with delay
        self.flight.actual_departure = delayed_departure
        self.assertGreater(self.flight.actual_departure, self.flight.scheduled_departure)
        
    def test_09_recurring_events(self):
        """Test recurring event patterns"""
        # Create recurring maintenance event
        recurring_event = self.env['flight.event.recurring'].create({
            'event_type_id': self.event_type_maintenance.id,
            'aircraft_id': self.aircraft.id,
            'recurrence_type': 'hours',
            'recurrence_value': 100,
            'last_occurrence': datetime.now(),
            'next_due': datetime.now() + timedelta(hours=100),
            'active': True,
        })
        
        self.assertTrue(recurring_event.id)
        self.assertEqual(recurring_event.recurrence_type, 'hours')
        self.assertEqual(recurring_event.recurrence_value, 100)
        
    def test_10_event_notifications(self):
        """Test event notification triggers"""
        # Create high severity event
        critical_event = self.env['flight.event'].create({
            'flight_id': self.flight.id,
            'event_type_id': self.event_type_emergency.id,
            'event_date': datetime.now(),
            'description': 'Engine failure',
            'status': 'active',
            'notify_required': True,
        })
        
        self.assertTrue(critical_event.notify_required)
        
        # Check notification recipients based on severity
        if critical_event.event_type_id.severity in ['high', 'critical']:
            self.assertTrue(critical_event.notify_required)
        
    def test_11_event_statistics(self):
        """Test event statistics and reporting"""
        # Create multiple events
        for i in range(10):
            event_type = self.event_type_delay if i % 2 == 0 else self.event_type_maintenance
            self.env['flight.event'].create({
                'flight_id': self.flight.id,
                'event_type_id': event_type.id,
                'event_date': datetime.now() - timedelta(days=i),
                'description': f'Event {i}',
            })
        
        # Count events by type
        delay_events = self.env['flight.event'].search_count([
            ('flight_id', '=', self.flight.id),
            ('event_type_id', '=', self.event_type_delay.id),
        ])
        
        maintenance_events = self.env['flight.event'].search_count([
            ('flight_id', '=', self.flight.id),
            ('event_type_id', '=', self.event_type_maintenance.id),
        ])
        
        self.assertEqual(delay_events, 5)
        self.assertEqual(maintenance_events, 5)
        
    def test_12_event_resolution_tracking(self):
        """Test event resolution and closure tracking"""
        event = self.env['flight.event'].create({
            'flight_id': self.flight.id,
            'event_type_id': self.event_type_emergency.id,
            'event_date': datetime.now(),
            'description': 'Passenger medical emergency',
            'status': 'active',
        })
        
        # Add resolution details
        event.write({
            'status': 'resolved',
            'resolution_date': datetime.now() + timedelta(hours=1),
            'resolution_notes': 'Passenger treated by medical team at gate',
            'resolved_by': self.env.user.id,
        })
        
        self.assertEqual(event.status, 'resolved')
        self.assertTrue(event.resolution_date)
        self.assertTrue(event.resolution_notes)
        self.assertEqual(event.resolved_by, self.env.user)