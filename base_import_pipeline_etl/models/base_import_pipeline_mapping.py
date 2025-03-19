from odoo import api, fields, models, _
import re
import logging

_logger = logging.getLogger(__name__)

class ImportPipelineMapping(models.Model):
    _name = "base.import.pipeline.mapping"
    _description = "Import Pipeline Field Mapping"
    _order = "sequence, id"
    
    description = fields.Text(string='Description about this mapping')
    pipeline_id = fields.Many2one('base.import.pipeline', string='Pipeline', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    source_field = fields.Char(string='Source Field', required=False, help="Field name in the source data")
    target_field = fields.Char(required=True, string='Target Field')
    transformation = fields.Selection(
        selection='_selection_transformation',
        default='direct', 
        required=True, 
        string='Transformation'
    )
    model_id = fields.Many2one('ir.model', string='Target Model', required=True, ondelete='cascade')
    model = fields.Char(related='model_id.model', string='Model Name', store=True)
    is_required = fields.Boolean(string='Required', default=False)
    
    # Relation configuration
    relation_model_id = fields.Many2one('ir.model', string='Related Model',
        help="For relational fields, specify the model to look up", ondelete='cascade')
    relation_model = fields.Char(related='relation_model_id.model', string='Related Model Name', store=True)
    relation_field = fields.Char(string='Relation Field',
        help="Field in the related model to use for lookup (e.g., 'icao' for aerodromes)")
    
    # Lookup configuration
    lookup_fields = fields.Char(
        string='Additional Lookup Fields',
        help="Comma-separated list of additional fields to use for lookup (e.g., 'name,code')"
    )
    
    # Context for new records during lookup
    context = fields.Text(
        string='Creation Context',
        help="""Context values to use when creating new records during lookup transformations.
Uses standard Odoo 'default_' prefix convention for setting default values.
Example: {"default_is_company": true, "default_company_type": "company"}

Common use cases:
- Setting is_company=True for new partners: {"default_is_company": true}
- Setting a default country: {"default_country_id": 233}
- Setting a default status: {"default_state": "draft"}"""
    )
    
    # Regex configuration
    regex_pattern = fields.Char(
        string='Regex Pattern',
        help="Regular expression pattern to apply to the source value"
    )
    regex_replacement = fields.Char(
        string='Regex Replacement',
        help="Replacement pattern for regex matches (use \\1, \\2, etc. for groups)"
    )
    
    # Default value
    default_value = fields.Char(
        string='Default Value',
        help="Default value to use if source field is empty or transformation fails"
    )
    
    # Record identification
    is_key_field = fields.Boolean(
        string='Is Key Field',
        help="If checked, this field will be used to identify existing records. For each model, at least one mapping should have this checked.",
        default=False
    )
    
    # Post-processing configuration
    is_post_process = fields.Boolean(
        string='Post-Process Mapping',
        help="If checked, this mapping will be processed after the main import is complete. Used for creating related records that depend on the newly created record IDs.",
        default=False
    )
    
    post_process_value = fields.Char(
        string='Post-Process Value',
        help="Static value to use for this field during post-processing, when not using a source field."
    )
    
    use_context_value = fields.Boolean(
        string='Use Context Value',
        help="If checked, the system will look for a value in the context using the context_variable_name",
        default=False
    )
    
    context_variable_name = fields.Char(
        string='Context Variable Name',
        help="Name of the context variable to use when use_context_value is True. For example: 'import_partner_id'"
    )
    
    group_key = fields.Char(string='Group Key', 
                           help="Mappings with the same group key will be processed together to create a single record. "
                                "Use different group keys for mappings that should create separate records even with the same model.")
    
    @api.model
    def _selection_transformation(self):
        """Selection function for transformation types.
        
        This can be extended by other modules to add custom transformations.
        """
        return [
            ('direct', 'Direct Mapping'),
            ('date_format', 'Date Format Conversion'),
            ('lookup', 'Lookup Reference'),
            ('regex', 'Regular Expression'),
            ('parent_record_id', 'Parent Record ID'),
            ('minutes_to_hours', 'Minutes to Hours'),
            ('ref_id', 'XML Reference to Database ID')
        ]
    
    def transform_value(self, value):
        """Transform a value based on the mapping configuration.
        
        This method uses a dispatch pattern to call the appropriate transformation
        method based on the transformation type.
        """
        if not value and self.default_value:
            return self.default_value
            
        # Use dispatch pattern for all transformations
        method_name = f"_transform_{self.transformation}"
        if hasattr(self, method_name) and callable(getattr(self, method_name)):
            return getattr(self, method_name)(value)
        
        # If no method found, return original value or default
        _logger.warning("No transformation method found for %s", self.transformation)
        return self.default_value if self.default_value else value
    
    def _transform_direct(self, value):
        """Direct mapping transformation - returns the value as is"""
        return value
    
    def _transform_date_format(self, value):
        """Date format transformation - converts DD-MM-YYYY to YYYY-MM-DD"""
        if value and len(value) == 10:  # Simple validation
            parts = value.split('-')
            if len(parts) == 3:
                return f"{parts[2]}-{parts[1]}-{parts[0]}"
        return value
    
    def _transform_lookup(self, value):
        """Lookup transformation - returns the value for lookup in the transform method"""
        # For lookup transformations, we just return the value
        # The actual lookup is handled in the transform method
        return value
    
    def _transform_regex(self, value):
        """Regex transformation - applies regex pattern and replacement"""
        if value and self.regex_pattern and self.regex_replacement:
            try:
                return re.sub(self.regex_pattern, self.regex_replacement, value)
            except Exception:
                # If regex fails, return original value or default
                return self.default_value if self.default_value else value
        return value
    
    def _transform_parent_record_id(self, value):
        """Parent record ID transformation
        
        This is a placeholder for the post-processing phase.
        During normal transformation this is not used.
        During post-processing, the parent record ID is set directly.
        """
        return value
    
    def _transform_minutes_to_hours(self, value):
        """Minutes to hours transformation - converts minutes to hours by dividing by 60"""
        try:
            minutes = float(value)
            return minutes / 60.0
        except (ValueError, TypeError):
            return 0.0
    
    def _transform_ref_id(self, value):
        """Transform an XML reference to its database ID"""
        if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
            # Already an ID
            return int(value)
        elif hasattr(self.env.ref, value):
            # It's a reference string like 'module.xmlid'
            try:
                result = self.env.ref(value).id
                _logger.info("Resolved ref_id %s to ID %s", value, result)
                return result
            except Exception:
                _logger.error("Failed to resolve ref_id %s", value)
        return value
    
    @api.onchange('transformation')
    def _onchange_transformation(self):
        """Show/hide relevant fields based on transformation type"""
        if self.transformation != 'lookup':
            self.lookup_fields = False
            self.relation_model_id = False
            self.relation_field = False
            self.context = False
        
        if self.transformation != 'regex':
            self.regex_pattern = False
            self.regex_replacement = False
            
    @api.onchange('relation_model_id')
    def _onchange_relation_model_id(self):
        """Clear relation field when model changes"""
        if self.relation_model_id:
            self.relation_field = False
