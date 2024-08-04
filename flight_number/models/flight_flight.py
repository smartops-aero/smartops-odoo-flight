# Copyright 2024 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).
from odoo import models, fields, api, _


class FlightFlight(models.Model):
    _inherit = 'flight.flight'

    number_id = fields.Many2one('flight.number', "Flight Number")
