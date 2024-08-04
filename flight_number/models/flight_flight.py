# Copyright 2024 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).
from odoo import models, fields, api, _


class FlightFlight(models.Model):
    _inherit = 'flight.flight'
    _rec_name = 'number_id'

    number_id = fields.Many2one('flight.number', "Flight Number")

    @api.depends("number_id", "aircraft_id", "date", "departure_id", "arrival_id")
    def _compute_display_name(self):
        for record in self:
            if record.number_id:
                record.display_name = (f"{record.date} / {record.number_id.display_name}")
            else:
                super(FlightFlight, record)._compute_display_name()
