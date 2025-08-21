from odoo import api, fields, models


class FlightFlight(models.Model):
    _name = "flight.flight"
    _description = "Flight"
    _inherit = ["mail.thread", "mail.activity.mixin", "flight.lock.mixin"]
    _order = "date desc, id desc"

    date = fields.Date(
        "Flight Date", help="Scheduled date of flight", required=True, tracking=True
    )
    aircraft_id = fields.Many2one("flight.aircraft", required=True, tracking=True, index=True)
    departure_id = fields.Many2one("flight.aerodrome", required=True, tracking=True, index=True)
    arrival_id = fields.Many2one("flight.aerodrome", required=True, tracking=True, index=True)
    locked = fields.Boolean(default=False, tracking=True)

    # Added crew relationship
    crew_ids = fields.One2many(
        "flight.crew", "flight_id", string="Crew Members", copy=True
    )

    @api.depends(
        "date", "aircraft_id.registration", "departure_id.icao", "arrival_id.icao"
    )
    def _compute_display_name(self):
        for record in self:
            # Build display name with safe field access
            date_str = record.date.strftime("%Y-%m-%d") if record.date else "No Date"
            aircraft_str = (
                record.aircraft_id.registration
                if record.aircraft_id and record.aircraft_id.registration
                else "No Aircraft"
            )
            departure_str = (
                record.departure_id.icao
                if record.departure_id and record.departure_id.icao
                else "No Departure"
            )
            arrival_str = (
                record.arrival_id.icao
                if record.arrival_id and record.arrival_id.icao
                else "No Arrival"
            )

            record.display_name = (
                f"{date_str} / {aircraft_str}: {departure_str} - {arrival_str}"
            )

    def toggle_locked(self):
        self.ensure_one()
        self.write({"locked": not self.locked})

    @api.onchange("aircraft_id")
    def _onchange_aircraft_id(self):
        """When aircraft changes and departure is empty, set departure to last arrival."""
        if self.aircraft_id and not self.departure_id:
            # Search for the last flight of this aircraft
            last_flight = self.search(
                [
                    ("aircraft_id", "=", self.aircraft_id.id),
                    ("date", "<", self.date),
                    ("arrival_id", "!=", False),
                ],
                order="date desc, id desc",
                limit=1,
            )

            if last_flight:
                self.departure_id = last_flight.arrival_id
