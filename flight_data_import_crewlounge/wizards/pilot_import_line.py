# Copyright 2025 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class FlightDataImportCrewLoungePilotLine(models.TransientModel):
    """Import line for CrewLounge pilot import."""

    _name = "flight.data.import.crewlounge.pilot.line"
    _description = "Pilot Import Line"
    _inherit = ["flight.data.import.line.mixin"]

    # Reference to import wizard
    import_id = fields.Many2one(
        "flight.data.import.crewlounge.pilot", "Import", ondelete="cascade"
    )

    # Raw data fields from file
    company_name = fields.Char("Company")
    employee_id = fields.Char("Employee ID")
    name = fields.Char("Name")
    email = fields.Char("Email")
    phone = fields.Char("Phone")
    notes = fields.Text("Notes")

    # Conflict detection info (not relational fields)
    existing_partner_id = fields.Integer("Existing Partner ID", readonly=True)
    is_new = fields.Boolean("New Pilot", default=True)

    @api.onchange('name', 'email', 'employee_id')
    def _onchange_validate(self):
        """Validate the line data when user changes values.
        
        This method is triggered when the user changes any of the
        fields that could affect the validity of the line.
        """
        for line in self:
            # Skip validation for imported lines
            if line.state == 'imported':
                continue
                
            # Reset conflict detection info before validation
            line.existing_partner_id = False
            line.is_new = True
                
            # Call the standard validate method
            line.validate()
            
    def sanitize_data(self):
        """Sanitize the import line data."""
        self.ensure_one()
        
        # Strip whitespace from text fields
        if self.name:
            self.name = self.name.strip()
        if self.email:
            self.email = self.email.strip()
        if self.phone:
            self.phone = self.phone.strip()
        if self.employee_id:
            self.employee_id = self.employee_id.strip()
        if self.company_name:
            self.company_name = self.company_name.strip()
        
        # Convert special values
        if self.company_name and self.company_name.upper() == "PRIVATE":
            self.company_name = False
        
        return True
    
    def _find_pilot(self, name=None, email=None, barcode=None):
        """Find an existing pilot by name or email.
        
        Args:
            name (str): Pilot name
            email (str): Pilot email
            
        Returns:
            res.partner: Existing pilot record, or False if not found
        """
        if not name and not email:
            return False
        
        domain = [("is_company", "=", False)]
        or_conditions = []
        
        # Add email condition if provided
        if email and email.strip():
            or_conditions.append(("email", "=ilike", email.strip()))
        
        # Add name condition if provided
        if name and name.strip():
            or_conditions.append(("name", "=ilike", name.strip()))
        
        # Add barcode condition if provided
        if barcode and barcode.strip():
            or_conditions.append(("barcode", "=", barcode.strip()))
        
        # Only add OR operator and conditions if we have conditions to add
        if len(or_conditions) > 1:
            domain.append('|')
            domain.extend(or_conditions)
        elif len(or_conditions) == 1:
            domain.extend(or_conditions)
        
        _logger.info("Domain: %s", domain)
        
        # Search for existing pilot
        partner = self.env["res.partner"].search(domain, limit=1)
        return partner if partner else False
    
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
            # Store the partner ID for later use in action_import
            # but don't create a relational field
            self.existing_partner_id = partner.id
            self.is_new = False
            return True
        
        return False
    
    def validate(self):
        """Validate the import line.
        
        Implementation of the abstract method from flight.data.import.line.mixin.
        
        Returns:
            bool: True if the line is valid, False otherwise
        """
        self.ensure_one()
        
        # Sanitize data first
        self.sanitize_data()
        
        # Basic validation
        if not self.name:
            self.mark_as_invalid(_("Pilot name is required"))
            return False
            
        # Check for conflicts
        if self.check_conflicts():
            self.mark_as_invalid(_("Pilot already exists"))
            # Conflict here is invalid as we don't want to import existing pilots
            return False
            
        # Mark as valid if no issues found
        self.mark_as_valid()
        return True
    
    def action_import(self):
        """Import the pilot data."""
        self.ensure_one()
        
        # Skip invalid lines
        if self.state == "invalid":
            return False
        
        # Skip conflicted lines if update_existing is False
        if self.state == "conflict" and not self.import_id.update_existing:
            return False
        
        try:
            # Get import values
            partner_vals = self.prepare_import_values()
            
            # Find or create company if needed
            if self.company_name:
                company = self.env["flight.import.helper"].find_company(self.company_name)
                if company:
                    partner_vals["parent_id"] = company.id
                else:
                    company = self.env["flight.import.helper"].create_or_update_company(self.company_name)
                    partner_vals["parent_id"] = company.id
            
            # Create or update partner
            if self.is_new:
                partner = self.env["res.partner"].create(partner_vals)
            else:
                # Get the partner from the stored ID
                partner = self.env["res.partner"].browse(self.existing_partner_id)
                partner.write(partner_vals)
            
            # Mark as imported
            self.mark_as_imported()
            
            return partner.id
        except Exception as e:
            _logger.exception("Error importing pilot: %s", self.name)
            self.mark_as_invalid(str(e))
            return False
    
    def mark_as_conflict(self, conflict_message):
        """Mark the line as conflict and set default import behavior."""
        self.write({
            "is_new": False,
        })
        
        super().mark_as_conflict(conflict_message)
    
    def prepare_import_values(self):
        """Prepare values for creating or updating a partner.
        
        Returns:
            dict: Values for creating or updating a partner
        """
        self.ensure_one()
        
        # Prepare base values
        vals = {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "comment": self.notes,
            "is_company": False,
        }
        
        # Add employee ID as barcode if provided
        if self.employee_id:
            vals["barcode"] = self.employee_id
        
        return vals
