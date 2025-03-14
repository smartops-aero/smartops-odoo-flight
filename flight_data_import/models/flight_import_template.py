# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class FlightImportTemplate(models.Model):
    _name = 'flight.import.template'
    _description = 'Flight Import Template'
    
    name = fields.Char(required=True)
    source_format = fields.Selection([], string='Source Format')
    description = fields.Text()
    active = fields.Boolean(default=True)
    
    # Mappings for different models
    mapping_ids = fields.One2many('flight.import.mapping', 'template_id', 
                                  string='Field Mappings')
    
    # Processing sequence - determines order of model processing
    model_sequence_ids = fields.One2many('flight.import.model.sequence', 'template_id', 
                                        string='Model Processing Sequence')
    
    def get_parser_method(self):
        """Return the method name to parse this format"""
        return f"_parse_{self.source_format}_data"
    
    def get_mappings_by_model(self, model_name):
        """Get all mappings for a specific model"""
        return self.mapping_ids.filtered(lambda m: m.model_id.model == model_name)
    
    def get_model_sequence(self):
        """Get the sequence of models to process in order"""
        return self.model_sequence_ids.sorted('sequence').mapped('model_id.model')


class FlightImportModelSequence(models.Model):
    _name = 'flight.import.model.sequence'
    _description = 'Flight Import Model Processing Sequence'
    
    template_id = fields.Many2one('flight.import.template', required=True, ondelete='cascade')
    model_id = fields.Many2one('ir.model', required=True, string='Model', 
                              domain=[('model', 'in', ['flight.flight', 'flight.pilot.time', 'flight.pilot.event'])],
                              ondelete='cascade')
    sequence = fields.Integer(default=10, help="Order in which models should be processed")
    
    _sql_constraints = [
        ('unique_model_template', 'unique(template_id, model_id)', 
         'Each model can only appear once in a template sequence!')
    ]
