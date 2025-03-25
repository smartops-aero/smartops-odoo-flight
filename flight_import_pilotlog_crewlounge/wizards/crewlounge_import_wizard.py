# Copyright 2024 Apexive <https://apexive.com/>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

import base64
import contextlib
import io
import logging
import os
import tempfile
import petl as etl
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from functools import partial
from collections import defaultdict

_logger = logging.getLogger(__name__)


class EntityProcessor:
    """Abstract entity processor that handles common operations for all entity types"""
    
    def __init__(self, wizard, model_name, entity_type):
        self.wizard = wizard
        self.env = wizard.env
        self.model_name = model_name
        self.model = self.env[model_name]
        self.entity_type = entity_type
        self.cache = {}
        self.count = 0
        
    def get_table_fields(self):
        """Return fields needed from CSV table"""
        raise NotImplementedError()
        
    def get_key_fields(self):
        """Return fields used for uniqueness"""
        raise NotImplementedError()
        
    def prepare_table(self, source_table):
        """Extract and transform table for this entity type"""
        fields = self.get_table_fields()
        table = etl.cut(source_table, *fields)
        key_fields = self.get_key_fields()
        
        if key_fields:
            return etl.distinct(table, key=key_fields)
        return etl.distinct(table)
        
    def get_record_key(self, record):
        """Get cache key for this record"""
        key_fields = self.get_key_fields()
        if not key_fields:
            return None
            
        if len(key_fields) == 1:
            return record.get(key_fields[0])
        return tuple(record.get(field) for field in key_fields)
        
    def search_existing(self, record, dependencies=None):
        """Search for existing entity in database"""
        domain = self.build_search_domain(record, dependencies)
        if not domain:
            return None
        return self.model.search(domain, limit=1)
        
    def build_search_domain(self, record, dependencies=None):
        """Build domain for searching existing record"""
        raise NotImplementedError()
        
    def prepare_create_values(self, record, dependencies=None):
        """Prepare values for creating a new record"""
        raise NotImplementedError()
        
    def is_valid_record(self, record, dependencies=None):
        """Check if record has all required data"""
        return bool(self.get_record_key(record))
        
    def process_batch(self, batch_records, batch_keys, dependencies_map):
        """Create records in batch and update cache"""
        created_records = self.model.create(batch_records)
        for i, (vals, key) in enumerate(zip(batch_records, batch_keys)):
            self.cache[key] = created_records[i].id
        self.count += len(batch_records)
        
    def process_records(self, table, entity_cache, batch_size=100):
        """Process all records for this entity type"""
        batch_records = []
        batch_keys = []
        
        for record in etl.dicts(table):
            # Validate record
            if not self.is_valid_record(record):
                self.wizard.skipped_count += 1
                continue
                
            # Get key for caching
            key = self.get_record_key(record)
            if not key:
                self.wizard.skipped_count += 1
                continue
                
            # Check if already processed
            if key in self.cache:
                continue
                
            # Get dependencies if needed
            dependencies = self.get_dependencies(record, entity_cache)
            if dependencies is False:  # Missing dependency
                self.wizard.skipped_count += 1
                continue
                
            # Check if exists in database
            existing = self.search_existing(record, dependencies)
            if existing:
                self.cache[key] = existing.id
                continue
                
            # Prepare values for creation
            create_vals = self.prepare_create_values(record, dependencies)
            if not create_vals:
                self.wizard.skipped_count += 1
                continue
                
            # Add to batch
            batch_records.append(create_vals)
            batch_keys.append(key)
            
            # Process batch if full
            if len(batch_records) >= batch_size:
                self.process_batch(batch_records, batch_keys, {})
                batch_records = []
                batch_keys = []
                
        # Process remaining batch
        if batch_records:
            self.process_batch(batch_records, batch_keys, {})
            
        return self.count, self.cache
        
    def get_dependencies(self, record, entity_cache):
        """Get dependencies from other entities"""
        return {}  # No dependencies by default


class AircraftMakeProcessor(EntityProcessor):
    """Processor for aircraft makes"""
    
    def get_table_fields(self):
        return ['AC_MAKE']
        
    def get_key_fields(self):
        return ['AC_MAKE']
        
    def build_search_domain(self, record, dependencies=None):
        make_name = record.get('AC_MAKE')
        if not make_name:
            return False
        return [('name', '=', make_name)]
        
    def prepare_create_values(self, record, dependencies=None):
        make_name = record.get('AC_MAKE')
        if not make_name:
            return False
        return {'name': make_name}


