# Copyright 2023 Apexive Solutions LLC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from functools import partial

import logging
import traceback
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.safe_eval import safe_eval
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class FlightDataProvider(models.Model):
    _name = "flight.data.provider"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Flight Data Provider"

    name = fields.Char(required=True)
    service = fields.Selection(
        selection=lambda self: self._selection_service(),
        required=True,
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    api_base = fields.Char()
    username = fields.Char()
    password = fields.Char()
    schedule_ids = fields.One2many(
        'flight.data.sync.schedule', 'provider_id',
        string='Sync Schedules', context={'active_test': False},
    )

    user_id = fields.Many2one('res.users', string='Run As User',
                              help="If set, schedules will run as this user. Otherwise, they will run as the current user.")

    @api.model
    def _get_available_services(self):
        """Hook for extension"""
        return []

    @api.model
    def _selection_service(self):
        return self._get_available_services() + [("dummy", "Dummy")]

    @api.model
    def _get_available_sync_models(self):
        """Hook for extension"""
        return [
            ('flight.flight', 'Flights'),
            ('flight.crew', 'Crew'),
            ('flight.aerodrome', 'Aerodromes'),
            ('flight.aircraft', 'Aircraft'),
        ]

    @api.model
    def _get_available_sync_operations(self):
        """Hook for extension"""
        return ['receive', 'process', 'prepare', 'send']

    @api.model
    def _selection_sync_model(self):
        return self._get_available_sync_models()

    def get_client(self, schedule):
        return self._raise_not_implemented("get_client")

    def _sync(self, schedule):
        _logger.info(f"Starting _sync for provider: {self.name}")
        self.ensure_one()

        try:
            kwargs = safe_eval(schedule.kwargs or "{}")

            # Use sudo() if user_id is set, otherwise use self
            provider = self
            if self.user_id:
                provider = provider.sudo().with_user(self.user_id)

            # Receive data
            received_data = provider.receive_data(schedule, **kwargs)
            provider.process_data(schedule, received_data)

            # Send data
            data_to_send = provider.prepare_data(schedule, **kwargs)
            provider.send_data(schedule, data_to_send, **kwargs)

            schedule.write({
                'last_run': fields.Datetime.now(),
                'last_success': fields.Datetime.now(),
            })
            provider.message_post(body=_("Data sync successful for schedule: %s") % schedule.name)
        except Exception as e:
            _logger.exception(f"Error in _sync method: {str(e)}")
            schedule.write({'last_run': fields.Datetime.now()})
            self.message_post(body=_("Error in schedule %s: %s") % (schedule.name, str(e)))


    def _dispatch(self, schedule, operation, *args, **kwargs):
        method_name = f"_{operation}_{schedule.model.replace('flight.', '')}_data"
        method = getattr(self, method_name, False)

        if not method:
            raise NotImplementedError(f"Method '{method_name}' not implemented")

        self.ensure_one()
        client = self.get_client(schedule)

        try:
            return partial(method, client, schedule, *args, **kwargs)()
        except Exception as e:
            print(traceback.format_exc())
            _logger.error(f"Error trying to {operation} {schedule.model} data for {self.service}: %s", e)
            raise UserError(_(f"Error trying to {operation} {schedule.model} data for {self.service}: %s") % e)

    def receive_data(self, schedule, **kwargs):
        return self._dispatch(schedule, "receive", **kwargs)

    def process_data(self, schedule, data):
        return self._dispatch(schedule, "process", data)

    def prepare_data(self, schedule, **kwargs):
        return self._dispatch(schedule, "prepare", **kwargs)

    def send_data(self, schedule, data, **kwargs):
        return self._dispatch(schedule, "send", data, **kwargs)

    def _update_or_create(self, model, search_domain, values):
        record = model.search(search_domain, limit=1)
        if not record:
            return model.create(values)
        record.ensure_one()
        record.write(values)
        return record

    def _raise_not_implemented(self, method_name):
        raise NotImplementedError(f"Method '{method_name}' not implemented for service {self.service[1]}")

    def _receive_flight_data(self, client, schedule, *args, **kwargs):
        self._raise_not_implemented("_receive_flight_data")

    def _process_flight_data(self, client, schedule, data, *args, **kwargs):
        self._raise_not_implemented("_process_flight_data")

    def _prepare_flight_data(self, client, schedule, *args, **kwargs):
        self._raise_not_implemented("_prepare_flight_data")

    def _send_flight_data(self, client, schedule, data, *args, **kwargs):
        self._raise_not_implemented("_send_flight_data")

    def _receive_aerodrome_data(self, client, schedule, *args, **kwargs):
        self._raise_not_implemented("_receive_aerodrome_data")

    def _process_aerodrome_data(self, client, schedule, data, *args, **kwargs):
        self._raise_not_implemented("_process_aerodrome_data")

    def _prepare_aerodrome_data(self, client, schedule, *args, **kwargs):
        self._raise_not_implemented("_prepare_aerodrome_data")

    def _send_aerodrome_data(self, client, schedule, data, *args, **kwargs):
        self._raise_not_implemented("_send_aerodrome_data")

    def _receive_crew_data(self, client, schedule, *args, **kwargs):
        self._raise_not_implemented("_receive_crew_data")

    def _process_crew_data(self, client, schedule, data, *args, **kwargs):
        self._raise_not_implemented("_process_crew_data")

    def _prepare_crew_data(self, client, schedule, *args, **kwargs):
        self._raise_not_implemented("_prepare_crew_data")

    def _send_crew_data(self, client, schedule, data, *args, **kwargs):
        self._raise_not_implemented("_send_crew_data")

    def _receive_aircraft_data(self, client, schedule, *args, **kwargs):
        self._raise_not_implemented("_receive_aircraft_data")

    def _process_aircraft_data(self, client, schedule, data, *args, **kwargs):
        self._raise_not_implemented("_process_aircraft_data")

    def _prepare_aircraft_data(self, client, schedule, *args, **kwargs):
        self._raise_not_implemented("_prepare_aircraft_data")

    def _send_aircraft_data(self, client, schedule, data, *args, **kwargs):
        self._raise_not_implemented("_send_aircraft_data")


class FlightDataSyncSchedule(models.Model):
    _name = "flight.data.sync.schedule"
    _description = "Flight Data Sync Schedule"

    name = fields.Char(required=True)
    provider_id = fields.Many2one('flight.data.provider', string='Provider', required=True, ondelete='cascade')
    model = fields.Selection(
        selection=lambda self: self.env['flight.data.provider']._selection_sync_model(),
        string='Flight Data Model',
        required=True
    )
    active = fields.Boolean(default=True)
    interval_number = fields.Integer(string="Run every", default=1, required=True)
    interval_type = fields.Selection([
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('days', 'Days'),
        ('weeks', 'Weeks')
    ], string='Interval Unit', default='hours', required=True)
    kwargs = fields.Text(string='Additional Parameters', help="Python dictionary stored as a string. These parameters will be passed to the data sync methods.")
    last_run = fields.Datetime(string='Last Run')
    last_success = fields.Datetime(string='Last Successful Run')
    next_run = fields.Datetime(string='Next Run', compute='_compute_next_run')

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.provider_id.name} ({record.provider_id.service}): {record.name}"
            result.append((record.id, name))
        return result

    def action_view_logs(self):
        self.ensure_one()
        return {
            'name': _('Sync Logs'),
            'res_model': 'flight.data.sync.log',
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
            'domain': [('schedule_id', '=', self.id)],
            'context': {'default_schedule_id': self.id},
        }

    @api.depends('last_run', 'interval_number', 'interval_type')
    def _compute_next_run(self):
        for schedule in self:
            if schedule.last_run:
                schedule.next_run = schedule.last_run + relativedelta(
                    **{schedule.interval_type: schedule.interval_number}
                )
            else:
                schedule.next_run = fields.Datetime.now()

    @api.constrains('kwargs')
    def _check_kwargs(self):
        for record in self:
            if record.kwargs:
                try:
                    safe_eval(record.kwargs)
                except Exception as e:
                    raise ValidationError(_("Invalid kwargs: %s") % str(e))

    @api.onchange('model')
    def _onchange_model(self):
        if self.model:
            self.name = dict(self.env['flight.data.provider']._selection_sync_model())[self.model]


class FlightDataSyncLog(models.Model):
    _name = "flight.data.sync.log"
    _description = "Flight Data Sync Log"
    _order = "timestamp desc"

    timestamp = fields.Datetime(default=fields.Datetime.now, required=True)
    schedule_id = fields.Many2one('flight.data.sync.schedule', string='Sync Schedule', required=True)
    direction = fields.Selection([('inbound', 'Inbound'), ('outbound', 'Outbound')], required=True)
    headers = fields.Text(string='Headers')
    body = fields.Text(string='Body')

    schedule_name = fields.Char(related='schedule_id.name', string='Schedule Name', store=False, readonly=True)
