# Copyright 2025 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).

import logging

from odoo import _, api, fields, models

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
                # Get company if applicable
                company_name = row[mapping["company"]] if len(row) > mapping["company"] else ""
                company = False
                if company_name and company_name != "PRIVATE":
                    # Only find company during preview, don't create
                    company = self.env["flight.import.helper"].find_company(company_name)
                
                # Safely get values with index checking
                employee_id = row[mapping["employee_id"]] if len(row) > mapping["employee_id"] else ""
                name = row[mapping["name"]] if len(row) > mapping["name"] else ""
                phone = row[mapping["phone"]] if len(row) > mapping["phone"] else ""
                email = row[mapping["email"]] if len(row) > mapping["email"] else ""
                notes = row[mapping["notes"]] if len(row) > mapping["notes"] else ""
                
                # Create import line
                line_vals = {
                    "import_id": self.id,
                    "raw_data": ",".join(row),
                    "company_name": company_name,
                    "company_id": company.id if company else False,
                    "employee_id": employee_id,
                    "name": name,
                    "phone": phone,
                    "email": email,
                    "notes": notes,
                }
                
                # Create the line - validation will happen automatically via onchange
                line = self.env["flight.data.import.crewlounge.pilot.line"].create(line_vals)
                
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
                self.env["flight.data.import.crewlounge.pilot.line"].create({
                    "import_id": self.id,
                    "raw_data": ",".join(row) if isinstance(row, list) else str(row),
                    "state": "invalid",
                    "error_message": str(e),
                })
                result["total"] += 1
                result["invalid"] += 1
    
    def _update_statistics(self):
        """Update import statistics based on import lines."""
        valid_count = len(self.import_line_ids.filtered(lambda l: l.state == 'valid'))
        invalid_count = len(self.import_line_ids.filtered(lambda l: l.state == 'invalid'))
        conflict_count = len(self.import_line_ids.filtered(lambda l: l.state == 'conflict'))
        imported_count = len(self.import_line_ids.filtered(lambda l: l.state == 'imported'))
        total_count = len(self.import_line_ids)
        
        # Update statistics fields
        self.write({
            'total_rows': total_count,
            'valid_rows': valid_count,
            'invalid_rows': invalid_count,
            'conflict_rows': conflict_count,
            'statistics': _(
                "Total: %(total)s\n"
                "Valid: %(valid)s\n"
                "Invalid: %(invalid)s\n"
                "Conflicts: %(conflict)s\n"
                "Imported: %(imported)s",
                total=total_count,
                valid=valid_count,
                invalid=invalid_count,
                conflict=conflict_count,
                imported=imported_count,
            ),
        })
    
    def action_import(self):
        """Import the selected lines."""
        self.ensure_one()
        
        # Only import lines that are selected and valid
        lines_to_import = self.import_line_ids.filtered(
            lambda l: l.to_import and l.state != "invalid"
        )
        
        if not lines_to_import:
            return self._show_error(_("Please select at least one valid line to import."))
        
        stats = {
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "failed": 0,
        }
        
        imported_ids = []
        for line in lines_to_import:
            try:
                partner_id = line.action_import()
                if partner_id:
                    imported_ids.append(partner_id)
                    if line.state == "imported":
                        if line.is_new:
                            stats["created"] += 1
                        else:
                            stats["updated"] += 1
                else:
                    stats["skipped"] += 1
            except Exception as e:
                _logger.exception("Error importing line %s", line.id)
                line.write({
                    "state": "invalid",
                    "error_message": str(e),
                })
                stats["failed"] += 1
        
        # Update statistics after import
        self._update_statistics()
        
        # Update state if all lines are imported
        if all(line.state in ['imported', 'invalid'] for line in self.import_line_ids):
            self.state = 'done'
        
        # Show import results
        message = _(
            "Import completed:\n"
            "Created: %(created)s\n"
            "Updated: %(updated)s\n"
            "Skipped: %(skipped)s\n"
            "Failed: %(failed)s",
            created=stats["created"],
            updated=stats["updated"],
            skipped=stats["skipped"],
            failed=stats["failed"],
        )
        
        return self._show_success(message)
