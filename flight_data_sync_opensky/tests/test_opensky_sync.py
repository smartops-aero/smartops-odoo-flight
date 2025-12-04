"""Tests for OpenSky Network Sync Wizard"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestOpenSkySync(TransactionCase):
    """Test OpenSky sync wizard functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create test data
        cls.provider = cls.env["flight.data.provider"].create(
            {
                "name": "Test OpenSky Provider",
                "service": "opensky",
                "username": "test_user",
                "password": "test_pass",
            }
        )

        cls.aerodrome_kjfk = cls.env["flight.aerodrome"].create(
            {
                "name": "John F. Kennedy International Airport",
                "icao": "KJFK",
                "iata": "JFK",
            }
        )

        cls.aerodrome_egll = cls.env["flight.aerodrome"].create(
            {
                "name": "London Heathrow Airport",
                "icao": "EGLL",
                "iata": "LHR",
            }
        )

        cls.aircraft = cls.env["flight.aircraft"].create(
            {
                "registration": "N12345",
                "icao24": "ABC123",
            }
        )

    def test_wizard_creation(self):
        """Test wizard creation and default values."""
        wizard = self.env["opensky.sync.wizard"].create(
            {
                "provider_id": self.provider.id,
                "sync_mode": "aircraft_range",
            }
        )

        self.assertEqual(wizard.state, "select")
        self.assertEqual(wizard.sync_mode, "aircraft_range")
        self.assertEqual(wizard.provider_id, self.provider)

    def test_date_range_validation(self):
        """Test date range validation."""
        wizard = self.env["opensky.sync.wizard"].create(
            {
                "provider_id": self.provider.id,
                "sync_mode": "aircraft_range",
                "aircraft_id": self.aircraft.id,
                "date_from": datetime.today().date(),
                "date_to": datetime.today().date() - timedelta(days=1),
            }
        )

        # Should raise error for invalid date range
        with self.assertRaises(ValidationError):
            wizard._check_date_range()

    def test_date_range_too_long(self):
        """Test that date range > 30 days raises error."""
        wizard = self.env["opensky.sync.wizard"].create(
            {
                "provider_id": self.provider.id,
                "sync_mode": "aircraft_range",
                "aircraft_id": self.aircraft.id,
                "date_from": datetime.today().date(),
                "date_to": datetime.today().date() + timedelta(days=31),
            }
        )

        # Should raise error for range > 30 days
        with self.assertRaises(ValidationError):
            wizard._check_date_range()

    @patch("odoo.addons.flight_data_sync_opensky.models.opensky_client.OpenSkyClient.get_flights_by_aircraft")
    def test_fetch_flights_by_aircraft_range(self, mock_get_flights):
        """Test fetching flights by aircraft and date range."""
        # Mock OpenSky API response
        mock_get_flights.return_value = [
            {
                "icao24": "abc123",
                "firstSeen": int(datetime.now().timestamp()),
                "lastSeen": int((datetime.now() + timedelta(hours=6)).timestamp()),
                "estDepartureAirport": "KJFK",
                "estArrivalAirport": "EGLL",
                "callsign": "TEST123",
            }
        ]

        wizard = self.env["opensky.sync.wizard"].create(
            {
                "provider_id": self.provider.id,
                "sync_mode": "aircraft_range",
                "aircraft_id": self.aircraft.id,
                "date_from": datetime.today().date(),
                "date_to": datetime.today().date(),
            }
        )

        wizard.action_fetch_flights()

        # Check wizard state changed
        self.assertEqual(wizard.state, "compare")

        # Check comparison lines created
        self.assertEqual(len(wizard.comparison_line_ids), 1)
        line = wizard.comparison_line_ids[0]
        self.assertEqual(line.aircraft_id, self.aircraft)
        self.assertEqual(line.departure_id, self.aerodrome_kjfk)
        self.assertEqual(line.arrival_id, self.aerodrome_egll)
        self.assertEqual(line.status, "new")
        self.assertEqual(line.action, "create")

    def test_fetch_without_aircraft_raises_error(self):
        """Test that fetching without aircraft raises error."""
        wizard = self.env["opensky.sync.wizard"].create(
            {
                "provider_id": self.provider.id,
                "sync_mode": "aircraft_range",
                "date_from": datetime.today().date(),
                "date_to": datetime.today().date(),
            }
        )

        with self.assertRaises(UserError):
            wizard.action_fetch_flights()

    def test_fetch_aircraft_without_icao24_raises_error(self):
        """Test that aircraft without ICAO24 raises error."""
        aircraft_no_icao = self.env["flight.aircraft"].create(
            {
                "registration": "N99999",
            }
        )

        wizard = self.env["opensky.sync.wizard"].create(
            {
                "provider_id": self.provider.id,
                "sync_mode": "aircraft_range",
                "aircraft_id": aircraft_no_icao.id,
                "date_from": datetime.today().date(),
                "date_to": datetime.today().date(),
            }
        )

        with self.assertRaises(UserError):
            wizard.action_fetch_flights()

    @patch("odoo.addons.flight_data_sync_opensky.models.opensky_client.OpenSkyClient.get_flights_by_aircraft")
    def test_apply_sync_creates_flights(self, mock_get_flights):
        """Test that applying sync creates flights."""
        # Mock OpenSky API response
        mock_get_flights.return_value = [
            {
                "icao24": "abc123",
                "firstSeen": int(datetime.now().timestamp()),
                "lastSeen": int((datetime.now() + timedelta(hours=6)).timestamp()),
                "estDepartureAirport": "KJFK",
                "estArrivalAirport": "EGLL",
                "callsign": "TEST123",
            }
        ]

        wizard = self.env["opensky.sync.wizard"].create(
            {
                "provider_id": self.provider.id,
                "sync_mode": "aircraft_range",
                "aircraft_id": self.aircraft.id,
                "date_from": datetime.today().date(),
                "date_to": datetime.today().date(),
            }
        )

        wizard.action_fetch_flights()

        # Verify no flights exist yet
        flights_before = self.env["flight.flight"].search_count(
            [("aircraft_id", "=", self.aircraft.id)]
        )

        # Apply sync
        wizard.action_apply_sync()

        # Verify flight was created
        flights_after = self.env["flight.flight"].search_count(
            [("aircraft_id", "=", self.aircraft.id)]
        )
        self.assertEqual(flights_after, flights_before + 1)

        # Verify flight details
        flight = self.env["flight.flight"].search(
            [("aircraft_id", "=", self.aircraft.id)], limit=1
        )
        self.assertEqual(flight.departure_id, self.aerodrome_kjfk)
        self.assertEqual(flight.arrival_id, self.aerodrome_egll)

    @patch("odoo.addons.flight_data_sync_opensky.models.opensky_client.OpenSkyClient.get_flights_by_aircraft")
    def test_apply_sync_skips_flights(self, mock_get_flights):
        """Test that applying sync with skip action doesn't create flights."""
        # Mock OpenSky API response
        mock_get_flights.return_value = [
            {
                "icao24": "abc123",
                "firstSeen": int(datetime.now().timestamp()),
                "lastSeen": int((datetime.now() + timedelta(hours=6)).timestamp()),
                "estDepartureAirport": "KJFK",
                "estArrivalAirport": "EGLL",
                "callsign": "TEST123",
            }
        ]

        wizard = self.env["opensky.sync.wizard"].create(
            {
                "provider_id": self.provider.id,
                "sync_mode": "aircraft_range",
                "aircraft_id": self.aircraft.id,
                "date_from": datetime.today().date(),
                "date_to": datetime.today().date(),
            }
        )

        wizard.action_fetch_flights()

        # Change action to skip
        wizard.comparison_line_ids.write({"action": "skip"})

        flights_before = self.env["flight.flight"].search_count(
            [("aircraft_id", "=", self.aircraft.id)]
        )

        # Apply sync
        wizard.action_apply_sync()

        # Verify no flights were created
        flights_after = self.env["flight.flight"].search_count(
            [("aircraft_id", "=", self.aircraft.id)]
        )
        self.assertEqual(flights_after, flights_before)

    def test_comparison_line_display_name(self):
        """Test comparison line display name computation."""
        line = self.env["opensky.sync.wizard.line"].create(
            {
                "wizard_id": self.env["opensky.sync.wizard"]
                .create(
                    {
                        "provider_id": self.provider.id,
                    }
                )
                .id,
                "aircraft_id": self.aircraft.id,
                "date": datetime.today().date(),
                "departure_id": self.aerodrome_kjfk.id,
                "arrival_id": self.aerodrome_egll.id,
                "status": "new",
                "action": "create",
            }
        )

        self.assertIn("N12345", line.display_name)
        self.assertIn("KJFK", line.display_name)
        self.assertIn("EGLL", line.display_name)

    def test_flight_duration_computation(self):
        """Test flight duration computation."""
        first_seen = datetime.now()
        last_seen = first_seen + timedelta(hours=6, minutes=30)

        line = self.env["opensky.sync.wizard.line"].create(
            {
                "wizard_id": self.env["opensky.sync.wizard"]
                .create(
                    {
                        "provider_id": self.provider.id,
                    }
                )
                .id,
                "aircraft_id": self.aircraft.id,
                "date": datetime.today().date(),
                "departure_id": self.aerodrome_kjfk.id,
                "arrival_id": self.aerodrome_egll.id,
                "opensky_first_seen": first_seen,
                "opensky_last_seen": last_seen,
                "status": "new",
                "action": "create",
            }
        )

        # Duration should be 6.5 hours
        self.assertAlmostEqual(line.flight_duration, 6.5, places=2)
