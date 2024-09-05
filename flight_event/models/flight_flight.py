from odoo import api, models, fields
from odoo.exceptions import UserError


class FlightFlight(models.Model):
    _inherit = 'flight.flight'

    event_time_ids = fields.One2many('flight.event.time', 'flight_id', string='Event Times',
                                     tracking=True,
                                     copy=True)
    phase_duration_ids = fields.One2many('flight.phase.duration', 'flight_id',
                                          compute='_compute_phase_durations', store=True,
                                          string='Phase Durations')

    block_duration = fields.Float(string='Block Time',
                                   compute='_compute_block_flight_durations',
                                   help="Duration of the Block phase in hours", store=True,)
    flight_duration = fields.Float(string='Flight Time',
                                    compute='_compute_block_flight_durations',
                                    help="Duration of the Flight phase in hours",store=True,)

    @api.depends('event_time_ids', 'event_time_ids.time', 'event_time_ids.time_kind', 'event_time_ids.code_id')
    def _compute_phase_durations(self):
        PhaseDuration = self.env['flight.phase.duration']

        for flight in self:
            phases = self.env['flight.phase'].search([])
            phase_durations = PhaseDuration

            for phase in phases:
                start_event = flight.event_time_ids.filtered(
                    lambda
                        e: e.code_id == phase.start_event_code_id and e.time_kind == 'A'
                )
                end_event = flight.event_time_ids.filtered(
                    lambda
                        e: e.code_id == phase.end_event_code_id and e.time_kind == 'A'
                )

                if start_event and end_event and start_event.time and end_event.time:
                    phase_durations |= PhaseDuration.create({
                        'flight_id': flight.id,
                        'phase_id': phase.id,
                        'start_time': start_event.time,
                        'end_time': end_event.time,
                    })
            flight.phase_duration_ids = phase_durations

    @api.depends('phase_duration_ids.duration', 'phase_duration_ids.phase_id.name')
    def _compute_block_flight_durations(self):
        for flight in self:
            block_phase = flight.phase_duration_ids.filtered(lambda p: p.phase_id.name == 'Block')
            flight_phase = flight.phase_duration_ids.filtered(lambda p: p.phase_id.name == 'Flight')

            flight.block_duration = block_phase[0].duration if block_phase else 0.0
            flight.flight_duration = flight_phase[0].duration if flight_phase else 0.0

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
                            changes.append(f"{old_event_time.display_name}: {field} changed from {old_value} to {new_value or 'None'}")

                elif command[0] == 0:  # Create new record
                    new_values = command[2]
                    changes.append(f"Added: {new_values}")

                elif command[0] == 2:  # Delete record
                    deleted_event_time = self.env['flight.event.time'].browse(command[1])
                    changes.append(f"Removed: {deleted_event_time.display_name}")

            if changes:
                message = "Event Times Updated:<br>" + "<br>".join(changes)
                record.message_post(body=message)

    def write(self, vals):
        print('vals ', vals)
        if 'event_time_ids' in vals:
            self._track_event_time_changes(vals['event_time_ids'])
        return super(FlightFlight, self).write(vals)

