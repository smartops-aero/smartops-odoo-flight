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
    existing_partner_id = fields.Integer("Existing Partner ID", readonly=True, compute="_compute_existing_partner_id", store=True)
    is_new = fields.Boolean("New Pilot", compute="_compute_is_new", store=True)

    @api.depends('name', 'email', 'employee_id')
    def _compute_existing_partner_id(self):
        """Find existing partner based on name, email, or employee ID."""
        for line in self:
            # Skip if no identifying information
            if not line.name and not line.email and not line.employee_id:
                line.existing_partner_id = False
                continue
                
            # Find existing pilot
            partner = self.env["flight.import.helper"].find_pilot(
                name=line.name,
                email=line.email,
                barcode=line.employee_id
            )
            
            line.existing_partner_id = partner.id if partner else False

    @api.depends('existing_partner_id')
    def _compute_is_new(self):
        """Determine if this is a new pilot based on existing partner."""
        for line in self:
            line.is_new = not line.existing_partner_id

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
    
    def check_conflicts(self):
        """Check for conflicts with existing records.
        
        Implementation of the abstract method from flight.data.import.line.mixin.
        
        Returns:
            bool: True if there is a conflict, False otherwise
        """
        self.ensure_one()
        
        # Use the computed field to determine if there's a conflict
        return bool(self.existing_partner_id)
    
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
        # No need to set is_new as it's now a computed field
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
