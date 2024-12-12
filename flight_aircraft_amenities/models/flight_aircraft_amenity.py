from odoo import fields, models

class FlightAircraftAmenity(models.Model):
    _name = "flight.aircraft.amenity"
    _description = "Aircraft Amenity"
    _order = "sequence, name"

    name = fields.Char("Name", required=True, translate=True)
    sequence = fields.Integer("Sequence", default=10)