from odoo import api, fields, models


class FlightPlanRoute(models.Model):
    _name = "flight.plan.route"
    _description = "Flight Plan Route"

    plan_id = fields.Many2one("flight.plan", required=False, ondelete="cascade")
    name = fields.Char()
    fms_name = fields.Char()
    route_type = fields.Selection(
        [
            ("flight", "Flight"),
            ("alternate", "Alternate"),
        ],
        default="flight",
        required=True,
    )
    waypoint_ids = fields.One2many(
        "flight.route.waypoint", "route_id", string="Waypoints"
    )

    @api.depends("name", "fms_name", "route_type")
    def _compute_display_name(self):
        for record in self:
            name = record.name or record.fms_name or "Unnamed Route"
            record.display_name = f"{name} ({record.route_type.title()})"
