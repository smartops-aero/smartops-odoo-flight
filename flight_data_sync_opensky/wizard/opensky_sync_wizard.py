"""OpenSky Network Synchronization Wizard

Interactive wizard for comparing and syncing flights from OpenSky Network.
"""

import logging
from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..models.opensky_client import OpenSkyClient

_logger = logging.getLogger(__name__)


class OpenskySyncWizard(models.TransientModel):
    _name = "opensky.sync.wizard"
    _description = "OpenSky Network Sync Wizard"

    # Step 1: Selection mode
    sync_mode = fields.Selection(
        [
            ("flights", "Sync Specific Flights"),
            ("aircraft_range", "Sync Aircraft by Date Range"),
        ],
        string="Sync Mode",
        required=True,
        default="aircraft_range",
    )

    # Provider selection
    provider_id = fields.Many2one(
        "flight.data.provider",
        string="OpenSky Provider",
        required=True,
        domain=[("service", "=", "opensky")],
    )

    # Flight selection mode
    flight_ids = fields.Many2many(
        "flight.flight",
        string="Flights to Sync",
        help="Select existing flights to check against OpenSky data",
    )

    # Aircraft range mode
    aircraft_id = fields.Many2one("flight.aircraft", string="Aircraft")
    date_from = fields.Date(string="Date From", default=fields.Date.context_today)
    date_to = fields.Date(string="Date To", default=fields.Date.context_today)

    # Step 2: Comparison results
    state = fields.Selection(
        [("select", "Select Mode"), ("compare", "Compare Results")],
        default="select",
        required=True,
    )

    comparison_line_ids = fields.One2many(
        "opensky.sync.wizard.line",
        "wizard_id",
        string="Flight Comparisons",
    )

    # Summary
    total_opensky_flights = fields.Integer(
        compute="_compute_summary", string="Total OpenSky Flights"
    )
    new_flights = fields.Integer(compute="_compute_summary", string="New Flights")
    existing_flights = fields.Integer(
        compute="_compute_summary", string="Existing Flights"
    )

    @api.depends("comparison_line_ids")
    def _compute_summary(self):
        for wizard in self:
            wizard.total_opensky_flights = len(wizard.comparison_line_ids)
            wizard.new_flights = len(
                wizard.comparison_line_ids.filtered(lambda l: l.status == "new")
            )
            wizard.existing_flights = len(
                wizard.comparison_line_ids.filtered(lambda l: l.status == "existing")
            )

    @api.constrains("date_from", "date_to")
    def _check_date_range(self):
        for wizard in self:
            if wizard.date_from and wizard.date_to:
                if wizard.date_from > wizard.date_to:
                    raise ValidationError(_("Date From must be before Date To"))

                # OpenSky API limitation: max 2 days for /flights/aircraft endpoint
                delta = (wizard.date_to - wizard.date_from).days
                if delta > 2:
                    raise ValidationError(
                        _(
                            "Date range cannot exceed 2 days due to OpenSky API limitations.\n\n"
                            "The /flights/aircraft endpoint only supports queries up to 2 days.\n"
                            "Please select a smaller range or split your sync into multiple 2-day periods."
                        )
                    )

    def action_fetch_flights(self):
        """Fetch flights from OpenSky and compare with existing flights."""
        self.ensure_one()

        if not self.provider_id:
            raise UserError(_("Please select an OpenSky provider"))

        # Get OpenSky client
        client = OpenSkyClient(
            base_url=self.provider_id.api_base or None,
            username=self.provider_id.username or None,
            password=self.provider_id.password or None,
        )

        # Fetch flights based on mode
        if self.sync_mode == "aircraft_range":
            opensky_flights = self._fetch_by_aircraft_range(client)
        else:
            opensky_flights = self._fetch_by_flights(client)

        # Clear existing comparison lines
        self.comparison_line_ids.unlink()

        # Create comparison lines
        self._create_comparison_lines(opensky_flights)

        # Move to comparison state
        self.state = "compare"

        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def _fetch_by_aircraft_range(self, client):
        """Fetch OpenSky flights by aircraft and date range."""
        if not self.aircraft_id:
            raise UserError(_("Please select an aircraft"))

        # Check if ICAO24 is available, if not try to look it up
        icao24 = self.aircraft_id.icao24
        if not icao24:
            _logger.info(
                f"ICAO24 not set for aircraft {self.aircraft_id.registration}, attempting lookup"
            )

            if not self.aircraft_id.registration:
                raise UserError(
                    _(
                        "Aircraft must have either ICAO24 address or registration number set"
                    )
                )

            # Try to lookup ICAO24 from registration
            try:
                aircraft_data = client.lookup_aircraft_by_registration(
                    self.aircraft_id.registration
                )

                if aircraft_data and aircraft_data.get("icao24"):
                    icao24 = aircraft_data["icao24"]
                    # Update the aircraft record with the found ICAO24
                    self.aircraft_id.write({"icao24": icao24})
                    _logger.info(
                        f"Found and saved ICAO24 {icao24} for {self.aircraft_id.registration}"
                    )
                else:
                    raise UserError(
                        _(
                            "Could not find ICAO24 address for aircraft registration %s\n\n"
                            "The automatic lookup failed. This can happen because:\n"
                            "• The aircraft is not in OpenSky's database\n"
                            "• The registration format is incorrect\n"
                            "• The lookup service is temporarily unavailable\n\n"
                            "Please set the ICAO24 address manually:\n"
                            "1. Go to Flights → Configuration → Aircraft\n"
                            "2. Edit aircraft %s\n"
                            "3. Set the ICAO24 field (6-character hex code)\n\n"
                            "You can find ICAO24 addresses at:\n"
                            "• https://opensky-network.org/aircraft-database\n"
                            "• https://flightaware.com\n"
                            "• https://flightradar24.com"
                        )
                        % (self.aircraft_id.registration, self.aircraft_id.registration)
                    )
            except UserError:
                # Re-raise UserError as-is (don't wrap it)
                raise
            except Exception as e:
                _logger.error(f"Error looking up ICAO24: {str(e)}", exc_info=True)
                raise UserError(
                    _(
                        "Unexpected error while looking up ICAO24 for aircraft %s\n\n"
                        "Error: %s\n\n"
                        "Please set the ICAO24 address manually:\n"
                        "1. Go to Flights → Configuration → Aircraft\n"
                        "2. Edit aircraft %s\n"
                        "3. Set the ICAO24 field\n\n"
                        "The automatic lookup is experimental and may not always work."
                    )
                    % (self.aircraft_id.registration, str(e), self.aircraft_id.registration)
                ) from e

        # Convert dates to timestamps
        # Use start of day for date_from and end of day for date_to
        dt_from = datetime.combine(self.date_from, datetime.min.time())
        dt_to = datetime.combine(self.date_to, datetime.max.time())

        begin_timestamp = int(dt_from.timestamp())
        end_timestamp = int(dt_to.timestamp())

        _logger.info(
            f"Fetching OpenSky flights for aircraft {icao24} "
            f"from {self.date_from} to {self.date_to}"
        )

        try:
            flights = client.get_flights_by_aircraft(
                icao24.lower(), begin_timestamp, end_timestamp
            )

            _logger.info(f"Fetched {len(flights)} flights from OpenSky")
            return flights

        except Exception as e:
            _logger.error(f"Error fetching OpenSky data: {str(e)}", exc_info=True)
            raise UserError(
                _("Error fetching data from OpenSky Network: %s") % str(e)
            ) from e

    def _fetch_by_flights(self, client):
        """Fetch OpenSky flights for selected existing flights."""
        if not self.flight_ids:
            raise UserError(_("Please select at least one flight"))

        all_flights = []

        for flight in self.flight_ids:
            # Get or lookup ICAO24
            icao24 = flight.aircraft_id.icao24

            if not icao24:
                # Try to lookup ICAO24 if we have registration
                if flight.aircraft_id.registration:
                    try:
                        aircraft_data = client.lookup_aircraft_by_registration(
                            flight.aircraft_id.registration
                        )
                        if aircraft_data and aircraft_data.get("icao24"):
                            icao24 = aircraft_data["icao24"]
                            flight.aircraft_id.write({"icao24": icao24})
                            _logger.info(
                                f"Found and saved ICAO24 {icao24} for {flight.aircraft_id.registration}"
                            )
                    except Exception as e:
                        _logger.warning(
                            f"Could not lookup ICAO24 for {flight.aircraft_id.registration}: {str(e)}"
                        )

            if not icao24:
                _logger.warning(
                    f"Skipping flight {flight.display_name} - no ICAO24 on aircraft"
                )
                continue

            # Search for flights on the same day
            dt_from = datetime.combine(flight.date, datetime.min.time())
            dt_to = datetime.combine(flight.date, datetime.max.time())

            begin_timestamp = int(dt_from.timestamp())
            end_timestamp = int(dt_to.timestamp())

            try:
                flights = client.get_flights_by_aircraft(
                    icao24.lower(), begin_timestamp, end_timestamp
                )
                all_flights.extend(flights)

            except Exception as e:
                _logger.error(
                    f"Error fetching OpenSky data for flight {flight.display_name}: {str(e)}"
                )
                continue

        _logger.info(f"Fetched {len(all_flights)} total flights from OpenSky")
        return all_flights

    def _create_comparison_lines(self, opensky_flights):
        """Create comparison lines from OpenSky flight data."""
        if not opensky_flights:
            return

        Flight = self.env["flight.flight"]
        Aerodrome = self.env["flight.aerodrome"]
        Aircraft = self.env["flight.aircraft"]

        for flight_data in opensky_flights:
            # Skip flights without airport data
            if not flight_data.get("estDepartureAirport") or not flight_data.get(
                "estArrivalAirport"
            ):
                continue

            # Find aircraft
            icao24 = flight_data["icao24"].upper()
            aircraft = Aircraft.search([("icao24", "=", icao24)], limit=1)

            if not aircraft:
                _logger.debug(f"Aircraft {icao24} not found in Odoo, skipping")
                continue

            # Find aerodromes
            departure_icao = flight_data["estDepartureAirport"].upper()
            arrival_icao = flight_data["estArrivalAirport"].upper()

            departure = Aerodrome.search([("icao", "=", departure_icao)], limit=1)
            arrival = Aerodrome.search([("icao", "=", arrival_icao)], limit=1)

            if not departure or not arrival:
                _logger.debug(
                    f"Aerodrome {departure_icao} or {arrival_icao} not found, skipping"
                )
                continue

            # Convert timestamps to datetime
            first_seen = datetime.utcfromtimestamp(flight_data["firstSeen"])
            last_seen = datetime.utcfromtimestamp(flight_data["lastSeen"])
            flight_date = first_seen.date()

            # Check if flight exists
            existing_flight = Flight.search(
                [
                    ("aircraft_id", "=", aircraft.id),
                    ("date", "=", flight_date),
                    ("departure_id", "=", departure.id),
                    ("arrival_id", "=", arrival.id),
                ],
                limit=1,
            )

            # Create comparison line
            self.env["opensky.sync.wizard.line"].create(
                {
                    "wizard_id": self.id,
                    "aircraft_id": aircraft.id,
                    "date": flight_date,
                    "departure_id": departure.id,
                    "arrival_id": arrival.id,
                    "opensky_first_seen": first_seen,
                    "opensky_last_seen": last_seen,
                    "opensky_callsign": flight_data.get("callsign", "").strip()
                    or False,
                    "existing_flight_id": existing_flight.id if existing_flight else False,
                    "status": "existing" if existing_flight else "new",
                    "action": "skip" if existing_flight else "create",
                }
            )

    def action_apply_sync(self):
        """Apply the synchronization based on selected actions."""
        self.ensure_one()

        Flight = self.env["flight.flight"]

        created = 0
        updated = 0
        skipped = 0

        for line in self.comparison_line_ids:
            if line.action == "skip":
                skipped += 1
                continue

            if line.action == "create":
                # Create new flight
                Flight.create(
                    {
                        "date": line.date,
                        "aircraft_id": line.aircraft_id.id,
                        "departure_id": line.departure_id.id,
                        "arrival_id": line.arrival_id.id,
                    }
                )
                created += 1

            elif line.action == "update" and line.existing_flight_id:
                # Update existing flight (currently just confirms the match)
                # In the future, this could update times or other fields
                updated += 1

        # Show result message
        message = _(
            "Synchronization complete!\n\n"
            "Created: %(created)s\n"
            "Updated: %(updated)s\n"
            "Skipped: %(skipped)s"
        ) % {
            "created": created,
            "updated": updated,
            "skipped": skipped,
        }

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Sync Complete"),
                "message": message,
                "type": "success",
                "sticky": False,
            },
        }