class AircraftModelProcessor(EntityProcessor):
    """Processor for aircraft models"""
    
    def get_table_fields(self):
        return ['AC_MAKE', 'AC_MODEL', 'AC_ENGTYPE', 'AC_CLASS', 'AC_SPSE', 'AC_SPME', 'AC_GLIDER', 'AC_SEA', 'AC_ENGINES']
        
    def get_key_fields(self):
        return ['AC_MAKE', 'AC_MODEL']
        
    def get_dependencies(self, record, entity_cache):
        make_name = record.get('AC_MAKE')
        if not make_name or 'makes' not in entity_cache or make_name not in entity_cache['makes']:
            return False
            
        return {
            'make_id': entity_cache['makes'][make_name]
        }
        
    def build_search_domain(self, record, dependencies):
        model_name = record.get('AC_MODEL')
        if not model_name or not dependencies or 'make_id' not in dependencies:
            return False
            
        return [
            ('name', '=', model_name),
            ('make_id', '=', dependencies['make_id'])
        ]
    
    def _normalize_boolean(self, value):
        """Normalize boolean values from string representation"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().upper() in ('TRUE', 'YES', 'Y', '1')
        return bool(value)
    
    def _get_aircraft_class_id(self, record):
        """Determine aircraft class ID based on the record fields"""
        # Get all relevant fields and normalize them
        ac_class = record.get('AC_CLASS', '').lower().strip()
        ac_spse = self._normalize_boolean(record.get('AC_SPSE', 'FALSE'))
        ac_spme = self._normalize_boolean(record.get('AC_SPME', 'FALSE'))
        ac_glider = self._normalize_boolean(record.get('AC_GLIDER', 'FALSE'))
        ac_sea = self._normalize_boolean(record.get('AC_SEA', 'FALSE'))
        ac_engines = record.get('AC_ENGINES', '').lower().strip()
        
        # Mapping of class patterns to XML IDs
        class_mappings = {
            'airplane_sel': {
                'conditions': lambda: (not ac_sea) and (not (ac_engines == 'multi' or ac_spme)),
                'xml_id': 'flight.class_airplane_sel'
            },
            'airplane_mel': {
                'conditions': lambda: (not ac_sea) and (ac_engines == 'multi' or ac_spme),
                'xml_id': 'flight.class_airplane_mel'
            },
            'airplane_ses': {
                'conditions': lambda: ac_sea and (not (ac_engines == 'multi' or ac_spme)),
                'xml_id': 'flight.class_airplane_ses'
            },
            'airplane_mes': {
                'conditions': lambda: ac_sea and (ac_engines == 'multi' or ac_spme),
                'xml_id': 'flight.class_airplane_mes'
            },
            'glider': {
                'conditions': lambda: ac_glider,
                'xml_id': 'flight.class_glider'
            }
        }
        
        # First check if it's a glider (prioritize this check)
        if ac_glider:
            return self._resolve_xml_id('flight.class_glider')
            
        # Check if it's an airplane
        if 'aeroplane' in ac_class or 'airplane' in ac_class:
            # Check specific airplane types
            for mapping in class_mappings.values():
                if 'airplane' in mapping['xml_id'] and mapping['conditions']():
                    return self._resolve_xml_id(mapping['xml_id'])
                    
            # Default for airplanes if no specific condition matched
            return self._resolve_xml_id('flight.class_airplane_sel')
            
        # Default to single engine land if we can't determine specifics
        return self._resolve_xml_id('flight.class_airplane_sel')
    
    def _resolve_xml_id(self, xml_id):
        """Convert XML ID to database ID"""
        try:
            return self.env.ref(xml_id).id
        except Exception as e:
            _logger.error(f"Failed to resolve XML ID {xml_id}: {str(e)}")
            return None
        
    def prepare_create_values(self, record, dependencies):
        model_name = record.get('AC_MODEL')
        eng_type = record.get('AC_ENGTYPE', '')
        
        if not model_name or not dependencies or 'make_id' not in dependencies:
            return False
            
        values = {
            'name': model_name,
            'make_id': dependencies['make_id'],
            'engine_type': 'turbofan' if eng_type == 'Jet' else 'piston',
            'gear_type': 'retractable_tricycle',  # Default value
            'code': model_name[:4].upper() if model_name else ''
        }
        
        # Add class_id if we can determine it
        class_id = self._get_aircraft_class_id(record)
        if class_id:
            values['class_id'] = class_id
            
        return values


class AircraftProcessor(EntityProcessor):
    """Processor for aircraft"""
    
    def get_table_fields(self):
        return ['AC_REG', 'AC_MAKE', 'AC_MODEL', 'AC_SEATS']
        
    def get_key_fields(self):
        return ['AC_REG']
        
    def get_dependencies(self, record, entity_cache):
        """Get related entities, but don't fail if not found"""
        result = {}
        registration = record.get('AC_REG')
        
        # If we don't have registration, we can't proceed
        if not registration:
            return False
            
        # Try to get make and model if available
        make_name = record.get('AC_MAKE')
        model_name = record.get('AC_MODEL')
        
        if make_name and model_name:
            # Try to find the model
            if 'makes' in entity_cache and make_name in entity_cache['makes']:
                make_id = entity_cache['makes'][make_name]
                
                # Find model by compound key
                model_key = (make_name, model_name)
                if 'models' in entity_cache and model_key in entity_cache['models']:
                    result['model_id'] = entity_cache['models'][model_key]
                else:
                    # Try with lookup by separate keys
                    models = self.env['flight.aircraft.model'].search([
                        ('name', '=', model_name),
                        ('make_id', '=', make_id)
                    ], limit=1)
                    
                    if models:
                        result['model_id'] = models.id
                        # Cache it for future lookups
                        if 'models' not in entity_cache:
                            entity_cache['models'] = {}
                        entity_cache['models'][model_key] = models.id
        
        # Return dependencies even if model_id is not found
        return result
        
    def build_search_domain(self, record, dependencies):
        registration = record.get('AC_REG')
        if not registration:
            return False
            
        return [('registration', '=', registration)]
        
    def prepare_create_values(self, record, dependencies):
        """Prepare values for creating aircraft with minimal required data"""
        registration = record.get('AC_REG')
        
        if not registration:
            return False
            
        values = {
            'registration': registration,
        }
        
        # Add model_id if available
        if dependencies and 'model_id' in dependencies:
            values['model_id'] = dependencies['model_id']
            
        return values


