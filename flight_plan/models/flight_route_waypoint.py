from odoo import api, fields, models
from odoo.exceptions import ValidationError


class FlightRouteWaypoint(models.Model):
    _name = "flight.route.waypoint"
    _description = "Flight Route Waypoint"
    _order = "sequence, id"

    _sql_constraints = [
        ("unique_sequence_per_route", "unique(route_id, sequence)", 
         "Sequence numbers must be unique within each route."),
    ]

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

    @api.constrains("latitude", "longitude")
    def _check_coordinates(self):
        for record in self:
            if record.latitude is not False and (record.latitude < -90 or record.latitude > 90):
                raise ValidationError("Latitude must be between -90.0 and +90.0 degrees.")
            if record.longitude is not False and (record.longitude < -180 or record.longitude > 180):
                raise ValidationError("Longitude must be between -180.0 and +180.0 degrees.")
