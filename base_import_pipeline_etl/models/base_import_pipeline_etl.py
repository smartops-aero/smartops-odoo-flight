import base64
import csv
import io
import json
import logging
import traceback

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class BaseImportPipeline(models.Model):
    _inherit = "base.import.pipeline"

    mapping_ids = fields.One2many(
        "base.import.pipeline.mapping", "pipeline_id", string="Field Mappings"
    )

    # Add batch size field for post-processing only
    batch_size = fields.Integer(
        string="Post-Process Batch Size",
        default=1000,
        help="Number of records to process in each batch during post-processing. Higher values are faster but use more memory.",
    )

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
            result = self._transform_single_record(
                i, record, regular_mappings, related_records_cache
            )
            if result:
                transformed_data.append(result)

        _logger.info(
            "Transformation complete, returning %s records", len(transformed_data)
        )
        return transformed_data

    def _get_regular_mappings(self):
        """Get regular mappings that are not marked for post-processing"""
        regular_mappings = self.mapping_ids.filtered(lambda m: not m.is_post_process)
        return regular_mappings

    def _transform_single_record(
        self, index, record, regular_mappings, related_records_cache
    ):
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
                self._process_field_mapping(
                    mapping, record, values, row_records, related_records_cache
                )

        # Add the transformed record to the result if it has values for the target model
        if values:
            return {"values": values, "original_data": record}
        else:
            return None

    def _process_field_mapping(
        self, mapping, record, values, row_records, related_records_cache
    ):
        """Process a single field mapping for a record"""
        source_value = record[mapping.source_field]

        # Skip if this is a relation mapping without a relation field
        if mapping.relation_model_id and not mapping.relation_field:
            return

        # Apply transformation to the source value
        transformed_value = self._apply_field_transformations(
            source_value, mapping, record
        )
        if transformed_value is None:
            _logger.warning(
                "Transformation returned None for mapping %s, value %s",
                mapping.description,
                source_value,
            )
            return

        # Handle direct field mappings (non-relational)
        if not mapping.relation_model_id:
            self._process_direct_field_mapping(
                mapping, transformed_value, values, row_records, related_records_cache
            )
        # Handle relational field mappings
        else:
            self._process_relational_field_mapping(
                mapping,
                transformed_value,
                values,
                row_records,
                related_records_cache,
                record,
            )

    def _process_direct_field_mapping(
        self, mapping, transformed_value, values, row_records, related_records_cache
    ):
        """Process a direct (non-relational) field mapping"""
        # If this mapping is for the target model, add it to the values
        if mapping.model_id.model == self.model_id.model:
            values[mapping.target_field] = transformed_value
        # Otherwise, it's for a related model - create/find it
        else:
            model_name = mapping.model_id.model
            field_name = mapping.target_field

            # If this is a key field, use it to identify the record
            if mapping.is_key_field:
                domain = [(field_name, "=", transformed_value)]

                # Check if we already have a record for this model in this row
                if model_name in row_records:
                    # Update the existing record with this field
                    model_record = row_records[model_name]
                    model_record.write({field_name: transformed_value})
                else:
                    # Create or find the record
                    model_values = {field_name: transformed_value}

                    model_record = self._get_or_create_record(
                        model_name, domain, model_values, mapping
                    )

                    # Store the record for this row
                    row_records[model_name] = model_record

                # Cache the record
                cache_key = f"{model_name}:{field_name}:{transformed_value}"
                related_records_cache[cache_key] = model_record
            else:
                # This is a non-key field for a related model
                # We need to find the record first
                if model_name in row_records:
                    # Update the existing record with this field
                    model_record = row_records[model_name]
                    model_record.write({field_name: transformed_value})

                    # Cache the record with this field value
                    cache_key = f"{model_name}:{field_name}:{transformed_value}"
                    related_records_cache[cache_key] = model_record

    def _process_relational_field_mapping(
        self,
        mapping,
        transformed_value,
        values,
        row_records,
        related_records_cache,
        record,
    ):
        """Process a relational field mapping"""
        relation_model = mapping.relation_model_id.model
        relation_field = mapping.relation_field

        # Try to find the related record in cache first or create it
        related_record = self._find_or_create_related_record(
            mapping,
            transformed_value,
            relation_model,
            relation_field,
            related_records_cache,
        )

        # If this mapping is for the target model, add it to the values
        if mapping.model_id.model == self.model_id.model:
            values[mapping.target_field] = related_record.id
        # Otherwise, it's for a related model - create/find it
        else:
            model_name = mapping.model_id.model
            field_name = mapping.target_field

            if model_name in row_records:
                # Update the existing record with this relation
                model_record = row_records[model_name]
                model_record.write({field_name: related_record.id})

                # Cache the updated record
                cache_key = f"{model_name}:{field_name}:{related_record.id}"
                related_records_cache[cache_key] = model_record
            else:
                # Create or find the record with this relation
                domain = [(field_name, "=", related_record.id)]
                model_values = {field_name: related_record.id}

                model_record = self._get_or_create_record(
                    model_name, domain, model_values, mapping
                )

                # Store the record for this row
                row_records[model_name] = model_record

                # Cache the record
                cache_key = f"{model_name}:{field_name}:{related_record.id}"
                related_records_cache[cache_key] = model_record

    def _find_or_create_related_record(
        self,
        mapping,
        transformed_value,
        relation_model,
        relation_field,
        related_records_cache,
    ):
        """Find or create a related record for a relational mapping"""
        # Try to find the related record in cache first
        cache_key = f"{relation_model}:{relation_field}:{transformed_value}"
        related_record = related_records_cache.get(cache_key)

        if related_record:
            return related_record

        # Build domain for lookup
        domain = [(relation_field, "=", transformed_value)]

        # Add additional lookup fields if specified
        if mapping.lookup_fields:
            additional_fields = [f.strip() for f in mapping.lookup_fields.split(",")]
            for field in additional_fields:
                if field:
                    domain = ["|", (field, "=", transformed_value)] + domain

        # Prepare values for creating the related record if needed
        related_values = {relation_field: transformed_value}

        # Find or create the related record
        related_record = self._get_or_create_record(
            relation_model, domain, related_values, mapping
        )

        # Cache the related record
        related_records_cache[cache_key] = related_record

        return related_record

    def load(self, transformed_data, **kwargs):
        """Load transformed data into the target model

        This method creates or updates records in the target model
        based on the transformed data.
        """

        # Initialize result structure
        result = self._initialize_import_result()

        if not transformed_data:
            return result

        # Get key fields for the target model
        key_mappings = self._get_key_mappings()

        has_key_fields = bool(key_mappings)
        if not has_key_fields:
            _logger.warning(
                "No key fields defined for target model %s. Will always create new records.",
                self.model_id.model,
            )

        try:
            # Process data in batches using bulk operations
            # Prepare data for bulk operations
            records_to_create = []
            records_to_update = []  # [(record, values)]
            
            # Map to track which original data corresponds to which record
            # This is needed for post-processing
            original_data_map = {}

            # First pass: identify existing records and prepare create/update lists
            for i, data in enumerate(transformed_data):
                try:
                    # Prepare values
                    values = data["values"]
                    original_data = kwargs.get("extracted_data", [])[i] if i < len(kwargs.get("extracted_data", [])) else {}
                    
                    # Find existing record if we have key fields
                    existing_record = None
                    if has_key_fields:
                        domain = []
                        for mapping in key_mappings:
                            field_name = mapping.target_field
                            if field_name in values:
                                domain.append((field_name, "=", values[field_name]))
                        
                        if domain:
                            existing_record = self.env[self.model_id.model].search(domain, limit=1)
                    
                    # Queue for creation or update
                    if existing_record:
                        records_to_update.append((existing_record, values))
                        # Store original data for post-processing
                        original_data_map[existing_record.id] = original_data
                        result["updated"].append(existing_record.id)
                    else:
                        records_to_create.append(values)
                        # We'll store original data after creation when we have IDs
                except Exception as record_error:
                    self._handle_record_error(record_error, i, data, len(transformed_data), result)
            
            # Bulk create new records - much more efficient than one by one
            if records_to_create:
                created_records = self.env[self.model_id.model].create(records_to_create)
                
                # Store IDs and map original data
                for i, record in enumerate(created_records):
                    result["created"].append(record.id)
                    # Map original data to record ID for potential post-processing
                    if i < len(kwargs.get("extracted_data", [])):
                        original_data_map[record.id] = kwargs.get("extracted_data", [])[i]
            
            # Bulk update records - group by identical values for efficiency
            update_groups = {}
            for record, values in records_to_update:
                values_key = str(sorted(values.items()))
                if values_key not in update_groups:
                    update_groups[values_key] = {
                        "values": values,
                        "records": self.env[self.model_id.model].browse(),
                    }
                update_groups[values_key]["records"] |= record
            
            # Process each update group
            for group_info in update_groups.values():
                if group_info["records"]:
                    group_info["records"].write(group_info["values"])
            
            # Store original data map in result for post-processing
            result["original_data_map"] = original_data_map
            
        except Exception as e:
            self._handle_batch_error(e, result)

        return result

    def _initialize_import_result(self):
        """Initialize the structure for import results"""
        return {
            "created": [],
            "updated": [],
            "errors": [],
        }

    def _get_key_mappings(self):
        """Get key mappings for the target model"""
        return self.mapping_ids.filtered(
            lambda m: m.model_id.model == self.model_id.model and m.is_key_field
        )

    def _handle_record_error(self, error, index, data, total_records, result):
        """Handle and log an error for a specific record"""
        error_msg = f"Error processing record {index+1}/{total_records}: {str(error)}"
        _logger.error(error_msg)
        _logger.error("Values that caused the error: %s", data)
        _logger.error("Stack trace: %s", traceback.format_exc())
        result["errors"].append(error_msg)

    def _handle_batch_error(self, error, result):
        """Handle and log a batch processing error"""
        error_msg = f"Error in batch processing: {str(error)}"
        _logger.error(error_msg)
        _logger.error("Stack trace: %s", traceback.format_exc())
        result["errors"].append(error_msg)

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
            return post_result

        # Get all post-process mappings
        post_mappings = self._get_post_process_mappings()
        if not post_mappings:
            return post_result
        
        # Associate original data with record IDs for reference
        original_data_by_id = self._associate_data_with_record_ids(
            import_result, extracted_data
        )

        # Get records that were created or updated
        records, main_model = self._get_parent_records_for_post_process(import_result)

        if not main_model:
            _logger.error("Could not determine main model for post-processing")
            post_result["post_errors"].append(
                "Could not determine main model for post-processing"
            )
            return post_result

        if not records:
            return post_result

        # Group mappings by model and group_key
        mapping_groups = self._group_post_process_mappings(post_mappings)

        # Process each group of mappings with batch operations
        for group_key, mappings in mapping_groups.items():
            model_name = mappings[0].model_id.model
            
            try:
                with self.env.cr.savepoint():
                    self._batch_process_post_records(
                        records, model_name, mappings, original_data_by_id, post_result
                    )
            except Exception as e:
                self._handle_post_process_error(e, model_name, post_result)

        return post_result

    def _initialize_post_process_result(self):
        """Initialize the structure for post-process results"""
        return {"post_created": [], "post_updated": [], "post_errors": []}

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
        # If the optimized load method was used, the mapping is already provided
        if "original_data_map" in import_result:
            return import_result["original_data_map"]
        
        original_data_by_id = {}
        for idx, data in enumerate(extracted_data):
            if idx < len(import_result.get("created", [])):
                record_id = import_result["created"][idx]
                original_data_by_id[record_id] = data
            elif idx - len(import_result.get("created", [])) < len(
                import_result.get("updated", [])
            ):
                record_id = import_result["updated"][
                    idx - len(import_result.get("created", []))
                ]
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
        main_model_mapping = self.mapping_ids.filtered(
            lambda m: not m.is_post_process and m.sequence == 0
        )
        main_model = (
            main_model_mapping.model_id.model
            if main_model_mapping
            else self.model_id.model
        )

        if import_result.get("created") or import_result.get("updated"):
            records = self.env[main_model].browse(
                import_result.get("created", []) + import_result.get("updated", [])
            )

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

    def _batch_process_post_records(self, parent_records, target_model, mappings, original_data_by_id, post_result):
        """Process creation and update of post-process records in batches

        Args:
            parent_records: Records that need post-processing
            target_model: Model name to create records in
            mappings: List of mapping records for the target model
            original_data_by_id: Dictionary mapping record IDs to original data
            post_result: Dictionary to update with results
        """
        # Prepare data for batch operations
        records_to_create, records_to_update = self._prepare_post_process_records(
            parent_records, target_model, mappings, original_data_by_id, post_result
        )
        
        # Bulk create new records
        self._bulk_create_post_process_records(
            target_model, records_to_create, post_result
        )
        
        # Group and bulk update existing records
        update_groups = self._group_records_for_update(target_model, records_to_update)
        
        # Process each update group in bulk
        self._bulk_update_post_process_records(target_model, update_groups, post_result)

    def _prepare_post_process_records(self, parent_records, target_model, mappings, original_data_by_id, post_result):
        """Prepare data for post-process records

        Args:
            parent_records: Records that need post-processing
            target_model: Model name to create records in
            mappings: List of mapping records for the target model
            original_data_by_id: Dictionary mapping record IDs to original data
            post_result: Dictionary to update with results

        Returns:
            Tuple of (records_to_create, records_to_update)
        """
        records_to_create = []
        records_to_update = []  # [(record, values)]
        
        # First pass: prepare data for batch operations
        for parent_record in parent_records:
            try:
                # Get original data for this record
                extracted_data = original_data_by_id.get(parent_record.id, {})
                
                # Build values and domain for finding/creating records
                values, domain = self._build_post_process_values_and_domain(
                    parent_record, target_model, mappings, extracted_data
                )
                
                # Skip if we don't have any values
                if not values:
                    continue
                    
                # Try to find an existing record
                existing = None
                if domain:
                    existing = self.env[target_model].search(domain, limit=1)
                    
                # Queue for update or creation
                if existing:
                    records_to_update.append((existing, values))
                else:
                    records_to_create.append(values)
                
            except Exception as e:
                self._handle_post_process_error(
                    e, target_model, post_result, record_id=parent_record.id
                )
        
        return records_to_create, records_to_update

    def _bulk_create_post_process_records(self, target_model, records_to_create, post_result):
        """Bulk create new post-process records

        Args:
            target_model: Model name to create records in
            records_to_create: List of dictionaries with values to create
            post_result: Dictionary to update with results
        """
        # Bulk create new records
        if records_to_create:
            try:
                created_records = self.env[target_model].create(records_to_create)
                post_result["post_created"].extend(created_records.ids)
            except Exception as e:
                error_msg = f"Error bulk creating {target_model} records: {str(e)}"
                post_result["post_errors"].append(error_msg)
                _logger.error(error_msg)
                _logger.error("Stack trace: %s", traceback.format_exc())

    def _group_records_for_update(self, target_model, records_to_update):
        """Group records to update by identical values for efficiency

        Args:
            target_model: Model name to update records in
            records_to_update: List of tuples with (record, values) to update

        Returns:
            Dictionary with groups of records to update
        """
        update_groups = {}
        for record, values in records_to_update:
            # Pre-process values if needed (to be overridden in specialized imports)
            values = self._prepare_update_values(target_model, record, values)
            
            values_key = str(sorted(values.items()))
            if values_key not in update_groups:
                update_groups[values_key] = {
                    "values": values,
                    "records": self.env[target_model].browse(),
                }
            update_groups[values_key]["records"] |= record
        
        return update_groups
        
    def _prepare_update_values(self, target_model, record, values):
        """Hook method to preprocess values before update
        Can be overridden in specialized imports to handle model-specific constraints
        
        Args:
            target_model: Model name to update records in
            record: Record to update
            values: Values to update
            
        Returns:
            Processed values dict ready for update
        """
        return values

    def _bulk_update_post_process_records(self, target_model, update_groups, post_result):
        """Bulk update post-process records

        Args:
            target_model: Model name to update records in
            update_groups: Dictionary with groups of records to update
            post_result: Dictionary to update with results
        """
        # Process each update group in bulk
        for group_info in update_groups.values():
            if group_info["records"]:
                try:
                    group_info["records"].write(group_info["values"])
                    post_result["post_updated"].extend(group_info["records"].ids)
                except Exception as e:
                    error_msg = f"Error bulk updating {target_model} records: {str(e)}"
                    post_result["post_errors"].append(error_msg)
                    _logger.error(error_msg)
                    _logger.error("Stack trace: %s", traceback.format_exc())

    def _build_post_process_values_and_domain(
        self, parent_record, target_model, mappings, extracted_data
    ):
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
            if mapping.transformation == "parent_record_id":
                values[field_name] = parent_record.id
                # If this is a key field, add it to the domain for finding existing records
                if mapping.is_key_field:
                    domain.append((field_name, "=", parent_record.id))
                continue

            # Handle static values (from post_process_value)
            if mapping.post_process_value:
                transformed_value = mapping.with_context(
                    parent_record_id=parent_record.id
                ).transform_value(mapping.post_process_value)
                values[field_name] = transformed_value
                # If this is a key field, add it to the domain for finding existing records
                if mapping.is_key_field:
                    domain.append((field_name, "=", transformed_value))
                continue

            # Handle context values
            if mapping.use_context_value and mapping.context_variable_name:
                context_value = self.env.context.get(mapping.context_variable_name)
                if context_value is not None:
                    values[field_name] = context_value
                    # If this is a key field, add it to the domain
                    if mapping.is_key_field:
                        domain.append((field_name, "=", context_value))
                    continue
                else:
                    _logger.warning(
                        "Context variable %s not found in context for field %s",
                        mapping.context_variable_name,
                        field_name,
                    )

            # Handle source field based values with transformation
            if mapping.source_field and mapping.source_field in extracted_data:
                # Get source value
                source_value = extracted_data.get(mapping.source_field)

                # Apply the standard transformation
                transformed_value = mapping.with_context(
                    parent_record_id=parent_record.id
                ).transform_value(source_value, extracted_data)

                if transformed_value is not None:
                    values[field_name] = transformed_value
                    # Only add key fields to domain
                    if mapping.is_key_field:
                        domain.append((field_name, "=", transformed_value))

        return values, domain

    def _handle_post_process_error(
        self, error, model_name, post_result, record_id=None
    ):
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
        post_result["post_errors"].append(error_msg)
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
        record = self.env[model_name].search(domain, limit=1)

        if record:
            # Update the existing record with any new values
            update_values = self._get_update_values(domain, values, record)

            if update_values:
                record.write(update_values)
        else:
            # Create a new record
            create_values = values.copy()
            create_context = {}

            # Apply context from mapping if provided
            if mapping and mapping.context:
                create_values, create_context = self._apply_mapping_context(
                    mapping, create_values
                )

            if create_context:
                record = (
                    self.env[model_name]
                    .with_context(**create_context)
                    .create(create_values)
                )
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
                    if key.startswith("default_"):
                        field_name = key[8:]  # Remove 'default_' prefix
                        create_values[field_name] = value
                    else:
                        create_context[key] = value

        except Exception as e:
            _logger.warning("Error parsing context from mapping: %s", str(e))

        return create_values, create_context

    def run_import(self, **kwargs):
        """Run the ETL import process"""

        try:
            # Extract data from the source
            extracted_data = self.extract(**kwargs)

            # Transform the data
            transformed_data = self.transform(extracted_data, **kwargs)

            # Initialize the combined result
            combined_result = {
                "created": [],
                "updated": [],
                "errors": [],
                "post_created": [],
                "post_updated": [],
                "post_errors": [],
            }

            # Process in batches for better performance and memory management
            batch_size = self.batch_size or 1000
            _logger.info(
                "Processing %s records in batches of %s",
                len(transformed_data),
                batch_size,
            )

            # Process each batch
            for i in range(0, len(transformed_data), batch_size):
                batch = transformed_data[i : i + batch_size]
                batch_extracted = extracted_data[i : i + batch_size]

                _logger.info(
                    "Processing batch %s to %s (%s records)",
                    i,
                    min(i + batch_size, len(transformed_data)),
                    len(batch),
                )

                # Load the batch
                batch_result = self.load(batch, extracted_data=batch_extracted)

                # Run post-processing for this batch
                batch_post_result = self.post_process(
                    batch_result, extracted_data=batch_extracted
                )

                # Merge batch results into combined result
                for key in ["created", "updated", "errors"]:
                    if key in batch_result:
                        combined_result[key].extend(batch_result[key])

                # Merge post-processing results
                for key in ["post_created", "post_updated", "post_errors"]:
                    if key in batch_post_result:
                        combined_result[key].extend(batch_post_result[key])

                # Commit after each batch except the last one
                if i + batch_size < len(transformed_data):
                    self.env.cr.commit()
                    _logger.info("Committed transaction after batch %s", i)

            # Log the combined result
            self._log_import_result(combined_result)

            return combined_result

        except Exception as e:
            _logger.error("Error running import: %s", str(e))
            _logger.error("Stack trace: %s", traceback.format_exc())
            # Log error
            self.env["base.import.pipeline.result"].create(
                {
                    "pipeline_id": self.id,
                    "date": fields.Datetime.now(),
                    "summary": str(e),
                    "records_created": 0,
                    "status": "error",
                    "log": str(e),
                }
            )

            return {
                "created": [],
                "updated": [],
                "errors": [{"type": "import_error", "error": str(e)}],
            }

    @api.model
    def _extract_from_csv(self, file_content, filename=None, delimiter=","):
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
        return base64.b64decode(file_content).decode("utf-8")

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
            cleaned_row = {
                k.strip(): v.strip() if isinstance(v, str) else v
                for k, v in row.items()
            }
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
        self.env["base.import.pipeline.result"].create(
            {
                "pipeline_id": self.id,
                "date": fields.Datetime.now(),
                "summary": f"Created: {len(result.get('created', []))}, Updated: {len(result.get('updated', []))}, Errors: {len(result.get('errors', []))}",
                "records_created": len(result.get("created", [])),
                "status": "success" if not result.get("errors", []) else "error",
                "log": str(result),
            }
        )
