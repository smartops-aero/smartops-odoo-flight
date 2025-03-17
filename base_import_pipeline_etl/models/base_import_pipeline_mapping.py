from odoo import api, fields, models, _


class ImportPipelineMapping(models.Model):
    _name = "base.import.pipeline.mapping"
    _description = "Import Pipeline Field Mapping"
    _order = "sequence, id"
    
    pipeline_id = fields.Many2one('base.import.pipeline', string='Pipeline', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    source_field = fields.Char(required=True, string='Source Field')
    target_field = fields.Char(required=True, string='Target Field')
    transformation = fields.Selection([
        ('direct', 'Direct Mapping'),
        ('date_format', 'Date Format Conversion'),
        ('lookup', 'Lookup Reference'),
    ], default='direct', required=True, string='Transformation')
    transformation_options = fields.Text(string='Transformation Options',
                                        help="Options for the transformation (JSON format)")
    model = fields.Selection([
        ('flight.aerodrome', 'Aerodrome'),
        ('flight.aircraft', 'Aircraft'),
        ('flight.flight', 'Flight'),
    ], string='Target Model', required=True)
    field_type = fields.Selection([
        ('source', 'Source Field'),
        ('target', 'Target Field'),
    ], string='Field Type', default='target', required=True)
    is_required = fields.Boolean(string='Required', default=False)
    note = fields.Text(string='Notes')
    context = fields.Selection([
        ('departure', 'Departure'),
        ('arrival', 'Arrival'),
        ('both', 'Both'),
        ('none', 'None'),
    ], string="Context", default='none', help="Additional context for the mapping")
