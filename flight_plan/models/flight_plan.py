from odoo import api, fields, models


class FlightPlan(models.Model):
    _name = "flight.plan"
    _description = "Flight Plan"
    _inherit = ["mail.thread", "mail.activity.mixin", "flight.lock.mixin"]

    flight_id = fields.Many2one("flight.flight", required=True, index=True)
    version_number = fields.Integer(string="Version Number", default=1)
    timestamp = fields.Datetime(string="Timestamp")

    remarks = fields.Json(string="Remarks")
    flight_plan_header = fields.Json(string="Flight Plan Header")
    fuel_header = fields.Json(string="Fuel Header")
    weight_header = fields.Json(string="Weight Header")


    route_id = fields.Many2one("flight.plan.route", index=True)
    alternate_route_ids = fields.Many2many(
        "flight.plan.route",
        "flight_plan_route_alternate_rel",
        "plan_id",
        "alternate_route_id",
        string="Alternate Routes",
        domain="[('route_type', '=', 'alternate')]",
    )

    aerodrome_ids = fields.One2many(
        "flight.plan.aerodrome", "plan_id", string="Aerodromes"
    )
    
    # Computed field to show main route waypoints directly
    main_route_waypoint_ids = fields.One2many(
        "flight.route.waypoint", compute="_compute_main_route_waypoints", 
        string="Main Route Waypoints", readonly=True
    )

    @api.depends("flight_id", "version_number", "route_id")
    def _compute_display_name(self):
        for record in self:
            route_name = record.route_id.name or "No Route"
            record.display_name = f"{record.flight_id.display_name} v{record.version_number} - {route_name}"

    
    @api.depends('route_id', 'route_id.waypoint_ids')
    def _compute_main_route_waypoints(self):
        for record in self:
            if record.route_id:
                record.main_route_waypoint_ids = record.route_id.waypoint_ids
            else:
                record.main_route_waypoint_ids = False
