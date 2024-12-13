from odoo import fields, models


class FlightAircraftSpecCode(models.Model):
    _name = "flight.aircraft.spec.code"
    _description = "Aircraft Specification Code"
    _order = "sequence, name"

    category_id = fields.Many2one(
        "flight.aircraft.spec.category",
        string="Category",
        required=True,
        ondelete="restrict",
    )
    code = fields.Char(required=True)
    name = fields.Char(required=True, translate=True)
    description = fields.Text(translate=True)
    type = fields.Selection(
        [
            ("numeric", "Numeric"),
            ("text", "Text"),
            ("bool", "Boolean")
        ],
        string="Value Type",
        required=True,
        default="text",
    )
    sequence = fields.Integer(default=10)
    

    _sql_constraints = [
        (
            "unique_spec_code",
            "UNIQUE(code)",
            "Specification code must be unique!",
        ),
    ]
