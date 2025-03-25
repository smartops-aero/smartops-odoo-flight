# Copyright 2024 Apexive <https://apexive.com/>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

import base64
import io
import logging
import os
import tempfile
import petl as etl
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class CrewLoungeImportWizard(models.TransientModel):
    _name = "flight.import.pilotlog.crewlounge.wizard"
    _description = "CrewLounge CSV Import Wizard"

    file = fields.Binary("CSV File", required=True)
    filename = fields.Char("Filename")
    delimiter = fields.Char("Delimiter", default=",")
    
    # Statistics
    total_rows = fields.Integer("Total Rows", readonly=True)
    makes_count = fields.Integer("Aircraft Makes", readonly=True)
    models_count = fields.Integer("Aircraft Models", readonly=True)
    aircraft_count = fields.Integer("Aircraft", readonly=True)
    aerodromes_count = fields.Integer("Aerodromes", readonly=True)
    flights_count = fields.Integer("Flights", readonly=True)
    skipped_count = fields.Integer("Skipped", readonly=True)
    failed_count = fields.Integer("Failed", readonly=True)
    
    def action_analyze_file(self):
        """Read the CSV file and count rows"""
        self.ensure_one()
        
        if not self.file:
            raise UserError(_("Please upload a CSV file first."))
            
        # Save binary data to a temporary file
        fd, temp_file_path = tempfile.mkstemp(suffix='.csv')
        try:
            with os.fdopen(fd, 'wb') as temp_file:
                temp_file.write(base64.b64decode(self.file))
            
            # Use petl to read the file
            table = etl.fromcsv(temp_file_path, delimiter=self.delimiter)
            self.total_rows = etl.nrows(table) - 1  # Subtract header row
        finally:
            # Clean up the temp file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
    
    def action_import(self):
        """Execute the actual import process"""
        self.ensure_one()
        
        if not self.file:
            raise UserError(_("Please upload a CSV file first."))
            
        # Save binary data to a temporary file
        fd, temp_file_path = tempfile.mkstemp(suffix='.csv')
        try:
            with os.fdopen(fd, 'wb') as temp_file:
                temp_file.write(base64.b64decode(self.file))
            
            # Process the file
            results = self._create_odoo_records(temp_file_path)
            
            # Update statistics
            self.makes_count = results.get('makes', 0)
            self.models_count = results.get('models', 0)
            self.aircraft_count = results.get('aircraft', 0)
            self.aerodromes_count = results.get('aerodromes', 0)
            self.flights_count = results.get('flights', 0)
            
        finally:
            # Clean up the temp file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
    
    def _parse_date(self, date_str):
        """
        Parse date from DD-MM-YYYY format to YYYY-MM-DD format
        """
        if not date_str:
            return False
            
        try:
            # Try to parse the date from DD-MM-YYYY format
            date_obj = datetime.strptime(date_str, '%d-%m-%Y')
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            try:
                # Try alternative format DD/MM/YYYY
                date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                # Return original if we can't parse it
                _logger.warning(f"Could not parse date: {date_str}")
                return False
    
    def _create_odoo_records(self, input_file):
        """
        Process flight data from CSV and create Odoo records directly
        """
        # Load the CSV file using petl
        table = etl.fromcsv(input_file, delimiter=self.delimiter)
        
        # Initialize counters
        results = {
            'makes': 0,
            'models': 0,
            'aircraft': 0,
            'aerodromes': 0,
            'flights': 0
        }
        
        # Step 1: Extract unique aircraft makes (manufacturers)
        makes_table = etl.cut(table, 'AC_MAKE')
        makes_table = etl.distinct(makes_table)
        
        # Process makes
        makes_dict = {}
        for record in etl.dicts(makes_table):
            make_name = record['AC_MAKE']
            if not make_name:
                continue
                
            # Check if make exists in database
            make = self.env['flight.aircraft.make'].search([('name', '=', make_name)], limit=1)
            if make:
                makes_dict[make_name] = make.id
            else:
                # Create new make
                make = self.env['flight.aircraft.make'].create({'name': make_name})
                makes_dict[make_name] = make.id
                results['makes'] += 1
        
        # Step 2: Extract unique aircraft models with make relationship
        models_table = etl.cut(table, 'AC_MAKE', 'AC_MODEL', 'AC_ENGTYPE')
        models_table = etl.distinct(models_table, key=('AC_MAKE', 'AC_MODEL'))
        
        # Process models
        models_dict = {}
        for record in etl.dicts(models_table):
            model_name = record['AC_MODEL']
            make_name = record['AC_MAKE']
            eng_type = record['AC_ENGTYPE']
            
            if not model_name or not make_name:
                continue
                
            # Get make_id
            make_id = makes_dict.get(make_name)
            if not make_id:
                continue
                
            # Create compound key
            key = (make_id, model_name)
            
            # Check if model exists in database
            model = self.env['flight.aircraft.model'].search([
                ('name', '=', model_name),
                ('make_id', '=', make_id)
            ], limit=1)
            
            if model:
                models_dict[key] = model.id
            else:
                # Map engine type
                engine_type = 'turbofan' if eng_type == 'Jet' else 'piston'
                
                model_vals = {
                    'name': model_name,
                    'make_id': make_id,
                    'engine_type': engine_type,
                    'gear_type': 'retractable_tricycle',  # Default value
                    'code': model_name[:4].upper() if model_name else ''
                }
                
                model = self.env['flight.aircraft.model'].create(model_vals)
                models_dict[key] = model.id
                results['models'] += 1
        
        # Step 3: Extract unique aircraft
        aircraft_table = etl.cut(table, 'AC_REG', 'AC_MAKE', 'AC_MODEL', 'AC_SEATS')
        aircraft_table = etl.distinct(aircraft_table, key='AC_REG')
        
        # Process aircraft
        aircraft_dict = {}
        for record in etl.dicts(aircraft_table):
            registration = record['AC_REG']
            if not registration:
                continue
                
            # Check if aircraft exists in database
            aircraft = self.env['flight.aircraft'].search([
                ('registration', '=', registration)
            ], limit=1)
            
            if aircraft:
                aircraft_dict[registration] = aircraft.id
            else:
                # Get model_id
                make_name = record['AC_MAKE']
                model_name = record['AC_MODEL']
                
                make_id = makes_dict.get(make_name)
                if not make_id:
                    continue
                    
                # Find the model
                model = self.env['flight.aircraft.model'].search([
                    ('name', '=', model_name),
                    ('make_id', '=', make_id)
                ], limit=1)
                
                if not model:
                    continue
                
                # Handle seats
                seats = record['AC_SEATS']
                try:
                    seats_int = int(seats) if seats else 5
                except:
                    seats_int = 5
                    
                # Create new aircraft
                aircraft_vals = {
                    'registration': registration,
                    'model_id': model.id,
                    'dom': '2015-01-01',  # Default manufacturing date
                    'mtow': seats_int * 1000,  # Estimated MTOW based on seats
                    'sn': f"SN{registration.replace('-', '')}"  # Generate a dummy serial number
                }
                
                aircraft = self.env['flight.aircraft'].create(aircraft_vals)
                aircraft_dict[registration] = aircraft.id
                results['aircraft'] += 1
        
        # Step 4: Process aerodromes (airports)
        dep_table = etl.cut(table, 'AF_DEP')
        arr_table = etl.cut(table, 'AF_ARR')
        aerodrome_table = etl.cat(dep_table, arr_table)
        aerodrome_table = etl.rename(aerodrome_table, {'AF_DEP': 'icao', 'AF_ARR': 'icao'})
        aerodrome_table = etl.distinct(aerodrome_table)
        
        # Process aerodromes
        aerodrome_dict = {}
        for record in etl.dicts(aerodrome_table):
            icao = record['icao']
            if not icao:
                continue
                
            # Check if aerodrome exists in database
            aerodrome = self.env['flight.aerodrome'].search([
                ('icao', '=', icao)
            ], limit=1)
            
            if aerodrome:
                aerodrome_dict[icao] = aerodrome.id
            else:
                # Create new aerodrome
                aerodrome_vals = {
                    'icao': icao,
                    'name': f"Airport {icao}",
                    'city': f"City for {icao}"
                }
                
                aerodrome = self.env['flight.aerodrome'].create(aerodrome_vals)
                aerodrome_dict[icao] = aerodrome.id
                results['aerodromes'] += 1
        
        # Step 5: Process flight data
        flight_table = etl.cut(table, 'PILOTLOG_DATE', 'AF_DEP', 'AF_ARR', 'AC_REG', 'REMARKS')
        
        # Process flights
        self.skipped_count = 0
        self.failed_count = 0
        for record in etl.dicts(flight_table):
            date_str = record['PILOTLOG_DATE']
            registration = record['AC_REG']
            dep_icao = record['AF_DEP']
            arr_icao = record['AF_ARR']
            
            if not all([date_str, registration, dep_icao, arr_icao]):
                self.skipped_count += 1
                continue
            
            # Parse the date to Odoo format (YYYY-MM-DD)
            date = self._parse_date(date_str)
            if not date:
                self.failed_count += 1
                continue
                
            # Get related records
            aircraft_id = aircraft_dict.get(registration)
            departure_id = aerodrome_dict.get(dep_icao)
            arrival_id = aerodrome_dict.get(arr_icao)
            
            if not all([aircraft_id, departure_id, arrival_id]):
                self.skipped_count += 1
                continue
                
            # Check if flight already exists
            existing_flight = self.env['flight.flight'].search([
                ('date', '=', date),
                ('aircraft_id', '=', aircraft_id),
                ('departure_id', '=', departure_id),
                ('arrival_id', '=', arrival_id)
            ], limit=1)
            
            if existing_flight:
                self.skipped_count += 1
                continue
                
            # Create new flight
            flight_vals = {
                'date': date,
                'aircraft_id': aircraft_id,
                'departure_id': departure_id,
                'arrival_id': arrival_id,
                'locked': False
            }
            
            self.env['flight.flight'].create(flight_vals)
            results['flights'] += 1
        
        # Log summary
        _logger.info(f"Created {results['makes']} aircraft makes")
        _logger.info(f"Created {results['models']} aircraft models")
        _logger.info(f"Created {results['aircraft']} aircraft")
        _logger.info(f"Created {results['aerodromes']} aerodromes")
        _logger.info(f"Created {results['flights']} flights")
        
        return results
