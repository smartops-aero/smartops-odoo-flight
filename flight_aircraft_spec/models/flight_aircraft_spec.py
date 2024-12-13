from odoo import api, fields, models


class FlightAircraftSpec(models.Model):
    _name = "flight.aircraft.spec"
    _description = "Aircraft Specification"
    _rec_name = "display_name"

    code_id = fields.Many2one(
        'flight.aircraft.spec.code',
        string='Specification Code',
        required=True,
        ondelete="restrict"
    )
    code_type = fields.Selection(
        related='code_id.type',
        string='Code Type',
        readonly=True,
        store=True
    )
    aircraft_id = fields.Many2one(
        "flight.aircraft",
        string="Aircraft",
        required=True,
        ondelete="cascade",
    )
    value_bool = fields.Boolean(string="Boolean Value")
    value_text = fields.Text(string="Text Value")
    value_numeric = fields.Float(string="Numeric Value")
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure'
    )

    display_name = fields.Char(
        string="Display Name", compute="_compute_display_name", store=True
    )

    _sql_constraints = [
        (
            "unique_aircraft_spec",
            "UNIQUE(code_id, aircraft_id)",
            "Only one specification of each type per aircraft is allowed!",
        ),
    ]

    @api.depends("code_id", "value_bool", "value_text", "value_numeric", "uom_id")
    def _compute_display_name(self):
        for spec in self:
            if not spec.code_id:
                spec.display_name = ""
                continue

            if spec.code_id.type == "bool":
                value = "Yes" if spec.value_bool else "No"
            elif spec.code_id.type == "text":
                value = spec.value_text or ""
            else:  # numeric
                value = f"{spec.value_numeric} {spec.uom_id.name or ''}"

            spec.display_name = f"{spec.code_id.name}: {value}"

    @api.onchange("code_id")
    def _onchange_code_id(self):
        if self.code_id:
            # Clear all values first
            self.value_bool = False
            self.value_text = False
            self.value_numeric = 0.0
            self.uom_id = False

            # Set default value if specified
            if self.code_id.default_value:
                if self.code_id.type == "bool":
                    self.value_bool = self.code_id.default_value.lower() in ("true", "1", "yes")
                elif self.code_id.type == "text":
                    self.value_text = self.code_id.default_value
                else:  # numeric
                    try:
                        self.value_numeric = float(self.code_id.default_value)
                    except (ValueError, TypeError):
                        pass
