# Copyright 2025 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).

from odoo import api, models


class FlightImportHelper(models.AbstractModel):
    """Helper model for flight.flight data imports.
    
    This model provides common functionality for flight.flight data imports,
    """
    _name = "flight.import.helper"
    _description = "Flight Import Helper"
    
    @api.model
    def find_or_create_company(self, company_name):
        """Find or create a company by name.
        
        This method uses a cache to avoid duplicate lookups and creation.
        
        Args:
            company_name (str): Name of the company to find or create
            
        Returns:
            res.partner: Company record or False
        """
        if not company_name or company_name == "PRIVATE":
            return False
            
            
        # Search for existing company (case-insensitive)
        company = self.env["res.partner"].search([
            ("name", "=ilike", company_name),
            ("is_company", "=", True),
        ], limit=1)
        
        # Create company if not found
        if not company:
            company = self.env["res.partner"].create({
                "name": company_name,
                "is_company": True,
            })
        
        return company

    
    @api.model
    def _generate_unique_import_id(self, record_vals, source=None):
        """Generate a unique import ID for flight records.
        
        Args:
            record_vals (dict): Values for creating/updating a flight record
            source (str): Source of the import (e.g., 'csv', 'excel')
            
        Returns:
            str: Unique import ID for the flight record
        """
        if not record_vals.get("import_id"):
            return None
            
        # Create a unique prefix based on source
        source_prefix = source or "import"
        
        # Include date and flight number for uniqueness
        date_str = record_vals.get("date", "").replace("-", "")
        flight_number = record_vals.get("flight_number", "")
        aircraft_reg = record_vals.get("aircraft_reg", "")
        
        return f"{source_prefix}_{date_str}_{flight_number}_{aircraft_reg}_{record_vals['import_id']}"
    
