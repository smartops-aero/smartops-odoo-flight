from odoo import api, fields, models


class FlightPlanAerodrome(models.Model):
    _name = "flight.plan.aerodrome"
    _description = "Flight Plan Aerodrome"
    _inherit = ["json.text.mixin"]

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
    
    # Computed text field for formatted display
    terminal_procedure_text = fields.Text(compute='_compute_terminal_procedure_text', store=False, readonly=True)

    @api.depends("aerodrome_id", "function", "planned_runway")
    def _compute_display_name(self):
        for record in self:
            aerodrome_name = record.aerodrome_id.display_name if record.aerodrome_id else "Unknown"
            function_name = dict(record._fields["function"].selection).get(record.function, record.function)
            runway = f" RW{record.planned_runway}" if record.planned_runway else ""
            record.display_name = f"{aerodrome_name} ({function_name}){runway}"

    @api.depends('terminal_procedure')
    def _compute_terminal_procedure_text(self):
        for record in self:
            record.terminal_procedure_text = record.json2text(record.terminal_procedure)
