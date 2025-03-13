# Copyright 2025 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).

import re
from odoo import _, api, fields, models
import logging

_logger = logging.getLogger(__name__)

class FlightDataImportCrewLoungeAircraftLine(models.TransientModel):
    """Aircraft import line for CrewLounge CSV imports."""

    _name = "flight.data.import.crewlounge.aircraft.line"
    _description = "Aircraft Import Line"
    _inherit = ["flight.data.import.line.mixin"]

    # Relation to parent import wizard
    import_id = fields.Many2one(
        "flight.data.import.crewlounge.aircraft",
        string="Import",
        required=True,
        ondelete="cascade",
    )
    
    # Raw fields from CSV
    dev = fields.Char(string="DEV", help="Equipment type from CSV")
    reference = fields.Char(string="Registration", help="Aircraft registration from CSV")
    ac = fields.Char(string="AC", help="Aircraft model code from CSV")
    cat = fields.Char(string="CAT", help="Aircraft category from CSV")
    company_name = fields.Char(string="Company", help="Operator company name from CSV")
    pw = fields.Char(string="PW", help="Engine type from CSV")
    wt = fields.Char(string="WT", help="Weight from CSV")
    
    # Conflict detection
    aircraft_id = fields.Many2one("flight.aircraft", string="Existing Aircraft", compute="_compute_aircraft_id", store=True)
    is_new = fields.Boolean(string="Is New", compute="_compute_is_new", store=True)
    
    @api.depends("reference")
    def _compute_aircraft_id(self):
        """Find existing aircraft by registration."""
        for line in self:
            if line.reference:
                # Sanitize registration
                registration = self._sanitize_registration(line.reference)
                
                # Find existing aircraft - use exact match as per the constraint
                aircraft = self.env["flight.aircraft"].search([
                    ("registration", "=", registration),
                ], limit=1)
                
                line.aircraft_id = aircraft.id if aircraft else False
            else:
                line.aircraft_id = False
    
    @api.depends("aircraft_id")
    def _compute_is_new(self):
        """Determine if this is a new aircraft."""
        for line in self:
            line.is_new = not line.aircraft_id
    
    def validate(self):
        """Validate the import line.
        
        Returns:
            bool: True if valid, False otherwise
        """
        self.ensure_one()
        
        if not self.reference:
            self.mark_as_invalid(_("Aircraft registration is required"))
            return False
            
        # Check for existing aircraft
        if self.aircraft_id and not self.import_id.update_existing:
            self.mark_as_conflict(_("Aircraft with this registration already exists"))
            return False
            
        self.mark_as_valid()
        return True
    
    def prepare_import_values(self):
        """Prepare values for aircraft import.
        
        Returns:
            dict: Values for aircraft creation/update
        """
        self.ensure_one()
        
        # Find or create company
        company_id = False
        if self.company_name:
            # Find existing company
            company = self.env["res.partner"].search([
                ("name", "=ilike", self.company_name),
                ("is_company", "=", True),
            ], limit=1)
            
            if not company and self.company_name != "PRIVATE" and self.company_name != "Other":
                # Create new company if not found
                company = self.env["res.partner"].create({
                    "name": self.company_name,
                    "is_company": True,
                })
            
            if company:
                company_id = company.id
        
        # Find or create tags for CAT (Multi Pilot/Single Pilot)
        tag_ids = []
        if self.cat:
            cat_value = self.cat.strip()
            cat_mapping = self._get_cat_tag_mapping()
            
            if cat_value in cat_mapping:
                tag_name = cat_mapping[cat_value]
                
                # Find existing tag
                tag = self.env["flight.aircraft.model.tag"].search([
                    ("name", "=", tag_name)
                ], limit=1)
                
                if not tag:
                    # Create new tag if not found
                    tag = self.env["flight.aircraft.model.tag"].create({
                        "name": tag_name
                    })
                
                if tag:
                    tag_ids.append(tag.id)
        
        # Prepare model
        model_id = False
        make_id = False
        if self.ac:
            # Parse model code to get clean value
            model_code = self._parse_model_code(self.ac)
            make_name = self._get_make_from_model(self.ac)
            if make_name:
                make = self.env["flight.aircraft.make"].search([
                    ("name", "=", make_name)
                ], limit=1)
                if not make:
                    make = self.env["flight.aircraft.make"].create({
                        "name": make_name
                    })
                
                make_id = make.id
            
            model_vals = {
                "name": model_code,
                "code": model_code,
                "make_id": make_id,
                "engine_type": self._map_engine_type(self.pw),
            }
            # Find existing model
            model = self.env["flight.aircraft.model"].search([
                ("code", "=", model_code)
            ], limit=1)
            
            if not model:
                # Create new model if not found
                model = self.env["flight.aircraft.model"].create(model_vals)
            elif tag_ids:
                # Update existing model with tags
                model.write({
                    "tag_ids": [(4, tag_id) for tag_id in tag_ids]
                })
            
            if model:
                model_id = model.id
        
        # Prepare values for aircraft creation/update
        values = {
            "registration": self._sanitize_registration(self.reference),
            "equipment_type": self._map_equipment_type(self.dev),
        }
        
        # Add related records if available
        if company_id:
            values["operator_id"] = company_id
        if model_id:
            values["model_id"] = model_id
        
        return values
    
    def mark_as_imported(self):
        """Mark the line as imported."""
        self.ensure_one()
        self.write({
            "state": "imported",
        })
    
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
    
    def _get_equipment_type_mapping(self):
        """Get mapping dictionary for equipment types."""
        return {
            "Aircraft": "aircraft",
            "Simulator": "ffs",
            "Drone": "aircraft",
        }
    
    def _get_engine_type_mapping(self):
        """Get mapping dictionary for engine types."""
        return {
            "SE - Piston": "piston",
            "ME - Piston": "piston",
            "ME - Turbine (jet-fan)": "turbofan",
            "ME - Turbine (prop-shaft)": "turboprop",
            " - Unpowered": "non_powered",
        }
    
    def _get_cat_tag_mapping(self):
        """Get mapping dictionary for CAT field to tag names."""
        return {
            "Multi Pilot": "multi-pilot",
            "Single Pilot": "single-pilot",
        }
    
    def _map_equipment_type(self, dev_value):
        """Map equipment type from DEV field.
        
        Args:
            dev_value (str): DEV field value
            
        Returns:
            str: Mapped equipment type
        """
        if not dev_value:
            return "aircraft"  # Default
            
        # Get the mapping dictionary
        mapping = self._get_equipment_type_mapping()
        
        # Try to get the mapped value, default to "aircraft" if not found
        return mapping.get(dev_value, "aircraft")
    
    def _map_engine_type(self, pw_value):
        """Map engine type from PW field.
        
        Args:
            pw_value (str): PW field value
            
        Returns:
            str: Mapped engine type
        """
        if not pw_value:
            return "piston"  # Default
            
        # Get the mapping dictionary
        mapping = self._get_engine_type_mapping()
        
        # Try exact match first
        pw_value = pw_value.strip()
        if pw_value in mapping:
            return mapping[pw_value]
            
        # If no exact match, try partial match
        for key, value in mapping.items():
            if key in pw_value:
                return value
                
        return "piston"  # Default
    
    def _is_multi_pilot(self, cat_value):
        """Determine if aircraft is multi-pilot based on CAT field.
        
        Args:
            cat_value (str): CAT field value
            
        Returns:
            bool: True if multi-pilot, False otherwise
        """
        if not cat_value:
            return False
            
        # Direct check for "Multi Pilot" value
        return cat_value.strip() == "Multi Pilot"
    
    def _is_multi_engine(self, pw_value):
        """Determine if aircraft is multi-engine based on PW field.
        
        Args:
            pw_value (str): PW field value
            
        Returns:
            bool: True if multi-engine, False otherwise
        """
        if not pw_value:
            return False
            
        # Direct check for ME prefix
        return pw_value.strip().startswith("ME")
    
    def _parse_model_code(self, ac_value):
        """Clean and parse model code from AC field.
        
        Args:
            ac_value (str): AC field value
            
        Returns:
            str: Cleaned model code
        """
        if not ac_value:
            return ""
            
        # The AC field in the CSV has format like "C150 - " or "A320 - 200"
        # We need to extract just the model code part
        
        # First remove any trailing spaces
        cleaned = ac_value.strip()
        
        # If there's a dash with spaces around it, handle it properly
        if " - " in cleaned:
            parts = cleaned.split(" - ")
            base_model = parts[0].strip()
            
            # If there's a second part with content, keep the original format
            if len(parts) > 1 and parts[1].strip():
                model_code = cleaned  # Keep as "A320 - 200"
            else:
                model_code = base_model  # Just "C172" without the dash
        else:
            model_code = cleaned
            
        return model_code
    

    def _get_make_from_model(self, model_str):
        """Identify aircraft manufacturer from model string using pattern matching.
        
        Args:
            model_str (str): The aircraft model string to analyze
            
        Returns:
            str: The identified manufacturer name or "Unknown"
        """
        if not model_str or not isinstance(model_str, str):
            return False
            
        # Clean and normalize the model string
        model = model_str.strip().upper()
        
        # First try exact prefix match (faster)
        prefix = model.split(' ')[0] if ' ' in model else model
        manufacturer = self._match_prefix(prefix)
        if manufacturer:
            return manufacturer
                
        # Then try regex pattern matching (more comprehensive)
        manufacturer = self._match_pattern(model)
        if manufacturer:
            return manufacturer
                
        # If no match is found, return a generic manufacturer
        return False
    
    def _match_prefix(self, prefix):
        """Match a model prefix against known manufacturer prefixes.
        
        Args:
            prefix (str): The prefix to match
            
        Returns:
            str: The manufacturer name or False if no match
        """
        common_prefixes = {
            'A': 'Airbus',
            'B': 'Boeing',
            'C': 'Cessna',
            'P': 'Piper',
            'PA': 'Piper',
            'BE': 'Beechcraft',
            'CE': 'Cessna',
            'F': 'Fokker',
            'G': 'Gulfstream',
            'SR': 'Cirrus',
            'ATR': 'ATR',
            'E': 'Embraer',
            'CRJ': 'Bombardier',
            'CL': 'Bombardier',
            'DHC': 'De Havilland Canada',
            'DO': 'Dornier',
            'PC': 'Pilatus',
            'LJ': 'Learjet',
            'DA': 'Diamond Aircraft',
            'TB': 'Socata',
            'BN': 'Britten-Norman',
            'YAK': 'Yakovlev',
            'Z': 'Zlin',
            'MD': 'McDonnell Douglas',
            'DC': 'Douglas',
            'M': 'Mooney',
        }
        
        for key, value in common_prefixes.items():
            if prefix.startswith(key):
                return value
                
        return False
    
    def _match_pattern(self, model):
        """Match a model string against known manufacturer patterns.
        
        Args:
            model (str): The model string to match
            
        Returns:
            str: The manufacturer name or False if no match
        """
        import re
        
        # Common manufacturer patterns
        manufacturer_patterns = [
            # Format: (pattern, manufacturer_name)
            (r'^A[0-9]{1,3}', 'Airbus'),  # A320, A321, A330, etc.
            (r'^B[0-9]{1,3}', 'Boeing'),  # B737, B747, B777, etc.
            (r'^C[0-9]{1,3}', 'Cessna'),  # C150, C172, C182, etc.
            (r'^PA[0-9]{1,2}', 'Piper'),  # PA28, PA34, etc.
            (r'^P[0-9]{1,2}[A-Z]', 'Piper'),  # P28A, P32R, etc.
            (r'^BE[0-9]{1,3}', 'Beechcraft'),  # BE76, BE20, etc.
            (r'^CE[0-9]{1,3}', 'Cessna'),  # CE550, CE560, etc.
            (r'^ATR[0-9]{1,2}', 'ATR'),  # ATR42, ATR72, etc.
            (r'^F[0-9]{1,3}', 'Fokker'),  # F100, F50, etc.
            (r'^G[0-9]{1,3}', 'Gulfstream'),  # G450, G550, G650, etc.
            (r'^SR[0-9]{1,2}', 'Cirrus'),  # SR20, SR22, etc.
            (r'^E[0-9]{1,3}', 'Embraer'),  # E170, E190, etc.
            (r'^ERJ[0-9]{1,3}', 'Embraer'),  # ERJ145, etc.
            (r'^CRJ[0-9]{1,3}', 'Bombardier'),  # CRJ200, CRJ700, etc.
            (r'^CL[0-9]{1,3}', 'Bombardier'),  # CL600, etc.
            (r'^DHC[0-9]{1,2}', 'De Havilland Canada'),  # DHC6, DHC8, etc.
            (r'^DO[0-9]{1,3}', 'Dornier'),  # DO228, DO328, etc.
            (r'^PC[0-9]{1,2}', 'Pilatus'),  # PC12, PC24, etc.
            (r'^LJ[0-9]{1,2}', 'Learjet'),  # LJ45, LJ60, etc.
            (r'^DA[0-9]{1,2}', 'Diamond Aircraft'),  # DA40, DA42, etc.
            (r'^TB[0-9]{1,2}', 'Socata'),  # TB20, TB21, etc.
            (r'^BN[0-9]{1,2}', 'Britten-Norman'),  # BN2, etc.
            (r'^YAK[0-9]{1,2}', 'Yakovlev'),  # YAK52, etc.
            (r'^Z[0-9]{1,3}', 'Zlin'),  # Z142, etc.
            (r'^MD[0-9]{1,2}', 'McDonnell Douglas'),  # MD80, MD11, etc.
            (r'^DC[0-9]{1,2}', 'Douglas'),  # DC9, DC10, etc.
            (r'^M20', 'Mooney'),  # M20J, etc.
            (r'^CESSNA', 'Cessna'),
            (r'^PIPER', 'Piper'),
            (r'^WARRIOR', 'Piper'),
            (r'^SIM', 'Simulator'),
            (r'^DRONE', 'Drone'),
        ]
        
        for pattern, manufacturer in manufacturer_patterns:
            if re.match(pattern, model):
                return manufacturer
                
        return False


    def action_import(self):
        """Import the aircraft data."""
        self.ensure_one()
        
        # Skip invalid lines
        if self.state == "invalid":
            return False
        
        # Skip conflicted lines if update_existing is False
        if self.state == "conflict" and not self.import_id.update_existing:
            return False
        
        try:
            # Get import values
            values = self.prepare_import_values()
            if not values:
                return False
            
            # Create or update aircraft
            if self.is_new:
                # Create new aircraft
                aircraft = self.env['flight.aircraft'].create(values)
            else:
                # Update existing aircraft
                aircraft = self.aircraft_id
                aircraft.write(values)
            
            # Mark as imported
            self.mark_as_imported()
            
            return aircraft.id
        except Exception as e:
            _logger.exception("Error importing aircraft: %s", self.reference)
            self.mark_as_invalid(str(e))
            return False