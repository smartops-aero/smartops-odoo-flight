# Copyright 2024 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).
from odoo import api, fields, models


class FlightFlight(models.Model):
    _inherit = "flight.flight"
    _rec_name = "number_id"
    number_id = fields.Many2one("flight.number", "Flight Number")

    @api.depends('date', 'number_id.prefix_id.name', 'number_id.number', 'aircraft_id.registration', 'departure_id.icao', 'arrival_id.icao')
    def _compute_display_name(self):
        for record in self:
            date_str = record.date.strftime('%Y-%m-%d') if record.date else 'No Date'
            
            if record.number_id:
                prefix_name = record.number_id.prefix_id.name if record.number_id.prefix_id else ''
                number = record.number_id.number if record.number_id.number else ''
                record.display_name = f"{date_str} / {prefix_name}{number}"
            else:
                # Fallback to original format if no flight number
                aircraft_str = record.aircraft_id.registration if record.aircraft_id and record.aircraft_id.registration else 'No Aircraft'
                departure_str = record.departure_id.icao if record.departure_id and record.departure_id.icao else 'No Departure'
                arrival_str = record.arrival_id.icao if record.arrival_id and record.arrival_id.icao else 'No Arrival'
                record.display_name = f"{date_str} / {aircraft_str}: {departure_str} - {arrival_str}"
