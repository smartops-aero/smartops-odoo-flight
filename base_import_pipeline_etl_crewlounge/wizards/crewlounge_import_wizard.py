import base64
import csv
import io
from odoo import fields, models, _
from odoo.exceptions import UserError

class CrewLoungeImportWizard(models.TransientModel):
    _name = "crewlounge.import.wizard"
    _description = "CrewLounge Import Wizard"
    
    file = fields.Binary(string='CSV File', required=True)
    filename = fields.Char(string='Filename')
    delimiter = fields.Char(string='Delimiter', default=',', required=True, help="CSV delimiter character")
    
    # Pilot selection
    partner_id = fields.Many2one(
        "res.partner", 
        string="Pilot", 
        required=True,
        domain=[('is_company', '=', False)],
        help="Select the pilot for whom this flight data is being imported"
    )
    
    # Preview fields
    preview_data = fields.Text(string='Preview Info', readonly=True)
    preview_row_count = fields.Integer(string='Total Rows', readonly=True)
    preview_column_count = fields.Integer(string='Total Columns', readonly=True)
    preview_column_names = fields.Text(string='Column Names', readonly=True)
    state = fields.Selection([
        ('upload', 'Upload'),
        ('preview', 'Preview'),
    ], default='upload', string='State')
    
    def action_back_to_upload(self):
        """Go back to the upload state"""
        self.ensure_one()
        self.state = 'upload'
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_preview(self):
        """Preview the CSV data before importing"""
        self.ensure_one()
        
        if not self.file:
            raise UserError(_("Please upload a CSV file"))
        
        try:
            # Decode the file content
            content = base64.b64decode(self.file).decode('utf-8')
            
            # First count total rows in the CSV
            row_count = sum(1 for _ in csv.reader(io.StringIO(content), delimiter=self.delimiter)) - 1  # Subtract header row
            
            # Parse CSV for preview
            reader = csv.DictReader(
                io.StringIO(content), 
                delimiter=self.delimiter
            )
            
            # Get the first 5 rows for preview
            preview_rows = []
            for i, row in enumerate(reader):
                if i >= 5:  # Limit to 5 rows
                    break
                preview_rows.append(row)
            
            if preview_rows:
                # Get all keys from the first row
                keys = list(preview_rows[0].keys())
                
                # Store the structured data
                self.preview_row_count = row_count
                self.preview_column_count = len(keys)
                self.preview_column_names = ", ".join(keys)
                
                # Simple text summary
                message = "Found %s rows with %s columns.\n\nColumn names: %s\n\nThe file appears to be valid and ready for import."
                self.preview_data = _(message) % (row_count, len(keys), self.preview_column_names)
            else:
                self.preview_data = _("No data found in the CSV file")
            
            self.state = 'preview'
            
            return {
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
            }
            
        except Exception as e:
            raise UserError(_("Error previewing data: %s") % str(e))
    
    def action_import(self):
        """Import the CSV file using the CrewLounge import pipeline"""
        self.ensure_one()
        
        if not self.file:
            raise UserError(_("Please upload a CSV file"))
            
        # Get the CrewLounge import pipeline
        pipeline = self.env['base.import.pipeline'].search([('implementation', '=', 'crewlounge')], limit=1)
        
        if not pipeline:
            raise UserError(_("CrewLounge import pipeline not found. Please create one first."))
        
        # Run the import with the file content, filename, and delimiter as parameters
        result = pipeline.with_context(import_partner_id=self.partner_id.id).run_import(
            file_content=self.file,
            filename=self.filename,
            csv_delimiter=self.delimiter,
        )
        
        # Show a success message with the number of records created
        created_count = len(result.get('created', []))
        updated_count = len(result.get('updated', []))
        error_count = len(result.get('errors', []))
        
        message = _("Import completed: %s flights created") % created_count
        if updated_count:
            message += _(", %s flights updated") % updated_count
        if error_count:
            message += _(", %s errors occurred") % error_count
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Import Result'),
                'message': message,
                'sticky': False,
                'type': 'success' if not error_count else 'warning',
            }
        }
