# Copyright 2025 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class FlightDataImportCrewLoungePilotLine(models.TransientModel):
    """Line for importing a pilot from CrewLounge CSV."""

    _name = "flight.data.import.crewlounge.pilot.line"
    _description = "CrewLounge Pilot Import Line"
    _inherit = ["flight.data.import.line.mixin"]

    # Reference to import wizard
    import_id = fields.Many2one(
        "flight.data.import.crewlounge.pilot", 
        string="Import", 
        required=True, 
        ondelete="cascade"
    )
    
    # Raw data fields from CSV
    company_name = fields.Char("Company")
    employee_id = fields.Char("Employee ID")
    name = fields.Char("Name")
    phone = fields.Char("Phone")
    email = fields.Char("Email")
    notes = fields.Char("Notes")
    
    # Processed data fields
    company_id = fields.Many2one("res.partner", "Company", domain=[("is_company", "=", True)])
    partner_id = fields.Many2one("res.partner", "Existing Pilot")
    is_new = fields.Boolean("Is New", default=True)
    
    def _find_pilot(self, name=None, email=None):
        """Find a pilot by name or email.
        
        This method searches for a pilot with the given name or email.
        
        Args:
            name (str, optional): Name of the pilot to find
            email (str, optional): Email of the pilot to find
            
        Returns:
            res.partner: Pilot record or False if not found
        """
        if not name and not email:
            return False
        
        domain = [("is_company", "=", False)]
        
        # Build search domain with OR conditions
        or_conditions = []
        if email and email.strip():
            or_conditions.append(("email", "=ilike", email.strip()))
        if name and name.strip():
            or_conditions.append(("name", "=", name.strip()))
            
        # Only add OR operator and conditions if we have conditions to add
        if len(or_conditions) > 1:
            domain.append('|')
            domain.extend(or_conditions)
        elif len(or_conditions) == 1:
            domain.extend(or_conditions)
            
        return self.env["res.partner"].search(domain, limit=1)
    
    @api.onchange("company_name", "name", "email")
    def _onchange_validate(self):
        """Validate the line data and check for conflicts."""
        for line in self:
            # Reset state
            line.state = "valid"
            line.error_message = False
            line.warning_message = False
            line.is_new = True
            line.partner_id = False
            
            # Basic validation
            if not line.name:
                line.mark_as_invalid(_("Pilot name is required"))
                continue
            
            # Find company if specified (only find, don't create during validation)
            if line.company_name and line.company_name != "PRIVATE":
                company = self.env["flight.import.helper"].find_company(line.company_name)
                line.company_id = company.id if company else False
            
            # Check for existing pilot by email or name
            partner = self._find_pilot(line.name, line.email)
            if partner:
                line.partner_id = partner.id
                line.is_new = False
                line.mark_as_conflict(_("Pilot already exists"))
    
    def prepare_import_values(self):
        """Prepare values for import.
        
        Returns:
            dict: Values for partner creation/update
        """
        self.ensure_one()
        
        # Prepare partner values
        vals = {
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "comment": self.notes,
            "barcode": self.employee_id,
            "is_company": False,
        }
        
        # Add company if specified
        if self.company_name and self.company_name != "PRIVATE":
            # First check if company exists
            company = self.env["flight.import.helper"].find_company(self.company_name)
            
            # If not found, create it
            if not company:
                company = self.env["flight.import.helper"].create_or_update_company(self.company_name)
                
            vals["parent_id"] = company.id if company else False
        
        return vals
    
    def validate(self):
        """Validate the import line.
        
        Implementation of the abstract method from flight.data.import.line.mixin.
        
        Returns:
            bool: True if the line is valid, False otherwise
        """
        self.ensure_one()
        self._onchange_validate()
        return self.state == 'valid'
    
    def check_conflicts(self):
        """Check for conflicts with existing records.
        
        Implementation of the abstract method from flight.data.import.line.mixin.
        
        Returns:
            bool: True if there is a conflict, False otherwise
        """
        self.ensure_one()
        
        # Check for existing pilot by email or name
        partner = self._find_pilot(self.name, self.email)
        if partner:
            return True
        
        return False

    def action_import(self):
        """Import the pilot data."""
        self.ensure_one()
        
        # Skip invalid lines
        if self.state == "invalid":
            return False
        
        try:
            # Get import values
            partner_vals = self.prepare_import_values()
            
            # Create or update partner
            if self.is_new:
                partner = self.env["res.partner"].create(partner_vals)
            else:
                self.partner_id.write(partner_vals)
                partner = self.partner_id
            
            # Mark as imported
            self.mark_as_imported()
            
            return partner.id
        except Exception as e:
            _logger.exception("Error importing pilot: %s", self.name)
            self.mark_as_invalid(str(e))
            return False
