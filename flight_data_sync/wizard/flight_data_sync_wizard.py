from odoo import fields, models, api


class FlightDataSyncWizard(models.TransientModel):
    _name = "flight.data.sync.wizard"
    _description = "Flight Data Sync Wizard"

    provider_id = fields.Many2one('flight.data.provider', string="Provider", required=True)
    schedule_ids = fields.Many2many('flight.data.sync.schedule', string="Schedules to Sync",
                                    required=True, domain=['|', ('active', '=', True), ('active', '=', False)])

    @api.onchange('provider_id')
    def _onchange_provider_id(self):
        self.schedule_ids = False
        return {'domain': {'schedule_ids': [('provider_id', '=', self.provider_id.id)]}}

    def action_sync(self):
        self.ensure_one()
        for schedule in self.schedule_ids:
            self.provider_id._sync(schedule)
        return {'type': 'ir.actions.act_window_close'}
