from odoo import fields, models


class FlightPilotRemark(models.Model):
    _name = "flight.pilot.remark"
    _description = "Pilot Flight Remark"
    _order = "flight_id desc, partner_id"
    _inherit = ["flight.lock.mixin"]

    flight_id = fields.Many2one(
        "flight.flight", string="Flight", required=True, index=True, ondelete="cascade"
    )
    partner_id = fields.Many2one(
        "res.partner", string="Pilot", required=True, index=True, ondelete="restrict"
    )
    remark = fields.Text(string="Remark", help="Pilot remark or note about the flight")
    signature = fields.Binary(string="Signature", attachment=True, help="Pilot signature image")
    date = fields.Date(related="flight_id.date", store=True, readonly=True)

    _sql_constraints = [
        (
            "unique_pilot_flight_remark",
            "UNIQUE(flight_id, partner_id)",
            "A pilot can only have one remark entry per flight.",
        ),
    ]
