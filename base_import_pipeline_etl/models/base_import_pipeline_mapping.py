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
    source_field = fields.Char(required=True, string='Source Field')
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
    
    @api.onchange('transformation')
    def _onchange_transformation(self):
        """Show/hide relevant fields based on transformation type"""
        if self.transformation != 'lookup':
            self.lookup_fields = False
            self.relation_model_id = False
            self.relation_field = False
        
        if self.transformation != 'regex':
            self.regex_pattern = False
            self.regex_replacement = False
            
    @api.onchange('relation_model_id')
    def _onchange_relation_model_id(self):
        """Clear relation field when model changes"""
        if self.relation_model_id:
            self.relation_field = False
