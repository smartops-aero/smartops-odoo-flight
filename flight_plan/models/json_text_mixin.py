import json
from odoo import models


class JsonTextMixin(models.AbstractModel):
    """Mixin to provide JSON to formatted text conversion utilities."""
    
    _name = 'json.text.mixin'
    _description = 'JSON to Text Conversion Mixin'

    def json2text(self, json_data, indent=2):
        """
        Convert JSON data to formatted text.
        
        Args:
            json_data: JSON data (dict, list, or None)
            indent: Number of spaces for indentation
            
        Returns:
            str: Formatted text representation or empty string if None/empty
        """
        if not json_data:
            return ""
        
        try:
            if isinstance(json_data, str):
                # If it's already a string, try to parse it as JSON
                parsed_data = json.loads(json_data)
            else:
                parsed_data = json_data
                
            return json.dumps(parsed_data, indent=indent, ensure_ascii=False, separators=(',', ': '))
        except (json.JSONDecodeError, TypeError):
            # If parsing fails, return the original data as string
            return str(json_data) if json_data is not None else ""