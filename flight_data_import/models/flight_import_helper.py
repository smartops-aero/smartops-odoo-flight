# Copyright 2025 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).

import re
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
    def find_pilot(self, name=None, email=None, barcode=None):
        """Find an existing pilot by name, email, or barcode.
        
        Args:
            name (str): Pilot name
            email (str): Pilot email
            barcode (str): Pilot barcode/employee ID
            
        Returns:
            res.partner: Existing pilot record, or False if not found
        """
        if not name and not email and not barcode:
            return False
        
        domain = [("is_company", "=", False)]
        or_conditions = []
        
        # Add email condition if provided
        if email and email.strip():
            or_conditions.append(("email", "=", email.strip()))
        
        # Add name condition if provided
        if name and name.strip():
            or_conditions.append(("name", "=", name.strip()))
        
        # Add barcode condition if provided
        if barcode and barcode.strip():
            or_conditions.append(("barcode", "=", barcode.strip()))
        
        # Only add OR operator and conditions if we have conditions to add
        if len(or_conditions) > 1:
            domain.append('|')
            domain.extend(or_conditions)
        elif len(or_conditions) == 1:
            domain.extend(or_conditions)
        
        # Search for existing pilot
        partner = self.env["res.partner"].search(domain, limit=1)
        return partner if partner else False

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

    # Aircraft related methods
    @api.model
    def find_aircraft(self, registration):
        """Find an aircraft by registration.
        
        Args:
            registration (str): Aircraft registration
            
        Returns:
            flight.aircraft: Aircraft record or False
        """
        if not registration:
            return False
            
        # Sanitize registration
        registration = self._sanitize_registration(registration)
            
        # Search for existing aircraft (case-insensitive)
        aircraft = self.env["flight.aircraft"].search([
            ("registration", "=", registration),
        ], limit=1)
        
        return aircraft
    
    @api.model
    def create_or_update_aircraft(self, registration, aircraft_vals=None):
        """Create or update an aircraft by registration.
        
        Args:
            registration (str): Aircraft registration
            aircraft_vals (dict, optional): Additional values for aircraft creation/update
            
        Returns:
            flight.aircraft: Aircraft record or False
        """
        if not registration:
            return False
            
        # Sanitize registration
        registration = self._sanitize_registration(registration)
            
        # Find existing aircraft
        aircraft = self.find_aircraft(registration)
        
        # Prepare values
        vals = aircraft_vals or {}
        vals.update({
            "registration": registration,
        })
        
        # Create or update aircraft
        if aircraft:
            aircraft.write(vals)
        else:
            aircraft = self.env["flight.aircraft"].create(vals)
        
        return aircraft
    
    @api.model
    def find_aircraft_model(self, code=None, name=None):
        """Find an aircraft model by code or name.
        
        Args:
            code (str): Model code
            name (str): Model name
            
        Returns:
            flight.aircraft.model: Model record or False
        """
        if not code and not name:
            return False
        
        domain = []
        or_conditions = []
        
        # Add code condition if provided
        if code and code.strip():
            or_conditions.append(("code", "=ilike", code.strip()))
        
        # Add name condition if provided
        if name and name.strip():
            or_conditions.append(("name", "=ilike", name.strip()))
        
        # Only add OR operator and conditions if we have conditions to add
        if len(or_conditions) > 1:
            domain.append('|')
            domain.extend(or_conditions)
        elif len(or_conditions) == 1:
            domain.extend(or_conditions)
        
        # Search for existing model
        model = self.env["flight.aircraft.model"].search(domain, limit=1)
        return model if model else False
    
    @api.model
    def create_or_update_aircraft_model(self, code, model_vals=None):
        """Create or update an aircraft model by code.
        
        Args:
            code (str): Model code
            model_vals (dict, optional): Additional values for model creation/update
            
        Returns:
            flight.aircraft.model: Model record or False
        """
        if not code:
            return False
            
        # Find existing model
        model = self.find_aircraft_model(code=code)
        
        # Prepare values
        vals = model_vals or {}
        vals.update({
            "code": code,
            "name": vals.get("name", code),
        })
        
        # Create or update model
        if model:
            model.write(vals)
        else:
            model = self.env["flight.aircraft.model"].create(vals)
        
        return model
    
    @api.model
    def find_aircraft_make(self, name):
        """Find an aircraft make by name.
        
        Args:
            name (str): Make name
            
        Returns:
            flight.aircraft.make: Make record or False
        """
        if not name:
            return False
            
        # Search for existing make (case-insensitive)
        make = self.env["flight.aircraft.make"].search([
            ("name", "=ilike", name),
        ], limit=1)
        
        return make
    
    @api.model
    def create_or_update_aircraft_make(self, name, make_vals=None):
        """Create or update an aircraft make by name.
        
        Args:
            name (str): Make name
            make_vals (dict, optional): Additional values for make creation/update
            
        Returns:
            flight.aircraft.make: Make record or False
        """
        if not name:
            return False
            
        # Find existing make
        make = self.find_aircraft_make(name)
        
        # Prepare values
        vals = make_vals or {}
        vals.update({
            "name": name,
        })
        
        # Create or update make
        if make:
            make.write(vals)
        else:
            make = self.env["flight.aircraft.make"].create(vals)
        
        return make
    
    # Helper methods
    @api.model
    def _sanitize_registration(self, registration):
        """Sanitize aircraft registration.
        
        Args:
            registration (str): Aircraft registration
            
        Returns:
            str: Sanitized registration
        """
        if not registration:
            return ""
            
        # Remove any non-alphanumeric characters except dash
        sanitized = re.sub(r"[^a-zA-Z0-9-]", "", registration).strip().upper()
        return sanitized
