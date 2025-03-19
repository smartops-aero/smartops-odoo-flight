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
        regular_mappings = self._get_regular_mappings()
            
        # Store created/found related records for reference in later mappings
        related_records_cache = {}
        
        # Process each record
        transformed_data = []
        for i, record in enumerate(extracted_data):
            _logger.info("Processing record %s/%s: %s", i+1, len(extracted_data), record)
            result = self._transform_single_record(i, record, regular_mappings, related_records_cache)
            if result:
                transformed_data.append(result)
                
        _logger.info("Transformation complete, returning %s records", len(transformed_data))
        return transformed_data
    
    def _get_regular_mappings(self):
        """Get regular mappings that are not marked for post-processing"""
        regular_mappings = self.mapping_ids.filtered(lambda m: not m.is_post_process)
        _logger.info("Starting transformation with %s regular mappings", len(regular_mappings))
        for mapping in regular_mappings:
            _logger.info("Mapping: %s, Source: %s, Target: %s, Model: %s, Sequence: %s", 
                        mapping.description, mapping.source_field, mapping.target_field, 
                        mapping.model_id.model, mapping.sequence)
            if mapping.relation_model_id:
                _logger.info("  Relation model: %s, Relation field: %s", 
                            mapping.relation_model_id.model, mapping.relation_field)
        
        return regular_mappings
    
    def _transform_single_record(self, index, record, regular_mappings, related_records_cache):
        """Transform a single record using the configured mappings"""
        # Create a dict to hold the values for the target model
        values = {}
        
        # Keep track of records we've created/found for this row
        # This allows us to update them with additional fields later
        row_records = {}
        
        # Process mappings in their natural sequence order
        # This ensures dependencies are created in the correct order
        for mapping in regular_mappings.sorted(key=lambda m: m.sequence):
            if mapping.source_field in record:
                self._process_field_mapping(mapping, record, values, row_records, related_records_cache)
        
        # Add the transformed record to the result if it has values for the target model
        if values:
            _logger.info("Adding transformed record to result: %s", values)
            return {'values': values, 'original_data': record}
        else:
            _logger.warning("No values for target model, skipping record")
            return None
    
    def _process_field_mapping(self, mapping, record, values, row_records, related_records_cache):
        """Process a single field mapping for a record"""
        source_value = record[mapping.source_field]
        _logger.info("Processing mapping %s for field %s with value %s", 
                    mapping.description, mapping.source_field, source_value)
        
        # Skip if this is a relation mapping without a relation field
        if mapping.relation_model_id and not mapping.relation_field:
            _logger.warning("Skipping mapping %s - relation field not defined", mapping.description)
            return
        
        # Apply transformation to the source value
        transformed_value = self._apply_field_transformations(source_value, mapping, record)
        if transformed_value is None:
            _logger.warning("Transformation returned None for mapping %s, value %s", 
                          mapping.description, source_value)
            return
        
        _logger.info("Transformed value: %s", transformed_value)
        
        # Handle direct field mappings (non-relational)
        if not mapping.relation_model_id:
            self._process_direct_field_mapping(
                mapping, transformed_value, values, row_records, related_records_cache
            )
        # Handle relational field mappings
        else:
            self._process_relational_field_mapping(
                mapping, transformed_value, values, row_records, related_records_cache, record
            )
    
    def _process_direct_field_mapping(self, mapping, transformed_value, values, row_records, related_records_cache):
        """Process a direct (non-relational) field mapping"""
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
    
    def _process_relational_field_mapping(self, mapping, transformed_value, values, row_records, related_records_cache, record):
        """Process a relational field mapping"""
        relation_model = mapping.relation_model_id.model
        relation_field = mapping.relation_field
        
        # Try to find the related record in cache first or create it
        related_record = self._find_or_create_related_record(
            mapping, transformed_value, relation_model, relation_field, related_records_cache
        )
        
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
                
    def _find_or_create_related_record(self, mapping, transformed_value, relation_model, relation_field, related_records_cache):
        """Find or create a related record for a relational mapping"""
        # Try to find the related record in cache first
        cache_key = f"{relation_model}:{relation_field}:{transformed_value}"
        related_record = related_records_cache.get(cache_key)
        
        if related_record:
            _logger.info("Found related record in cache with key %s: %s (ID: %s)", 
                        cache_key, related_record, related_record.id)
            return related_record
        
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
        
        return related_record
    
    def load(self, transformed_data, **kwargs):
        """Load transformed data into the target model
        
        This method creates or updates records in the target model
        based on the transformed data.
        """
        _logger.info("Loading data into %s", self.model_id.model)
        
        # Initialize result structure
        result = self._initialize_import_result()
        
        if not transformed_data:
            _logger.info("No transformed data to load")
            return result
            
        _logger.info("Starting to load %s records into %s", len(transformed_data), self.model_id.model)
        
        # Get key fields for the target model
        key_mappings = self._get_key_mappings()
        
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
                    self._process_single_record(
                        i, data, has_key_fields, key_mappings, result, kwargs
                    )
        except Exception as e:
            self._handle_batch_error(e, result)
        
        self._log_import_summary(result)
        
        return result
    
    def _initialize_import_result(self):
        """Initialize the structure for import results"""
        return {
            'created': [],
            'updated': [],
            'errors': [],
        }
    
    def _get_key_mappings(self):
        """Get key mappings for the target model"""
        return self.mapping_ids.filtered(
            lambda m: m.model_id.model == self.model_id.model and m.is_key_field
        )
    
    def _process_single_record(self, index, data, has_key_fields, key_mappings, result, kwargs):
        """Process a single record for import
        
        This handles finding an existing record or creating a new one
        with proper error handling.
        """
        try:
            _logger.debug("Processing record %s with values: %s", 
                         index+1, data)
            
            # Store original source data in values as context for post-processing
            original_data = self._get_original_data(index, kwargs)
            
            # Check if record already exists
            existing_record = None
            if has_key_fields:
                existing_record = self._find_existing_record_for_import(key_mappings, data)
            
            # Update existing or create new record
            if existing_record:
                self._update_existing_record(existing_record, data, original_data, result)
            else:
                self._create_new_record(data, original_data, result)
                
        except Exception as record_error:
            self._handle_record_error(record_error, index, data, len(data), result)
    
    def _get_original_data(self, index, kwargs):
        """Get original data for the record at the given index"""
        extracted_data = kwargs.get('extracted_data', [])
        return extracted_data[index] if index < len(extracted_data) else {}
    
    def _find_existing_record_for_import(self, key_mappings, data):
        """Find an existing record based on key mappings"""
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
                return existing_record
        return None
    
    def _update_existing_record(self, existing_record, data, original_data, result):
        """Update an existing record and log the result"""
        existing_record.with_context(original_data=original_data).write(data['values'])
        result['updated'].append(existing_record.id)
        _logger.debug("Successfully updated record with ID %s", existing_record.id)
    
    def _create_new_record(self, data, original_data, result):
        """Create a new record and log the result"""
        record = self.env[self.model_id.model].with_context(original_data=original_data).create(data['values'])
        result['created'].append(record.id)
        _logger.debug("Successfully created record with ID %s", record.id)
    
    def _handle_record_error(self, error, index, data, total_records, result):
        """Handle and log an error for a specific record"""
        error_msg = f"Error processing record {index+1}/{total_records}: {str(error)}"
        _logger.error(error_msg)
        _logger.error("Values that caused the error: %s", data)
        _logger.error("Stack trace: %s", traceback.format_exc())
        result['errors'].append(error_msg)
    
    def _handle_batch_error(self, error, result):
        """Handle and log a batch processing error"""
        error_msg = f"Error in batch processing: {str(error)}"
        _logger.error(error_msg)
        _logger.error("Stack trace: %s", traceback.format_exc())
        result['errors'].append(error_msg)
    
    def _log_import_summary(self, result):
        """Log a summary of the import results"""
        _logger.info("Import completed. Created: %s, Updated: %s, Errors: %s", 
                    len(result['created']), len(result['updated']), len(result['errors']))
    
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
        # Initialize result structure
        post_result = self._initialize_post_process_result()
        
        if not extracted_data:
            _logger.warning("No extracted data for post processing")
            return post_result
            
        # Get all post-process mappings
        post_mappings = self._get_post_process_mappings()
        if not post_mappings:
            _logger.info("No post-process mappings defined")
            return post_result
            
        # Associate original data with record IDs for reference
        original_data_by_id = self._associate_data_with_record_ids(import_result, extracted_data)
        
        # Get records that were created or updated
        records, main_model = self._get_parent_records_for_post_process(import_result)
        
        if not main_model:
            _logger.error("Could not determine main model for post-processing")
            post_result['post_errors'].append("Could not determine main model for post-processing")
            return post_result
            
        if not records:
            _logger.warning("No records were created or updated, skipping post-processing")
            return post_result
        
        # Group mappings by model and group_key
        mapping_groups = self._group_post_process_mappings(post_mappings)
        
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
                    self._handle_post_process_error(e, model_name, post_result, record_id=record.id)
        
        return post_result
    
    def _initialize_post_process_result(self):
        """Initialize the structure for post-process results"""
        return {
            'post_created': [],
            'post_updated': [],
            'post_errors': []
        }
    
    def _get_post_process_mappings(self):
        """Get mappings that are marked for post-processing"""
        return self.mapping_ids.filtered(lambda m: m.is_post_process)
    
    def _associate_data_with_record_ids(self, import_result, extracted_data):
        """Associate original data with created/updated record IDs
        
        Args:
            import_result: Dictionary with created/updated record IDs
            extracted_data: Original extracted data
            
        Returns:
            Dictionary mapping record IDs to original data
        """
        original_data_by_id = {}
        for idx, data in enumerate(extracted_data):
            if idx < len(import_result.get('created', [])):
                record_id = import_result['created'][idx]
                original_data_by_id[record_id] = data
            elif idx - len(import_result.get('created', [])) < len(import_result.get('updated', [])):
                record_id = import_result['updated'][idx - len(import_result.get('created', []))]
                original_data_by_id[record_id] = data
        return original_data_by_id
    
    def _get_parent_records_for_post_process(self, import_result):
        """Get parent records that were created or updated
        
        Args:
            import_result: Dictionary with created/updated record IDs
            
        Returns:
            Tuple of (records, model_name)
        """
        records = None
        # Find the main model - safely handle the case where filtering returns no records
        main_model_mapping = self.mapping_ids.filtered(lambda m: not m.is_post_process and m.sequence == 0)
        main_model = main_model_mapping.model_id.model if main_model_mapping else self.model_id.model
        
        if import_result.get('created') or import_result.get('updated'):
            records = self.env[main_model].browse(import_result.get('created', []) + import_result.get('updated', []))
        
        return records, main_model
    
    def _group_post_process_mappings(self, post_mappings):
        """Group post-process mappings by model and group_key
        
        Args:
            post_mappings: Collection of post-process mapping records
            
        Returns:
            Dictionary with groups of mappings
        """
        mapping_groups = {}
        for mapping in post_mappings:
            model_name = mapping.model_id.model
            # Use combination of model and group_key as the dictionary key
            # This allows separate processing for different group keys within the same model
            group_key = f"{model_name}_{mapping.group_key or 'default'}"
            
            if group_key not in mapping_groups:
                mapping_groups[group_key] = []
            mapping_groups[group_key].append(mapping)
        return mapping_groups
    
    def _create_post_process_record(self, parent_record, target_model, mappings, post_result, extracted_data):
        """Create or update a record in the target model linked to the parent record
        
        Args:
            parent_record: The parent record (e.g., flight.flight) to link to
            target_model: The name of the model to create record in
            mappings: List of mapping records for the target model
            post_result: Dictionary to store results
            extracted_data: Dictionary with original source data
        """
        # Build values and domain
        values, domain = self._build_post_process_values_and_domain(
            parent_record, target_model, mappings, extracted_data
        )
        
        # Skip if we don't have any values to create/update
        if not values:
            _logger.warning("No values to create/update for post-processing record, skipping")
            return
        
        # Ensure we have a valid domain for finding existing
        if not domain:
            _logger.warning("No domain criteria for finding existing records, will always create new")
        
        try:
            existing = self._find_existing_record(target_model, domain)
            
            if existing:
                self._update_post_process_record(target_model, existing, values, post_result)
            else:
                self._create_new_post_process_record(target_model, values, post_result)
                
        except Exception as e:
            self._handle_post_process_error(e, target_model, post_result)
    
    def _build_post_process_values_and_domain(self, parent_record, target_model, mappings, extracted_data):
        """Build values and domain for post-processing record
        
        Args:
            parent_record: The parent record to link to
            target_model: The name of the model to create record in
            mappings: List of mapping records for the target model
            extracted_data: Dictionary with original source data
            
        Returns:
            Tuple of (values, domain)
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
                transformed_value = mapping.with_context(parent_record_id=parent_record.id).transform_value(mapping.post_process_value)
                values[field_name] = transformed_value
                # If this is a key field, add it to the domain for finding existing records
                if mapping.is_key_field:
                    domain.append((field_name, '=', transformed_value))
                continue
            
            # Handle context values
            if mapping.use_context_value and mapping.context_variable_name:
                context_value = self.env.context.get(mapping.context_variable_name)
                if context_value is not None:
                    _logger.info("Using context value %s for field %s from variable %s", 
                                context_value, field_name, mapping.context_variable_name)
                    values[field_name] = context_value
                    # If this is a key field, add it to the domain
                    if mapping.is_key_field:
                        domain.append((field_name, '=', context_value))
                    continue
                else:
                    _logger.warning("Context variable %s not found in context for field %s", 
                                   mapping.context_variable_name, field_name)
                
            # Handle source field based values with transformation
            if mapping.source_field and mapping.source_field in extracted_data:
                # Get source value
                source_value = extracted_data.get(mapping.source_field)
                _logger.info("Processing source field %s with value: %s", mapping.source_field, source_value)
                
                # Apply the standard transformation
                transformed_value = mapping.with_context(parent_record_id=parent_record.id).transform_value(source_value, extracted_data)
                
                if transformed_value is not None:
                    values[field_name] = transformed_value
                    # Only add key fields to domain
                    if mapping.is_key_field:
                        domain.append((field_name, '=', transformed_value))
        
        return values, domain
    
    def _find_existing_record(self, model_name, domain):
        """Find an existing record by domain
        
        Args:
            model_name: Name of the model to search
            domain: Domain to use for search
            
        Returns:
            Record if found, None otherwise
        """
        if not domain:
            return None
            
        _logger.info("Checking for existing record with domain: %s", domain)
        existing = self.env[model_name].search(domain, limit=1)
        
        if existing:
            _logger.info("Found existing record %s with domain %s", existing, domain)
            
        return existing
    
    def _update_post_process_record(self, model_name, record, values, post_result):
        """Update an existing record
        
        Args:
            model_name: Name of the model
            record: Record to update
            values: Values to update with
            post_result: Dictionary to update with results
        """
        _logger.info("Updating existing %s record: %s with values: %s", model_name, record.id, values)
        record.write(values)
        post_result['post_updated'].append(record.id)
        _logger.info("Updated existing %s record: %s with values: %s", model_name, record.id, values)
    
    def _create_new_post_process_record(self, model_name, values, post_result):
        """Create a new record
        
        Args:
            model_name: Name of the model to create
            values: Values to create with
            post_result: Dictionary to update with results
        """
        _logger.info("Creating new %s record with values: %s", model_name, values)
        new_record = self.env[model_name].create(values)
        post_result['post_created'].append(new_record.id)
        _logger.info("Created new %s record: %s with values: %s", model_name, new_record.id, values)
    
    def _handle_post_process_error(self, error, model_name, post_result, record_id=None):
        """Handle error in post processing
        
        Args:
            error: The exception
            model_name: Name of the model that caused the error
            post_result: Dictionary to update with error
            record_id: ID of the record that caused the error (optional)
        """
        error_msg = f"Error creating/updating {model_name}: {str(error)}"
        if record_id:
            error_msg += f" for record {record_id}"
        post_result['post_errors'].append(error_msg)
        _logger.error(error_msg)
        _logger.error("Stack trace: %s", traceback.format_exc())
    
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
            update_values = self._get_update_values(domain, values, record)
            
            if update_values:
                _logger.debug("Updating record %s with values: %s", record, update_values)
                record.write(update_values)
        else:
            # Create a new record
            create_values = values.copy()
            create_context = {}
            
            # Apply context from mapping if provided
            if mapping and mapping.context:
                create_values, create_context = self._apply_mapping_context(mapping, create_values)
            
            _logger.debug("Creating new record with values: %s", create_values)
            if create_context:
                record = self.env[model_name].with_context(**create_context).create(create_values)
            else:
                record = self.env[model_name].create(create_values)
            
        return record
        
    def _get_update_values(self, domain, values, record):
        """Extract values that are not part of the search domain
        
        Args:
            domain: The domain used to search for the record
            values: All values for the record
            record: The existing record
            
        Returns:
            Dictionary of values that can be updated
        """
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
                
        return update_values
    
    def _apply_mapping_context(self, mapping, values):
        """Apply context from mapping to values
        
        Args:
            mapping: The mapping record that may contain context
            values: The values to apply context to
            
        Returns:
            Tuple of (updated_values, context_dict)
        """
        create_values = values.copy()
        create_context = {}
        
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
            
        return create_values, create_context

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
            content = self._decode_file_content(file_content)
            csv_reader = self._create_csv_reader(content, delimiter)
            records = self._process_csv_rows(csv_reader)
            return records
        except Exception as e:
            raise UserError(_("Error extracting data: %s") % str(e))
    
    @api.model
    def _decode_file_content(self, file_content):
        """Decode base64 file content to UTF-8 string"""
        return base64.b64decode(file_content).decode('utf-8')
        
    @api.model
    def _create_csv_reader(self, content, delimiter):
        """Create a CSV DictReader from string content"""
        return csv.DictReader(io.StringIO(content), delimiter=delimiter)
        
    @api.model
    def _process_csv_rows(self, reader):
        """Process CSV rows and clean values"""
        records = []
        for row in reader:
            # Clean up the row (strip whitespace from keys and values)
            cleaned_row = {k.strip(): v.strip() if isinstance(v, str) else v 
                          for k, v in row.items()}
            records.append(cleaned_row)
        return records
    
    def _apply_field_transformations(self, value, mapping, record=None):
        """Apply transformations to field values based on mapping configuration
        
        This method delegates to the mapping model's transform_value method,
        which implements the transformation logic.
        
        Args:
            value: The value to transform
            mapping: The mapping record to use for transformation
            record: The complete record dictionary (optional)
        """
        return mapping.transform_value(value, record)
    
    def _log_import_result(self, result):
        """Log the import result"""
        _logger.info("Import result: %s", result)
        self.env['base.import.pipeline.result'].create({
            'pipeline_id': self.id,
            'date': fields.Datetime.now(),
            'summary': f"Created: {len(result.get('created', []))}, Updated: {len(result.get('updated', []))}, Errors: {len(result.get('errors', []))}",
            'records_created': len(result.get('created', [])),
            'status': 'success' if not result.get('errors', []) else 'error',
            'log': str(result),
        })
