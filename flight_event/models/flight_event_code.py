# Copyright 2024 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).
from datetime import datetime
from odoo import fields, models


class FlightEventCode(models.Model):
    _name = 'flight.event.code'
    _description = 'Flight Event Code'
    _rec_name = 'code'
    _order = 'sequence, id'

    code = fields.Char(required=True)
    name = fields.Char(required=True)
    description = fields.Char()
    sequence = fields.Integer(default=10)

    _sql_constraints = [
        ('code_unique', 'unique(code)', "The event code must be unique!"),
    ]
