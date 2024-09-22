from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError


class FlightFlight(models.Model):
    _inherit = 'flight.flight'

    event_time_ids = fields.One2many('flight.event.time', 'flight_id',
                                     string='Event Times',
                                     tracking=True,
                                     copy=True)
    phase_duration_ids = fields.One2many('flight.phase.duration', 'flight_id',
                                         compute='_compute_phase_durations', store=True,
                                         string='Phase Durations')

    block_duration = fields.Float(string='Block Duration',
                                  compute='_compute_block_and_flight_duration',
                                  store=False)
    flight_duration = fields.Float(string='Flight Duration',
                                   compute='_compute_block_and_flight_duration',
                                   store=False)

    @api.constrains('event_time_ids')
    def _check_event_sequence(self):
        """
        Constraint method to ensure event times are in the correct sequence.
        Raises a ValidationError if any event time is out of order.
        """
        for flight in self:
            latest_times = {}
            for event in flight.event_time_ids.sorted(
                    key=lambda r: r.code_id.sequence):
                if event.time_kind in latest_times and event.time < latest_times[
                    event.time_kind]:
                    raise ValidationError(_(
                        "Invalid event sequence: %(event)s (%(time_kind)s) is out of order.",
                        event=event.code_id.name,
                        time_kind=event.time_kind
                    ))
                latest_times[event.time_kind] = event.time

    @api.depends('event_time_ids', 'event_time_ids.time', 'event_time_ids.code_id')
    def _compute_phase_durations(self):
        """
        Compute method to calculate phase durations for each flight.
        Orchestrates the duration calculation by processing existing
        durations and cleaning up outdated ones.
        """
        for flight in self:
            updated_phase_durations = flight._process_existing_durations()
            flight._cleanup_outdated_durations(updated_phase_durations)

    def _process_existing_durations(self):
        """
        Processes and updates or creates phase durations for the given flight.
        Focuses on existing events to calculate durations.
        Returns a list of updated phase durations.
        """
        updated_phase_durations = []
        # Fetch only phases that have matching start or end events in event_time_ids
        relevant_phases = self._get_relevant_phases_from_events()

        # Iterate over all phases and time kinds to calculate durations for existing events
        for phase in relevant_phases:
            for time_kind in set(self.event_time_ids.mapped('time_kind')):
                start_event = self.event_time_ids.filter_event_time(
                    phase.start_event_code_id, time_kind)
                end_event = self.event_time_ids.filter_event_time(
                    phase.end_event_code_id, time_kind)

                if start_event and end_event and start_event.time and end_event.time:
                    # Calculate duration and update/create duration record
                    self.env['flight.phase.duration'].update_or_create_duration(
                        self.id, phase.id, time_kind, start_event.time, end_event.time
                    )

                    # Track the phase and time kind processed
                    updated_phase_durations.append((phase.id, time_kind))

        return updated_phase_durations

    def _get_relevant_phases_from_events(self):
        """
        Get phases that have matching start or end events in the flight's event_time_ids.
        Returns a recordset of relevant phases.
        """
        event_codes = self.event_time_ids.mapped('code_id')

        relevant_phases = self.env['flight.phase'].search([
            '|',
            ('start_event_code_id', 'in', event_codes.ids),
            ('end_event_code_id', 'in', event_codes.ids)
        ])

        return relevant_phases

    def _cleanup_outdated_durations(self, updated_phase_durations):
        """
        Removes outdated phase duration records that were not updated.
        """
        PhaseDuration = self.env['flight.phase.duration']


        # Search for all existing phase durations for this flight
        existing_durations = PhaseDuration.search([('flight_id', '=', self.id)])

        # Unlink any duration records that were not updated
        for duration in existing_durations:
            duration_info = (duration.phase_id.id, duration.time_kind)
            if duration_info not in updated_phase_durations:
                duration.unlink()

    def get_duration(self, phase_name, time_kind):
        """
        Get the duration for a specific phase and time kind.
        Returns the duration or 0 if not found.
        """
        pd_id = self.phase_duration_ids.filtered(lambda pd_id:
                                                 pd_id.time_kind == time_kind
                                                 and pd_id.phase_id.name == phase_name)

        return pd_id.duration or 0

    @api.depends('phase_duration_ids')
    def _compute_block_and_flight_duration(self):
        """
        Compute method to calculate block and flight durations.
        """
        for flight in self:
            flight.block_duration = flight.get_duration('Block', 'A')
            flight.flight_duration = flight.get_duration('Flight', 'A')

    def _track_event_time_changes(self, event_time_vals):
        for record in self:
            changes = []
            for command in event_time_vals:
                if command[0] == 1:  # Update existing record
                    event_time_id = command[1]
                    new_values = command[2]
                    old_event_time = self.env['flight.event.time'].browse(event_time_id)

                    for field, new_value in new_values.items():
                        old_value = old_event_time[field]
                        if old_value != new_value:
                            changes.append(
                                f"{old_event_time.display_name}: {field} changed from {old_value} to {new_value or 'None'}")

                elif command[0] == 0:  # Create new record
                    new_values = command[2]
                    changes.append(f"Added: {new_values}")

                elif command[0] == 2:  # Delete record
                    deleted_event_time = self.env['flight.event.time'].browse(
                        command[1])
                    changes.append(f"Removed: {deleted_event_time.display_name}")

            if changes:
                message = "Event Times Updated:<br>" + "<br>".join(changes)
                record.message_post(body=message)

    def write(self, vals):
        """
        Override the write method to track changes in event times.
        """
        if 'event_time_ids' in vals:
            self._track_event_time_changes(vals['event_time_ids'])
        return super(FlightFlight, self).write(vals)