class AerodromeProcessor(EntityProcessor):
    """Processor for aerodromes"""
    
    def get_table_fields(self):
        # Special case, will be handled in prepare_table
        return []
        
    def get_key_fields(self):
        return ['icao']
        
    def prepare_table(self, source_table):
        """Extract from both departure and arrival fields"""
        dep_table = etl.cut(source_table, 'AF_DEP')
        arr_table = etl.cut(source_table, 'AF_ARR')
        
        dep_table = etl.rename(dep_table, {'AF_DEP': 'icao'})
        arr_table = etl.rename(arr_table, {'AF_ARR': 'icao'})
        
        combined = etl.cat(dep_table, arr_table)
        return etl.distinct(combined)
        
    def build_search_domain(self, record, dependencies):
        icao = record.get('icao')
        if not icao:
            return False
            
        return [('icao', '=', icao)]
        
    def prepare_create_values(self, record, dependencies):
        icao = record.get('icao')
        if not icao:
            return False
            
        return {'icao': icao}


class FlightProcessor(EntityProcessor):
    """Processor for flight records"""
    
    def get_table_fields(self):
        return ['PILOTLOG_DATE', 'AF_DEP', 'AF_ARR', 'AC_REG', 'REMARKS']
        
    def get_key_fields(self):
        return ['PILOTLOG_DATE', 'AF_DEP', 'AF_ARR', 'AC_REG']
        
    def is_valid_record(self, record, dependencies=None):
        required_fields = ['PILOTLOG_DATE', 'AF_DEP', 'AF_ARR', 'AC_REG']
        return all(record.get(field) for field in required_fields)
        
    def get_dependencies(self, record, entity_cache):
        """Get related entities with detailed logging"""
        registration = record.get('AC_REG')
        dep_icao = record.get('AF_DEP')
        arr_icao = record.get('AF_ARR')
        date_str = record.get('PILOTLOG_DATE')
        
        _logger.info(f"Processing flight: Date={date_str}, From={dep_icao}, To={arr_icao}, Reg={registration}")
        
        if not all([registration, dep_icao, arr_icao]):
            _logger.warning(f"Skipping: Missing required fields - Date={date_str}, From={dep_icao}, To={arr_icao}, Reg={registration}")
            return False
            
        # Aircraft lookup
        if 'aircraft' not in entity_cache or registration not in entity_cache['aircraft']:
            _logger.warning(f"Skipping: Aircraft not found - {registration}")
            return False
            
        # Departure aerodrome lookup
        if 'aerodromes' not in entity_cache or dep_icao not in entity_cache['aerodromes']:
            _logger.warning(f"Skipping: Departure aerodrome not found - {dep_icao}")
            return False
            
        # Arrival aerodrome lookup
        if 'aerodromes' not in entity_cache or arr_icao not in entity_cache['aerodromes']:
            _logger.warning(f"Skipping: Arrival aerodrome not found - {arr_icao}")
            return False
            
        # Date parsing
        date = self.wizard._parse_date(date_str)
        if not date:
            _logger.warning(f"Skipping: Could not parse date - {date_str}")
            return False
            
        return {
            'date': date,
            'aircraft_id': entity_cache['aircraft'][registration],
            'departure_id': entity_cache['aerodromes'][dep_icao],
            'arrival_id': entity_cache['aerodromes'][arr_icao],
        }
        
    def build_search_domain(self, record, dependencies):
        if not dependencies:
            return False
            
        return [
            ('date', '=', dependencies['date']),
            ('aircraft_id', '=', dependencies['aircraft_id']),
            ('departure_id', '=', dependencies['departure_id']),
            ('arrival_id', '=', dependencies['arrival_id']),
        ]
        
    def prepare_create_values(self, record, dependencies):
        if not dependencies:
            return False
            
        return {
            'date': dependencies['date'],
            'aircraft_id': dependencies['aircraft_id'],
            'departure_id': dependencies['departure_id'],
            'arrival_id': dependencies['arrival_id'],
        }

