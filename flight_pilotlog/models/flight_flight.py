from odoo import fields, models

class FlightFlight(models.Model):
    
    _inherit = "flight.flight"

    remark_ids = fields.One2many(
        "flight.pilot.remark", "flight_id", string="Pilot Remarks", copy=True
    )

    pilot_event_ids = fields.One2many(
        "flight.pilot.event", "flight_id", string="Pilot Events", copy=True
    )

    pilot_time_ids = fields.One2many(
        "flight.pilot.time", "flight_id", string="Pilot Times", copy=True
    )
        
        



    