from odoo import fields, models


class FlightAircraftSpecCategory(models.Model):
    _name = "flight.aircraft.spec.category"
    _description = "Aircraft Specification Category"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    description = fields.Text(translate=True)

    _sql_constraints = [
        (
            "unique_category_code",
            "UNIQUE(code)",
            "Category code must be unique!",
        ),
    ]
