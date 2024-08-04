from odoo import models, fields, api
from odoo.exceptions import UserError


class FlightFlight(models.Model):
    _inherit = 'flight.flight'

    event_time_ids = fields.One2many('flight.event.time', 'flight_id', string='Event Times', tracking=True)
    phase_duration_ids = fields.One2many('flight.phase.duration', 'flight_id', string='Phase Durations')


class FlightFlight(models.Model):
    _inherit = 'flight.flight'

    event_time_ids = fields.One2many('flight.event.time', 'flight_id', string='Event Times', tracking=True)
    phase_duration_ids = fields.One2many('flight.phase.duration', 'flight_id', string='Phase Durations')

    block_duration = fields.Float(string='Block Time', compute='_compute_phase_durations', store=True, help="Duration of the Block phase in hours")
    flight_duration = fields.Float(string='Flight Time', compute='_compute_phase_durations', store=True, help="Duration of the Flight phase in hours")

    @api.depends('phase_duration_ids.duration', 'phase_duration_ids.phase_id.name')
    def _compute_phase_durations(self):
        for flight in self:
            block_phase = flight.phase_duration_ids.filtered(lambda p: p.phase_id.name == 'Block')
            flight_phase = flight.phase_duration_ids.filtered(lambda p: p.phase_id.name == 'Flight')

            flight.block_duration = block_phase[0].duration if block_phase else 0.0
            flight.flight_duration = flight_phase[0].duration if flight_phase else 0.0

    def write(self, vals):
        if 'event_time_ids' in vals:
            self._track_event_time_changes(vals['event_time_ids'])
        result = super(FlightFlight, self).write(vals)
        if 'event_time_ids' in vals:
            self.env['flight.phase.duration'].refresh_view()
        return result

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
