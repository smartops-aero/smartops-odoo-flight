from odoo import fields, models

class FlightAircraft(models.Model):
    _inherit = "flight.aircraft"

    # Aircraft specifications
    seat_map_1920 = fields.Image(
        "Seat Map",
        max_width=1920,
        max_height=1920,
        help="Upload a seat map image showing the aircraft's seating configuration",
    )

    # Aircraft specifications
    passenger_capacity = fields.Integer("Passenger Capacity")
    range_nm = fields.Integer("Range (Nautical Miles)")
    cruise_speed = fields.Integer("Cruise Speed (Knots)")
    cabin_length = fields.Float("Cabin Length (ft)")
    cabin_width = fields.Float("Cabin Width (ft)")
    cabin_height = fields.Float("Cabin Height (ft)")
    luggage_capacity = fields.Integer("Luggage Capacity (cu ft)")
    useful_load = fields.Integer(
        "Useful Load (lb)", 
        help="Maximum useful load in pounds"
    )