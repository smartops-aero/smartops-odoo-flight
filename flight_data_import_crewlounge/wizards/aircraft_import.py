# Copyright 2025 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).

import logging

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


class FlightDataImportCrewLoungeAircraft(models.TransientModel):
    """Wizard to import aircraft from CrewLounge CSV exports."""

    _name = "flight.data.import.crewlounge.aircraft"
    _description = "Import Aircraft from CrewLounge"
    _inherit = ["flight.data.file.import.mixin"]

    import_line_ids = fields.One2many(
        "flight.data.import.crewlounge.aircraft.line", "import_id", string="Import Lines"
    )
    
    def _get_default_field_mapping(self):
        """Return default field mapping for CrewLounge aircraft CSV format."""
        return {
            "dev": 2,            # DEV (equipment type)
            "reference": 4,      # Reference (registration)
            "ac": 5,             # AC (model code)
            "cat": 7,            # CAT (category - multi/single pilot)
            "company": 8,        # Company (operator)
            "pw": 9,             # PW (engine type)
            "wt": 10,            # WT (weight)
        }
    
    def _get_import_line_model(self):
        """Get the model name for import lines."""
        return "flight.data.import.crewlounge.aircraft.line"
    
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
                dev = row[mapping["dev"]] if len(row) > mapping["dev"] else ""
                reference = row[mapping["reference"]] if len(row) > mapping["reference"] else ""
                ac = row[mapping["ac"]] if len(row) > mapping["ac"] else ""
                cat = row[mapping["cat"]] if len(row) > mapping["cat"] else ""
                company = row[mapping["company"]] if len(row) > mapping["company"] else ""
                pw = row[mapping["pw"]] if len(row) > mapping["pw"] else ""
                wt = row[mapping["wt"]] if len(row) > mapping["wt"] else ""
                
                # Create import line with raw data only
                line_vals = {
                    "import_id": self.id,
                    "raw_data": ",".join(row),
                    "dev": dev,
                    "reference": reference,
                    "ac": ac,
                    "cat": cat,
                    "company_name": company,
                    "pw": pw,
                    "wt": wt,
                    "state": "valid",  # Start in valid state
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
