# Copyright 2023 Apexive Solutions LLC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval
from dateutil.relativedelta import relativedelta


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
    def _selection_sync_model(self):
        return self._get_available_sync_models()

    def _sync(self, schedule):
        self.ensure_one()
        try:
            kwargs = safe_eval(schedule.kwargs or "{}")

            # Receive data
            received_data = self._receive_flight_data(schedule, **kwargs)
            self._process_received_flight_data(schedule, received_data)

            # Send data
            data_to_send = self._prepare_data_to_send(schedule, **kwargs)
            self._send_flight_data(schedule, data_to_send, **kwargs)

            schedule.write({
                'last_run': fields.Datetime.now(),
                'last_success': fields.Datetime.now(),
            })
            self.message_post(body=_("Data sync successful for schedule: %s") % schedule.name)
        except Exception as e:
            schedule.write({'last_run': fields.Datetime.now()})
            self.message_post(body=_("Error in schedule %s: %s") % (schedule.name, str(e)))

    def _receive_flight_data(self, schedule, **kwargs):
        # This method should be implemented in provider-specific subclasses
        return []

    def _process_received_flight_data(self, schedule, data):
        Model = self.env[schedule.model]
        for item in data:
            # Assume each item has a unique identifier field 'external_id'
            existing = Model.search([('external_id', '=', item['external_id'])])
            if existing:
                existing.write(item)
            else:
                Model.create(item)

    def _prepare_data_to_send(self, schedule, **kwargs):
        # This method should be implemented in provider-specific subclasses
        return []

    def _send_flight_data(self, schedule, data, **kwargs):
        # This method should be implemented in provider-specific subclasses
        pass


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
