# -*- coding: utf-8 -*-
import base64
import csv
import io
import logging
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class FlightImportTemplate(models.Model):
    _inherit = 'flight.import.template'
    
    source_format = fields.Selection(
        selection_add=[('crewlounge_pilotlog', 'CrewLounge PILOTLOG')],
        ondelete={'crewlounge_pilotlog': 'cascade'}
    )


class FlightImportWizard(models.TransientModel):
    _inherit = 'flight.import.wizard'
    
    def _parse_crewlounge_pilotlog_data(self, log_messages):
        """Parse CrewLounge PILOTLOG format data"""
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
                
            # Parse CSV
            reader = csv.DictReader(
                io.StringIO(file_content),
                delimiter=self.delimiter or ',',
                quotechar=self.quotechar or '"'
            )
            
            # Convert to list for processing
            data_rows = list(reader)
            
            # Process data
            result = self._process_crewlounge_data(data_rows, log_messages)
            
            return result
            
        except Exception as e:
            raise UserError(_("Error parsing file: %s") % str(e))
    
    def _process_crewlounge_data(self, data_rows, log_messages):
        """Process CrewLounge PILOTLOG data"""
        result = {
            'flights': 0,
            'times': 0,
            'events': 0,
        }
        
        # Process each row
        for row in data_rows:
            # Create or get aircraft
            aircraft = self._get_or_create_aircraft(row, log_messages)
            if not aircraft:
                log_messages.append(_("Skipping row due to aircraft creation failure"))
                continue
                
            # Create or get aerodromes
            dep_aerodrome = self._get_or_create_aerodrome(row['AF_DEP'], log_messages)
            arr_aerodrome = self._get_or_create_aerodrome(row['AF_ARR'], log_messages)
            if not dep_aerodrome or not arr_aerodrome:
                log_messages.append(_("Skipping row due to aerodrome creation failure"))
                continue
                
            # Create or update flight
            flight_date = self._parse_date(row['PILOTLOG_DATE'])
            if not flight_date:
                log_messages.append(_("Skipping row due to invalid date format"))
                continue
                
            # Prepare flight data
            flight_data = {
                'date': flight_date,
                'aircraft_id': aircraft.id,
                'departure_id': dep_aerodrome.id,
                'arrival_id': arr_aerodrome.id,
                'flight_number': row['FLIGHTNUMBER'] if row['FLIGHTNUMBER'] else False,
                'remarks': row['REMARKS'] if row['REMARKS'] else False,
            }
            
            # Add times if available
            if row['TIME_DEP']:
                flight_data['time_departure'] = self._parse_time(row['TIME_DEP'])
            if row['TIME_ARR']:
                flight_data['time_arrival'] = self._parse_time(row['TIME_ARR'])
                
            # Create or update flight
            flight = self._create_or_update_flight(flight_data, row, log_messages)
            if not flight:
                log_messages.append(_("Skipping row due to flight creation failure"))
                continue
                
            result['flights'] += 1
            
            # Create pilot time entries
            time_entries = self._create_pilot_time_entries(flight, row, log_messages)
            result['times'] += len(time_entries)
            
            # Create pilot event entries
            event_entries = self._create_pilot_event_entries(flight, row, log_messages)
            result['events'] += len(event_entries)
            
        return result
    
    def _get_or_create_aircraft(self, row, log_messages):
        """Get or create aircraft from row data"""
        Aircraft = self.env['flight.aircraft']
        AircraftModel = self.env['flight.aircraft.model']
        AircraftMake = self.env['flight.aircraft.make']
        
        # Check if registration exists
        registration = row['AC_REG']
        if not registration:
            log_messages.append(_("Missing aircraft registration"))
            return None
            
        # Search for existing aircraft
        aircraft = Aircraft.search([('registration', '=', registration)], limit=1)
        if aircraft:
            return aircraft
            
        # Create new aircraft
        # First, get or create make
        make_name = row['AC_MAKE']
        make = AircraftMake.search([('name', '=', make_name)], limit=1)
        if not make and make_name:
            make = AircraftMake.create({'name': make_name})
            
        # Get or create model
        model_name = row['AC_MODEL']
        domain = [('name', '=', model_name)]
        if make:
            domain.append(('make_id', '=', make.id))
            
        model = AircraftModel.search(domain, limit=1)
        if not model and model_name:
            model_vals = {'name': model_name}
            if make:
                model_vals['make_id'] = make.id
                
            # Set engine type if available
            engine_type = row['AC_ENGTYPE'].lower() if row['AC_ENGTYPE'] else False
            if engine_type in ['piston', 'turboprop', 'turbofan', 'turbojet', 'turboshaft', 'electric', 'diesel', 'radial']:
                model_vals['engine_type'] = engine_type
                
            # Set class
            aircraft_class = self.env['flight.aircraft.class'].search([], limit=1)
            if aircraft_class:
                model_vals['class_id'] = aircraft_class.id
                
            model = AircraftModel.create(model_vals)
            
        # Create aircraft
        aircraft_vals = {
            'registration': registration,
            'equipment_type': 'aircraft',
        }
        
        if model:
            aircraft_vals['model_id'] = model.id
            
        try:
            aircraft = Aircraft.create(aircraft_vals)
            log_messages.append(_("Created new aircraft: %s") % registration)
            return aircraft
        except Exception as e:
            log_messages.append(_("Failed to create aircraft: %s") % str(e))
            return None
    
    def _get_or_create_aerodrome(self, icao, log_messages):
        """Get or create aerodrome from ICAO code"""
        if not icao:
            log_messages.append(_("Missing aerodrome ICAO code"))
            return None
            
        Aerodrome = self.env['flight.aerodrome']
        
        # Search for existing aerodrome
        aerodrome = Aerodrome.search([('icao', '=', icao)], limit=1)
        if aerodrome:
            return aerodrome
            
        # Create new aerodrome
        try:
            aerodrome = Aerodrome.create({
                'icao': icao,
                'name': icao,  # Use ICAO as name until we have more info
            })
            log_messages.append(_("Created new aerodrome: %s") % icao)
            return aerodrome
        except Exception as e:
            log_messages.append(_("Failed to create aerodrome: %s") % str(e))
            return None
    
    def _parse_date(self, date_str):
        """Parse date from string in DD-MM-YYYY format"""
        if not date_str:
            return False
            
        try:
            return datetime.strptime(date_str, '%d-%m-%Y').strftime('%Y-%m-%d')
        except ValueError:
            return False
    
    def _parse_time(self, time_str):
        """Parse time from string in HH:MM format"""
        if not time_str:
            return False
            
        try:
            # Add seconds if not present
            if len(time_str.split(':')) == 2:
                time_str += ':00'
            return time_str
        except ValueError:
            return False
    
    def _create_or_update_flight(self, flight_data, row, log_messages):
        """Create or update flight record"""
        Flight = self.env['flight.flight']
        
        # Check for existing flight with same aircraft, date, departure and arrival
        domain = [
            ('aircraft_id', '=', flight_data['aircraft_id']),
            ('date', '=', flight_data['date']),
            ('departure_id', '=', flight_data['departure_id']),
            ('arrival_id', '=', flight_data['arrival_id']),
        ]
        
        if flight_data.get('time_departure'):
            domain.append(('time_departure', '=', flight_data['time_departure']))
            
        existing_flight = Flight.search(domain, limit=1)
        
        try:
            if existing_flight:
                existing_flight.write(flight_data)
                log_messages.append(_("Updated existing flight: %s") % existing_flight.display_name)
                return existing_flight
            else:
                flight = Flight.create(flight_data)
                log_messages.append(_("Created new flight: %s") % flight.display_name)
                return flight
        except Exception as e:
            log_messages.append(_("Failed to create/update flight: %s") % str(e))
            return None
    
    def _create_pilot_time_entries(self, flight, row, log_messages):
        """Create pilot time entries for the flight"""
        PilotTime = self.env['flight.pilot.time']
        created_entries = []
        
        # Get or create pilot
        pilot = self._get_or_create_pilot(row, log_messages)
        if not pilot:
            return created_entries
            
        # Get time codes
        time_codes = self.env['flight.pilot.time.code'].search([])
        
        # Map CrewLounge time fields to time codes
        time_mappings = {
            'TIME_PIC': 'PIC',
            'TIME_SIC': 'SIC',
            'TIME_DUAL': 'DUAL',
            'TIME_INSTRUCTOR': 'INST',
            'TIME_NIGHT': 'NIGHT',
            'TIME_IFR': 'IFR',
            'TIME_HOOD': 'HOOD',
            'TIME_ACTUAL': 'ACTUAL',
        }
        
        # Create time entries
        for crewlounge_field, code_name in time_mappings.items():
            time_value = row.get(crewlounge_field, '0')
            if time_value and float(time_value) > 0:
                # Find the time code
                time_code = time_codes.filtered(lambda c: c.code == code_name)
                if not time_code:
                    log_messages.append(_("Time code %s not found") % code_name)
                    continue
                    
                # Create time entry
                try:
                    time_entry = PilotTime.create({
                        'flight_id': flight.id,
                        'partner_id': pilot.id,
                        'time_code_id': time_code.id,
                        'time': float(time_value),
                    })
                    created_entries.append(time_entry)
                    log_messages.append(_("Created time entry: %s") % time_entry.display_name)
                except Exception as e:
                    log_messages.append(_("Failed to create time entry: %s") % str(e))
                    
        return created_entries
    
    def _create_pilot_event_entries(self, flight, row, log_messages):
        """Create pilot event entries for the flight"""
        PilotEvent = self.env['flight.pilot.event']
        created_entries = []
        
        # Get or create pilot
        pilot = self._get_or_create_pilot(row, log_messages)
        if not pilot:
            return created_entries
            
        # Get event codes
        event_codes = self.env['flight.pilot.event.code'].search([])
        
        # Map CrewLounge event fields to event codes
        event_mappings = {
            'TO_DAY': 'TO_DAY',
            'TO_NIGHT': 'TO_NIGHT',
            'LDG_DAY': 'LDG_DAY',
            'LDG_NIGHT': 'LDG_NIGHT',
        }
        
        # Create event entries
        for crewlounge_field, code_name in event_mappings.items():
            event_count = row.get(crewlounge_field, '0')
            if event_count and int(event_count) > 0:
                # Find the event code
                event_code = event_codes.filtered(lambda c: c.code == code_name)
                if not event_code:
                    log_messages.append(_("Event code %s not found") % code_name)
                    continue
                    
                # Create event entry
                try:
                    event_entry = PilotEvent.create({
                        'flight_id': flight.id,
                        'partner_id': pilot.id,
                        'event_code_id': event_code.id,
                        'count': int(event_count),
                    })
                    created_entries.append(event_entry)
                    log_messages.append(_("Created event entry: %s") % event_entry.display_name)
                except Exception as e:
                    log_messages.append(_("Failed to create event entry: %s") % str(e))
                    
        return created_entries
    
    def _get_or_create_pilot(self, row, log_messages):
        """Get or create pilot from row data"""
        Partner = self.env['res.partner']
        
        # Check if pilot name exists
        pilot_name = row.get('PILOT1_NAME', False)
        if not pilot_name and row.get('PILOT1_ID') == 'SELF':
            # Use the current user's partner
            return self.env.user.partner_id
            
        if not pilot_name:
            log_messages.append(_("Missing pilot name"))
            return None
            
        # Search for existing pilot
        pilot = Partner.search([
            ('name', '=', pilot_name),
            ('is_pilot', '=', True)
        ], limit=1)
        
        if pilot:
            return pilot
            
        # Create new pilot
        try:
            # Check if is_pilot field exists
            has_is_pilot = 'is_pilot' in Partner._fields
            
            pilot_vals = {
                'name': pilot_name,
                'email': row.get('PILOT1_EMAIL', False),
                'phone': row.get('PILOT1_PHONE', False),
            }
            
            if has_is_pilot:
                pilot_vals['is_pilot'] = True
                
            pilot = Partner.create(pilot_vals)
            log_messages.append(_("Created new pilot: %s") % pilot_name)
            return pilot
        except Exception as e:
            log_messages.append(_("Failed to create pilot: %s") % str(e))
            return None
