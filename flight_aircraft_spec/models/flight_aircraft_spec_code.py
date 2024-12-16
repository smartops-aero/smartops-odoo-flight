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
    code_type = fields.Selection(
        [
            ("float", "Float"),
            ("text", "Text"),
            ("bool", "Boolean")
        ],
        string="Value Type",
        required=True,
        default="text",
    )
    sequence = fields.Integer(default=10)
    default_uom_id = fields.Many2one(
        'uom.uom',
        string='Default Unit of Measure',
        help="Default unit of measure for this specification code"
    )    

    _sql_constraints = [
        (
            "unique_spec_code",
            "UNIQUE(code)",
            "Specification code must be unique!",
        ),
    ]
