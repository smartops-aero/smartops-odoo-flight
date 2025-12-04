"""Tests for OpenSky Network API Client"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase

from ..models.opensky_client import OpenSkyClient, OpenSkyAPIError


class TestOpenSkyClient(TransactionCase):
    """Test OpenSky API client functionality."""

    def setUp(self):
        super().setUp()
        self.client = OpenSkyClient()

    def test_client_initialization(self):
        """Test client initialization with and without auth."""
        # Test default initialization
        client = OpenSkyClient()
        self.assertEqual(client.base_url, "https://opensky-network.org/api")
        self.assertIsNone(client.username)
        self.assertIsNone(client.password)

        # Test with authentication
        client_auth = OpenSkyClient(
            username="test_user", password="test_pass"
        )
        self.assertEqual(client_auth.username, "test_user")
        self.assertEqual(client_auth.password, "test_pass")
        self.assertEqual(
            client_auth.session.auth, ("test_user", "test_pass")
        )

    @patch("requests.Session.get")
    def test_get_flights_by_aircraft_success(self, mock_get):
        """Test successful flight fetch by aircraft."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "icao24": "abc123",
                "firstSeen": 1640000000,
                "lastSeen": 1640010000,
                "estDepartureAirport": "KJFK",
                "estArrivalAirport": "EGLL",
                "callsign": "AAL100  ",
            }
        ]
        mock_get.return_value = mock_response

        # Test
        flights = self.client.get_flights_by_aircraft(
            "ABC123", 1640000000, 1640020000
        )

        self.assertEqual(len(flights), 1)
        self.assertEqual(flights[0]["icao24"], "abc123")
        self.assertEqual(flights[0]["estDepartureAirport"], "KJFK")

        # Verify icao24 was lowercased in request
        mock_get.assert_called_once()
        call_params = mock_get.call_args[1]["params"]
        self.assertEqual(call_params["icao24"], "abc123")

    @patch("requests.Session.get")
    def test_get_flights_no_data(self, mock_get):
        """Test handling of 404 (no data) response."""
        # Mock 404 response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")

        from requests.exceptions import HTTPError
        http_error = HTTPError()
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_get.return_value = mock_response

        # Test - should return empty list for 404
        flights = self.client.get_flights_by_aircraft(
            "abc123", 1640000000, 1640020000
        )

        self.assertEqual(flights, [])

    @patch("requests.Session.get")
    def test_get_flights_api_error(self, mock_get):
        """Test handling of API errors."""
        # Mock error response
        mock_response = MagicMock()
        mock_response.status_code = 500

        from requests.exceptions import HTTPError
        http_error = HTTPError("500 Server Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_get.return_value = mock_response

        # Test - should raise OpenSkyAPIError
        with self.assertRaises(OpenSkyAPIError):
            self.client.get_flights_by_aircraft(
                "abc123", 1640000000, 1640020000
            )

    def test_timestamp_conversion(self):
        """Test datetime/timestamp conversion methods."""
        # Test datetime to timestamp
        dt = datetime(2021, 12, 20, 12, 0, 0)
        timestamp = OpenSkyClient.timestamp_from_datetime(dt)
        self.assertIsInstance(timestamp, int)

        # Test timestamp to datetime
        converted_dt = OpenSkyClient.datetime_from_timestamp(timestamp)
        # Allow for some precision loss in conversion
        self.assertEqual(converted_dt.date(), dt.date())
        self.assertEqual(converted_dt.hour, dt.hour)
        self.assertEqual(converted_dt.minute, dt.minute)
