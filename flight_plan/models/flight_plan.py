from odoo import api, fields, models


class FlightPlan(models.Model):
    _name = "flight.plan"
    _description = "Flight Plan"
    _inherit = ["mail.thread", "mail.activity.mixin", "flight.lock.mixin", "json.text.mixin"]

    flight_id = fields.Many2one("flight.flight", required=True, index=True)
    version_number = fields.Integer(default=1)
    timestamp = fields.Datetime()

    remarks = fields.Json()
    flight_plan_header = fields.Json()
    fuel_header = fields.Json()
    weight_header = fields.Json()

    # Computed text fields for formatted display
    remarks_text = fields.Text(compute='_compute_remarks_text', store=False, readonly=True)
    flight_plan_header_text = fields.Text(compute='_compute_flight_plan_header_text', store=False, readonly=True)
    fuel_header_text = fields.Text(compute='_compute_fuel_header_text', store=False, readonly=True)
    weight_header_text = fields.Text(compute='_compute_weight_header_text', store=False, readonly=True)

    route_id = fields.Many2one("flight.plan.route")
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

    @api.depends("flight_id", "version_number", "route_id")
    def _compute_display_name(self):
        for record in self:
            route_name = record.route_id.name or "No Route"
            record.display_name = f"{record.flight_id.display_name} v{record.version_number} - {route_name}"

    @api.depends('remarks')
    def _compute_remarks_text(self):
        for record in self:
            record.remarks_text = record.json2text(record.remarks)

    @api.depends('flight_plan_header')
    def _compute_flight_plan_header_text(self):
        for record in self:
            record.flight_plan_header_text = record.json2text(record.flight_plan_header)

    @api.depends('fuel_header')
    def _compute_fuel_header_text(self):
        for record in self:
            record.fuel_header_text = record.json2text(record.fuel_header)

    @api.depends('weight_header')
    def _compute_weight_header_text(self):
        for record in self:
            record.weight_header_text = record.json2text(record.weight_header)
