# Copyright 2024 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).
from odoo import fields, models


class FlightPhase(models.Model):
    _name = "flight.phase"
    _description = "Flight Phase"

    name = fields.Char()
    sequence = fields.Integer()
    start_event_code_id = fields.Many2one("flight.event.code")
    end_event_code_id = fields.Many2one("flight.event.code")
