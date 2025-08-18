import json

from odoo import models


class JsonTextMixin(models.AbstractModel):
    """Mixin to provide JSON to formatted text conversion utilities."""
    
    _name = 'json.text.mixin'
    _description = 'JSON to Text Conversion Mixin'

    def json2text(self, json_data, indent=2):
        """
        Convert JSON data to formatted text with proper newline handling.
        
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
            
            # Convert to formatted JSON
            formatted_json = json.dumps(parsed_data, indent=indent, ensure_ascii=False, separators=(',', ': '))
            
            # Process the JSON string to convert \n to actual newlines in text values
            # This handles cases where text content contains newline characters
            def process_newlines(text):
                """Replace literal \\n with actual newlines in JSON string values"""
                import re
                # Find all string values and replace \n with actual newlines
                def replace_newlines(match):
                    content = match.group(1)
                    # Replace literal \n with actual newlines
                    content = content.replace('\\n', '\n')
                    return f'"{content}"'
                
                # Match quoted strings and process newlines within them
                return re.sub(r'"([^"]*(?:\\.[^"]*)*)"', replace_newlines, text)
            
            return process_newlines(formatted_json)
            
        except (json.JSONDecodeError, TypeError):
            # If parsing fails, return the original data as string
            return str(json_data) if json_data is not None else ""