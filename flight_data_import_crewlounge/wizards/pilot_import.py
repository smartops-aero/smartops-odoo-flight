# Copyright 2025 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).

import logging

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


class FlightDataImportCrewLoungePilot(models.TransientModel):
    """Wizard to import pilots from CrewLounge CSV exports."""

    _name = "flight.data.import.crewlounge.pilot"
    _description = "Import Pilots from CrewLounge"
    _inherit = ["flight.data.file.import.mixin"]

    import_line_ids = fields.One2many(
        "flight.data.import.crewlounge.pilot.line", "import_id", string="Import Lines"
    )
    
    def _get_default_field_mapping(self):
        """Return default field mapping for CrewLounge pilot CSV format."""
        return {
            "company": 0,  # Company
            "employee_id": 1,  # Employee ID, mapped as barcode in res.partner
            "name": 2,  # Pilot FullName
            "phone": 3,  # Phone
            "email": 4,  # Email
            "notes": 5,  # Notes
        }
    
    def _get_import_line_model(self):
        """Get the model name for import lines."""
        return "flight.data.import.crewlounge.pilot.line"
    
    def _get_lines_to_import(self):
        """Get lines to import based on state."""
        return self.import_line_ids.filtered(
            lambda l: l.state in ['valid', 'conflict'] and 
            (l.state != 'conflict' or self.update_existing)
        )
    
    def _get_all_import_lines(self):
        """Get all import lines."""
        return self.import_line_ids
    
    def _update_statistics(self):
        """Update import statistics based on import lines."""
        self.write({
            'total_rows': len(self.import_line_ids),
            'valid_rows': len(self.import_line_ids.filtered(lambda l: l.state == 'valid')),
            'invalid_rows': len(self.import_line_ids.filtered(lambda l: l.state == 'invalid')),
            'conflict_rows': len(self.import_line_ids.filtered(lambda l: l.state == 'conflict')),
        })
    
    def action_reset(self):
        """Reset the import wizard to draft state."""
        self.ensure_one()
        
        # Delete existing import lines
        if self.import_line_ids:
            self.import_line_ids.unlink()
        
        return super().action_reset()
    
    def _process_parsed_data(self, parsed_data, result):
        """Process the parsed data and create import lines.
        
        This method implements the abstract method from flight.data.file.import.mixin.
        It processes the parsed data and creates import lines for each row.
        
        Args:
            parsed_data (dict): Parsed data with header and rows
            result (dict): Dictionary to store import results
        """
        self.ensure_one()
        
        # Get field mapping
        mapping = self._get_default_field_mapping()
        
        # Process rows
        for i, row in enumerate(parsed_data.get('rows', []), start=1):
            # Skip empty rows
            if not any(row):
                continue
            
            try:
                # Safely get values with index checking
                company_name = row[mapping["company"]] if len(row) > mapping["company"] else ""
                employee_id = row[mapping["employee_id"]] if len(row) > mapping["employee_id"] else ""
                name = row[mapping["name"]] if len(row) > mapping["name"] else ""
                phone = row[mapping["phone"]] if len(row) > mapping["phone"] else ""
                email = row[mapping["email"]] if len(row) > mapping["email"] else ""
                notes = row[mapping["notes"]] if len(row) > mapping["notes"] else ""
                
                # Create import line with raw data only
                line_vals = {
                    "import_id": self.id,
                    "raw_data": ",".join(row),
                    "company_name": company_name,
                    "employee_id": employee_id,
                    "name": name,
                    "phone": phone,
                    "email": email,
                    "notes": notes,
                    "state": "valid",  # Start in draft state
                }
                
                # Create the line
                line = self.env[self._get_import_line_model()].create(line_vals)
                
                # Validate the line (sanitizes data, checks conflicts, etc.)
                line.validate()

                # Update result statistics
                result["total"] += 1
                if line.state == "valid":
                    result["valid"] += 1
                elif line.state == "invalid":
                    result["invalid"] += 1
                elif line.state == "conflict":
                    result["conflict"] += 1
                    
            except Exception as e:
                _logger.exception("Error processing row %s: %s", i, e)
                # Create an invalid line with error message
                self.env[self._get_import_line_model()].create({
                    "import_id": self.id,
                    "raw_data": ",".join(row) if isinstance(row, list) else str(row),
                    "state": "invalid",
                    "error_message": str(e),
                })
                result["total"] += 1
                result["invalid"] += 1
