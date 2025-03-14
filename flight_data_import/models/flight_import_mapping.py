# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class FlightImportMapping(models.Model):
    _name = 'flight.import.mapping'
    _description = 'Flight Import Field Mapping'
    _order = 'model_id, sequence'
    
    template_id = fields.Many2one('flight.import.template', required=True, ondelete='cascade')
    model_id = fields.Many2one('ir.model', required=True, string='Model',
                              domain=[('model', 'in', ['flight.flight', 'flight.pilot.time', 'flight.pilot.event', 
                                                     'flight.aircraft', 'flight.aerodrome'])],
                              ondelete='cascade')
    field_id = fields.Many2one('ir.model.fields', required=True, string='Target Field',
                              domain="[('model_id', '=', model_id)]",
                              ondelete='cascade')
    source_field = fields.Char(string='Source Field', help="Field name in the source file")
    sequence = fields.Integer(default=10)
    
    # For complex transformations
    transform_type = fields.Selection([
        ('direct', 'Direct Mapping'),
        ('function', 'Function Call'),
        ('constant', 'Constant Value'),
        ('relation', 'Relation Lookup'),
    ], default='direct', required=True, string='Transformation Type')
    
    transform_function = fields.Char(string='Transform Function', 
                                    help="Name of the function to call for transformation")
    constant_value = fields.Char(string='Constant Value', 
                                help="Value to use for constant mapping")
    relation_field = fields.Char(string='Relation Field', 
                               help="Field to use for relation lookup")
    
    is_required = fields.Boolean(string='Required', 
                               help="Whether this field is required for import")
    is_identifier = fields.Boolean(string='Is Identifier', 
                                 help="Whether this field is used to identify existing records")
    
    _sql_constraints = [
        ('unique_field_template', 'unique(template_id, model_id, field_id)', 
         'Each field can only be mapped once per template and model!')
    ]
    
    @api.onchange('model_id')
    def _onchange_model_id(self):
        """Reset field_id when model changes"""
        self.field_id = False
    
    @api.onchange('transform_type')
    def _onchange_transform_type(self):
        """Reset related fields when transform type changes"""
        if self.transform_type != 'function':
            self.transform_function = False
        if self.transform_type != 'constant':
            self.constant_value = False
        if self.transform_type != 'relation':
            self.relation_field = False
