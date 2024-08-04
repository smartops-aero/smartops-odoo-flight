# Copyright 2024 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).
from odoo import models, fields, api


class FlightFlight(models.Model):
    _name = 'flight.flight'
    _description = 'Flight'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Name", compute='_compute_name', store=True)
    date = fields.Date("Flight Date", help="Scheduled date of flight", required=True, tracking=True)
    aircraft_id = fields.Many2one('flight.aircraft', required=True, tracking=True)
    departure_id = fields.Many2one('flight.aerodrome', required=True, tracking=True)
    arrival_id = fields.Many2one('flight.aerodrome', required=True, tracking=True)

    @api.depends("date", "aircraft_id", "departure_id", "arrival_id")
    def _compute_name(self):
        for record in self:
            record.name = f"{record.date} - {record.aircraft_id.registration} - {record.departure_id.icao} - {record.arrival_id.icao}"

    def name_get(self):
        return [(record.id, record.name) for record in self]
