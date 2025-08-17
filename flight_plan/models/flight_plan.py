from odoo import fields, models


class FlightPlan(models.Model):
    _name = "flight.plan"
    _description = "Flight Plan"
    _inherit = ["flight.lock.mixin"]

    flight_id = fields.Many2one("flight.flight", required=True, index=True)
    version_number = fields.Integer()
    timestamp = fields.Datetime()

    remarks = fields.Json()
    flight_plan_header = fields.Json()
    fuel_header = fields.Json()
    weight_header = fields.Json()

    route_id = fields.Many2one("flight.plan.route")
    alternate_plan_ids = fields.Many2many(
        "flight.plan",
        "flight_plan_alternate_rel",
        "plan_id",
        "alternate_id",
        string="Alternate Plans",
    )

    aerodrome_ids = fields.One2many(
        "flight.plan.aerodrome", "plan_id", string="Aerodromes"
    )
