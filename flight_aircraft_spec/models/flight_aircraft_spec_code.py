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
            ("bool", "Boolean"),
            ("text", "Text"),
            ("float", "Numeric"),
        ],
        required=True,
        default="text",
    )
    sequence = fields.Integer(default=10)
    default_value = fields.Char(
        help="Default value for the specification. Must match the selected type."
    )
    default_uom_id = fields.Many2one(
        'uom.uom',
        string='Default Unit of Measure',
        help="Default unit of measure for numeric specifications"
    )

    _sql_constraints = [
        (
            "unique_spec_code",
            "UNIQUE(code)",
            "Specification code must be unique!",
        ),
    ]
