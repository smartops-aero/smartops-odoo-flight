from odoo import api, fields, models


class FlightRouteWaypoint(models.Model):
    _name = "flight.route.waypoint"
    _description = "Flight Route Waypoint"
    _order = "sequence, id"

    route_id = fields.Many2one(
        "flight.plan.route", required=True, ondelete="cascade", index=True
    )
    sequence = fields.Integer(string="Sequence", default=10)
    name = fields.Char(string="Name")
    description = fields.Char(string="Description")
    latitude = fields.Float(string="Latitude")
    longitude = fields.Float(string="Longitude")
    icao_country_code = fields.Char(string="ICAO Country Code")

    @api.depends("name", "sequence", "latitude", "longitude")
    def _compute_display_name(self):
        for record in self:
            if record.name:
                record.display_name = f"{record.sequence:03d} - {record.name}"
            elif record.latitude and record.longitude:
                record.display_name = f"{record.sequence:03d} - {record.latitude:.4f},{record.longitude:.4f}"
            else:
                record.display_name = f"{record.sequence:03d} - Waypoint"
