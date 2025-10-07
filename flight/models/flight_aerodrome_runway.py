from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FlightAerodromeRunway(models.Model):
    _name = "flight.aerodrome.runway"
    _description = "Aerodrome Runway"
    _order = "code"

    name = fields.Char(
        compute="_compute_name",
        store=True,
        help="Runway name (e.g., KORD 05R)"
    )
    code = fields.Char(
        required=True,
        size=3,
        help="Runway code (e.g., 05R, 23L, 88)"
    )
    aerodrome_id = fields.Many2one(
        "flight.aerodrome",
        required=True,
        ondelete="cascade"
    )
    length = fields.Float(
        string="Length",
        help="Runway length"
    )
    length_uom_id = fields.Many2one(
        "uom.uom",
        string="Length UoM",
        domain="[('category_id.name', '=', 'Length')]",
        default=lambda self: self.env.ref('uom.product_uom_meter', raise_if_not_found=False),
        help="Unit of measure for runway length"
    )
    width = fields.Float(
        string="Width",
        help="Runway width"
    )
    width_uom_id = fields.Many2one(
        "uom.uom",
        string="Width UoM",
        domain="[('category_id.name', '=', 'Length')]",
        default=lambda self: self.env.ref('uom.product_uom_meter', raise_if_not_found=False),
        help="Unit of measure for runway width"
    )

    _sql_constraints = [
        (
            "unique_runway_per_aerodrome",
            "UNIQUE(aerodrome_id, code)",
            "Runway code must be unique per aerodrome!",
        ),
    ]

    @api.depends("aerodrome_id.icao", "code")
    def _compute_name(self):
        for record in self:
            if record.aerodrome_id and record.code:
                record.name = f"{record.aerodrome_id.icao} {record.code}"
            else:
                record.name = record.code or "New Runway"

    @api.constrains("code")
    def _check_runway_code(self):
        for record in self:
            if record.code == "88":  # Special case for all runways
                continue
            if len(record.code) < 2 or len(record.code) > 3:
                raise ValidationError(_("Runway code must be 2-3 characters"))

            # Check first two digits (01-36)
            try:
                runway_num = int(record.code[:2])
                if runway_num < 1 or runway_num > 36:
                    raise ValidationError(
                        _("Runway number must be between 01 and 36")
                    )
            except ValueError as e:
                raise ValidationError(
                    _("First two characters must be digits")
                ) from e

            # Check optional third character (L/R/C)
            if len(record.code) == 3:
                if record.code[2] not in ["L", "R", "C"]:
                    raise ValidationError(
                        _("Third character must be L, R, or C")
                    )
