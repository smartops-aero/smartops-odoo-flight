# models/flight_aircraft_image_category.py
from odoo import fields, models


class FlightAircraftImageCategory(models.Model):
    _name = "flight.aircraft.image.category"
    _description = "Aircraft Image Category"
    _order = "sequence, name"

    name = fields.Char("Name", required=True, translate=True)
    code = fields.Char("Code", required=True)
    sequence = fields.Integer("Sequence", default=10)
    description = fields.Text("Description", translate=True)
    active = fields.Boolean("Active", default=True)

    _sql_constraints = [
        ("unique_code", "unique(code)", "Category code must be unique!")
    ]
