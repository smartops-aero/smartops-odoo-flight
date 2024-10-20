# Copyright 2024 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).
from odoo import fields, models


class FlightFlight(models.Model):
    _inherit = "flight.flight"
    _rec_name = "number_id"
    number_id = fields.Many2one("flight.number", "Flight Number")

    def name_get(self):
        result = []
        for record in self:
            if record.number_id:
                name = f"{record.date} / {record.number_id.prefix_id.name}{record.number_id.number}"
            else:
                name = f"{record.date} / {record.aircraft_id.registration}: {record.departure_id.icao} - {record.arrival_id.icao}"
            result.append((record.id, name))
        return result
