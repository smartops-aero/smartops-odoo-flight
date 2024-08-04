# Copyright 2024 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).
from odoo import fields, models, api


class FlightPhase(models.Model):
    _name = 'flight.phase'
    _description = 'Flight Phase'

    name = fields.Char()
    sequence = fields.Integer()
    start_event_code_id = fields.Many2one("flight.event.code")
    end_event_code_id = fields.Many2one("flight.event.code")


class FlightPhaseDuration(models.Model):
    _name = 'flight.phase.duration'
    _description = 'Flight Phase Duration'
    _auto = False

    flight_id = fields.Many2one('flight.flight', string='Flight', readonly=True)
    phase_id = fields.Many2one('flight.phase', string='Phase', readonly=True)
    start_time = fields.Datetime(string='Start Time', readonly=True)
    end_time = fields.Datetime(string='End Time', readonly=True)
    duration = fields.Float(string='Duration (hours)', readonly=True)

    def init(self):
        self.env.cr.execute("""
        CREATE OR REPLACE VIEW flight_phase_duration AS (
            WITH phase_events AS (
                SELECT 
                    f.id AS flight_id,
                    p.id AS phase_id,
                    p.name AS phase_name,
                    start_event.time AS start_time,
                    end_event.time AS end_time
                FROM 
                    flight_flight f
                CROSS JOIN flight_phase p
                LEFT JOIN flight_event_time start_event ON start_event.flight_id = f.id 
                    AND start_event.code_id = p.start_event_code_id
                    AND start_event.time_kind = 'A'
                LEFT JOIN flight_event_time end_event ON end_event.flight_id = f.id 
                    AND end_event.code_id = p.end_event_code_id
                    AND end_event.time_kind = 'A'
            )
            SELECT
                ROW_NUMBER() OVER () AS id,
                flight_id,
                phase_id,
                start_time,
                end_time,
                EXTRACT(EPOCH FROM (end_time - start_time)) / 3600.0 AS duration
            FROM phase_events
            WHERE start_time IS NOT NULL AND end_time IS NOT NULL
        )
        """)

    @api.model
    def refresh_view(self):
        self.init()

