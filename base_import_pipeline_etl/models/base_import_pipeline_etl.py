import base64
import csv
import io
import re
import logging
import traceback
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class BaseImportPipeline(models.Model):
    _inherit = "base.import.pipeline"
    
    mapping_ids = fields.One2many('base.import.pipeline.mapping', 'pipeline_id', string='Field Mappings')

    
    def extract(self, **kwargs):
        """Extract data from source file
        
        This is a base ETL method that should be implemented by modules 
        that extend this one.
        """
        return self._dispatch("extract", **kwargs)
        
    def transform(self, extracted_data, **kwargs):
        """Transform extracted data
        
        This method applies the configured mappings to transform the extracted data.
        It handles direct mappings, lookups, and other transformations.
        """
        if not self.mapping_ids:
            return extracted_data
            
        _logger.info("Starting transformation with %s mappings", len(self.mapping_ids))
        for mapping in self.mapping_ids:
            _logger.info("Mapping: %s, Source: %s, Target: %s, Model: %s, Sequence: %s", 
                        mapping.description, mapping.source_field, mapping.target_field, 
                        mapping.model_id.model, mapping.sequence)
            if mapping.relation_model_id:
                _logger.info("  Relation model: %s, Relation field: %s", 
                            mapping.relation_model_id.model, mapping.relation_field)
            
        # Store created/found related records for reference in later mappings
        related_records_cache = {}
        
        # Process each record
        transformed_data = []
        for i, record in enumerate(extracted_data):
            _logger.info("Processing record %s/%s: %s", i+1, len(extracted_data), record)
            
            # Create a dict to hold the values for the target model
            values = {}
            
            # Keep track of records we've created/found for this row
            # This allows us to update them with additional fields later
            row_records = {}
            
            # Process mappings in their natural sequence order
            # This ensures dependencies are created in the correct order
            for mapping in self.mapping_ids.sorted(key=lambda m: m.sequence):
                if mapping.source_field in record:
                    source_value = record[mapping.source_field]
                    _logger.info("Processing mapping %s for field %s with value %s", 
                                mapping.description, mapping.source_field, source_value)
                    
                    # Skip if this is a relation mapping without a relation field
                    if mapping.relation_model_id and not mapping.relation_field:
                        _logger.warning("Skipping mapping %s - relation field not defined", mapping.description)
                        continue
                    
                    # Apply transformation to the source value
                    transformed_value = self._apply_field_transformations(source_value, mapping)
                    if transformed_value is None:
                        _logger.warning("Transformation returned None for mapping %s, value %s", 
                                      mapping.description, source_value)
                        continue
                    
                    _logger.info("Transformed value: %s", transformed_value)
                    
                    # Handle direct field mappings (non-relational)
                    if not mapping.relation_model_id:
                        # If this mapping is for the target model, add it to the values
                        if mapping.model_id.model == self.model_id.model:
                            _logger.info("Adding %s = %s to target model %s", 
                                        mapping.target_field, transformed_value, self.model_id.model)
                            values[mapping.target_field] = transformed_value
                        # Otherwise, it's for a related model - create/find it
                        else:
                            model_name = mapping.model_id.model
                            field_name = mapping.target_field
                            
                            # If this is a key field, use it to identify the record
                            if mapping.is_key_field:
                                domain = [(field_name, '=', transformed_value)]
                                
                                # Check if we already have a record for this model in this row
                                if model_name in row_records:
                                    # Update the existing record with this field
                                    model_record = row_records[model_name]
                                    model_record.write({field_name: transformed_value})
                                    _logger.info("Updated existing record %s with %s = %s", 
                                                model_record, field_name, transformed_value)
                                else:
                                    # Create or find the record
                                    model_values = {field_name: transformed_value}
                                    _logger.info("Creating/finding record in %s with domain %s and values %s", 
                                                model_name, domain, model_values)
                                    
                                    model_record = self._get_or_create_record(
                                        model_name, domain, model_values
                                    )
                                    
                                    _logger.info("Result: %s (ID: %s)", model_record, model_record.id)
                                    
                                    # Store the record for this row
                                    row_records[model_name] = model_record
                                
                                # Cache the record
                                cache_key = f"{model_name}:{field_name}:{transformed_value}"
                                related_records_cache[cache_key] = model_record
                                _logger.info("Cached with key: %s", cache_key)
                            else:
                                # This is a non-key field for a related model
                                # We need to find the record first
                                if model_name in row_records:
                                    # Update the existing record with this field
                                    model_record = row_records[model_name]
                                    model_record.write({field_name: transformed_value})
                                    _logger.info("Updated existing record %s with %s = %s", 
                                                model_record, field_name, transformed_value)
                                    
                                    # Cache the record with this field value
                                    cache_key = f"{model_name}:{field_name}:{transformed_value}"
                                    related_records_cache[cache_key] = model_record
                                    _logger.info("Cached with key: %s", cache_key)
                    
                    # Handle relational field mappings
                    else:
                        relation_model = mapping.relation_model_id.model
                        relation_field = mapping.relation_field
                        
                        # Try to find the related record in cache first
                        cache_key = f"{relation_model}:{relation_field}:{transformed_value}"
                        related_record = related_records_cache.get(cache_key)
                        
                        if related_record:
                            _logger.info("Found related record in cache with key %s: %s (ID: %s)", 
                                        cache_key, related_record, related_record.id)
                        
                        if not related_record:
                            # Build domain for lookup
                            domain = [(relation_field, '=', transformed_value)]
                            
                            # Add additional lookup fields if specified
                            if mapping.lookup_fields:
                                additional_fields = [f.strip() for f in mapping.lookup_fields.split(',')]
                                for field in additional_fields:
                                    if field:
                                        domain = ['|', (field, '=', transformed_value)] + domain
                            
                            # Prepare values for creating the related record if needed
                            related_values = {relation_field: transformed_value}
                            
                            _logger.info("Looking up related record in %s with domain %s and values %s", 
                                        relation_model, domain, related_values)
                            
                            # Find or create the related record
                            related_record = self._get_or_create_record(
                                relation_model, domain, related_values
                            )
                            
                            _logger.info("Result: %s (ID: %s)", related_record, related_record.id)
                            
                            # Cache the related record
                            related_records_cache[cache_key] = related_record
                            _logger.info("Cached with key: %s", cache_key)
                        
                        # If this mapping is for the target model, add it to the values
                        if mapping.model_id.model == self.model_id.model:
                            _logger.info("Adding %s = %s to target model %s", 
                                        mapping.target_field, related_record.id, self.model_id.model)
                            values[mapping.target_field] = related_record.id
                        # Otherwise, it's for a related model - create/find it
                        else:
                            model_name = mapping.model_id.model
                            field_name = mapping.target_field
                            
                            if model_name in row_records:
                                # Update the existing record with this relation
                                model_record = row_records[model_name]
                                model_record.write({field_name: related_record.id})
                                _logger.info("Updated existing record %s with %s = %s", 
                                            model_record, field_name, related_record.id)
                                
                                # Cache the updated record
                                cache_key = f"{model_name}:{field_name}:{related_record.id}"
                                related_records_cache[cache_key] = model_record
                                _logger.info("Cached with key: %s", cache_key)
                            else:
                                # Create or find the record with this relation
                                domain = [(field_name, '=', related_record.id)]
                                model_values = {field_name: related_record.id}
                                
                                _logger.info("Creating/finding record in %s with domain %s and values %s", 
                                            model_name, domain, model_values)
                                
                                model_record = self._get_or_create_record(
                                    model_name, domain, model_values
                                )
                                
                                _logger.info("Result: %s (ID: %s)", model_record, model_record.id)
                                
                                # Store the record for this row
                                row_records[model_name] = model_record
                                
                                # Cache the record
                                cache_key = f"{model_name}:{field_name}:{related_record.id}"
                                related_records_cache[cache_key] = model_record
                                _logger.info("Cached with key: %s", cache_key)
            
            # Add the transformed record to the result if it has values for the target model
            if values:
                _logger.info("Adding transformed record to result: %s", values)
                transformed_data.append(values)
            else:
                _logger.warning("No values for target model, skipping record")
                
        _logger.info("Transformation complete, returning %s records", len(transformed_data))
        return transformed_data
        
    def load(self, transformed_data, **kwargs):
        """Load transformed data into the target model
        
        This method creates or updates records in the target model
        based on the transformed data.
        """
        _logger.info("Loading data into %s", self.model_id.model)
        
        result = {
            'created': [],
            'updated': [],
            'errors': [],
        }
        
        if not transformed_data:
            _logger.info("No transformed data to load")
            return result
            
        _logger.info("Starting to load %s records into %s", len(transformed_data), self.model_id.model)
        
        # Get key fields for the target model
        key_mappings = self.mapping_ids.filtered(
            lambda m: m.model_id.model == self.model_id.model and m.is_key_field
        )
        
        has_key_fields = bool(key_mappings)
        if not has_key_fields:
            _logger.warning(
                "No key fields defined for target model %s. Will always create new records.",
                self.model_id.model
            )
        
        try:
            # Create all records in a single transaction
            with self.env.cr.savepoint():
                for i, values in enumerate(transformed_data):
                    try:
                        _logger.debug("Processing record %s/%s with values: %s", 
                                     i+1, len(transformed_data), values)
                        
                        # Check if record already exists
                        existing_record = None
                        if has_key_fields:
                            domain = []
                            for mapping in key_mappings:
                                field_name = mapping.target_field
                                if field_name in values:
                                    domain.append((field_name, '=', values[field_name]))
                            
                            if domain:
                                _logger.debug("Searching for existing record with domain: %s", domain)
                                existing_record = self.env[self.model_id.model].search(domain, limit=1)
                                if existing_record:
                                    _logger.info("Found existing record: %s (ID: %s)", 
                                                existing_record, existing_record.id)
                        
                        # Update existing or create new record
                        if existing_record:
                            existing_record.write(values)
                            result['updated'].append(existing_record.id)
                            _logger.debug("Successfully updated record with ID %s", existing_record.id)
                        else:
                            record = self.env[self.model_id.model].create(values)
                            result['created'].append(record.id)
                            _logger.debug("Successfully created record with ID %s", record.id)
                    except Exception as record_error:
                        error_msg = f"Error processing record {i+1}/{len(transformed_data)}: {str(record_error)}"
                        _logger.error(error_msg)
                        _logger.error("Values that caused the error: %s", values)
                        _logger.error("Stack trace: %s", traceback.format_exc())
                        result['errors'].append(error_msg)
                        # Continue with next record instead of failing the whole batch
        except Exception as e:
            error_msg = f"Error in batch processing: {str(e)}"
            _logger.error(error_msg)
            _logger.error("Stack trace: %s", traceback.format_exc())
            result['errors'].append(error_msg)
        
        _logger.info("Import completed. Created: %s, Updated: %s, Errors: %s", 
                    len(result['created']), len(result['updated']), len(result['errors']))
        
        return result
    
    def run_import(self, **kwargs):
        """Run the ETL import process"""
        try:
            extracted_data = self.extract(**kwargs)
            transformed_data = self.transform(extracted_data)
            result = self.load(transformed_data)
            
            # Log the result
            self._log_import_result(result)
            
            return result
            
        except Exception as e:
            _logger.error("Error running import: %s", str(e))
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
    
    @api.model
    def _extract_from_csv(self, file_content, filename=None, delimiter=','):
        """Extract data from CSV file - helper method for implementations"""
        if not file_content:
            raise UserError(_("No file content provided"))
        
        try:
            # Decode the file content
            content = base64.b64decode(file_content).decode('utf-8')
            
            # Parse CSV
            reader = csv.DictReader(
                io.StringIO(content), 
                delimiter=delimiter
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
        """Apply transformations to field values based on mapping configuration
        
        This method delegates to the mapping model's transform_value method,
        which implements the transformation logic.
        """
        return mapping.transform_value(value)
    
    def _get_or_create_record(self, model_name, domain, values):
        """Get or create a record in the specified model
        
        This method tries to find a record matching the domain.
        If not found, it creates a new record with the provided values.
        If found, it updates the record with any new values.
        
        Args:
            model_name: The name of the model to search/create in
            domain: The domain to search for existing records
            values: The values to use when creating a new record or updating an existing one
            
        Returns:
            The found or created record
        """
        _logger.debug("_get_or_create_record: model=%s, domain=%s, values=%s", 
                     model_name, domain, values)
        
        record = self.env[model_name].search(domain, limit=1)
        _logger.debug("Search result: %s", record)
        
        if record:
            # Update the existing record with any new values
            # This ensures that if we find a record by one field (e.g., name)
            # we can still update other fields (e.g., make_id)
            update_values = {}
            for field, value in values.items():
                # Check if this field is part of the domain
                field_in_domain = False
                for domain_item in domain:
                    if isinstance(domain_item, (list, tuple)) and domain_item[0] == field:
                        field_in_domain = True
                        break
                
                # Only update if not in domain and either not set or empty
                if not field_in_domain and (field not in record or not record[field]):
                    update_values[field] = value
            
            if update_values:
                _logger.debug("Updating record %s with values: %s", record, update_values)
                record.write(update_values)
        else:
            # Create a new record
            _logger.debug("Creating new record with values: %s", values)
            record = self.env[model_name].create(values)
            
        return record
