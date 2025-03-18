from odoo import api, fields, models, _
from odoo.exceptions import UserError


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
