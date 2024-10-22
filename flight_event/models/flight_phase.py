# Copyright 2024 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).
from odoo import api, fields, models

from .flight_event import EVENT_TIME_KINDS


class FlightPhase(models.Model):
    _name = "flight.phase"
    _description = "Flight Phase"

    name = fields.Char()
    sequence = fields.Integer()
    start_event_code_id = fields.Many2one("flight.event.code")
    end_event_code_id = fields.Many2one("flight.event.code")


class FlightPhaseDuration(models.Model):
    _name = "flight.phase.duration"
    _description = "Flight Phase Duration"
    _inherit = ["flight.lock.mixin"]

    flight_id = fields.Many2one("flight.flight", required=True, ondelete="cascade")
    phase_id = fields.Many2one("flight.phase", required=True)
    start_event_id = fields.Many2one(
        "flight.event.time", string="Start Event", required=True
    )
    end_event_id = fields.Many2one(
        "flight.event.time", string="End Event", required=True
    )
    duration = fields.Float(
        string="Duration (hours)", compute="_compute_duration", store=True
    )
    time_kind = fields.Selection(
        EVENT_TIME_KINDS,
        string="Time Kind",
        required=True,
    )

    @api.depends("start_event_id.time", "end_event_id.time")
    def _compute_duration(self):
        for record in self:
            if record.start_event_id.time and record.end_event_id.time:
                duration = (
                    record.end_event_id.time - record.start_event_id.time
                ).total_seconds() / 3600
                record.duration = max(duration, 0)  # Ensure non-negative duration
            else:
                record.duration = 0

    _sql_constraints = [
        (
            "unique_flight_phase_time_kind",
            "UNIQUE(flight_id, phase_id, time_kind)",
            "A flight can only have one duration entry per phase and time kind.",
        )
    ]
