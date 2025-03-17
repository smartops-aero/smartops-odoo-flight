from odoo import api, fields, models, _
from odoo.exceptions import UserError


class BaseImportPipeline(models.Model):
    _inherit = "base.import.pipeline"
    
    def _selection_implementation(self):
        selection = super()._selection_implementation()
        selection.append(('crewlounge', 'Flight Import - CrewLounge'))
        return selection
    
    def _crewlounge_extract(self, file_content, filename=None, csv_delimiter=',', **kwargs):
        """Extract data from CrewLounge CSV file"""
        if not file_content:
            raise UserError(_("No file content provided"))
            
        # Use the CSV extraction helper method
        return self.env['base.import.pipeline']._extract_from_csv(
            file_content, 
            filename,
            delimiter=csv_delimiter
        )
