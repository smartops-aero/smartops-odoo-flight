from odoo import api, fields, models


class ImportPipelineResult(models.Model):
    _name = "base.import.pipeline.result"
    _description = "Import Pipeline Result"
    _order = "date desc, id desc"
    
    pipeline_id = fields.Many2one('base.import.pipeline', string='Pipeline', required=True, ondelete='cascade')
    date = fields.Datetime(string='Import Date', required=True)
    summary = fields.Text(string='Summary')
    records_created = fields.Integer(string='Records Created', default=0)
    status = fields.Selection([
        ('success', 'Success'),
        ('error', 'Error'),
    ], string='Status', required=True)
    log = fields.Text(string='Log')
