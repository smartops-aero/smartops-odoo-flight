from odoo import fields, models


class FlightAircraft(models.Model):
    _inherit = "flight.aircraft"

    seat_map_1920 = fields.Image(
        "Seat Map",
        max_width=1920,
        max_height=1920,
        help="Upload a seat map image showing the aircraft's seating configuration",
    )

    spec_ids = fields.One2many(
        "flight.aircraft.spec", "aircraft_id", string="Specifications", tracking=True
    )
