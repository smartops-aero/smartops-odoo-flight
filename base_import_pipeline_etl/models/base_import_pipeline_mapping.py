from odoo import api, fields, models, _


class ImportPipelineMapping(models.Model):
    _name = "base.import.pipeline.mapping"
    _description = "Import Pipeline Field Mapping"
    _order = "sequence, id"
    
    description = fields.Text(string='Description about this mapping')
    pipeline_id = fields.Many2one('base.import.pipeline', string='Pipeline', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    source_field = fields.Char(required=True, string='Source Field')
    target_field = fields.Char(required=True, string='Target Field')
    transformation = fields.Selection([
        ('direct', 'Direct Mapping'),
        ('date_format', 'Date Format Conversion'),
        ('lookup', 'Lookup Reference'),
        ('regex', 'Regular Expression'),
    ], default='direct', required=True, string='Transformation')
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
