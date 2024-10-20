import json

from odoo import api, fields, models


class FlightFlight(models.Model):
    _inherit = "flight.flight"

    event_time_ids = fields.One2many(
        "flight.event.time", "flight_id", string="Event Times", tracking=True
    )
    durations = fields.Json(compute="_compute_durations", store=False)

    @api.depends(
        "event_time_ids.time", "event_time_ids.code_id", "event_time_ids.time_kind"
    )
    def _compute_durations(self):
        Phase = self.env["flight.phase"]
        phases = Phase.search([])
        time_kinds = dict(self.env["flight.event.time"]._fields["time_kind"].selection)

        for flight in self:
            durations = {}
            for phase in phases:
                for time_kind in time_kinds:
                    field_name = (
                        f"{phase.name.lower().replace(' ', '_')}_{time_kind.lower()}"
                    )
                    start_time = flight.event_time_ids.filtered(
                        lambda et: et.code_id == phase.start_event_code_id
                        and et.time_kind == time_kind
                    )
                    end_time = flight.event_time_ids.filtered(
                        lambda et: et.code_id == phase.end_event_code_id
                        and et.time_kind == time_kind
                    )
                    if start_time and end_time:
                        # Take the first record if multiple exist
                        duration = (
                            end_time[0].time - start_time[0].time
                        ).total_seconds() / 3600
                        durations[field_name] = duration
                    else:
                        durations[field_name] = 0.0

            # Set specific durations
            durations["block"] = durations.get("block_a", 0.0) or durations.get(
                "block_s", 0.0
            )
            durations["flight"] = durations.get("flight_a", 0.0) or durations.get(
                "flight_s", 0.0
            )

            flight.durations = json.dumps(durations)

    # Helper method to get duration values
    def get_duration(self, duration_name):
        self.ensure_one()
        durations = json.loads(self.durations or "{}")
        return durations.get(duration_name, 0.0)

    @api.depends("durations")
    def _compute_block_duration(self):
        for flight in self:
            flight.block_duration = flight.get_duration("block")

    @api.depends("durations")
    def _compute_flight_duration(self):
        for flight in self:
            flight.flight_duration = flight.get_duration("flight")

    block_duration = fields.Float(
        string="Block Duration", compute="_compute_block_duration", store=False
    )
    flight_duration = fields.Float(
        string="Flight Duration", compute="_compute_flight_duration", store=False
    )

    def write(self, vals):
        if "event_time_ids" in vals:
            self._track_event_time_changes(vals["event_time_ids"])
        result = super(FlightFlight, self).write(vals)
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
