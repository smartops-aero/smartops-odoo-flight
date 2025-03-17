import base64
import csv
import io
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class BaseImportPipelineETL(models.Model):
    _name = "base.import.pipeline.etl"
    _inherit = "base.import.pipeline"
    _description = "ETL Import Pipeline"
    
    mapping_ids = fields.One2many('base.import.pipeline.mapping', 'pipeline_id', string='Field Mappings')
    csv_delimiter = fields.Char(string='CSV Delimiter', default=',', required=True)
    skip_header = fields.Boolean(string='Skip Header', default=True, 
                                help="Skip the first row of the file (header)")
    
    def extract(self, file_content, filename=None):
        """Extract data from source file
        
        This is a base ETL method that should be implemented by modules 
        that extend this one.
        """
        return self._dispatch("extract", file_content, filename)
        
    def transform(self, extracted_data):
        """Transform extracted data
        
        This is a base ETL method that should be implemented by modules
        that extend this one.
        """
        return self._dispatch("transform", extracted_data)
        
    def load(self, transformed_data):
        """Load transformed data into target model
        
        This is a base ETL method that should be implemented by modules
        that extend this one.
        """
        return self._dispatch("load", transformed_data)
    
    def run_import(self, file_content=None, filename=None, **kwargs):
        """Run the ETL import process"""
        try:
            extracted_data = self.extract(file_content, filename)
            transformed_data = self.transform(extracted_data)
            result = self.load(transformed_data)
            
            # Log the result
            self._log_import_result(result)
            
            return result
            
        except Exception as e:
            # Log error
            self.env['base.import.pipeline.result'].create({
                'pipeline_id': self.id,
                'date': fields.Datetime.now(),
                'summary': str(e),
                'records_created': 0,
                'status': 'error',
                'log': str(e),
            })
            raise
    
    def _extract_from_csv(self, file_content, filename=None):
        """Extract data from CSV file - helper method for implementations"""
        if not file_content:
            raise UserError(_("No file content provided"))
        
        try:
            # Decode the file content
            content = base64.b64decode(file_content).decode('utf-8')
            
            # Parse CSV
            reader = csv.DictReader(
                io.StringIO(content), 
                delimiter=self.csv_delimiter
            )
            
            # Convert to list of dicts
            records = []
            for row in reader:
                # Clean up the row (strip whitespace from keys and values)
                cleaned_row = {k.strip(): v.strip() if isinstance(v, str) else v 
                              for k, v in row.items()}
                records.append(cleaned_row)
                
            return records
        except Exception as e:
            raise UserError(_("Error extracting data: %s") % str(e))
    
    def _apply_field_transformations(self, source_field, value, transformation, options=None):
        """Apply transformations to field values - helper method for implementations"""
        if transformation == 'direct':
            return value
        elif transformation == 'date_format':
            # Basic date format conversion (DD-MM-YYYY to YYYY-MM-DD)
            if value and len(value) == 10:  # Simple validation
                parts = value.split('-')
                if len(parts) == 3:
                    return f"{parts[2]}-{parts[1]}-{parts[0]}"
            return value
        elif transformation == 'lookup':
            # This would implement lookup logic
            return value
        else:
            return value
    
    def _get_or_create_record(self, model, domain, values):
        """Get or create a record - helper method for implementations"""
        record = self.env[model].search(domain, limit=1)
        if not record:
            record = self.env[model].create(values)
        return record
