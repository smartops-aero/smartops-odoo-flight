from odoo import api, fields, models
from odoo.exceptions import ValidationError


class FlightPlanAerodrome(models.Model):
    _name = "flight.plan.aerodrome"
    _description = "Flight Plan Aerodrome"

    # Note: Using Python constraints instead of SQL due to PostgreSQL partial constraint issues

    plan_id = fields.Many2one("flight.plan", required=True, ondelete="cascade", index=True)
    aerodrome_id = fields.Many2one("flight.aerodrome", required=True, index=True)
    function = fields.Selection(
        [
            ("departure", "Departure"),
            ("arrival", "Arrival"),
            ("departure_alternate", "Departure Alternate"),
            ("arrival_alternate", "Arrival Alternate"),
        ],
        required=True,
    )
    planned_runway = fields.Char(string="Planned Runway")
    terminal_procedure = fields.Json(string="Terminal Procedure")

    @api.depends("aerodrome_id", "function", "planned_runway")
    def _compute_display_name(self):
        for record in self:
            aerodrome_name = record.aerodrome_id.display_name if record.aerodrome_id else "Unknown"
            function_name = dict(record._fields["function"].selection).get(record.function, record.function)
            runway = f" RW{record.planned_runway}" if record.planned_runway else ""
            record.display_name = f"{aerodrome_name} ({function_name}){runway}"

    @api.constrains("plan_id", "function")
    def _check_unique_departure_arrival(self):
        """Ensure only one departure and one arrival per flight plan"""
        for record in self:
            if record.function in ("departure", "arrival"):
                # Count existing records with same plan_id and function
                count = self.search_count([
                    ("plan_id", "=", record.plan_id.id),
                    ("function", "=", record.function),
                    ("id", "!=", record.id)
                ])
                if count > 0:
                    function_name = dict(record._fields["function"].selection).get(record.function)
                    raise ValidationError(f"A flight plan can only have one {function_name.lower()} aerodrome.")

