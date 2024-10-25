import json

from odoo import api, fields, models


class FlightFlight(models.Model):
    _inherit = "flight.flight"

    event_time_ids = fields.One2many(
        "flight.event.time", "flight_id", string="Event Times", tracking=True
    )

    phase_duration_ids = fields.One2many(
        "flight.phase.duration", "flight_id", string="Phase Durations"
    )

    block_duration = fields.Float(
        string="Block Duration",
        compute="_compute_durations",
        store=True,
    )

    flight_duration = fields.Float(
        string="Flight Duration",
        compute="_compute_durations",
        store=True,
    )

    @api.depends(
        "phase_duration_ids",
        "phase_duration_ids.duration",
        "phase_duration_ids.phase_id",
        "phase_duration_ids.time_kind",
    )
    def _compute_durations(self):
        for flight in self:
            actual_durations = flight.phase_duration_ids.filtered(
                lambda d: d.time_kind == "A"
            )
            flight.block_duration = actual_durations.filtered(
                lambda d: d.phase_id.name == "Block"
            ).duration
            flight.flight_duration = actual_durations.filtered(
                lambda d: d.phase_id.name == "Flight"
            ).duration

    def _get_event_time(self, code_id, time_kind):
        event_times = self.event_time_ids.filtered(
            lambda et: et.code_id == code_id and et.time_kind == time_kind
        )
        return event_times[0] if event_times else None

    def _find_matching_end_event(self, flight, phase, time_kind):
        return flight.event_time_ids.filtered(
            lambda e: e.code_id == phase.end_event_code_id and e.time_kind == time_kind
        )

    def create_missing_phase_durations(self):
        FlightPhaseDuration = self.env["flight.phase.duration"]

        for flight in self:
            # Get all events for the current flight that start a phase and are not already linked to phase durations
            start_events = flight.event_time_ids.filtered(
                lambda e: e.start_phase_ids and not e.start_durations_ids
            )

            new_durations = []
            for event in start_events:
                for phase in event.start_phase_ids:
                    end_event = self._find_matching_end_event(
                        flight, phase, event.time_kind
                    )
                    if end_event:
                        new_durations.append(
                            {
                                "flight_id": flight.id,
                                "phase_id": phase.id,
                                "start_event_id": event.id,
                                "end_event_id": end_event.id,
                                "time_kind": event.time_kind,
                            }
                        )

            # Create new phase durations in batch
            if new_durations:
                FlightPhaseDuration.create(new_durations)

    def write(self, vals):
        result = super().write(vals)

        if "event_time_ids" in vals:
            self._log_event_time_changes(vals["event_time_ids"])
        return result

    def _format_display_time(self, time_value, flight_date):
        """Format time value with day offset relative to flight date."""
        if not time_value:
            return ""

        time_str = time_value.strftime("%H:%M")
        days = (time_value.date() - flight_date).days
        if days > 0:
            time_str += f" (+{days})"
        elif days < 0:
            time_str += f" ({days})"
        return time_str

    def _log_event_time_changes(self, event_time_vals):
        """Log changes to event times using a single optimized query."""
        for record in self:
            tracking = []

            # Extract IDs and new values from commands
            updates = {}
            deletes = []

            for command in event_time_vals:
                if command[0] == 1 and "time" in command[2]:  # Update
                    updates[str(command[1])] = command[2]["time"]
                elif command[0] == 2:  # Delete
                    deletes.append(command[1])
                elif command[0] == 0:  # Create
                    new_time = fields.Datetime.from_string(command[2].get("time"))
                    new_display = self._format_display_time(new_time, record.date)
                    event_code_display = f"{command[2].get('time_kind')}{self.env['flight.event.code'].browse(command[2].get('code_id')).code}T"
                    tracking.append(f"* → {new_display} ({event_code_display})")

            # Process updates and deletes if any exist
            event_ids = list(map(int, updates.keys())) + deletes
            if event_ids:
                query = """
                    WITH event_changes AS (
                        SELECT
                            fet.id as event_id,
                            fet.time_kind,
                            fec.code as event_code,
                            COALESCE(feth.time, fet.time) as old_time,
                            CASE
                                WHEN fet.id = ANY(%(delete_ids)s) THEN NULL
                                ELSE (%(updates)s::jsonb->>fet.id::text)::timestamp
                            END as new_time
                        FROM
                            flight_event_time fet
                            JOIN flight_event_code fec ON fet.code_id = fec.id
                            LEFT JOIN LATERAL (
                                SELECT time
                                FROM flight_event_time_history feth
                                WHERE feth.event_id = fet.id
                                ORDER BY write_date DESC
                                LIMIT 1
                            ) feth ON true
                        WHERE
                            fet.id = ANY(%(event_ids)s)
                    )
                    SELECT
                        event_id,
                        time_kind,
                        event_code,
                        old_time,
                        new_time
                    FROM
                        event_changes
                    WHERE
                        old_time IS DISTINCT FROM new_time
                    ORDER BY
                        event_id
                """

                self.env.cr.execute(
                    query,
                    {
                        "event_ids": event_ids,
                        "delete_ids": deletes,
                        "updates": json.dumps(updates),
                    },
                )

                # Process existing events (updates and deletes)
                for (
                    event_id,
                    time_kind,
                    event_code,
                    old_time,
                    new_time,
                ) in self.env.cr.fetchall():
                    if event_id:
                        old_display = (
                            self._format_display_time(old_time, record.date)
                            if old_time
                            else ""
                        )
                        new_display = (
                            self._format_display_time(new_time, record.date)
                            if new_time
                            else ""
                        )
                        event_code_display = f"{time_kind}{event_code}T"

                        if new_time is None:  # Delete
                            tracking.append(f"* {old_display} → ({event_code_display})")
                        else:  # Update
                            tracking.append(
                                f"* {old_display} → {new_display} ({event_code_display})"
                            )

            if tracking:
                body = "\n".join(tracking)
                self.message_post(
                    body=body,
                )
