from datetime import datetime
from odoo import api, models


class FlightImportUtils(models.AbstractModel):
    _name = "flight.import.utils"
    _description = "Flight Import Utilities"

    @api.model
    def parse_date(self, date_str, format_str=None):
        """
        Parse a date string into a date object
        
        :param date_str: Date string to parse
        :param format_str: Format string to use (defaults to config's date_format)
        :return: Date object
        """
        if not date_str:
            return False
            
        if not format_str:
            # Get the default format from a config
            config = self.env["flight.import.config"].search([], limit=1)
            format_str = config.date_format or "%d-%m-%Y"
            
        try:
            return datetime.strptime(date_str, format_str).date()
        except Exception as e:
            self.env.user.notify_warning(
                title="Date Parsing Error",
                message=f"Could not parse date '{date_str}' with format '{format_str}': {e}"
            )
            return False

    @api.model
    def parse_datetime(self, date_str, time_str=None, format_str=None):
        """
        Parse date and time strings into a datetime object
        
        :param date_str: Date string to parse
        :param time_str: Time string to parse (optional)
        :param format_str: Format string to use for date
        :return: Datetime object
        """
        if not date_str:
            return False
            
        # Parse the date
        date_val = self.parse_date(date_str, format_str)
        if not date_val:
            return False
            
        # If no time provided, return datetime at midnight
        if not time_str:
            return datetime.combine(date_val, datetime.min.time())
            
        # Parse the time
        try:
            # Handle different time formats
            hours, minutes = 0, 0
            
            if ":" in time_str:
                time_parts = time_str.strip().split(":")
                hours = int(time_parts[0])
                if len(time_parts) > 1:
                    minutes = int(time_parts[1])
            else:
                # Assume it's in HHMM format
                time_str = time_str.strip()
                if len(time_str) == 4:
                    hours = int(time_str[:2])
                    minutes = int(time_str[2:])
                elif len(time_str) <= 2:
                    hours = int(time_str)
            
            # Create the datetime
            return datetime.combine(
                date_val, 
                datetime.min.time().replace(hour=hours, minute=minutes)
            )
        except Exception as e:
            self.env.user.notify_warning(
                title="Time Parsing Error",
                message=f"Could not parse time '{time_str}': {e}"
            )
            return datetime.combine(date_val, datetime.min.time())

    @api.model
    def map_aircraft_category(self, class_name):
        """
        Map from imported class name to Odoo aircraft category
        
        :param class_name: Class name from import (e.g. 'Aeroplane')
        :return: Aircraft category (e.g. 'airplane')
        """
        if not class_name:
            return "airplane"  # Default
            
        # Define mapping of common class names
        category_mapping = {
            "aeroplane": "airplane",
            "airplane": "airplane",
            "helicopter": "rotorcraft",
            "rotorcraft": "rotorcraft",
            "glider": "glider",
            "balloon": "lighter_than_air",
            "airship": "lighter_than_air",
            "powered lift": "powered_lift",
            "powered parachute": "powered_parachute",
            "weight shift control": "weight_shift_control",
        }
        
        # Normalize the input
        normalized = class_name.lower().strip()
        
        # Return the mapped category or the default
        return category_mapping.get(normalized, "airplane")

    @api.model
    def convert_to_float(self, value):
        """
        Convert a string value to float
        
        :param value: String value to convert
        :return: Float value
        """
        if not value:
            return 0.0
            
        # Handle different formats
        try:
            # Replace comma with dot for decimal separator
            clean_value = value.replace(",", ".")
            return float(clean_value)
        except (ValueError, AttributeError):
            return 0.0

    @api.model
    def get_pilot_from_row(self, row, config):
        """
        Get the pilot from the row data
        
        :param row: Row data
        :param config: Import configuration
        :return: res.partner record for the pilot
        """
        # Check if there's a specific field for pilot mapping
        pilot = None
        
        # Try common pilot fields
        for field in ["PILOT_ID", "PILOT1_ID", "PILOT_NAME", "PILOT1_NAME"]:
            if field in row and row[field]:
                # Try to find the pilot by the given identifier
                pilot_domain = []
                if field.endswith("_ID"):
                    pilot_domain = [("ref", "=", row[field])]
                else:
                    pilot_domain = [("name", "ilike", row[field])]
                
                pilot = self.env["res.partner"].search(pilot_domain, limit=1)
                if pilot:
                    break
        
        # Fall back to default pilot from config
        if not pilot and config.default_pilot_id:
            pilot = config.default_pilot_id
            
        return pilot