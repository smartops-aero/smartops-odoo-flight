from datetime import datetime

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "flight_data_sync")
class TestDataSync(TransactionCase):
    """Test cases for flight data synchronization"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create base data
        cls.company = cls.env.company

        # Create data provider
        cls.provider = cls.env["flight.data.provider"].create(
            {
                "name": "Test Provider",
                "service": "dummy",  # Use available service type
                "active": True,
                "company_id": cls.company.id,
            }
        )

    def test_01_provider_creation(self):
        """Test data provider creation and validation"""
        provider = self.env["flight.data.provider"].create(
            {
                "name": "Test Provider 2",
                "service": "dummy",
                "active": True,
                "company_id": self.company.id,
            }
        )

        self.assertTrue(provider.id)
        self.assertEqual(provider.name, "Test Provider 2")
        self.assertEqual(provider.service, "dummy")
        self.assertTrue(provider.active)

    def test_02_sync_schedule_creation(self):
        """Test sync schedule creation"""
        schedule = self.env["flight.data.sync.schedule"].create(
            {
                "name": "Test Schedule",
                "provider_id": self.provider.id,
                "model": "flight.flight",  # Required field
                "active": True,
                "interval_number": 1,
                "interval_type": "hours",
            }
        )

        self.assertTrue(schedule.id)
        self.assertEqual(schedule.provider_id, self.provider)
        self.assertTrue(schedule.active)

    def test_03_sync_log_creation(self):
        """Test sync log creation and tracking"""
        # First create a schedule since it's required
        schedule = self.env["flight.data.sync.schedule"].create(
            {
                "name": "Log Test Schedule",
                "provider_id": self.provider.id,
                "model": "flight.flight",
                "active": True,
            }
        )

        sync_log = self.env["flight.data.sync.log"].create(
            {
                "schedule_id": schedule.id,
                "direction": "inbound",
                "timestamp": datetime.now(),
            }
        )

        self.assertTrue(sync_log.id)
        self.assertEqual(sync_log.schedule_id, schedule)
        self.assertEqual(sync_log.direction, "inbound")
        self.assertTrue(sync_log.timestamp)

    def test_04_data_registry(self):
        """Test data registry functionality"""
        registry = self.env["flight.data.registry"].create(
            {
                "provider_id": self.provider.id,
                "model": "flight.flight",
                "local_id": 123,
                "external_id": "EXT123",
                "external_provider_id": "PROV456",
            }
        )

        self.assertTrue(registry.id)
        self.assertEqual(registry.external_id, "EXT123")
        self.assertEqual(registry.model, "flight.flight")
        self.assertEqual(registry.provider_id, self.provider)
        self.assertEqual(registry.local_id, 123)

    def test_05_provider_service_selection(self):
        """Test provider service type validation"""
        # Test that provider has service selection method
        self.assertTrue(hasattr(self.provider, "_selection_service"))

        # Get available services
        services = self.provider._selection_service()
        self.assertTrue(isinstance(services, list))

        # Verify dummy service is available (as used in our test)
        service_codes = [service[0] for service in services]
        self.assertIn("dummy", service_codes)

    def test_06_sync_log_body_and_headers(self):
        """Test sync log body and headers functionality"""
        schedule = self.env["flight.data.sync.schedule"].create(
            {
                "name": "Headers Test Schedule",
                "provider_id": self.provider.id,
                "model": "flight.flight",
                "active": True,
            }
        )

        sync_log = self.env["flight.data.sync.log"].create(
            {
                "schedule_id": schedule.id,
                "direction": "outbound",
                "timestamp": datetime.now(),
                "headers": '{"Content-Type": "application/json"}',
                "body": '{"test": "data"}',
            }
        )

        self.assertTrue(sync_log.headers)
        self.assertTrue(sync_log.body)
        self.assertEqual(sync_log.direction, "outbound")

    def test_07_multiple_providers(self):
        """Test managing multiple data providers"""
        provider2 = self.env["flight.data.provider"].create(
            {
                "name": "Second Provider",
                "service": "dummy",
                "active": True,
                "company_id": self.company.id,
            }
        )

        # Verify both providers exist
        providers = self.env["flight.data.provider"].search(
            [("company_id", "=", self.company.id)]
        )

        self.assertGreaterEqual(len(providers), 2)
        self.assertIn(self.provider, providers)
        self.assertIn(provider2, providers)

    def test_08_provider_deactivation(self):
        """Test provider deactivation"""
        # Deactivate provider
        self.provider.active = False

        # Verify it's deactivated
        self.assertFalse(self.provider.active)

        # Verify active providers search excludes it
        active_providers = self.env["flight.data.provider"].search(
            [("active", "=", True), ("company_id", "=", self.company.id)]
        )

        self.assertNotIn(self.provider, active_providers)
