from odoo import fields, models


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
