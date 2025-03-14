# -*- coding: utf-8 -*-
import base64
import csv
import io
import logging
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class FlightImportWizard(models.TransientModel):
    _name = 'flight.import.wizard'
    _description = 'Flight Data Import Wizard'
    
    name = fields.Char('Import Name', default=lambda self: _('Import %s') % datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    template_id = fields.Many2one('flight.import.template', string='Import Template', required=True)
    file = fields.Binary(string='Import File', required=True)
    file_name = fields.Char(string='File Name')
    delimiter = fields.Char(string='Delimiter', default=',', help='CSV delimiter character')
    quotechar = fields.Char(string='Quote Character', default='"', help='CSV quote character')
    
    state = fields.Selection([
        ('upload', 'Upload File'),
        ('mapping', 'Mapping'),
        ('preview', 'Preview'),
        ('done', 'Done')
    ], default='upload', string='Import State')
    
    # Preview data
    preview_ids = fields.One2many('flight.import.preview.line', 'wizard_id', string='Preview Lines')
    
    # Results
    log_messages = fields.Text(string='Log Messages', readonly=True)
    imported_flight_count = fields.Integer(string='Imported Flights', readonly=True)
    imported_time_count = fields.Integer(string='Imported Time Entries', readonly=True)
    imported_event_count = fields.Integer(string='Imported Events', readonly=True)
    
    @api.onchange('template_id')
    def _onchange_template_id(self):
        """Update delimiter and quotechar based on template"""
        if self.template_id:
            # Could be extended to set format-specific delimiters
            pass
    
    def action_parse_file(self):
        """Parse the uploaded file and prepare for mapping"""
        self.ensure_one()
        if not self.file:
            raise UserError(_("Please upload a file first."))
        
        # Read the file
        try:
            file_content = base64.b64decode(self.file)
            # Try to detect encoding, default to utf-8
            try:
                file_content = file_content.decode('utf-8')
            except UnicodeDecodeError:
                file_content = file_content.decode('latin-1')
                
            # Parse CSV
            reader = csv.DictReader(
                io.StringIO(file_content),
                delimiter=self.delimiter or ',',
                quotechar=self.quotechar or '"'
            )
            
            # Create preview lines (first 5 rows)
            self.preview_ids.unlink()
            for i, row in enumerate(reader):
                if i >= 5:  # Limit preview to 5 rows
                    break
                    
                self.env['flight.import.preview.line'].create({
                    'wizard_id': self.id,
                    'row_index': i,
                    'row_data': str(row),
                })
                
            self.state = 'mapping'
            
        except Exception as e:
            raise UserError(_("Error parsing file: %s") % str(e))
            
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_preview_import(self):
        """Generate a preview of the import"""
        self.ensure_one()
        # This would normally parse the file and show what would be imported
        # For now, just move to the preview state
        self.state = 'preview'
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_import(self):
        """Execute the actual import process"""
        self.ensure_one()
        
        if not self.file:
            raise UserError(_("Please upload a file first."))
            
        try:
            file_content = base64.b64decode(self.file)
            # Try to detect encoding, default to utf-8
            try:
                file_content = file_content.decode('utf-8')
            except UnicodeDecodeError:
                file_content = file_content.decode('latin-1')
                
            # Get the parser method based on the template
            parser_method = self.template_id.get_parser_method()
            
            # Check if the method exists
            if not hasattr(self, parser_method):
                raise UserError(_("No parser found for format %s") % self.template_id.source_format)
                
            # Call the parser method
            log_messages = []
            result = getattr(self, parser_method)(log_messages)
            
            # Update counters
            self.imported_flight_count = result.get('flights', 0)
            self.imported_time_count = result.get('times', 0)
            self.imported_event_count = result.get('events', 0)
            
            # Update log
            self.log_messages = '\n'.join(log_messages)
            
            # Update state
            self.state = 'done'
            
        except Exception as e:
            raise UserError(_("Error during import: %s") % str(e))
            
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def _parse_data_common(self, data_rows, log_messages):
        """Common parsing logic for all formats"""
        result = {
            'flights': 0,
            'times': 0,
            'events': 0,
        }
        
        # Get the model sequence from the template
        model_sequence = self.template_id.get_model_sequence()
        
        # Process each model in sequence
        for model_name in model_sequence:
            # Get mappings for this model
            mappings = self.template_id.get_mappings_by_model(model_name)
            
            # Skip if no mappings for this model
            if not mappings:
                continue
                
            # Process each row
            for row in data_rows:
                # Transform data according to mappings
                record_data = self._transform_row_data(row, mappings, log_messages)
                
                # Skip if no data
                if not record_data:
                    continue
                    
                # Create or update record
                record = self._create_or_update_record(model_name, record_data, log_messages)
                
                # Update counters
                if record and model_name == 'flight.flight':
                    result['flights'] += 1
                elif record and model_name == 'flight.pilot.time':
                    result['times'] += 1
                elif record and model_name == 'flight.pilot.event':
                    result['events'] += 1
                    
        return result
    
    def _transform_row_data(self, row, mappings, log_messages):
        """Transform row data according to mappings"""
        result = {}
        
        for mapping in mappings:
            field_name = mapping.field_id.name
            
            # Skip if source field not in row and not constant
            if mapping.transform_type != 'constant' and mapping.source_field not in row:
                if mapping.is_required:
                    log_messages.append(_("Required field %s not found in row") % mapping.source_field)
                    return None
                continue
                
            # Get value based on transform type
            if mapping.transform_type == 'direct':
                result[field_name] = row[mapping.source_field]
            elif mapping.transform_type == 'function':
                # Call transform function
                if hasattr(self, mapping.transform_function):
                    result[field_name] = getattr(self, mapping.transform_function)(
                        row[mapping.source_field], mapping, row
                    )
                else:
                    log_messages.append(_("Transform function %s not found") % mapping.transform_function)
            elif mapping.transform_type == 'constant':
                result[field_name] = mapping.constant_value
            elif mapping.transform_type == 'relation':
                # Lookup related record
                relation_model = mapping.field_id.relation
                domain = [(mapping.relation_field, '=', row[mapping.source_field])]
                related_record = self.env[relation_model].search(domain, limit=1)
                if related_record:
                    result[field_name] = related_record.id
                else:
                    log_messages.append(_("Related record not found for %s = %s") % 
                                      (mapping.relation_field, row[mapping.source_field]))
                    
        return result
    
    def _create_or_update_record(self, model_name, record_data, log_messages):
        """Create or update a record"""
        model = self.env[model_name]
        
        # Get identifier fields
        identifier_mappings = self.template_id.mapping_ids.filtered(
            lambda m: m.model_id.model == model_name and m.is_identifier
        )
        
        # If no identifiers, always create
        if not identifier_mappings:
            try:
                return model.create(record_data)
            except Exception as e:
                log_messages.append(_("Error creating %s: %s") % (model_name, str(e)))
                return None
                
        # Build domain for existing record lookup
        domain = []
        for mapping in identifier_mappings:
            field_name = mapping.field_id.name
            if field_name in record_data:
                domain.append((field_name, '=', record_data[field_name]))
                
        # Search for existing record
        existing = model.search(domain, limit=1) if domain else None
        
        try:
            if existing:
                # Update existing record
                existing.write(record_data)
                return existing
            else:
                # Create new record
                return model.create(record_data)
        except Exception as e:
            log_messages.append(_("Error creating/updating %s: %s") % (model_name, str(e)))
            return None


class FlightImportPreviewLine(models.TransientModel):
    _name = 'flight.import.preview.line'
    _description = 'Flight Import Preview Line'
    
    wizard_id = fields.Many2one('flight.import.wizard', required=True, ondelete='cascade')
    row_index = fields.Integer(string='Row')
    row_data = fields.Text(string='Data')
    is_valid = fields.Boolean(string='Valid', default=True)
    validation_message = fields.Text(string='Validation Message')
