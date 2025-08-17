from odoo import api, fields, models


class FlightRouteWaypoint(models.Model):
    _name = "flight.route.waypoint"
    _description = "Flight Route Waypoint"
    _order = "sequence, id"

    route_id = fields.Many2one(
        "flight.plan.route", required=True, ondelete="cascade", index=True
    )
    sequence = fields.Integer(default=10)
    name = fields.Char()
    description = fields.Char()
    latitude = fields.Float()
    longitude = fields.Float()
    icao_country_code = fields.Char()

    @api.depends("name", "sequence", "latitude", "longitude")
    def _compute_display_name(self):
        for record in self:
            if record.name:
                record.display_name = f"{record.sequence:03d} - {record.name}"
            elif record.latitude and record.longitude:
                record.display_name = f"{record.sequence:03d} - {record.latitude:.4f},{record.longitude:.4f}"
            else:
                record.display_name = f"{record.sequence:03d} - Waypoint"
