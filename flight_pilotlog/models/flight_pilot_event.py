from odoo import fields, models


class FlightPilotEventCode(models.Model):
    _name = "flight.pilot.event.code"
    _description = "Pilot Event Code"
    _order = "sequence, name"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("unique_code", "unique(code)", "The event code must be unique!"),
    ]

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.code} - {record.name}"
            result.append((record.id, name))
        return result

class FlightPilotEvent(models.Model):
    _name = "flight.pilot.event"
    _description = "Pilot Flight Event"
    _order = "flight_id desc, datetime, partner_id"
    _inherit = ["flight.lock.mixin"]

    flight_id = fields.Many2one(
        "flight.flight", string="Flight", required=True, index=True, ondelete="cascade"
    )
    partner_id = fields.Many2one(
        "res.partner", string="Pilot", required=True, index=True, ondelete="restrict"
    )
    event_code_id = fields.Many2one(
        "flight.pilot.event.code",
        string="Event Code",
        required=True,
        index=True,
        ondelete="restrict",
    )
    count = fields.Integer(string="Count", default=1, help="Number of times this event occurred")
    datetime = fields.Datetime(string="Datetime")
    date = fields.Date(related="flight_id.date", store=True, readonly=True)

    _sql_constraints = [
        (
            "unique_pilot_flight_event",
            "UNIQUE(flight_id, partner_id, event_code_id)",
            "A pilot can only have one event entry per flight and event code.",
        ),
    ]