class FlightPilotRemarkProcessor(EntityProcessor):
    """Processor for pilot flight remarks"""
    
    def get_table_fields(self):
        return ['PILOTLOG_DATE', 'AF_DEP', 'AF_ARR', 'AC_REG', 'REMARKS']
        
    def get_key_fields(self):
        return ['PILOTLOG_DATE', 'AF_DEP', 'AF_ARR', 'AC_REG']
    
    def prepare_table(self, source_table):
        """Extract only records that have remarks"""
        table = super().prepare_table(source_table)
        # Filter to include only rows with remarks
        return etl.select(table, lambda rec: rec.get('REMARKS', '').strip() != '')
        
    def is_valid_record(self, record, dependencies=None):
        """Check if record has required data and pilot is selected"""
        if not self.wizard.partner_id:
            return False
            
        return (super().is_valid_record(record, dependencies) and 
                record.get('REMARKS', '').strip() != '')
        
    def get_dependencies(self, record, entity_cache):
        """Get related flight record"""
        # Get flight key
        registration = record.get('AC_REG')
        dep_icao = record.get('AF_DEP')
        arr_icao = record.get('AF_ARR')
        date_str = record.get('PILOTLOG_DATE')
        
        if not all([date_str, registration, dep_icao, arr_icao]):
            return False
            
        # Parse date
        date = self.wizard._parse_date(date_str)
        if not date:
            return False
            
        # Build flight key similar to how FlightProcessor does it
        flight_key = (date_str, dep_icao, arr_icao, registration)
        
        # Get flight id from cache
        if 'flights' not in entity_cache or flight_key not in entity_cache['flights']:
            # Try to find flight in database
            flight = self.wizard.env['flight.flight'].search([
                ('date', '=', date),
                ('aircraft_id.registration', '=', registration),
                ('departure_id.icao', '=', dep_icao),
                ('arrival_id.icao', '=', arr_icao)
            ], limit=1)
            
            if not flight:
                return False
                
            flight_id = flight.id
        else:
            flight_id = entity_cache['flights'][flight_key]
            
        return {
            'flight_id': flight_id,
            'partner_id': self.wizard.partner_id.id,
            'remark': record.get('REMARKS', '').strip()
        }
        
    def build_search_domain(self, record, dependencies):
        """Search for existing remark"""
        if not dependencies or 'flight_id' not in dependencies or 'partner_id' not in dependencies:
            return False
            
        return [
            ('flight_id', '=', dependencies['flight_id']),
            ('partner_id', '=', dependencies['partner_id'])
        ]
        
    def prepare_create_values(self, record, dependencies):
        """Prepare values for creating a new remark"""
        if not dependencies:
            return False
            
        return {
            'flight_id': dependencies['flight_id'],
            'partner_id': dependencies['partner_id'],
            'remark': dependencies['remark']
        }

