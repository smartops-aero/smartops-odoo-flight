# Copyright 2024 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).

from odoo import api, fields, models


class FlightFlightCrew(models.Model):
    _name = "flight.flight.crew"
    _description = "Flight Crew Assignment"
    _inherit = ["flight.lock.mixin"]
    _table = "flight_crew"  # Keep existing table name for data compatibility

    partner_id = fields.Many2one("res.partner", string="Contact", required=True)
    flight_id = fields.Many2one(
        "flight.flight", string="Flight", required=True, ondelete="cascade", index=True
    )

    @api.depends("partner_id")
    def _compute_display_name(self):
        """Compute display name to show partner name"""
        for record in self:
            record.display_name = (
                record.partner_id.name
                if record.partner_id and record.partner_id.name
                else f"Crew Member #{record.id}"
            )
