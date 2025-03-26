# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
from datetime import datetime
import io
import csv
import base64
import itertools
_logger = logging.getLogger(__name__)

class ImportExtended(models.TransientModel):
    _inherit = 'base_import.import'

    transformation_type = fields.Selection([
        ('none', 'No Transformation'),
        ('crewlounge', 'CrewLounge Format')
    ], string='Transformation', default='none', required=True)
    
    base_pilot_id = fields.Many2one('res.partner', string='Base Pilot',
                                   help="Default pilot to use for imported flights")

    @api.model
    def update_transformation_preview(self, id):
        """Log and skip transformation for now"""
        _logger.info("update_transformation_preview called with ID: %s", id)
        record = self.browse(id)
        _logger.info("Record: %s, Model: %s, Transformation Type: %s",
                     record, record.res_model, record.transformation_type)
        
        if record.res_model != 'flight.flight':
            _logger.info("Skipping: Not importing into flight.flight model")
            return {'status': 'success'}

        try:
            if not record.file:
                _logger.warning("No file data found for record ID: %s", id)
                return {'status': 'error', 'message': 'No file data available'}

            _logger.info("File found for record ID: %s, proceeding with original data", id)
            return {'status': 'success'}
        except Exception as e:
            _logger.exception("Error in update_transformation_preview: %s", e)
            return {'status': 'error', 'message': str(e)}

    def parse_preview(self, options, count=10):
        """Follow base parse_preview pattern with optional transformation"""
        self.ensure_one()
        _logger.info("parse_preview called with transformation_type: %s", self.transformation_type)
        
        if self.transformation_type != 'crewlounge':
            return super(ImportExtended, self).parse_preview(options, count)
        else:

            try:
                fields_tree = self.get_fields_tree(self.res_model)
                file_length, rows = self._read_file(options)
                if file_length <= 0:
                    raise UserError(_("Import file has no content or is corrupt"))
                    
                # Apply transformation if crewlounge is selected
                if self.transformation_type == 'crewlounge':
                    _logger.info("Applying CrewLounge transformation")
                    
                    # Extract headers if present
                    original_headers = []
                    if options.get('has_headers') and rows:
                        original_headers = rows[0]
                        _logger.info("Original headers: %s", original_headers)
                    
                    # Transform the data
                    rows = self._transform_crewlounge_to_odoo(rows, original_headers)
                    _logger.info("Transformation complete, got %s rows", len(rows))
                    
                    # Force has_headers to True for transformed data
                    options = dict(options)
                    options['has_headers'] = True
                
                # Continue with standard processing, same as base implementation
                preview = rows[:count]
                
                # Get file headers
                if options.get('has_headers') and preview:
                    # We need the header types before matching columns to fields
                    headers = preview.pop(0)
                    header_types = self._extract_headers_types(headers, preview, options)
                else:
                    header_types, headers = {}, []
                    
                # Get matches: the ones already selected by the user or propose a new matching.
                matches = {}
                # If user checked to the advanced mode, we re-parse the file but we keep the mapping "as is".
                # No need to make another mapping proposal
                if options.get('keep_matches') and options.get('fields'):
                    for index, match in enumerate(options.get('fields', [])):
                        if match:
                            matches[index] = match.split('/')
                elif options.get('has_headers'):
                    matches = self._get_mapping_suggestions(headers, header_types, fields_tree)
                    # remove header_name for matches keys as tuples are no supported in json.
                    # and remove distance from suggestion (keep only the field path) as not used at client side.
                    matches = {
                        header_key[0]: suggestion['field_path']
                        for header_key, suggestion in matches.items()
                        if suggestion
                    }
                    
                # compute if we should activate advanced mode or not:
                # if was already activated of if file contains "relational fields".
                if options.get('keep_matches'):
                    advanced_mode = options.get('advanced')
                else:
                    # Check is label contain relational field
                    from odoo import models
                    has_relational_header = any(len(models.fix_import_export_id_paths(col)) > 1 for col in headers)
                    # Check is matches fields have relational field
                    has_relational_match = any(len(match) > 1 for field, match in matches.items() if match)
                    advanced_mode = has_relational_header or has_relational_match
                    
                # Take first non null values for each column to show preview to users.
                column_example = []
                if preview and preview[0]:  # Ensure we have data to process
                    for column_index, _unused in enumerate(preview[0]):
                        vals = []
                        for record in preview:
                            if record[column_index]:
                                vals.append("%s%s" % (record[column_index][:50], "..." if len(record[column_index]) > 50 else ""))
                            if len(vals) == 5:
                                break
                        column_example.append(
                            vals or
                            [""]  # blank value if no example have been found at all for the current column
                        )
                        
                # Batch management
                batch = False
                batch_cutoff = options.get('limit')
                if batch_cutoff:
                    if count > batch_cutoff:
                        batch = len(preview) > batch_cutoff
                    else:
                        batch = bool(next(
                            itertools.islice(rows, batch_cutoff - count, None),
                            None
                        ))
                        
                result = {
                    'fields': fields_tree,
                    'matches': matches or False,
                    'headers': headers or False,
                    'header_types': list(header_types.values()) if header_types else False,
                    'preview': column_example,
                    'options': options,
                    'advanced_mode': advanced_mode,
                    'debug': self.user_has_groups('base.group_no_one'),
                    'batch': batch,
                    'file_length': file_length
                }
                
                # Add transformation info if applicable
                if self.transformation_type:
                    result['transformation_type'] = self.transformation_type
                    result['is_transformed'] = self.transformation_type == 'crewlounge'
                    
                # Add base_pilot_id if available
                if self.base_pilot_id:
                    result['base_pilot_id'] = {
                        'id': self.base_pilot_id.id,
                        'name': self.base_pilot_id.name
                    }
                    
                return result
                
            except Exception as error:
                _logger.exception("Error during parsing preview: %s", error)
                preview = None
                if self.file_type == 'text/csv' and self.file:
                    preview = self.file[:1024].decode('iso-8859-1')
                return {
                    'error': str(error),
                    'preview': preview,
                    'transformation_type': self.transformation_type,
                    'base_pilot_id': {'id': self.base_pilot_id.id, 'name': self.base_pilot_id.name} if self.base_pilot_id else False
                }

    def execute_import(self, fields, columns, options, dryrun=False):
        """Log and delegate to parent method"""
        self.ensure_one()  # Ensure singleton
        _logger.info("execute_import called for record ID: %s with fields: %s, columns: %s, options: %s, dryrun: %s",
                     self.id, fields, columns, options, dryrun)
        
        try:
            result = super(ImportExtended, self).execute_import(fields, columns, options, dryrun)
            _logger.info("Import executed successfully, result: %s", result)
            return result
        except Exception as e:
            _logger.exception("Error in execute_import: %s", e)
            raise

    def _transform_crewlounge_to_odoo(self, data_rows, headers):
        """Transform CrewLounge data to Odoo flight.flight format
        
        Returns a list where:
        - First element is the list of transformed headers
        - Each subsequent element is a row of data matching those headers
        """
        _logger.info("Starting transformation of CrewLounge data with %d rows", len(data_rows))
        
        # Define the transformed headers we want in our output
        transformed_headers = [
            'id', 'date', 'aircraft_id/registration', 'departure_id/icao', 'arrival_id/icao',
            'remarks'  # Simplified for now - we'll use a simple text field instead of a relation
        ]
        
        # Create a mapping of original headers to their indices
        header_map = {}
        if headers:
            for idx, col in enumerate(headers):
                header_map[col.upper()] = idx
            _logger.info("Created header map: %s", header_map)
        
        # Create the result with headers as the first row
        transformed_data = [transformed_headers]
        
        # Process each row of the original data
        for idx, row in enumerate(data_rows):
            # Skip header row if present in data_rows
            if idx == 0 and headers and row == headers:
                continue
                
            # Skip empty rows
            if not row or all(not cell for cell in row):
                continue
                
            # Make sure row has enough elements
            if len(row) < max(header_map.values()) + 1 if header_map else 1:
                _logger.warning("Row %d has insufficient columns, skipping", idx)
                continue
                
            # Generate a unique ID for this flight
            flight_id = f"flight_import_{idx:03d}"
            
            # Extract and format date
            date_str = ''
            date_idx = header_map.get('PILOTLOG_DATE', 0)
            if date_idx < len(row) and row[date_idx]:
                try:
                    date_str = datetime.strptime(row[date_idx], '%d-%m-%Y').strftime('%Y-%m-%d')
                except (ValueError, TypeError) as e:
                    _logger.warning("Failed to parse date '%s': %s", row[date_idx] if date_idx < len(row) else 'N/A', e)
            
            # Extract other basic fields with safety checks
            aircraft_reg = ''
            reg_idx = header_map.get('AC_REG')
            if reg_idx is not None and reg_idx < len(row):
                aircraft_reg = row[reg_idx] or ''
                
            departure = ''
            dep_idx = header_map.get('AF_DEP')
            if dep_idx is not None and dep_idx < len(row):
                departure = row[dep_idx] or ''
                
            arrival = ''
            arr_idx = header_map.get('AF_ARR')
            if arr_idx is not None and arr_idx < len(row):
                arrival = row[arr_idx] or ''
                
            remarks = ''
            rem_idx = header_map.get('REMARKS')
            if rem_idx is not None and rem_idx < len(row):
                remarks = row[rem_idx] or ''
            
            # Create a transformed row with all required fields
            transformed_row = [
                flight_id,
                date_str,
                aircraft_reg,
                departure,
                arrival,
                remarks
            ]
            
            # Add this row to our transformed data
            transformed_data.append(transformed_row)
        
        _logger.info("Transformation complete, generated %d rows", len(transformed_data))
        return transformed_data