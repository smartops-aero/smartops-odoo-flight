from odoo import fields, models

class FlightAircraft(models.Model):
    _inherit = "flight.aircraft"

    amenity_ids = fields.Many2many("flight.aircraft.amenity", string="Amenities")