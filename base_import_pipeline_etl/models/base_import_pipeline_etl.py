import base64
import csv
import io
import logging
import traceback
import json
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
            
        # Only process mappings that are NOT marked for post-processing
        regular_mappings = self.mapping_ids.filtered(lambda m: not m.is_post_process)
            
        _logger.info("Starting transformation with %s regular mappings", len(regular_mappings))
        for mapping in regular_mappings:
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
            for mapping in regular_mappings.sorted(key=lambda m: m.sequence):
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
                                        model_name, domain, model_values, mapping
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
                                relation_model, domain, related_values, mapping
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
                                    model_name, domain, model_values, mapping
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
                transformed_data.append({'values': values, 'original_data': record})
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
                for i, data in enumerate(transformed_data):
                    try:
                        _logger.debug("Processing record %s/%s with values: %s", 
                                     i+1, len(transformed_data), data)
                        
                        # Store original source data in values as context for post-processing
                        original_data = kwargs.get('extracted_data', [])[i] if i < len(kwargs.get('extracted_data', [])) else {}
                        
                        # Check if record already exists
                        existing_record = None
                        if has_key_fields:
                            domain = []
                            for mapping in key_mappings:
                                field_name = mapping.target_field
                                if field_name in data['values']:
                                    domain.append((field_name, '=', data['values'][field_name]))
                            
                            if domain:
                                _logger.debug("Searching for existing record with domain: %s", domain)
                                existing_record = self.env[self.model_id.model].search(domain, limit=1)
                                if existing_record:
                                    _logger.info("Found existing record: %s (ID: %s)", 
                                                existing_record, existing_record.id)
                        
                        # Update existing or create new record
                        if existing_record:
                            existing_record.with_context(original_data=original_data).write(data['values'])
                            result['updated'].append(existing_record.id)
                            _logger.debug("Successfully updated record with ID %s", existing_record.id)
                        else:
                            record = self.env[self.model_id.model].with_context(original_data=original_data).create(data['values'])
                            result['created'].append(record.id)
                            _logger.debug("Successfully created record with ID %s", record.id)
                    except Exception as record_error:
                        error_msg = f"Error processing record {i+1}/{len(transformed_data)}: {str(record_error)}"
                        _logger.error(error_msg)
                        _logger.error("Values that caused the error: %s", data)
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
    
    def post_process(self, import_result, extracted_data=None):
        """Process post-import actions that depend on created/updated records
        
        This method runs after the main import is complete and handles creating
        related records that depend on the IDs of the newly created records.
        
        Args:
            import_result: Dictionary containing created/updated record IDs
            extracted_data: List of dictionaries containing original data
            
        Returns:
            Dictionary with post-processing results
        """
        post_result = {
            'post_created': [],
            'post_updated': [],
            'post_errors': []
        }
        
        if not extracted_data:
            _logger.warning("No extracted data for post processing")
            return post_result
            
        # Get all post-process mappings
        post_mappings = self.mapping_ids.filtered(lambda m: m.is_post_process)
        if not post_mappings:
            _logger.info("No post-process mappings defined")
            return post_result
            
        # Associate original data with record IDs for reference
        original_data_by_id = {}
        for idx, data in enumerate(extracted_data):
            if idx < len(import_result.get('created', [])):
                record_id = import_result['created'][idx]
                original_data_by_id[record_id] = data
            elif idx - len(import_result.get('created', [])) < len(import_result.get('updated', [])):
                record_id = import_result['updated'][idx - len(import_result.get('created', []))]
                original_data_by_id[record_id] = data
        
        # Get records that were created or updated
        records = None
        # Find the main model - safely handle the case where filtering returns no records
        main_model_mapping = self.mapping_ids.filtered(lambda m: not m.is_post_process and m.sequence == 0)
        main_model = main_model_mapping.model_id.model if main_model_mapping else self.model_id.model
        
        if not main_model:
            _logger.error("Could not determine main model for post-processing")
            post_result['post_errors'].append("Could not determine main model for post-processing")
            return post_result
            
        if import_result.get('created') or import_result.get('updated'):
            records = self.env[main_model].browse(import_result.get('created', []) + import_result.get('updated', []))
        
        if not records:
            _logger.warning("No records were created or updated, skipping post-processing")
            return post_result
        
        # First, group mappings by model AND group_key (if set)
        mapping_groups = {}
        for mapping in post_mappings:
            model_name = mapping.model_id.model
            # Use combination of model and group_key as the dictionary key
            # This allows separate processing for different group keys within the same model
            group_key = f"{model_name}_{mapping.group_key or 'default'}"
            
            if group_key not in mapping_groups:
                mapping_groups[group_key] = []
            mapping_groups[group_key].append(mapping)
        
        # Process each group of mappings
        for group_key, mappings in mapping_groups.items():
            model_name = mappings[0].model_id.model
            _logger.info("Processing mappings for group: %s (model: %s)", group_key, model_name)
            
            # For each parent record, create related records
            for record in records:
                try:
                    original_data = original_data_by_id.get(record.id, {})
                    self._create_post_process_record(record, model_name, mappings, post_result, original_data)
                except Exception as e:
                    error_msg = f"Error in post-processing for record {record.id}: {str(e)}"
                    _logger.error(error_msg)
                    _logger.error("Stack trace: %s", traceback.format_exc())
                    post_result['post_errors'].append(error_msg)
        
        return post_result

    def _create_post_process_record(self, parent_record, target_model, mappings, post_result, extracted_data):
        """Create or update a record in the target model linked to the parent record
        
        Args:
            parent_record: The parent record (e.g., flight.flight) to link to
            target_model: The name of the model to create record in
            mappings: List of mapping records for the target model
            post_result: Dictionary to store results
            extracted_data: Dictionary with original source data
        """
        values = {}
        domain = []
        
        # Process each mapping to build values
        for mapping in mappings:
            field_name = mapping.target_field
            
            # Handle parent record ID transformation
            if mapping.transformation == 'parent_record_id':
                values[field_name] = parent_record.id
                # If this is a key field, add it to the domain for finding existing records
                if mapping.is_key_field:
                    domain.append((field_name, '=', parent_record.id))
                continue
                
            # Handle static values (from post_process_value)
            if mapping.post_process_value:
                values[field_name] = mapping.post_process_value
                # If this is a key field, add it to the domain for finding existing records
                if mapping.is_key_field:
                    domain.append((field_name, '=', mapping.post_process_value))
                continue
                
            # Handle source field based values with transformation
            if mapping.source_field and mapping.source_field in extracted_data:
                # Get source value
                source_value = extracted_data.get(mapping.source_field)
                _logger.info("Processing source field %s with value: %s", mapping.source_field, source_value)
                
                # Apply the standard transformation
                transformed_value = mapping.transform_value(source_value)
                
                if transformed_value is not None:
                    values[field_name] = transformed_value
                    # Only add key fields to domain
                    if mapping.is_key_field:
                        domain.append((field_name, '=', transformed_value))
        
        # Skip if we don't have any values to create/update
        if not values:
            _logger.warning("No values to create/update for post-processing record, skipping")
            return
        
        # Ensure we have a valid domain for finding existing
        if not domain:
            _logger.warning("No domain criteria for finding existing records, will always create new")
        
        try:
            # Check if record already exists
            existing = None
            if domain:
                existing = self.env[target_model].search(domain, limit=1)
                if existing:
                    _logger.info("Found existing record %s with domain %s", existing, domain)
            
            if existing:
                existing.write(values)
                post_result['post_updated'].append(existing.id)
                _logger.info("Updated existing %s record: %s with values: %s", target_model, existing.id, values)
            else:
                new_record = self.env[target_model].create(values)
                post_result['post_created'].append(new_record.id)
                _logger.info("Created new %s record: %s with values: %s", target_model, new_record.id, values)
        except Exception as e:
            error_msg = f"Error creating/updating {target_model}: {str(e)}"
            post_result['post_errors'].append(error_msg)
            _logger.error(error_msg)
            _logger.error("Stack trace: %s", traceback.format_exc())
    
    def run_import(self, **kwargs):
        """Run the ETL import process"""
        _logger.info("Starting import with pipeline: %s", self.name)
        
        try:
            # Extract data from the source
            extracted_data = self.extract(**kwargs)
            _logger.info("Extracted %s records", len(extracted_data))
            
            # Transform the data
            transformed_data = self.transform(extracted_data, **kwargs)
            _logger.info("Transformed data for %s records", len(transformed_data))
            
            # Load the data into the target model
            result = self.load(transformed_data, extracted_data=extracted_data)
            
            # Log the result
            self._log_import_result(result)
            
            # Run post-processing
            post_result = self.post_process(result, extracted_data=extracted_data)
            
            # Merge post-processing results into main result
            for key in ['post_created', 'post_updated', 'post_errors']:
                if key in post_result:
                    result[key] = post_result[key]
            
            # Log the merged result
            self._log_import_result(result)
            
            return result
            
        except Exception as e:
            _logger.error("Error running import: %s", str(e))
            _logger.error("Stack trace: %s", traceback.format_exc())
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
    
    def _get_or_create_record(self, model_name, domain, values, mapping=None):
        """Get or create a record in the specified model
        
        This method tries to find a record matching the domain.
        If not found, it creates a new record with the provided values.
        If found, it updates the record with any new values.
        
        Args:
            model_name: The name of the model to search/create in
            domain: The domain to search for existing records
            values: The values to use when creating a new record or updating an existing one
            mapping: Optional mapping record that may contain context for new records
            
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
            create_values = values.copy()
            create_context = {}
            
            # Apply context from mapping if provided
            if mapping and mapping.context:
                try:
                    context_values = json.loads(mapping.context)
                    if isinstance(context_values, dict):
                        # Extract default values from context
                        for key, value in context_values.items():
                            if key.startswith('default_'):
                                field_name = key[8:]  # Remove 'default_' prefix
                                create_values[field_name] = value
                            else:
                                create_context[key] = value
                        
                        _logger.debug("Added values from context: %s", context_values)
                except Exception as e:
                    _logger.warning("Error parsing context from mapping: %s", str(e))
            
            _logger.debug("Creating new record with values: %s", create_values)
            if create_context:
                record = self.env[model_name].with_context(**create_context).create(create_values)
            else:
                record = self.env[model_name].create(create_values)
            
        return record
