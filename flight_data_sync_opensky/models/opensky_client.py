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

    Supports both Basic Authentication (legacy) and OAuth2 Client Credentials.

    Attributes:
        base_url: Base URL for the OpenSky API
        auth_type: 'basic' or 'oauth2'
        username: Username or Client ID
        password: Password or Client Secret
        access_token: OAuth2 access token (auto-managed)
    """

    def __init__(
        self, base_url=None, username=None, password=None, auth_type="basic"
    ):
        """Initialize the OpenSky client.

        Args:
            base_url: Base URL for the API (defaults to official endpoint)
            username: Username (basic auth) or Client ID (OAuth2)
            password: Password (basic auth) or Client Secret (OAuth2)
            auth_type: 'basic' for username/password, 'oauth2' for client credentials
        """
        self.base_url = base_url or "https://opensky-network.org/api"
        self.auth_url = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
        self.username = username
        self.password = password
        self.auth_type = auth_type
        self.access_token = None
        self.token_expiry = None
        self.session = requests.Session()

        if self.auth_type == "basic" and self.username and self.password:
            # Basic HTTP Authentication (legacy)
            self.session.auth = (self.username, self.password)
        elif self.auth_type == "oauth2" and self.username and self.password:
            # OAuth2 - token will be obtained on first request
            pass

    def _get_oauth2_token(self):
        """Obtain OAuth2 access token using client credentials flow.

        Returns:
            Access token string

        Raises:
            OpenSkyAPIError: If token request fails
        """
        from datetime import datetime, timedelta

        # Check if we have a valid cached token
        if self.access_token and self.token_expiry:
            if datetime.now() < self.token_expiry:
                return self.access_token

        # Request new token
        _logger.info(
            f"Obtaining OAuth2 access token for client {self.username}"
        )

        try:
            response = requests.post(
                self.auth_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.username,
                    "client_secret": self.password,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10,
            )
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data["access_token"]

            # Token expires in 30 minutes, refresh 5 minutes early
            expires_in = token_data.get("expires_in", 1800)
            self.token_expiry = datetime.now() + timedelta(
                seconds=expires_in - 300
            )

            _logger.info(
                f"✓ OAuth2 token obtained, expires in {expires_in} seconds"
            )
            return self.access_token

        except Exception as e:
            error_msg = f"Failed to obtain OAuth2 token: {str(e)}"
            _logger.error(error_msg)
            raise OpenSkyAPIError(error_msg) from e

    def _make_request(self, endpoint, params=None):
        """Make a request to the OpenSky API.

        Automatically handles OAuth2 token management if configured.

        Args:
            endpoint: API endpoint to call
            params: Query parameters

        Returns:
            Response JSON data

        Raises:
            OpenSkyAPIError: If the request fails
        """
        url = f"{self.base_url}/{endpoint}"

        # Prepare headers
        headers = {}
        if self.auth_type == "oauth2":
            token = self._get_oauth2_token()
            headers["Authorization"] = f"Bearer {token}"

        try:
            response = self.session.get(
                url, params=params, headers=headers, timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                # 404 can mean no data available for the requested parameters
                _logger.info(
                    f"No data found for {endpoint} with params {params}: {str(e)}"
                )
                return None
            elif e.response.status_code == 401:
                error_msg = f"Unauthorized - check your credentials (auth_type={self.auth_type})"
                _logger.error(error_msg)
                raise OpenSkyAPIError(error_msg) from e
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

    def lookup_aircraft_by_registration(self, registration):
        """Look up aircraft ICAO24 by registration number.

        **WARNING**: This uses an UNDOCUMENTED endpoint that may not be reliable.
        The OpenSky Network official API does not provide a registration→ICAO24
        lookup endpoint. This method attempts to use an unofficial endpoint but
        it may be unavailable or removed at any time.

        **Recommendation**: Manually set ICAO24 addresses for reliable operation.

        Args:
            registration: Aircraft registration/tail number (e.g., "N12345", "F-GFKY")

        Returns:
            Dictionary with aircraft data including icao24, or None if not found
            Example: {
                'icao24': 'abc123',
                'registration': 'N12345',
                'manufacturericao': 'BOEING',
                'model': '737-800',
                ...
            }
            Returns None if lookup fails or aircraft not found.

        Note:
            This method never raises exceptions. All errors are logged and
            None is returned to allow graceful fallback to manual entry.
        """
        # Clean registration (remove spaces, convert to uppercase)
        registration = registration.strip().upper()

        _logger.info(
            f"[EXPERIMENTAL] Attempting ICAO24 lookup for registration {registration} "
            f"using undocumented endpoint"
        )

        # Try the undocumented metadata endpoint
        # WARNING: This is NOT part of the official OpenSky REST API
        # It may be removed or changed without notice
        try:
            url = f"{self.base_url}/metadata/aircraft/registration/{registration}"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, dict) and data.get("icao24"):
                    _logger.info(
                        f"✓ Found ICAO24 {data.get('icao24')} for registration {registration}"
                    )
                    return data
                else:
                    _logger.warning(
                        f"⚠ Endpoint returned 200 but no valid ICAO24 for {registration}"
                    )
                    return None
            elif response.status_code == 404:
                _logger.info(
                    f"⚠ No aircraft found for registration {registration} (404)"
                )
                return None
            elif response.status_code == 503:
                _logger.warning(
                    f"⚠ OpenSky metadata service unavailable (503) for {registration}"
                )
                return None
            else:
                _logger.warning(
                    f"⚠ Unexpected response {response.status_code} for {registration}"
                )
                return None

        except requests.exceptions.Timeout:
            _logger.warning(
                f"⚠ Timeout while looking up registration {registration}"
            )
            return None
        except requests.exceptions.RequestException as e:
            _logger.warning(
                f"⚠ Network error during lookup for {registration}: {str(e)}"
            )
            return None
        except Exception as e:
            _logger.error(
                f"✗ Unexpected error during ICAO24 lookup for {registration}: {str(e)}",
                exc_info=True,
            )
            return None
