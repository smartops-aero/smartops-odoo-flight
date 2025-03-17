from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ImportWizard(models.TransientModel):
    _name = "import.wizard"
    _description = "Import Wizard"
    
    pipeline_id = fields.Many2one('base.import.pipeline', string='Import Pipeline', required=True,
                                 domain=[('active', '=', True)])
    file = fields.Binary(string='File', required=True)
    filename = fields.Char(string='Filename')
    delimiter = fields.Char(string='Delimiter', default=',', required=True)
    
    def action_import(self):
        """Run the import pipeline with the selected file"""
        self.ensure_one()
        
        if not self.file:
            raise UserError(_("You must select a file to import"))
        
        # Update delimiter on the pipeline if it's an ETL pipeline
        if hasattr(self.pipeline_id, 'csv_delimiter'):
            self.pipeline_id.write({'csv_delimiter': self.delimiter})
        
        # Run the import
        result = self.pipeline_id.run_import(self.file, self.filename)
        
        # Show result message
        record_count = len(result.get('created', []))
        message = _('%s records successfully imported.') % record_count
        if result.get('errors'):
            message += _('\nErrors encountered: %s') % ', '.join(result.get('errors'))
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Import Result'),
                'message': message,
                'sticky': True,
                'type': 'success' if not result.get('errors') else 'warning',
            }
        }
