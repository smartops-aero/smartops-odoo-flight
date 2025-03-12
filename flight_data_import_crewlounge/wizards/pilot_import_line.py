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
    row_index = fields.Integer("Row Index", readonly=True)
    
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
            
            # Find company if specified
            if line.company_name and line.company_name != "PRIVATE":
                company = self.env["res.partner"].search([
                    ("name", "=", line.company_name),
                    ("is_company", "=", True),
                ], limit=1)
                line.company_id = company.id if company else False
            
            # Check for existing pilot by email
            if line.email:
                partner = self.env["res.partner"].search([
                    ("email", "=", line.email),
                    ("is_company", "=", False),
                ], limit=1)
                if partner:
                    line.partner_id = partner.id
                    line.is_new = False
                    line.mark_as_conflict(_("Pilot with this email already exists"))
    
    def validate(self):
        """Validate the import line.
        
        Implementation of the abstract method from flight.data.import.line.mixin.
        
        Returns:
            bool: True if the line is valid, False otherwise
        """
        self.ensure_one()
        self._onchange_validate()
        return self.state == 'valid'
    
    def prepare_import_values(self):
        """Prepare values for import.
        
        Implementation of the abstract method from flight.data.import.line.mixin.
        
        Returns:
            dict: Values for creating/updating the target record
        """
        self.ensure_one()
        
        # Prepare partner values
        partner_vals = {
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "comment": self.notes,
            "is_company": False,
        }
        
        # Handle company
        if self.company_name and self.company_name != "PRIVATE":
            # Find or create company
            if self.company_id:
                company = self.company_id
            else:
                company = self.env["res.partner"].create({
                    "name": self.company_name,
                    "is_company": True,
                })
            
            # Link pilot to company
            partner_vals["parent_id"] = company.id
            
        return partner_vals
    
    def check_conflicts(self):
        """Check for conflicts with existing records.
        
        Implementation of the abstract method from flight.data.import.line.mixin.
        
        Returns:
            tuple: (has_conflict, conflict_record_id, conflict_message)
        """
        self.ensure_one()
        
        # Check for existing pilot by email
        if self.email:
            partner = self.env["res.partner"].search([
                ("email", "=", self.email),
                ("is_company", "=", False),
            ], limit=1)
            if partner:
                return (True, partner.id, _("Pilot with this email already exists"))
        
        return (False, False, False)
    
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
