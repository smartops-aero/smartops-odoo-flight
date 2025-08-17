from odoo import fields, models


class FlightPlanAerodrome(models.Model):
    _name = "flight.plan.aerodrome"
    _description = "Flight Plan Aerodrome"

    plan_id = fields.Many2one("flight.plan", required=True, ondelete="cascade")
    aerodrome_id = fields.Many2one("flight.aerodrome", required=True)
    function = fields.Selection(
        [
            ("departure", "Departure"),
            ("arrival", "Arrival"),
            ("departure_alternate", "Departure Alternate"),
            ("arrival_alternate", "Arrival Alternate"),
        ],
        required=True,
    )
    planned_runway = fields.Char()
    terminal_procedure = fields.Json()
