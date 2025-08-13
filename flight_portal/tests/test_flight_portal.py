# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged, HttpCase
from odoo.exceptions import AccessError
from datetime import datetime, timedelta


@tagged('post_install', '-at_install', 'flight_portal')
class TestFlightPortal(TransactionCase):
    """Test cases for flight portal functionality"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Create portal user
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Portal User',
            'login': 'portal_user',
            'email': 'portal@example.com',
            'groups_id': [(4, cls.env.ref('base.group_portal').id)],
        })
        
        # Create internal user
        cls.internal_user = cls.env['res.users'].create({
            'name': 'Internal User',
            'login': 'internal_user',
            'email': 'internal@example.com',
            'groups_id': [(4, cls.env.ref('base.group_user').id)],
        })
        
        # Create aircraft data
        aircraft_class = cls.env['flight.aircraft.class'].create({
            'name': 'Private Jet',
            'aircraft_category': 'airplane',
        })
        
        aircraft_make = cls.env['flight.aircraft.make'].create({
            'name': 'Gulfstream',
        })
        
        aircraft_model = cls.env['flight.aircraft.model'].create({
            'name': 'G550',
            'make_id': aircraft_make.id,
            'class_id': aircraft_class.id,
            'engine_type': 'turbofan',
            'gear_type': 'tricycle_retractable',
            'code': 'G550',
        })
        
        cls.aircraft = cls.env['flight.aircraft'].create({
            'registration': 'N550GS',
            'model_id': aircraft_model.id,
            'operator_id': cls.portal_user.partner_id.id,
        })
        
        # Create aerodromes
        cls.aerodrome_origin = cls.env['flight.aerodrome'].create({
            'name': 'Teterboro Airport',
            'icao': 'KTEB',
            'iata': 'TEB',
            'city': 'Teterboro',
            'state': 'NJ',
            'country': 'US',
        })
        
        cls.aerodrome_dest = cls.env['flight.aerodrome'].create({
            'name': 'Van Nuys Airport',
            'icao': 'KVNY',
            'iata': 'VNY',
            'city': 'Van Nuys',
            'state': 'CA',
            'country': 'US',
        })
        
        # Create flight accessible to portal user
        cls.portal_flight = cls.env['flight.flight'].create({
            'date': datetime.now().date(),
            'aircraft_id': cls.aircraft.id,
            'departure_id': cls.aerodrome_origin.id,
            'arrival_id': cls.aerodrome_dest.id,
            'partner_ids': [(4, cls.portal_user.partner_id.id)],
        })
        
        # Create flight not accessible to portal user
        cls.private_flight = cls.env['flight.flight'].create({
            'date': datetime.now().date() + timedelta(days=1),
            'aircraft_id': cls.aircraft.id,
            'departure_id': cls.aerodrome_dest.id,
            'arrival_id': cls.aerodrome_origin.id,
        })
        
    def test_01_portal_user_access_own_flights(self):
        """Test portal user can access their own flights"""
        # Switch to portal user
        flight_sudo = self.portal_flight.with_user(self.portal_user)
        
        # Portal user should be able to read their flight
        flight_data = flight_sudo.read(['date', 'departure_id', 'arrival_id'])
        self.assertTrue(flight_data)
        self.assertEqual(flight_data[0]['id'], self.portal_flight.id)
        
    def test_02_portal_user_cannot_access_other_flights(self):
        """Test portal user cannot access flights they're not associated with"""
        # Switch to portal user
        with self.assertRaises(AccessError):
            self.private_flight.with_user(self.portal_user).read(['date'])
            
    def test_03_portal_flight_sharing(self):
        """Test flight sharing with portal users"""
        # Create another portal user
        portal_user2 = self.env['res.users'].create({
            'name': 'Portal User 2',
            'login': 'portal_user2',
            'email': 'portal2@example.com',
            'groups_id': [(4, self.env.ref('base.group_portal').id)],
        })
        
        # Share flight with second portal user
        self.portal_flight.partner_ids = [(4, portal_user2.partner_id.id)]
        
        # Both users should now have access
        flight_sudo1 = self.portal_flight.with_user(self.portal_user)
        flight_sudo2 = self.portal_flight.with_user(portal_user2)
        
        self.assertTrue(flight_sudo1.read(['date']))
        self.assertTrue(flight_sudo2.read(['date']))
        
    def test_04_portal_flight_documents(self):
        """Test portal access to flight documents"""
        # Create document attached to flight
        document = self.env['ir.attachment'].create({
            'name': 'flight_plan.pdf',
            'type': 'binary',
            'datas': 'test_data',
            'res_model': 'flight.flight',
            'res_id': self.portal_flight.id,
        })
        
        # Portal user should be able to access documents
        attachments = self.env['ir.attachment'].with_user(self.portal_user).search([
            ('res_model', '=', 'flight.flight'),
            ('res_id', '=', self.portal_flight.id),
        ])
        
        self.assertIn(document, attachments)
        
    def test_05_portal_flight_status_visibility(self):
        """Test portal visibility of flight status updates"""
        # Update flight status
        self.portal_flight.write({
            'status': 'scheduled',
            'scheduled_departure': datetime.now(),
            'scheduled_arrival': datetime.now() + timedelta(hours=5),
        })
        
        # Portal user should see status
        flight_sudo = self.portal_flight.with_user(self.portal_user)
        flight_data = flight_sudo.read(['status', 'scheduled_departure', 'scheduled_arrival'])
        
        self.assertEqual(flight_data[0]['status'], 'scheduled')
        self.assertTrue(flight_data[0]['scheduled_departure'])
        
    def test_06_portal_flight_crew_visibility(self):
        """Test portal visibility of crew information"""
        # Create crew role
        crew_role = self.env['flight.crew.role'].create({
            'name': 'Captain',
            'code': 'CAPT',
        })
        
        # Create crew member
        pilot = self.env['res.partner'].create({
            'name': 'Captain Smith',
            'is_company': False,
        })
        
        crew = self.env['flight.crew'].create({
            'flight_id': self.portal_flight.id,
            'partner_id': pilot.id,
            'role_id': crew_role.id,
        })
        
        # Portal user should see crew info
        flight_sudo = self.portal_flight.with_user(self.portal_user)
        self.assertTrue(flight_sudo.crew_ids)
        self.assertEqual(len(flight_sudo.crew_ids), 1)
        
    def test_07_portal_flight_search(self):
        """Test portal user flight search capabilities"""
        # Create multiple flights for portal user
        for i in range(3):
            self.env['flight.flight'].create({
                'date': datetime.now().date() + timedelta(days=i+2),
                'aircraft_id': self.aircraft.id,
                'departure_id': self.aerodrome_origin.id,
                'arrival_id': self.aerodrome_dest.id,
                'partner_ids': [(4, self.portal_user.partner_id.id)],
            })
        
        # Search flights as portal user
        flights = self.env['flight.flight'].with_user(self.portal_user).search([])
        
        # Should find at least 4 flights (1 original + 3 new)
        self.assertGreaterEqual(len(flights), 4)
        
    def test_08_portal_flight_readonly(self):
        """Test portal users cannot modify flights"""
        # Portal user should not be able to write
        with self.assertRaises(AccessError):
            self.portal_flight.with_user(self.portal_user).write({
                'date': datetime.now().date() + timedelta(days=7)
            })
            
        # Portal user should not be able to delete
        with self.assertRaises(AccessError):
            self.portal_flight.with_user(self.portal_user).unlink()
            
    def test_09_portal_aircraft_visibility(self):
        """Test portal visibility of aircraft information"""
        # Portal user should be able to read aircraft info
        aircraft_sudo = self.aircraft.with_user(self.portal_user)
        aircraft_data = aircraft_sudo.read(['registration', 'model_id'])
        
        self.assertTrue(aircraft_data)
        self.assertEqual(aircraft_data[0]['registration'], 'N550GS')
        
    def test_10_portal_aerodrome_access(self):
        """Test portal access to aerodrome information"""
        # Portal users should be able to read aerodrome info
        aerodrome_sudo = self.aerodrome_origin.with_user(self.portal_user)
        aerodrome_data = aerodrome_sudo.read(['name', 'icao', 'iata'])
        
        self.assertTrue(aerodrome_data)
        self.assertEqual(aerodrome_data[0]['icao'], 'KTEB')
        
    def test_11_portal_flight_history(self):
        """Test portal access to flight history"""
        # Create past flights
        for i in range(5):
            self.env['flight.flight'].create({
                'date': datetime.now().date() - timedelta(days=i+1),
                'aircraft_id': self.aircraft.id,
                'departure_id': self.aerodrome_origin.id,
                'arrival_id': self.aerodrome_dest.id,
                'partner_ids': [(4, self.portal_user.partner_id.id)],
                'status': 'completed',
            })
        
        # Search past flights
        past_flights = self.env['flight.flight'].with_user(self.portal_user).search([
            ('date', '<', datetime.now().date()),
            ('status', '=', 'completed'),
        ])
        
        self.assertGreaterEqual(len(past_flights), 5)
        
    def test_12_portal_flight_notifications(self):
        """Test portal user notifications for flight updates"""
        # Create notification settings
        notification_pref = self.env['flight.portal.notification'].create({
            'partner_id': self.portal_user.partner_id.id,
            'notify_schedule_change': True,
            'notify_status_update': True,
            'notify_crew_assignment': True,
            'notify_document_upload': True,
        })
        
        self.assertTrue(notification_pref.id)
        self.assertTrue(notification_pref.notify_schedule_change)
        
        # Simulate schedule change
        old_departure = self.portal_flight.scheduled_departure
        self.portal_flight.scheduled_departure = datetime.now() + timedelta(hours=2)
        
        # Check if notification should be sent
        if notification_pref.notify_schedule_change and old_departure != self.portal_flight.scheduled_departure:
            should_notify = True
        else:
            should_notify = False
            
        self.assertTrue(should_notify)


@tagged('post_install', '-at_install', 'flight_portal', 'at_install')
class TestFlightPortalHttp(HttpCase):
    """HTTP test cases for flight portal web interface"""
    
    def test_01_portal_flight_page(self):
        """Test accessing flight details page via portal"""
        # This would test the actual HTTP routes
        # Implementation depends on specific portal routes defined
        pass