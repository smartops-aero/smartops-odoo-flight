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
    def find_company(self, company_name):
        """Find a company by name.
        
        Args:
            company_name (str): Name of the company to find
            
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
        
        return company
    
    @api.model
    def create_or_update_company(self, company_name, company_vals=None):
        """Create or update a company by name.
        
        Args:
            company_name (str): Name of the company to create or update
            company_vals (dict, optional): Additional values for company creation/update
            
        Returns:
            res.partner: Company record or False
        """
        if not company_name or company_name == "PRIVATE":
            return False
            
        # Find existing company
        company = self.find_company(company_name)
        
        # Prepare values
        vals = company_vals or {}
        vals.update({
            "name": company_name,
            "is_company": True,
        })
        
        # Create or update company
        if company:
            company.write(vals)
        else:
            company = self.env["res.partner"].create(vals)
        
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
    
