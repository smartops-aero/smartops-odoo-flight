from odoo import fields, models


class FlightPlanRoute(models.Model):
    _name = "flight.plan.route"
    _description = "Flight Plan Route"

    plan_id = fields.Many2one("flight.plan", required=True, ondelete="cascade")
    route_type = fields.Selection(
        [
            ("flight", "Flight"),
            ("fms", "FMS"),
            ("alternate", "Alternate"),
        ],
        default="flight",
        required=True,
    )
    waypoint_ids = fields.One2many(
        "flight.route.waypoint", "route_id", string="Waypoints"
    )
