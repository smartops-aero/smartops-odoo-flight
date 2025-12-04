"""Flight Data Provider for OpenSky Network

Extends the base flight data provider to add OpenSky Network support.
"""

import logging
from datetime import datetime

from odoo import api, models

from .opensky_client import OpenSkyClient

_logger = logging.getLogger(__name__)


class FlightDataProvider(models.Model):
    _inherit = "flight.data.provider"

    @api.model
    def _get_available_services(self):
        """Add OpenSky Network to available services."""
        services = super()._get_available_services()
        services.append(("opensky", "OpenSky Network"))
        return services

    def get_client(self, schedule):
        """Get OpenSky client instance.

        Args:
            schedule: The sync schedule record

        Returns:
            OpenSkyClient instance
        """
        if self.service == "opensky":
            return OpenSkyClient(
                base_url=self.api_base or None,
                username=self.username or None,
                password=self.password or None,
                auth_type=self.auth_type or "basic",
            )
        return super().get_client(schedule)

    def _receive_flight_data(self, client, schedule, *args, **kwargs):
        """Receive flight data from OpenSky Network.

        This method is called by the base sync mechanism but is not used
        for the interactive wizard workflow. The wizard calls
        fetch_opensky_flights directly.

        Args:
            client: OpenSkyClient instance
            schedule: The sync schedule
            **kwargs: Additional parameters from schedule.kwargs

        Returns:
            List of flight data dictionaries
        """
        if self.service != "opensky":
            return super()._receive_flight_data(client, schedule, *args, **kwargs)

        # Get parameters from kwargs
        icao24 = kwargs.get("icao24")
        begin_timestamp = kwargs.get("begin_timestamp")
        end_timestamp = kwargs.get("end_timestamp")

        if not icao24 or not begin_timestamp or not end_timestamp:
            raise ValueError(
                "Missing required parameters: icao24, begin_timestamp, end_timestamp"
            )

        return client.get_flights_by_aircraft(icao24, begin_timestamp, end_timestamp)

    def _process_flight_data(self, client, schedule, data, *args, **kwargs):
        """Process flight data from OpenSky Network.

        This converts OpenSky flight data into Odoo flight records.

        Args:
            client: OpenSkyClient instance
            schedule: The sync schedule
            data: List of flight dictionaries from OpenSky API

        Returns:
            Number of flights processed
        """
        if self.service != "opensky":
            return super()._process_flight_data(client, schedule, data, *args, **kwargs)

        if not data:
            _logger.info("No flight data to process")
            return 0

        Flight = self.env["flight.flight"]
        Aerodrome = self.env["flight.aerodrome"]
        Aircraft = self.env["flight.aircraft"]

        processed = 0

        for flight_data in data:
            try:
                # Skip flights without departure or arrival airports
                if not flight_data.get("estDepartureAirport") or not flight_data.get(
                    "estArrivalAirport"
                ):
                    _logger.debug(
                        f"Skipping flight {flight_data.get('icao24')} - missing airport data"
                    )
                    continue

                # Find or skip aircraft
                icao24 = flight_data["icao24"].upper()
                aircraft = Aircraft.search([("icao24", "=", icao24)], limit=1)

                if not aircraft:
                    _logger.warning(
                        f"Aircraft with ICAO24 {icao24} not found, skipping flight"
                    )
                    continue

                # Find or create aerodromes
                departure_icao = flight_data["estDepartureAirport"].upper()
                arrival_icao = flight_data["estArrivalAirport"].upper()

                departure = Aerodrome.search([("icao", "=", departure_icao)], limit=1)
                arrival = Aerodrome.search([("icao", "=", arrival_icao)], limit=1)

                if not departure:
                    _logger.warning(
                        f"Departure aerodrome {departure_icao} not found, skipping flight"
                    )
                    continue

                if not arrival:
                    _logger.warning(
                        f"Arrival aerodrome {arrival_icao} not found, skipping flight"
                    )
                    continue

                # Convert timestamp to date
                flight_date = datetime.utcfromtimestamp(
                    flight_data["firstSeen"]
                ).date()

                # Check if flight already exists
                existing = Flight.search(
                    [
                        ("aircraft_id", "=", aircraft.id),
                        ("date", "=", flight_date),
                        ("departure_id", "=", departure.id),
                        ("arrival_id", "=", arrival.id),
                    ],
                    limit=1,
                )

                if existing:
                    _logger.debug(
                        f"Flight {aircraft.registration} {departure_icao}-{arrival_icao} "
                        f"on {flight_date} already exists"
                    )
                    continue

                # Create flight
                Flight.create(
                    {
                        "date": flight_date,
                        "aircraft_id": aircraft.id,
                        "departure_id": departure.id,
                        "arrival_id": arrival.id,
                    }
                )

                processed += 1
                _logger.info(
                    f"Created flight {aircraft.registration} {departure_icao}-{arrival_icao} on {flight_date}"
                )

            except Exception as e:
                _logger.error(f"Error processing flight data: {str(e)}", exc_info=True)
                continue

        _logger.info(f"Processed {processed} flights from OpenSky data")
        return processed

    def _prepare_flight_data(self, client, schedule, *args, **kwargs):
        """OpenSky Network is read-only, no data to prepare for sending."""
        if self.service != "opensky":
            return super()._prepare_flight_data(client, schedule, *args, **kwargs)
        return []

    def _send_flight_data(self, client, schedule, data, *args, **kwargs):
        """OpenSky Network is read-only, no data to send."""
        if self.service != "opensky":
            return super()._send_flight_data(client, schedule, data, *args, **kwargs)
        return None
