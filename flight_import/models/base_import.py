# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import base64
import csv
import io
import tempfile
import logging

_logger = logging.getLogger(__name__)

class ImportExtended(models.TransientModel):
    _inherit = 'base_import.import'

    transformation_type = fields.Selection([
        ('none', 'No Transformation'),
        ('crewlounge', 'CrewLounge Format')
    ], string='Transformation', default='none')
    
    base_pilot_id = fields.Many2one('res.partner', string='Base Pilot', 
                                   help="Default pilot to use for imported flights")
    
    @api.onchange('base_pilot_id')
    def _onchange_base_pilot_id(self):
        """Update context when base pilot changes"""
        if self.base_pilot_id:
            self.env.context = dict(self.env.context, default_base_pilot_id=self.base_pilot_id.id)
    
    @api.onchange('transformation_type')
    def _onchange_transformation_type(self):
        """When transformation type changes, prepare the transformation preview"""
        if self.res_model != 'flight.flight' or not self.file or self.transformation_type == 'none':
            return
            
        if self.transformation_type == 'crewlounge':
            self._prepare_crewlounge_preview()
    
    def _prepare_crewlounge_preview(self):
        """Prepare a preview of the CrewLounge transformation"""
        if not self.file:
            return
            
        # Get file content
        file_content = base64.b64decode(self.file)
        
        # Parse options
        options = self.import_options()
        encoding = options.get('encoding', 'utf-8')
        separator = options.get('separator', ',')
        quoting = options.get('quoting', '"')
        
        # Parse the file into a list of lists
        try:
            reader = csv.reader(io.StringIO(file_content.decode(encoding)), 
                               delimiter=separator,
                               quotechar=quoting)
            crewlounge_data = [row for row in reader]
            
            # Keep only first few rows for preview
            preview_data = crewlounge_data[:10] if len(crewlounge_data) > 10 else crewlounge_data
            
            # Create temporary transformed file for preview
            transformed_data = self._transform_crewlounge_to_odoo(preview_data, is_preview=True)
            
            if transformed_data:
                # Create a temporary file with the transformed data
                output = io.StringIO()
                writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
                for row in transformed_data:
                    writer.writerow(row)
                
                # Update the file content temporarily for preview
                # We'll do the real transformation during execute_import
                temp_file = base64.b64encode(output.getvalue().encode('utf-8'))
                
                # Store original file content to restore it later
                self.env.context = dict(
                    self.env.context, 
                    original_file=self.file,
                    original_file_name=self.file_name,
                    preview_file=temp_file,
                    preview_file_name=self.file_name.rsplit('.', 1)[0] + '_transformed.csv'
                )
                
                # Set the transformed file for preview
                self.file = temp_file
                self.file_name = self.file_name.rsplit('.', 1)[0] + '_transformed_preview.csv'
                
                # Update import options
                options['has_headers'] = True
                options['separator'] = ','
                options['quoting'] = '"'
        
        except Exception as e:
            _logger.error("Error preparing CrewLounge preview: %s", e)
            return {
                'warning': {
                    'title': _("Transformation Preview Error"),
                    'message': _("Could not prepare transformation preview: %s") % str(e)
                }
            }

    def _transform_crewlounge_to_odoo(self, crewlounge_data, is_preview=False):
        """
        Transform CrewLounge CSV data to Odoo-compatible format for flight.flight model
        
        :param crewlounge_data: List of lists containing the CrewLounge data
        :param is_preview: Whether this is a preview transformation
        :return: Transformed data as a list of lists
        """
        if not crewlounge_data or len(crewlounge_data) < 2:  # Need at least header + one data row
            return []
        
        # Create header for Odoo format
        odoo_header = [
            'id', 'date', 'aircraft_id/registration', 'departure_id/icao', 'arrival_id/icao', 
            'remark_ids/id', 'remark_ids/partner_id/id', 'remark_ids/remark', 
            'pilot_time_ids/id', 'pilot_time_ids/partner_id/id', 'pilot_time_ids/code_id/id', 'pilot_time_ids/duration',
            'pilot_event_ids/id', 'pilot_event_ids/partner_id/id', 'pilot_event_ids/event_code_id/id', 'pilot_event_ids/count'
        ]
        
        odoo_data = [odoo_header]
        
        # Get base pilot information
        base_pilot = self.base_pilot_id or self.env.user.partner_id
        partner_xml_id = self.env['ir.model.data'].search([
            ('model', '=', 'res.partner'),
            ('res_id', '=', base_pilot.id)
        ]).complete_name or 'base.partner_admin'
        
        # Create a header map for easier access
        header_map = {col: idx for idx, col in enumerate(crewlounge_data[0])}
        
        # Process data rows
        for idx, row in enumerate(crewlounge_data[1:], 1):
            # Skip if this is just a preview and we've processed enough rows
            if is_preview and idx > 5:
                break
                
            # Create a dictionary for easier access - handle variable length rows
            crew_dict = {}
            for col_name, col_idx in header_map.items():
                if col_idx < len(row):
                    crew_dict[col_name] = row[col_idx]
                else:
                    crew_dict[col_name] = ""
            
            flight_id = f"flight_import_{idx:03d}"
            
            # Basic flight data
            date = crew_dict.get('PILOTLOG_DATE', '')
            if date:
                # Convert date format if needed (assuming it's in MM/DD/YYYY)
                try:
                    month, day, year = date.split('/')
                    date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                except (ValueError, AttributeError):
                    # Keep as is if not in expected format
                    pass
            
            aircraft_reg = crew_dict.get('AC_REG', '')
            departure = crew_dict.get('AF_DEP', '')
            arrival = crew_dict.get('AF_ARR', '')
            remarks = crew_dict.get('REMARKS', '')
            
            # Time data - convert from minutes to hours if needed
            pic_time = self._safe_convert_time(crew_dict.get('TIME_PIC', 0))
            sic_time = self._safe_convert_time(crew_dict.get('TIME_SIC', 0))
            night_time = self._safe_convert_time(crew_dict.get('TIME_NIGHT', 0))
            
            # Event data
            to_day = int(float(crew_dict.get('TO_DAY', 0)) if crew_dict.get('TO_DAY') else 0)
            to_night = int(float(crew_dict.get('TO_NIGHT', 0)) if crew_dict.get('TO_NIGHT') else 0)
            ldg_day = int(float(crew_dict.get('LDG_DAY', 0)) if crew_dict.get('LDG_DAY') else 0)
            ldg_night = int(float(crew_dict.get('LDG_NIGHT', 0)) if crew_dict.get('LDG_NIGHT') else 0)
            
            # Create base row with flight info
            base_row = [
                flight_id, date, aircraft_reg, departure, arrival
            ]
            
            # Add remark if exists
            if remarks:
                remark_row = base_row + [
                    f"remark_{idx:03d}", partner_xml_id, remarks, "", "", "", "", "", "", "", ""
                ]
                odoo_data.append(remark_row)
            else:
                # Add empty row to maintain structure
                empty_remark_row = base_row + ["", "", "", "", "", "", "", "", "", "", ""]
                odoo_data.append(empty_remark_row)
            
            # Add PIC time if exists
            if pic_time > 0:
                pic_row = base_row + [
                    "", "", "", f"time_{(idx*10)+1:03d}", partner_xml_id, 
                    "flight_pilotlog.flight_pilot_time_code_pic", str(pic_time), "", "", "", ""
                ]
                odoo_data.append(pic_row)
            
            # Add SIC time if exists
            if sic_time > 0:
                sic_row = base_row + [
                    "", "", "", f"time_{(idx*10)+2:03d}", partner_xml_id, 
                    "flight_pilotlog.flight_pilot_time_code_sic", str(sic_time), "", "", "", ""
                ]
                odoo_data.append(sic_row)
            
            # Add Night time if exists
            if night_time > 0:
                night_row = base_row + [
                    "", "", "", f"time_{(idx*10)+3:03d}", partner_xml_id, 
                    "flight_pilotlog.flight_pilot_time_code_night", str(night_time), "", "", "", ""
                ]
                odoo_data.append(night_row)
            
            # Add takeoff day if exists
            if to_day > 0:
                to_day_row = base_row + [
                    "", "", "", "", "", "", "", f"event_{(idx*10)+1:03d}", partner_xml_id, 
                    "flight_pilotlog.flight_pilot_event_code_to_day", str(to_day)
                ]
                odoo_data.append(to_day_row)
            
            # Add takeoff night if exists
            if to_night > 0:
                to_night_row = base_row + [
                    "", "", "", "", "", "", "", f"event_{(idx*10)+2:03d}", partner_xml_id, 
                    "flight_pilotlog.flight_pilot_event_code_to_night", str(to_night)
                ]
                odoo_data.append(to_night_row)
            
            # Add landing day if exists
            if ldg_day > 0:
                ldg_day_row = base_row + [
                    "", "", "", "", "", "", "", f"event_{(idx*10)+3:03d}", partner_xml_id, 
                    "flight_pilotlog.flight_pilot_event_code_ldg_day", str(ldg_day)
                ]
                odoo_data.append(ldg_day_row)
            
            # Add landing night if exists
            if ldg_night > 0:
                ldg_night_row = base_row + [
                    "", "", "", "", "", "", "", f"event_{(idx*10)+4:03d}", partner_xml_id, 
                    "flight_pilotlog.flight_pilot_event_code_ldg_night", str(ldg_night)
                ]
                odoo_data.append(ldg_night_row)
        
        return odoo_data

    def _safe_convert_time(self, time_value):
        """Safely convert time values to float hours"""
        try:
            # Try to convert to float first
            time_float = float(time_value)
            # Check if it's likely in minutes (common in pilot logs)
            if time_float > 10:  # Assume it's minutes if > 10
                return time_float / 60
            return time_float
        except (ValueError, TypeError):
            return 0

    def parse_preview(self, options, count=10):
        """Override to handle transformation preview"""
        # Check if we need to restore original file for transformation preview
        ctx = self.env.context
        if self.res_model == 'flight.flight' and ctx.get('original_file') and self.transformation_type != 'none':
            # Restore original file for actual parsing
            original_file = ctx.get('original_file')
            original_file_name = ctx.get('original_file_name')
            
            # Store current file
            current_file = self.file
            current_file_name = self.file_name
            
            # Set original file
            self.file = original_file
            self.file_name = original_file_name
            
            # Get result
            result = super(ImportExtended, self).parse_preview(options, count)
            
            # Restore transformed file
            self.file = current_file
            self.file_name = current_file_name
            
            return result
        
        # Normal parse preview
        result = super(ImportExtended, self).parse_preview(options, count)
        
        # Add transformation type if this is flight.flight
        if hasattr(result, 'get') and self.res_model == 'flight.flight':
            result['transformation_type'] = self.transformation_type
            if self.base_pilot_id:
                result['base_pilot_id'] = {
                    'id': self.base_pilot_id.id,
                    'name': self.base_pilot_id.name
                }
        
        return result
    
    def execute_import(self, fields, columns, options, dryrun=False):
        """Override to transform data if needed"""
        # Check if we need to transform the data
        if self.res_model == 'flight.flight' and self.transformation_type != 'none':
            # Get original file content if we're in preview mode
            ctx = self.env.context
            file_content = base64.b64decode(ctx.get('original_file', self.file))
            
            # Parse the file
            encoding = options.get('encoding', 'utf-8')
            separator = options.get('separator', ',')
            quoting = options.get('quoting', '"')
            
            try:
                reader = csv.reader(io.StringIO(file_content.decode(encoding)), 
                                  delimiter=separator,
                                  quotechar=quoting)
                source_data = [row for row in reader]
                
                # Transform based on type
                if self.transformation_type == 'crewlounge':
                    transformed_data = self._transform_crewlounge_to_odoo(source_data)
                else:
                    transformed_data = source_data
                
                if not transformed_data:
                    return {
                        'messages': [{
                            'type': 'error',
                            'message': _("Failed to transform data to Odoo format."),
                            'record': False
                        }]
                    }
                
                # Write to a new CSV file
                output = io.StringIO()
                writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
                for row in transformed_data:
                    writer.writerow(row)
                
                # Update the import object with the new file
                self.file = base64.b64encode(output.getvalue().encode('utf-8'))
                self.file_name = (ctx.get('original_file_name', '') or self.file_name).rsplit('.', 1)[0] + '_transformed.csv'
                
                # Update options for the new file
                options['has_headers'] = True
                options['separator'] = ','
                options['quoting'] = '"'
                
                # Setup field mappings for the transformed file
                odoo_fields = [
                    'id', 'date', 'aircraft_id/registration', 'departure_id/icao', 'arrival_id/icao', 
                    'remark_ids/id', 'remark_ids/partner_id/id', 'remark_ids/remark', 
                    'pilot_time_ids/id', 'pilot_time_ids/partner_id/id', 'pilot_time_ids/code_id/id', 'pilot_time_ids/duration',
                    'pilot_event_ids/id', 'pilot_event_ids/partner_id/id', 'pilot_event_ids/event_code_id/id', 'pilot_event_ids/count'
                ]
                
                fields = odoo_fields
                columns = odoo_fields
            
            except Exception as e:
                _logger.error("Error transforming data: %s", e)
                return {
                    'messages': [{
                        'type': 'error',
                        'message': _("Error transforming data: %s") % str(e),
                        'record': False
                    }]
                }
        
        # Proceed with normal import
        return super(ImportExtended, self).execute_import(fields, columns, options, dryrun)
    @api.model
    def update_transformation_preview(self, id):
        """Public method that can be called remotely"""
        record = self.browse(id)
        return record._onchange_transformation_type()