class CrewLoungeImportWizard(models.TransientModel):
    _name = "flight.import.pilotlog.crewlounge.wizard"
    _description = "CrewLounge CSV Import Wizard"

    file = fields.Binary("CSV File", required=True)
    filename = fields.Char("Filename")
    delimiter = fields.Char("Delimiter", default=",")
    partner_id = fields.Many2one(
        "res.partner", 
        string="Pilot", 
        domain=[('is_company', '=', False)],
        help="Select the pilot to associate with flight remarks"
    )
    remarks_count = fields.Integer("Pilot Remarks", readonly=True)
    # Statistics
    total_rows = fields.Integer("Total Rows", readonly=True)
    makes_count = fields.Integer("Aircraft Makes", readonly=True)
    models_count = fields.Integer("Aircraft Models", readonly=True)
    aircraft_count = fields.Integer("Aircraft", readonly=True)
    aerodromes_count = fields.Integer("Aerodromes", readonly=True)
    flights_count = fields.Integer("Flights", readonly=True)
    skipped_count = fields.Integer("Skipped", readonly=True)
    failed_count = fields.Integer("Failed", readonly=True)
    
    @contextlib.contextmanager
    def _temp_file_from_binary(self):
        """Create a temporary file from binary data"""
        if not self.file:
            raise UserError(_("Please upload a CSV file first."))
            
        fd, temp_file_path = tempfile.mkstemp(suffix='.csv')
        try:
            with os.fdopen(fd, 'wb') as temp_file:
                temp_file.write(base64.b64decode(self.file))
            yield temp_file_path
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    def action_analyze_file(self):
        """Read the CSV file and count rows"""
        self.ensure_one()
        
        with self._temp_file_from_binary() as temp_file_path:
            # Use petl to read the file
            table = etl.fromcsv(temp_file_path, delimiter=self.delimiter)
            self.total_rows = etl.nrows(table) - 1  # Subtract header row
        
        return self._refresh_wizard_view()
    
    def _refresh_wizard_view(self):
        """Return an action to refresh the wizard view"""
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
        
        with self._temp_file_from_binary() as temp_file_path:
            # Reset counters
            self.skipped_count = 0
            self.failed_count = 0
            
            # Process the file
            results = self._create_odoo_records(temp_file_path)
            
            # Update statistics
            for entity_type, count in results.items():
                setattr(self, f"{entity_type}_count", count)
        
        return self._refresh_wizard_view()
    
    def _parse_date(self, date_str):
        """Parse date from various formats to YYYY-MM-DD format"""
        if not date_str:
            return False
            
        formats = ['%d-%m-%Y', '%d/%m/%Y']
        
        for fmt in formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
                
        _logger.warning(f"Could not parse date: {date_str}")
        return False
    
    def _get_entity_processors(self):
        """Return entity processors in proper processing order"""
        return [
            ('makes', AircraftMakeProcessor(self, 'flight.aircraft.make', 'makes')),
            ('models', AircraftModelProcessor(self, 'flight.aircraft.model', 'models')),
            ('aircraft', AircraftProcessor(self, 'flight.aircraft', 'aircraft')),
            ('aerodromes', AerodromeProcessor(self, 'flight.aerodrome', 'aerodromes')),
            ('flights', FlightProcessor(self, 'flight.flight', 'flights')),
            ('remarks', FlightPilotRemarkProcessor(self, 'flight.pilot.remark', 'remarks')),
        ]
        
    def _create_odoo_records(self, input_file):
        """Process flight data from CSV and create Odoo records"""
        # Load the CSV file using petl
        table = etl.fromcsv(input_file, delimiter=self.delimiter)
        
        # Initialize results and entity cache
        results = {}
        entity_cache = {}
        
        # Process entities in order
        for entity_type, processor in self._get_entity_processors():
            try:
                _logger.info(f"Processing {entity_type}...")
                
                # Prepare table for this entity
                entity_table = processor.prepare_table(table)
                
                # Process records
                count, cache = processor.process_records(entity_table, entity_cache)
                
                # Store results
                results[entity_type] = count
                entity_cache[entity_type] = cache
                
                _logger.info(f"Created {count} {entity_type}")
            except Exception as e:
                _logger.error(f"Error processing {entity_type}: {str(e)}")
                self.failed_count += 1
        
        return results