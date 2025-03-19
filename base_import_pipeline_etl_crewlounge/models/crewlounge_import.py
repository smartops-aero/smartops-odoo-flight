from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class BaseImportPipeline(models.Model):
    _inherit = "base.import.pipeline"
    
    def _selection_implementation(self):
        selection = super()._selection_implementation()
        selection.append(('crewlounge', 'Flight Import - CrewLounge'))
        return selection
    
    def _crewlounge_extract(self, file_content, filename=None, csv_delimiter=',', **kwargs):
        """Extract data from CrewLounge CSV file"""
        if not file_content:
            raise UserError(_("No file content provided"))
            
        # Use the CSV extraction helper method
        return self.env['base.import.pipeline']._extract_from_csv(
            file_content, 
            filename,
            delimiter=csv_delimiter
        )


class BaseImportPipelineMapping(models.Model):
    _inherit = "base.import.pipeline.mapping"
    
    def _selection_transformation(self):
        selection = super()._selection_transformation()
        selection.append(('crewlounge_engine_type_mapping', 'Crewlounge Engine Type Mapping'))
        selection.append(('crewlounge_equipment_type_mapping', 'Crewlounge Equipment Type Mapping'))
        selection.append(('crewlounge_aircraft_class_mapping', 'Crewlounge Aircraft Class Mapping'))
        selection.append(('crewlounge_gear_type_mapping', 'Crewlounge Gear Type Mapping'))
        return selection
    
    def _transform_crewlounge_engine_type_mapping(self, value):
        """Map engine type values from CrewLounge format to Odoo format"""
        if not value:
            return value
            
        # Normalize the input by converting to lowercase and removing extra spaces
        normalized_value = value.lower().strip()
        
        # Define mapping from source values to target values
        engine_type_map = {
            'piston': 'piston',
            'turbine (jet-fan)': 'turbofan',
            'turbine (prop-shaft)': 'turboprop',
            'unpowered': 'non_powered',
        }
        
        # Try exact match first
        if normalized_value in engine_type_map:
            return engine_type_map[normalized_value]
            
        # If not found, try partial matches
        for src, target in engine_type_map.items():
            if src in normalized_value:
                return target
                
        # For more complex cases
        if 'jet' in normalized_value or 'fan' in normalized_value:
            return 'turbofan'
        elif 'prop' in normalized_value:
            return 'turboprop'
        elif 'diesel' in normalized_value:
            return 'diesel'
        elif 'electric' in normalized_value:
            return 'electric'
        elif 'radial' in normalized_value:
            return 'radial'
        elif 'turbojet' in normalized_value:
            return 'turbojet'
        elif 'turboshaft' in normalized_value:
            return 'turboshaft'
            
        # Log warning for unrecognized values
        _logger.warning("Unrecognized engine type: %s", value)
        
        # Return default if available, otherwise return None
        return self.default_value if self.default_value else None
        
    def _transform_crewlounge_equipment_type_mapping(self, value):
        """Map equipment type based on AC_ISSIM field (TRUE/FALSE)
        
        If AC_ISSIM is TRUE, it's a simulator (FFS)
        If AC_ISSIM is FALSE, it's an aircraft
        """
        if not value:
            return 'aircraft'  # Default to aircraft if no value
            
        # Normalize the value
        normalized_value = str(value).strip().upper()
        
        # Map based on TRUE/FALSE
        if normalized_value == 'TRUE':
            return 'ffs'  # Full Flight Simulator
        else:
            return 'aircraft'  # Default to aircraft for any other value
            
    def _transform_crewlounge_aircraft_class_mapping(self, value, record):
        """
        Determine aircraft class based on CSV fields:
        - AC_CLASS (Aeroplane, etc.)
        - AC_SPSE (Single Pilot Single Engine)
        - AC_SPME (Single Pilot Multi Engine)
        - AC_GLIDER (Glider)
        - AC_SEA (Seaplane)
        - AC_ENGINES (Single or Multi)
        
        Maps to appropriate class_id reference from flight.aircraft.class model
        
        Args:
            value: The value of the source field (if any)
            record: The complete record dictionary with all CSV fields
        """
        if not record:
            return None
            
        # Default to None if we can't determine
        class_ref = None
        
        # Get all relevant fields and normalize them
        ac_class = self._get_field_value(record, 'AC_CLASS', '').lower().strip()
        ac_spse = self._normalize_boolean(self._get_field_value(record, 'AC_SPSE', 'FALSE'))
        ac_spme = self._normalize_boolean(self._get_field_value(record, 'AC_SPME', 'FALSE'))
        ac_glider = self._normalize_boolean(self._get_field_value(record, 'AC_GLIDER', 'FALSE'))
        ac_sea = self._normalize_boolean(self._get_field_value(record, 'AC_SEA', 'FALSE'))
        ac_engines = self._get_field_value(record, 'AC_ENGINES', '').lower().strip()
        
        # Determine class based on fields
        if ac_glider:
            # It's a glider
            class_ref = 'flight.class_glider'
        elif 'aeroplane' in ac_class or 'airplane' in ac_class:
            # It's an airplane, determine which type
            if ac_sea:
                # Seaplane
                if ac_engines == 'multi' or ac_spme:
                    class_ref = 'flight.class_airplane_mes'  # Multi-Engine Sea
                else:
                    class_ref = 'flight.class_airplane_ses'  # Single-Engine Sea
            else:
                # Land plane
                if ac_engines == 'multi' or ac_spme:
                    class_ref = 'flight.class_airplane_mel'  # Multi-Engine Land
                else:
                    class_ref = 'flight.class_airplane_sel'  # Single-Engine Land
        elif 'rotorcraft' in ac_class or 'helicopter' in ac_class:
            # It's a rotorcraft
            class_ref = 'flight.class_rotorcraft_helicopter'
        elif 'gyroplane' in ac_class or 'gyrocopter' in ac_class:
            class_ref = 'flight.class_rotorcraft_gyroplane'
        elif 'balloon' in ac_class:
            class_ref = 'flight.class_lighter_than_air_balloon'
        elif 'airship' in ac_class:
            class_ref = 'flight.class_lighter_than_air_airship'
        elif 'powered lift' in ac_class:
            class_ref = 'flight.class_powered_lift'
        elif 'powered parachute' in ac_class:
            class_ref = 'flight.class_powered_parachute'
        elif 'weight shift' in ac_class:
            class_ref = 'flight.class_weight_shift_control'
            
        # Default for airplanes if nothing else matches
        if not class_ref and ('aeroplane' in ac_class or 'airplane' in ac_class or ac_class == ''):
            # Default to single engine land if we can't determine specifics
            class_ref = 'flight.class_airplane_sel'
            
        # Log warning if we couldn't determine the class
        if not class_ref:
            _logger.warning("Could not determine aircraft class for record: %s", record)
            return None
            
        # Convert XML ID to database ID
        try:
            class_id = self.env.ref(class_ref).id
            _logger.info("Resolved XML ID %s to database ID %s", class_ref, class_id)
            return class_id
        except Exception as e:
            _logger.error("Failed to resolve XML ID %s: %s", class_ref, e)
            return None
        
    def _transform_crewlounge_gear_type_mapping(self, value, record):
        """
        Determine aircraft gear type based on CSV fields:
        - AC_SEA (Seaplane)
        - AC_TAILWHEEL (Tailwheel aircraft)
        - AC_COMPLEX (Complex aircraft with retractable landing gear)
        
        Maps to appropriate gear_type selection option in flight.aircraft model
        
        Args:
            value: The value of the source field (if any)
            record: The complete record dictionary with all CSV fields
        """
        if not record:
            return None
            
        # Get all relevant fields and normalize them as booleans
        ac_sea = self._normalize_boolean(self._get_field_value(record, 'AC_SEA', 'FALSE'))
        ac_tailwheel = self._normalize_boolean(self._get_field_value(record, 'AC_TAILWHEEL', 'FALSE'))
        ac_complex = self._normalize_boolean(self._get_field_value(record, 'AC_COMPLEX', 'FALSE'))
        
        # Determine gear type based on fields using the logic provided
        if ac_sea:
            return "floats"
        elif ac_tailwheel and not ac_complex:
            return "fixed_tailwheel"
        elif ac_tailwheel and ac_complex:
            return "retractable_tailwheel"
        elif not ac_tailwheel and not ac_complex:
            return "fixed_tricycle"
        elif not ac_tailwheel and ac_complex:
            return "retractable_tricycle"
        
        # Default if we can't determine
        _logger.warning("Could not determine gear type for record: %s", record)
        return None
        
    def _get_field_value(self, record, field_name, default=''):
        """Helper method to safely get field value from record"""
        return record.get(field_name, default)
        
    def _normalize_boolean(self, value):
        """Convert string boolean values to actual boolean"""
        if isinstance(value, bool):
            return value
            
        normalized = str(value).strip().upper()
        return normalized == 'TRUE' or normalized == '1' or normalized == 'YES'
