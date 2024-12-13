from odoo import fields, models

class FlightAircraft(models.Model):
    _inherit = 'flight.aircraft'

    spec_ids = fields.One2many(
        'flight.aircraft.spec',
        'aircraft_id',
        string='Specifications',
        tracking=True
    )