class OpenskySyncWizardLine(models.TransientModel):
    _name = "opensky.sync.wizard.line"
    _description = "OpenSky Sync Comparison Line"
    _order = "date desc, opensky_first_seen desc"

    wizard_id = fields.Many2one(
        "opensky.sync.wizard", required=True, ondelete="cascade"
    )

    # OpenSky data
    aircraft_id = fields.Many2one("flight.aircraft", string="Aircraft", required=True)
    date = fields.Date(string="Flight Date", required=True)
    departure_id = fields.Many2one(
        "flight.aerodrome", string="Departure", required=True
    )
    arrival_id = fields.Many2one("flight.aerodrome", string="Arrival", required=True)
    opensky_first_seen = fields.Datetime(string="First Seen (UTC)")
    opensky_last_seen = fields.Datetime(string="Last Seen (UTC)")
    opensky_callsign = fields.Char(string="Callsign")

    # Comparison
    existing_flight_id = fields.Many2one("flight.flight", string="Existing Flight")
    status = fields.Selection(
        [("new", "New"), ("existing", "Existing")],
        string="Status",
        required=True,
    )

    # Action
    action = fields.Selection(
        [("create", "Create"), ("update", "Update"), ("skip", "Skip")],
        string="Action",
        required=True,
        default="create",
    )

    @api.depends(
        "date", "aircraft_id.registration", "departure_id.icao", "arrival_id.icao"
    )
    def _compute_display_name(self):
        for record in self:
            date_str = record.date.strftime("%Y-%m-%d") if record.date else "No Date"
            aircraft_str = (
                record.aircraft_id.registration
                if record.aircraft_id
                else "No Aircraft"
            )
            departure_str = (
                record.departure_id.icao if record.departure_id else "No Departure"
            )
            arrival_str = record.arrival_id.icao if record.arrival_id else "No Arrival"

            record.display_name = (
                f"{date_str} / {aircraft_str}: {departure_str} - {arrival_str}"
            )

    # Computed fields for display
    flight_duration = fields.Float(
        compute="_compute_flight_duration", string="Duration (hours)"
    )

    @api.depends("opensky_first_seen", "opensky_last_seen")
    def _compute_flight_duration(self):
        for record in self:
            if record.opensky_first_seen and record.opensky_last_seen:
                delta = record.opensky_last_seen - record.opensky_first_seen
                record.flight_duration = delta.total_seconds() / 3600.0
            else:
                record.flight_duration = 0.0
