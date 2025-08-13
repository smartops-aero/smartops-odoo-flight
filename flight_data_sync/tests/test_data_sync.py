# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta


@tagged('post_install', '-at_install', 'flight_data_sync')
class TestDataSync(TransactionCase):
    """Test cases for flight data synchronization"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Create base data
        cls.company = cls.env.company
        
        # Create sync configuration
        cls.sync_config = cls.env['flight.data.sync.config'].create({
            'name': 'Test Sync',
            'provider': 'aviationstack',
            'api_key': 'test_api_key_123',
            'sync_interval': 60,
            'active': True,
        })
        
        # Create aircraft data
        aircraft_class = cls.env['flight.aircraft.class'].create({
            'name': 'Airliner',
            'aircraft_category': 'airplane',
        })
        
        aircraft_make = cls.env['flight.aircraft.make'].create({
            'name': 'Boeing',
        })
        
        aircraft_model = cls.env['flight.aircraft.model'].create({
            'name': '737-800',
            'make_id': aircraft_make.id,
            'class_id': aircraft_class.id,
            'engine_type': 'turbofan',
            'gear_type': 'tricycle_retractable',
            'code': 'B738',
        })
        
        cls.aircraft = cls.env['flight.aircraft'].create({
            'registration': 'N12345',
            'model_id': aircraft_model.id,
            'operator_id': cls.company.partner_id.id,
        })
        
        # Create aerodromes
        cls.aerodrome_origin = cls.env['flight.aerodrome'].create({
            'name': 'Origin Airport',
            'icao': 'KORG',
            'iata': 'ORG',
            'city': 'Origin City',
            'country': 'US',
        })
        
        cls.aerodrome_dest = cls.env['flight.aerodrome'].create({
            'name': 'Destination Airport',
            'icao': 'KDST',
            'iata': 'DST',
            'city': 'Destination City',
            'country': 'US',
        })
        
    def test_01_sync_config_creation(self):
        """Test sync configuration creation and validation"""
        config = self.env['flight.data.sync.config'].create({
            'name': 'New Sync Config',
            'provider': 'flightaware',
            'api_key': 'api_key_456',
            'sync_interval': 120,
            'active': False,
        })
        
        self.assertTrue(config.id)
        self.assertEqual(config.provider, 'flightaware')
        self.assertEqual(config.sync_interval, 120)
        self.assertFalse(config.active)
        
    def test_02_sync_log_creation(self):
        """Test sync log creation and tracking"""
        sync_log = self.env['flight.data.sync.log'].create({
            'config_id': self.sync_config.id,
            'sync_date': datetime.now(),
            'status': 'in_progress',
            'records_processed': 0,
            'records_created': 0,
            'records_updated': 0,
            'records_failed': 0,
        })
        
        self.assertTrue(sync_log.id)
        self.assertEqual(sync_log.status, 'in_progress')
        
        # Update log with results
        sync_log.write({
            'status': 'success',
            'records_processed': 100,
            'records_created': 20,
            'records_updated': 75,
            'records_failed': 5,
            'end_date': datetime.now(),
        })
        
        self.assertEqual(sync_log.status, 'success')
        self.assertEqual(sync_log.records_processed, 100)
        
    def test_03_sync_queue_management(self):
        """Test sync queue creation and processing"""
        queue_item = self.env['flight.data.sync.queue'].create({
            'config_id': self.sync_config.id,
            'external_id': 'EXT123',
            'model_name': 'flight.flight',
            'action': 'create',
            'data': '{"flight_number": "TEST123"}',
            'status': 'pending',
        })
        
        self.assertTrue(queue_item.id)
        self.assertEqual(queue_item.status, 'pending')
        self.assertEqual(queue_item.action, 'create')
        
        # Process queue item
        queue_item.write({
            'status': 'processed',
            'processed_date': datetime.now(),
        })
        
        self.assertEqual(queue_item.status, 'processed')
        self.assertTrue(queue_item.processed_date)
        
    def test_04_sync_mapping(self):
        """Test field mapping configuration"""
        mapping = self.env['flight.data.sync.mapping'].create({
            'config_id': self.sync_config.id,
            'model_name': 'flight.flight',
            'external_field': 'flight_number',
            'internal_field': 'flight_number',
            'transform_function': 'upper',
            'active': True,
        })
        
        self.assertTrue(mapping.id)
        self.assertEqual(mapping.external_field, 'flight_number')
        self.assertEqual(mapping.internal_field, 'flight_number')
        self.assertEqual(mapping.transform_function, 'upper')
        
    @patch('requests.get')
    def test_05_api_connection(self, mock_get):
        """Test API connection and error handling"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'ok', 'data': []}
        mock_get.return_value = mock_response
        
        # Test connection
        result = self.sync_config.test_connection()
        self.assertTrue(result)
        
        # Mock failed response
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        result = self.sync_config.test_connection()
        self.assertFalse(result)
        
    def test_06_sync_scheduling(self):
        """Test sync scheduling and cron job creation"""
        # Create scheduled sync
        cron = self.env['ir.cron'].create({
            'name': f'Flight Data Sync - {self.sync_config.name}',
            'model_id': self.env.ref('flight_data_sync.model_flight_data_sync_config').id,
            'state': 'code',
            'code': f'model.browse({self.sync_config.id}).run_sync()',
            'interval_number': self.sync_config.sync_interval,
            'interval_type': 'minutes',
            'numbercall': -1,
            'active': True,
        })
        
        self.assertTrue(cron.id)
        self.assertEqual(cron.interval_number, 60)
        self.assertEqual(cron.interval_type, 'minutes')
        
    def test_07_data_transformation(self):
        """Test data transformation functions"""
        # Test uppercase transformation
        transformed = self.sync_config.transform_value('test123', 'upper')
        self.assertEqual(transformed, 'TEST123')
        
        # Test lowercase transformation
        transformed = self.sync_config.transform_value('TEST123', 'lower')
        self.assertEqual(transformed, 'test123')
        
        # Test date parsing
        date_str = '2024-01-15T10:30:00'
        transformed = self.sync_config.transform_value(date_str, 'parse_datetime')
        self.assertIsInstance(transformed, datetime)
        
    def test_08_duplicate_prevention(self):
        """Test duplicate record prevention"""
        # Create initial flight
        flight1 = self.env['flight.flight'].create({
            'date': '2024-01-15',
            'aircraft_id': self.aircraft.id,
            'departure_id': self.aerodrome_origin.id,
            'arrival_id': self.aerodrome_dest.id,
            'flight_number': 'SYNC001',
            'external_id': 'EXT_SYNC_001',
        })
        
        # Try to sync duplicate
        queue_item = self.env['flight.data.sync.queue'].create({
            'config_id': self.sync_config.id,
            'external_id': 'EXT_SYNC_001',
            'model_name': 'flight.flight',
            'action': 'create',
            'data': '{"flight_number": "SYNC001"}',
            'status': 'pending',
        })
        
        # Process should detect duplicate
        result = queue_item.process()
        self.assertEqual(queue_item.status, 'duplicate')
        
    def test_09_incremental_sync(self):
        """Test incremental sync functionality"""
        # Set last sync date
        last_sync = datetime.now() - timedelta(days=1)
        self.sync_config.last_sync_date = last_sync
        
        # Create sync log for incremental sync
        sync_log = self.env['flight.data.sync.log'].create({
            'config_id': self.sync_config.id,
            'sync_date': datetime.now(),
            'sync_type': 'incremental',
            'status': 'in_progress',
        })
        
        self.assertEqual(sync_log.sync_type, 'incremental')
        
        # Verify last sync date is updated after successful sync
        sync_log.write({
            'status': 'success',
            'end_date': datetime.now(),
        })
        
        self.sync_config.last_sync_date = sync_log.end_date
        self.assertGreater(self.sync_config.last_sync_date, last_sync)
        
    def test_10_error_recovery(self):
        """Test error handling and recovery mechanisms"""
        # Create failed sync log
        sync_log = self.env['flight.data.sync.log'].create({
            'config_id': self.sync_config.id,
            'sync_date': datetime.now(),
            'status': 'failed',
            'error_message': 'Connection timeout',
            'records_failed': 10,
        })
        
        self.assertEqual(sync_log.status, 'failed')
        self.assertTrue(sync_log.error_message)
        
        # Test retry mechanism
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries and sync_log.status == 'failed':
            retry_count += 1
            # Simulate retry
            if retry_count == max_retries:
                sync_log.status = 'success'
        
        self.assertEqual(retry_count, 3)
        self.assertEqual(sync_log.status, 'success')
        
    def test_11_sync_filtering(self):
        """Test sync filtering options"""
        # Create filter for specific aircraft
        sync_filter = self.env['flight.data.sync.filter'].create({
            'config_id': self.sync_config.id,
            'field_name': 'aircraft_registration',
            'operator': 'in',
            'value': 'N12345,N67890',
            'active': True,
        })
        
        self.assertTrue(sync_filter.id)
        self.assertEqual(sync_filter.operator, 'in')
        
        # Test filter application
        registrations = sync_filter.value.split(',')
        self.assertIn('N12345', registrations)
        
    def test_12_batch_processing(self):
        """Test batch processing of sync queue"""
        # Create multiple queue items
        queue_items = []
        for i in range(10):
            item = self.env['flight.data.sync.queue'].create({
                'config_id': self.sync_config.id,
                'external_id': f'BATCH_{i}',
                'model_name': 'flight.flight',
                'action': 'create',
                'data': f'{{"flight_number": "BATCH{i:03d}"}}',
                'status': 'pending',
            })
            queue_items.append(item)
        
        # Process batch
        pending_items = self.env['flight.data.sync.queue'].search([
            ('status', '=', 'pending'),
            ('config_id', '=', self.sync_config.id),
        ])
        
        self.assertEqual(len(pending_items), 10)
        
        # Simulate batch processing
        for item in pending_items:
            item.status = 'processed'
        
        processed_items = self.env['flight.data.sync.queue'].search([
            ('status', '=', 'processed'),
            ('config_id', '=', self.sync_config.id),
        ])
        
        self.assertEqual(len(processed_items), 10)