from odoo import api, fields, models


class FlightFlight(models.Model):
    _name = "flight.flight"
    _description = "Flight"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
        "flight.lock.mixin",
        "map.path.mixin",
    ]
    _order = "date desc, id desc"

    date = fields.Date(
        "Flight Date", help="Scheduled date of flight", required=True, tracking=True
    )
    aircraft_id = fields.Many2one(
        "flight.aircraft", required=True, tracking=True, index=True
    )
    departure_id = fields.Many2one(
        "flight.aerodrome", required=True, tracking=True, index=True
    )
    arrival_id = fields.Many2one(
        "flight.aerodrome", required=True, tracking=True, index=True
    )
    locked = fields.Boolean(default=False, tracking=True)

    # Added crew relationship
    crew_ids = fields.One2many(
        "flight.flight.crew", "flight_id", string="Crew Members", copy=True
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

    @api.depends("departure_id", "arrival_id")
    def _compute_map_data(self):
        """Generate map data for flight path visualization"""
        for record in self:
            if not record.departure_id or not record.arrival_id:
                record.map_data = {}
                continue

            # Check if coordinates are available
            dep_lat = record.departure_id.latitude
            dep_lng = record.departure_id.longitude
            arr_lat = record.arrival_id.latitude
            arr_lng = record.arrival_id.longitude

            if not all([dep_lat, dep_lng, arr_lat, arr_lng]):
                record.map_data = {}
                continue

            # Get ICAO codes for labels
            dep_icao = record.departure_id.icao or "DEP"
            arr_icao = record.arrival_id.icao or "ARR"

            record.map_data = {
                "paths": [
                    {
                        "id": f"route_{record.id}",
                        "points": [[dep_lat, dep_lng], [arr_lat, arr_lng]],
                        "options": {
                            "color": "#2196F3",
                            "weight": 3,
                            "animated": True,
                            "markerHtml": '<img src="/flight/static/description/plane-icon-top-view.png" style="width: 28px; height: 28px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));" />',
                            "markerSize": [32, 32],
                            "markerAnchor": [16, 16],
                            "initialPosition": [dep_lat, dep_lng],
                            "initialState": {"opacity": 1, "scale": 1, "rotation": 0},
                            "loop": True,
                            "animations": [
                                {
                                    "duration": 2.0,
                                    "easing": "power1.inOut",
                                    "properties": {"position": {"to": [arr_lat, arr_lng]}},
                                }
                            ],
                        },
                    }
                ],
                "markers": [
                    {
                        "id": f"dep_{record.id}",
                        "position": [dep_lat, dep_lng],
                        "options": {
                            "icon": '<div style="width: 26px; height: 26px; background: white; border: 2px solid #333; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; box-shadow: 0 2px 6px rgba(0,0,0,0.3);">🛫</div>',
                            "iconSize": [28, 28],
                            "iconAnchor": [14, 14],
                            "iconClass": "departure-marker",
                            "popup": f"<b>Departure</b><br/>{record.departure_id.name or dep_icao}",
                            "label": dep_icao,
                        },
                    },
                    {
                        "id": f"arr_{record.id}",
                        "position": [arr_lat, arr_lng],
                        "options": {
                            "icon": '<div style="width: 26px; height: 26px; background: white; border: 2px solid #333; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; box-shadow: 0 2px 6px rgba(0,0,0,0.3);">🛬</div>',
                            "iconSize": [28, 28],
                            "iconAnchor": [14, 14],
                            "iconClass": "arrival-marker",
                            "popup": f"<b>Arrival</b><br/>{record.arrival_id.name or arr_icao}",
                            "label": arr_icao,
                        },
                    },
                ],
            }
