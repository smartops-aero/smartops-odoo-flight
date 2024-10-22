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

    def write(self, vals):
        if "event_time_ids" in vals:
            self._track_event_time_changes(vals["event_time_ids"])
        result = super().write(vals)
        return result

    def _track_event_time_changes(self, event_time_vals):
        for record in self:
            changes = []
            for command in event_time_vals:
                if command[0] == 1:  # Update existing record
                    event_time_id = command[1]
                    new_values = command[2]
                    old_event_time = self.env["flight.event.time"].browse(event_time_id)

                    for field, new_value in new_values.items():
                        old_value = old_event_time[field]
                        if old_value != new_value:
                            changes.append(
                                f"{old_event_time.display_name}: {field} changed from {old_value} to {new_value or 'None'}"
                            )

                elif command[0] == 0:  # Create new record
                    new_values = command[2]
                    changes.append(f"Added: {new_values}")

                elif command[0] == 2:  # Delete record
                    deleted_event_time = self.env["flight.event.time"].browse(
                        command[1]
                    )
                    changes.append(f"Removed: {deleted_event_time.display_name}")

            if changes:
                message = "Event Times Updated:<br>" + "<br>".join(changes)
                record.message_post(body=message)

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

    def _find_matching_end_event(self, flight, phase, time_kind):
        return flight.event_time_ids.filtered(
            lambda e: e.code_id == phase.end_event_code_id and e.time_kind == time_kind
        )
