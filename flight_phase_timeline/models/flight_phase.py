from odoo import fields, models


class FlightPhaseDuration(models.Model):
    _inherit = "flight.phase.duration"

    # Add related fields with storage for timeline performance
    aircraft_id = fields.Many2one(
        "flight.aircraft",
        related="flight_id.aircraft_id",
        store=True,  # Store for better performance in timeline view
        readonly=True,
        index=True,
    )

    start_time = fields.Datetime(
        string="Start Time",
        related="start_event_id.time",
        readonly=True,
        store=True,  # Store for timeline performance
    )

    end_time = fields.Datetime(
        string="End Time",
        related="end_event_id.time",
        readonly=True,
        store=True,  # Store for timeline performance
    )
