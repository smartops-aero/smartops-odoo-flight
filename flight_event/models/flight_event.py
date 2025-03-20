from datetime import datetime

from odoo import api, fields, models
from odoo.exceptions import UserError


class FlightEventCode(models.Model):
    _name = "flight.event.code"
    _description = "Flight Event Code"
    _rec_name = "code"
    _order = "sequence, id"

    code = fields.Char(required=True)
    name = fields.Char(required=True)
    description = fields.Char()
    sequence = fields.Integer(default=10)

    start_phase_ids = fields.One2many(
        "flight.phase", "start_event_code_id", string="Starts Phases"
    )
    end_phase_ids = fields.One2many(
        "flight.phase", "end_event_code_id", string="Ends Phases"
    )

    _sql_constraints = [
        ("code_unique", "unique(code)", "The event code must be unique!"),
    ]


EVENT_TIME_KINDS = [
    ("A", "Actual"),
    ("S", "Scheduled"),
    ("R", "Requested"),
    ("T", "Target"),
    ("E", "Estimated"),
]


class FlightEventTimeHistory(models.Model):
    _name = "flight.event.time.history"
    _description = "Flight Event Time Change History"
    _order = "write_date DESC"
    _log_access = False

    event_id = fields.Many2one(
        "flight.event.time",
        required=True,
        ondelete="cascade",
        index=True,
    )
    time = fields.Datetime()
    write_uid = fields.Many2one("res.users", required=True, index=True)
    write_date = fields.Datetime(required=True)


class FlightEventTime(models.Model):
    _name = "flight.event.time"
    _description = "Flight Event Time"
    _order = "code_id, time_kind"
    _inherit = ["flight.lock.mixin"]

    flight_id = fields.Many2one(
        "flight.flight", required=True, index=True, ondelete="cascade"
    )
    aircraft_id = fields.Many2one(
        "flight.aircraft",
        related="flight_id.aircraft_id",
        string="Aircraft",
        index=True,
    )
    code_id = fields.Many2one(
        "flight.event.code",
        "Flight Event Code",
        required=True,
        index=True,
    )
    code_name = fields.Char(string="Code Name", related="code_id.name")
    time_kind = fields.Selection(
        EVENT_TIME_KINDS,
        "Time Kind",
        default="A",
        required=True,
        index=True,
    )
    time = fields.Datetime()
    display_time = fields.Char(compute="_compute_display_time")

    start_phase_ids = fields.One2many(
        "flight.phase", related="code_id.start_phase_ids", string="Starts Phases"
    )
    end_phase_ids = fields.One2many(
        "flight.phase", related="code_id.end_phase_ids", string="Ends Phases"
    )
    start_durations_ids = fields.One2many(
        "flight.phase.duration", "start_event_id", string="Starts Durations"
    )
    end_durations_ids = fields.One2many(
        "flight.phase.duration", "end_event_id", string="Ends Durations"
    )

    history_ids = fields.One2many(
        "flight.event.time.history", "event_id", string="History Records"
    )
    has_history = fields.Boolean(compute="_compute_has_history")

    @api.depends("history_ids")
    def _compute_has_history(self):
        for record in self:
            record.has_history = bool(record.history_ids)

    def write(self, vals):
        # Only allow updating the 'time' field
        if set(vals.keys()) - {"time"}:
            raise UserError("Only the time field can be modified after creation")

        history_vals = []
        for record in self:
            if record.time != vals["time"]:
                history_vals.append(
                    {
                        "event_id": record.id,
                        "time": record.time,
                        "write_uid": record.write_uid.id,
                        "write_date": record.write_date,
                    }
                )

        if history_vals:
            self.env["flight.event.time.history"].create(history_vals)

        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        self._create_phase_durations(records)
        return records

    def _create_phase_durations(self, new_events):
        FlightPhaseDuration = self.env["flight.phase.duration"]
        durations_to_create = []

        # Group events by flight to process all events for each flight together
        events_by_flight = {}
        for event in new_events:
            events_by_flight.setdefault(event.flight_id, []).append(event)

        for flight, flight_events in events_by_flight.items():
            # Get existing phase durations for this flight to avoid duplicates
            existing_durations = set(
                (d.flight_id.id, d.phase_id.id, d.time_kind)
                for d in flight.phase_duration_ids
            )

            # Process all new events for this flight
            for event in flight_events:
                # Check phases that this event starts
                for phase in event.start_phase_ids:
                    end_event = self._find_matching_end_event(
                        flight, phase, event.time_kind
                    )
                    if (
                        end_event
                        and (flight.id, phase.id, event.time_kind)
                        not in existing_durations
                    ):
                        durations_to_create.append(
                            {
                                "flight_id": flight.id,
                                "phase_id": phase.id,
                                "start_event_id": event.id,
                                "end_event_id": end_event.id,
                                "time_kind": event.time_kind,
                            }
                        )
                        existing_durations.add((flight.id, phase.id, event.time_kind))

                # Check phases that this event ends
                for phase in event.end_phase_ids:
                    start_event = self._find_matching_start_event(
                        flight, phase, event.time_kind
                    )
                    if (
                        start_event
                        and (flight.id, phase.id, event.time_kind)
                        not in existing_durations
                    ):
                        durations_to_create.append(
                            {
                                "flight_id": flight.id,
                                "phase_id": phase.id,
                                "start_event_id": start_event.id,
                                "end_event_id": event.id,
                                "time_kind": event.time_kind,
                            }
                        )
                        existing_durations.add((flight.id, phase.id, event.time_kind))

        # Create all durations in a single batch operation
        if durations_to_create:
            FlightPhaseDuration.create(durations_to_create)

    def _find_matching_end_event(self, flight, phase, time_kind):
        return flight.event_time_ids.filtered(
            lambda e: e.code_id == phase.end_event_code_id and e.time_kind == time_kind
        )

    def _find_matching_start_event(self, flight, phase, time_kind):
        return flight.event_time_ids.filtered(
            lambda e: e.code_id == phase.start_event_code_id
            and e.time_kind == time_kind
        )

    @api.depends("time", "flight_id.date")
    def _compute_display_time(self):
        # display time portion only HH:MM but append +/- days difference with the flight
        # e.g. 01:15+1 - landing time next day
        # self.time.date - self.flight_id.date => append after time or skip if same / 0
        for record in self:
            if not record.time or not record.flight_id.date:
                record.display_time = ""
                continue

            time_str = record.time.strftime("%H:%M")
            flight_date = datetime.combine(record.flight_id.date, datetime.min.time())
            days = (record.time - flight_date).days
            if days > 0:
                time_str += f" (+{days})"
            elif days < 0:
                time_str += f" (-{days})"
            record.display_time = time_str

    @api.depends("time_kind", "code_id.code", "display_time")
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.time_kind}{record.code_id.code}T {record.display_time}".upper()

    def action_view_time_changes(self):
        self.ensure_one()
        return {
            "name": f"Time Changes - {self.display_name}",
            "type": "ir.actions.act_window",
            "res_model": "flight.event.time.history",
            "view_mode": "tree",
            "views": [[False, "tree"]],
            "domain": [("event_id", "=", self.id)],
            "target": "new",
            "context": {"create": False},
        }
