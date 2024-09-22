# Copyright 2024 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).
from datetime import datetime
from odoo import api, fields, models


class FlightEventTime(models.Model):
    """
    All events times are in UTC
    """
    _name = 'flight.event.time'
    _description = 'Flight Event Time'
    _order = 'code_id, time_kind'

    flight_id = fields.Many2one('flight.flight', required=True, index=True,
                                ondelete='cascade')
    code_id = fields.Many2one('flight.event.code', 'Flight Event Code', required=True,
                              index=True)
    code_name = fields.Char(string='Code Name', related='code_id.name')

    time_kind = fields.Selection([
        ("A", "Actual"),
        ("S", "Scheduled"),
        ("R", "Requested"),
        ("T", "Target"),
        ("E", "Estimated"),
    ], "Time Kind", default="A", required=True, index=True)

    time = fields.Datetime()
    # time = fields.Char()
    display_time = fields.Char(compute="_compute_display_time")

    @api.depends("time", "flight_id.date")
    def _compute_display_time(self):
        # display time portion only HH:MM but append +/- days difference with the flight
        # e.g. 01:15+1 - landing time next day
        # self.time.date - self.flight_id.date => append after time or skip if same / 0
        for record in self:
            if not record.time or not record.flight_id.date:
                record.display_time = ''
                continue

            time_str = record.time.strftime('%H:%M')
            flight_date = datetime.combine(record.flight_id.date, datetime.min.time())
            days = (record.time - flight_date).days
            if days > 0:
                time_str += f' (+{days})'
            elif days < 0:
                time_str += f' (-{days})'
            record.display_time = time_str

    @api.depends("time_kind", "code_id.code", "display_time")
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.time_kind}{record.code_id.code}T {record.display_time}".upper()

    @api.model
    def open_edit_form(self, event_time_id):
        if not event_time_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'flight.event.time',
                'view_mode': 'form',
                'view_type': 'form',
                'views': [(False, 'form')],
                'target': 'new',
                'context': self.env.context,
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'flight.event.time',
                'res_id': event_time_id,
                'view_mode': 'form',
                'view_type': 'form',
                'views': [(False, 'form')],
                'target': 'new',
            }

    @api.model
    def filter_event_time(self, code_id, time_kind):
        """
        Filter event times based on the given code ID and time kind.
        Returns:
        recordset: A recordset of `flight.event.time` records that match the given code ID and time kind.
        """
        return self.filtered(lambda e: e.code_id == code_id and
                                       e.time_kind == time_kind)
