import base64
import csv
import io
import re
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class BaseImportPipelineETL(models.Model):
    _inherit = "base.import.pipeline"
    
    mapping_ids = fields.One2many('base.import.pipeline.mapping', 'pipeline_id', string='Field Mappings')

    
    def extract(self, file_content, filename=None):
        """Extract data from source file
        
        This is a base ETL method that should be implemented by modules 
        that extend this one.
        """
        return self._dispatch("extract", file_content, filename)
        
    def transform(self, extracted_data):
        """Transform extracted data
        
        This method applies the configured mappings to transform the extracted data.
        It handles direct mappings, lookups, and other transformations.
        """
        if not self.mapping_ids:
            return extracted_data
            
        # Group mappings by target model
        model_mappings = {}
        for mapping in self.mapping_ids:
            if mapping.model not in model_mappings:
                model_mappings[mapping.model] = []
            model_mappings[mapping.model].append(mapping)
        
        # Process each record
        transformed_data = []
        for record in extracted_data:
            # Create a dict to hold the values for the main record
            values = {}
            
            # Process direct field mappings first (non-relational fields)
            for mapping in self.mapping_ids.filtered(lambda m: not m.relation_model_id):
                if mapping.source_field in record:
                    source_value = record[mapping.source_field]
                    transformed_value = self._apply_field_transformations(source_value, mapping)
                    if transformed_value is not None:
                        values[mapping.target_field] = transformed_value
            
            # Process relational field mappings
            for mapping in self.mapping_ids.filtered(lambda m: m.relation_model_id):
                if mapping.source_field in record:
                    source_value = record[mapping.source_field]
                    
                    # Skip if no relation field is defined
                    if not mapping.relation_field:
                        continue
                    
                    # Apply transformation to the source value
                    transformed_value = self._apply_field_transformations(source_value, mapping)
                    if transformed_value is None:
                        continue
                    
                    # Build domain for lookup
                    domain = [(mapping.relation_field, '=', transformed_value)]
                    
                    # Add additional lookup fields if specified
                    if mapping.lookup_fields:
                        additional_fields = [f.strip() for f in mapping.lookup_fields.split(',')]
                        for field in additional_fields:
                            if field:
                                domain = ['|', (field, '=', transformed_value)] + domain
                    
                    # Prepare values for creating the related record if needed
                    related_values = {mapping.relation_field: transformed_value}
                    
                    # Find or create the related record
                    related_record = self._get_or_create_record(
                        mapping.relation_model, domain, related_values
                    )
                    
                    # Set the relation in the main record
                    values[mapping.target_field] = related_record.id
            
            # Add the transformed record to the result
            if values:
                transformed_data.append(values)
                
        return transformed_data
        
    def load(self, transformed_data):
        """Load transformed data into target model
        
        Creates records in the target model using the transformed data.
        All records are created in a single transaction.
        """
        result = {
            'created': [],
            'errors': [],
        }
        
        if not transformed_data:
            return result
            
        try:
            # Create all records in a single transaction
            with self.env.cr.savepoint():
                for values in transformed_data:
                    record = self.env[self.model_id.model].create(values)
                    result['created'].append(record.id)
        except Exception as e:
            result['errors'].append(str(e))
        
        return result
    
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
    
    def _apply_field_transformations(self, value, mapping):
        """Apply transformations to field values based on mapping configuration"""
        if not value and mapping.default_value:
            return mapping.default_value
            
        transformation = mapping.transformation
        
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
            # For lookup transformations, we just return the value
            # The actual lookup is handled in the transform method
            return value
            
        elif transformation == 'regex':
            # Apply regex transformation if pattern is defined
            if value and mapping.regex_pattern and mapping.regex_replacement:
                try:
                    return re.sub(mapping.regex_pattern, mapping.regex_replacement, value)
                except Exception:
                    # If regex fails, return original value or default
                    return mapping.default_value if mapping.default_value else value
            return value
            
        else:
            # Default fallback
            return mapping.default_value if mapping.default_value else value
    
    def _get_or_create_record(self, model, domain, values):
        """Get or create a record - helper method for implementations"""
        record = self.env[model].search(domain, limit=1)
        if not record:
            record = self.env[model].create(values)
        return record
