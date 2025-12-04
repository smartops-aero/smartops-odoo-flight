"""OpenSky Network API Client

This module provides a Python client for the OpenSky Network REST API.
The OpenSky Network is a non-profit association that provides free access
to real-time and historical ADS-B flight data.

For API documentation, see: https://openskynetwork.github.io/opensky-api/
"""

import logging
from datetime import datetime, timedelta

import requests

_logger = logging.getLogger(__name__)


class OpenSkyAPIError(Exception):
    """Exception raised for OpenSky API errors."""

    pass


class OpenSkyClient:
    """Client for OpenSky Network API.

    The OpenSky Network provides free access to ADS-B flight data.
    Authenticated users have higher rate limits.

    Attributes:
        base_url: Base URL for the OpenSky API
        username: Optional username for authentication
        password: Optional password for authentication
    """

    def __init__(self, base_url=None, username=None, password=None):
        """Initialize the OpenSky client.

        Args:
            base_url: Base URL for the API (defaults to official endpoint)
            username: Username for authentication (optional, increases rate limits)
            password: Password for authentication (optional)
        """
        self.base_url = base_url or "https://opensky-network.org/api"
        self.username = username
        self.password = password
        self.session = requests.Session()

        if self.username and self.password:
            self.session.auth = (self.username, self.password)

    def _make_request(self, endpoint, params=None):
        """Make a request to the OpenSky API.

        Args:
            endpoint: API endpoint to call
            params: Query parameters

        Returns:
            Response JSON data

        Raises:
            OpenSkyAPIError: If the request fails
        """
        url = f"{self.base_url}/{endpoint}"

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                # 404 can mean no data available for the requested parameters
                _logger.info(
                    f"No data found for {endpoint} with params {params}: {str(e)}"
                )
                return None
            error_msg = f"OpenSky API HTTP error: {str(e)}"
            _logger.error(error_msg)
            raise OpenSkyAPIError(error_msg) from e
        except requests.exceptions.RequestException as e:
            error_msg = f"OpenSky API request failed: {str(e)}"
            _logger.error(error_msg)
            raise OpenSkyAPIError(error_msg) from e
        except ValueError as e:
            error_msg = f"Invalid JSON response from OpenSky API: {str(e)}"
            _logger.error(error_msg)
            raise OpenSkyAPIError(error_msg) from e

    def get_flights_by_aircraft(self, icao24, begin_timestamp, end_timestamp):
        """Get all flights for a specific aircraft in a time interval.

        Args:
            icao24: ICAO 24-bit address (hex string, e.g., "3c6444")
            begin_timestamp: Unix timestamp for interval start
            end_timestamp: Unix timestamp for interval end

        Returns:
            List of flight dictionaries, or empty list if no flights found.
            Each flight contains:
            - icao24: Aircraft ICAO24 address
            - firstSeen: Unix timestamp of first position
            - estDepartureAirport: ICAO code of departure airport
            - lastSeen: Unix timestamp of last position
            - estArrivalAirport: ICAO code of arrival airport
            - callsign: Flight callsign (may be None)
            - estDepartureAirportHorizDistance: Horizontal distance to departure
            - estDepartureAirportVertDistance: Vertical distance to departure
            - estArrivalAirportHorizDistance: Horizontal distance to arrival
            - estArrivalAirportVertDistance: Vertical distance to arrival
            - departureAirportCandidatesCount: Number of departure candidates
            - arrivalAirportCandidatesCount: Number of arrival candidates

        Raises:
            OpenSkyAPIError: If the request fails
        """
        # Ensure icao24 is lowercase as required by the API
        icao24 = icao24.lower()

        params = {
            "icao24": icao24,
            "begin": int(begin_timestamp),
            "end": int(end_timestamp),
        }

        _logger.info(
            f"Fetching flights for aircraft {icao24} from {begin_timestamp} to {end_timestamp}"
        )

        data = self._make_request("flights/aircraft", params=params)

        if data is None:
            _logger.info(f"No flights found for aircraft {icao24} in time range")
            return []

        flights = data if isinstance(data, list) else []
        _logger.info(f"Found {len(flights)} flights for aircraft {icao24}")

        return flights

    def get_flights_by_interval(self, begin_timestamp, end_timestamp):
        """Get all flights in a time interval.

        Note: This endpoint requires authentication and is limited to intervals
        of max 2 hours for regular users.

        Args:
            begin_timestamp: Unix timestamp for interval start
            end_timestamp: Unix timestamp for interval end

        Returns:
            List of flight dictionaries

        Raises:
            OpenSkyAPIError: If the request fails
        """
        params = {
            "begin": int(begin_timestamp),
            "end": int(end_timestamp),
        }

        _logger.info(f"Fetching all flights from {begin_timestamp} to {end_timestamp}")

        data = self._make_request("flights/all", params=params)

        if data is None:
            return []

        flights = data if isinstance(data, list) else []
        _logger.info(f"Found {len(flights)} flights in time range")

        return flights

    def get_flight_track(self, icao24, timestamp):
        """Get track (positions over time) for a specific flight.

        Note: Tracks are only available for up to 30 days in the past.

        Args:
            icao24: ICAO 24-bit address
            timestamp: Unix timestamp (use flight's firstSeen or lastSeen)

        Returns:
            Dictionary with:
            - icao24: Aircraft ICAO24 address
            - startTime: Unix timestamp of track start
            - endTime: Unix timestamp of track end
            - callsign: Flight callsign
            - path: List of [time, lat, lon, altitude] position arrays

        Raises:
            OpenSkyAPIError: If the request fails
        """
        icao24 = icao24.lower()

        params = {
            "icao24": icao24,
            "time": int(timestamp),
        }

        _logger.info(f"Fetching track for aircraft {icao24} at time {timestamp}")

        data = self._make_request("tracks/all", params=params)

        if data is None:
            return None

        return data

    @staticmethod
    def timestamp_from_datetime(dt):
        """Convert a datetime to Unix timestamp.

        Args:
            dt: datetime object

        Returns:
            Unix timestamp (integer)
        """
        return int(dt.timestamp())

    @staticmethod
    def datetime_from_timestamp(timestamp):
        """Convert Unix timestamp to datetime.

        Args:
            timestamp: Unix timestamp

        Returns:
            datetime object in UTC
        """
        return datetime.utcfromtimestamp(timestamp)
