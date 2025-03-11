# Copyright 2024 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).
import base64
import csv
import io
import re
import logging
from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AircraftImport(models.TransientModel):
    """Wizard for importing aircraft from CSV"""
    _name = "flight.aircraft.import.wizard"
    _description = "Aircraft Import Wizard"
    _inherit = "flight.import.wizard.mixin"

    # Field mappings
    registration_field = fields.Char(string="Registration Field", default="Reference")
    model_field = fields.Char(string="Model Field", default="AC")
    operator_field = fields.Char(string="Operator Field", default="Company")
    equipment_type_field = fields.Char(string="Equipment Type Field", default="DEV")
    engine_type_field = fields.Char(string="Engine Type Field", default="PW")
    category_field = fields.Char(string="Category Field", default="CAT")
    
    # Import lines
    line_ids = fields.One2many(
        "flight.aircraft.import.line",
        "wizard_id",
        string="Import Lines",
    )
    
    # Equipment type mapping
    def _get_equipment_type_mapping(self):
        return {
            "1": "aircraft",  # Aircraft
            "2": "ffs",       # Simulator
            "3": "aircraft",  # Drone (no exact match, using aircraft)
        }
    
    # Engine type mapping
    def _get_engine_type_mapping(self):
        return {
            "SE - Piston": "piston",
            "ME - Piston": "piston",
            "ME - Turbine (jet-fan)": "turbofan",
            "ME - Turbine (prop-shaft)": "turboprop",
            " - Unpowered": "non_powered",
            "PW": False,  # Empty or unknown engine type
        }
    
    # Aircraft make mapping with pattern matching
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
        return "Unknown"
    
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
    
    def _get_model_number(self, model_str):
        """Extract model number from model string.
        
        Args:
            model_str (str): The aircraft model string to parse
            
        Returns:
            str: The extracted model number or the original string if parsing fails
            
        Examples:
            "B737 - 800" -> "737-800"
            "C172 - " -> "172"
        """
        if not model_str or not isinstance(model_str, str):
            return False
            
        # Clean the model string
        model = model_str.strip()
        
        # Default to the original string
        model_number = model
        
        # Parse model with format like "B737 - 800"
        if ' - ' in model:
            return self._parse_model_with_separator(model)
                
        return model_number
    
    def _parse_model_with_separator(self, model):
        """Parse a model string that contains a separator.
        
        Args:
            model (str): The model string with separator (e.g., "B737 - 800")
            
        Returns:
            str: The parsed model number
        """
        import re
        
        parts = model.split(' - ')
        prefix = parts[0].strip()
        suffix = parts[1].strip() if len(parts) > 1 else ''
        
        # Extract numeric part from prefix
        numeric_match = re.search(r'[0-9]+', prefix)
        if numeric_match:
            model_number = numeric_match.group(0)
            if suffix:
                model_number = f"{model_number}-{suffix}"
            return model_number
            
        # If no numeric part found, return the original string
        return model
    
    def _parse_model_name(self, model_str):
        """Parse model name to extract make and model
        """
        if not model_str:
            return False, False
            
        # Get make and model number using separate methods
        make = self._get_make_from_model(model_str)
        model_number = self._get_model_number(model_str)
        
        return make, model_number
    
    def action_parse_file(self):
        """Parse the uploaded CSV file and prepare preview data"""
        self.ensure_one()
        
        if not self.csv_file:
            raise UserError(_("Please upload a CSV file first."))
            
        # Clear existing import lines
        self.line_ids.unlink()
        
        # Reset statistics
        self.write({
            "state": "preview",
            "total_rows": 0,
            "valid_count": 0,
            "invalid_count": 0,
            "conflict_count": 0,
            "imported_count": 0,
            "skipped_count": 0,
        })
        
        # Parse CSV file
        csv_data = base64.b64decode(self.csv_file)
        csv_file = io.StringIO(csv_data.decode("utf-8"))
        
        # Log the CSV content for debugging
        _logger.info("CSV content: %s", csv_data.decode("utf-8"))
        _logger.info("Delimiter: %s", self.delimiter)
        
        reader = csv.DictReader(csv_file, delimiter=self.delimiter)
        
        # Log the headers for debugging
        _logger.info("CSV headers: %s", reader.fieldnames)
        _logger.info("Looking for registration field: %s", self.registration_field)
        _logger.info("Looking for model field: %s", self.model_field)
        
        # Check if required headers exist
        required_headers = [self.registration_field]
        for header in required_headers:
            if header not in reader.fieldnames:
                available_headers = ', '.join(reader.fieldnames) if reader.fieldnames else 'None'
                raise UserError(_(
                    'Required header "%s" not found in the CSV file.\n\n'
                    'Available headers: %s\n\n'
                    'You can adjust the field mapping in the wizard to match your CSV headers.'
                ) % (header, available_headers))
        
        # Process each row
        import_lines = []
        equipment_type_mapping = self._get_equipment_type_mapping()
        
        for row in reader:
            # Log the row for debugging
            _logger.info("Processing row: %s", row)
            
            # Extract data from CSV
            registration = row.get(self.registration_field, "").strip()
            model_str = row.get(self.model_field, "").strip()
            operator = row.get(self.operator_field, "").strip()
            equipment_type_code = row.get(self.equipment_type_field, "").strip()
            engine_type_str = row.get(self.engine_type_field, "").strip()
            category = row.get(self.category_field, "").strip()
            
            # Log extracted data for debugging
            _logger.info("Extracted data - Registration: %s, Model: %s", registration, model_str)
            
            # Skip empty registrations
            if not registration:
                _logger.warning("Skipping row with empty registration")
                continue
                
            # Map equipment type
            equipment_type = equipment_type_mapping.get(equipment_type_code, "aircraft")
            
            # Check for existing aircraft
            existing_aircraft = self.env["flight.aircraft"].search([
                ("registration", "=", registration)
            ], limit=1)
            
            # Determine status and message
            status = "valid"
            message = ""
            
            if existing_aircraft:
                status = "conflict"
                message = _("Aircraft with registration %s already exists.") % registration
            
            # Create import line
            import_line = {
                "registration": registration,
                "model": model_str,
                "operator": operator,
                "equipment_type": equipment_type,
                "engine_type": engine_type_str,
                "category": category,
                "status": status,
                "message": message,
                "aircraft_id": existing_aircraft.id if existing_aircraft else False,
                "to_import": status == "valid",  # Only set to_import to True for valid records
            }
            
            import_lines.append((0, 0, import_line))
            
        # Create import lines
        self.write({"line_ids": import_lines})
        
        # Update statistics
        total_rows = len(import_lines)
        valid_rows = len([line for line in self.line_ids if line.status == "valid"])
        invalid_rows = len([line for line in self.line_ids if line.status == "invalid"])
        conflict_rows = len([line for line in self.line_ids if line.status == "conflict"])
        
        self.write({
            "total_rows": total_rows,
            "valid_count": valid_rows,
            "invalid_count": invalid_rows,
            "conflict_count": conflict_rows,
        })
        
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
    
    def action_import(self):
        """Import the selected aircraft"""
        self.ensure_one()
        
        if self.state != "preview":
            raise UserError(_("Please preview the data before importing."))
            
        # Get lines to import
        lines_to_import = self.line_ids.filtered(lambda l: l.to_import)
        
        if not lines_to_import:
            raise UserError(_("No lines selected for import."))
            
        # Reset statistics
        self.write({
            "imported_count": 0,
            "skipped_count": 0,
        })
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        # Process each line
        for line in lines_to_import:
            result = self._process_import_line(line)
            
            if result == "created":
                created_count += 1
            elif result == "updated":
                updated_count += 1
            elif result == "skipped":
                skipped_count += 1
        
        # Update statistics
        self.write({
            "imported_count": created_count + updated_count,
            "skipped_count": skipped_count,
            "state": "import",
        })
        
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
    
    def _process_import_line(self, line):
        """Process a single import line"""
        # Skip invalid lines
        if line.status == "invalid":
            line.result = "skipped"
            return "skipped"
            
        # Get or create related records
        model_id = self._get_or_create_model(line)
        operator_id = self._get_or_create_operator(line)
        
        # Prepare aircraft values
        vals = {
            "registration": line.registration,
            "model_id": model_id,
            "operator_id": operator_id,
            "equipment_type": line.equipment_type,
        }
        
        # Create or update aircraft
        if line.aircraft_id:
            # Update existing aircraft
            line.aircraft_id.write(vals)
            line.result = "updated"
            return "updated"
        else:
            # Create new aircraft
            aircraft = self.env["flight.aircraft"].create(vals)
            line.aircraft_id = aircraft.id
            line.result = "created"
            return "created"
    
    def _get_or_create_model(self, line):
        """Get or create aircraft model"""
        if not line.model:
            return False
            
        # Get make and model number using separate methods
        make, model_number = self._parse_model_name(line.model)
        
        # Check for existing model
        model = self.env["flight.aircraft.model"].search([
            ("name", "=", model_number)
        ], limit=1)
        
        if model:
            return model.id
            
        # Create new model
        make_id = self._get_or_create_make(make) if make else False
        class_id = self._get_or_create_class(line) if line.category else False
        engine_type = self._map_engine_type(line.engine_type) if line.engine_type else False
        
        model_vals = {
            "name": model_number,
            "make_id": make_id,
            "class_id": class_id,
            "engine_type": engine_type,
        }
        
        # Remove False values to use model defaults
        model_vals = {k: v for k, v in model_vals.items() if v is not False}
        
        model = self.env["flight.aircraft.model"].create(model_vals)
        return model.id
    
    def _get_or_create_make(self, make):
        """Get or create aircraft make"""
        if not make:
            return False
            
        # Check for existing make
        make = self.env["flight.aircraft.make"].search([
            ("name", "=", make)
        ], limit=1)
        
        if make:
            return make.id
            
        # Create new make
        make = self.env["flight.aircraft.make"].create({"name": make})
        return make.id
    
    def _get_or_create_class(self, line):
        """Get or create aircraft class"""
        if not line.category:
            return False
            
        # Check for existing class
        aircraft_class = self.env["flight.aircraft.class"].search([
            ("name", "=", line.category)
        ], limit=1)
        
        if aircraft_class:
            return aircraft_class.id
            
        # Create new class
        aircraft_category = "airplane"  # Default to airplane
        
        class_vals = {
            "name": line.category,
            "aircraft_category": aircraft_category,
        }
        
        aircraft_class = self.env["flight.aircraft.class"].create(class_vals)
        return aircraft_class.id
    
    def _get_or_create_operator(self, line):
        """Get or create operator (res.partner)"""
        if not line.operator:
            return False
            
        # Check for existing partner
        partner = self.env["res.partner"].search([
            ("name", "=", line.operator)
        ], limit=1)
        
        if partner:
            return partner.id
            
        # Create new partner
        partner = self.env["res.partner"].create({
            "name": line.operator,
            "is_company": True,
        })
        
        return partner.id
    
    def _map_engine_type(self, engine_type_str):
        """Map engine type string to selection value"""
        engine_mapping = self._get_engine_type_mapping()
        return engine_mapping.get(engine_type_str, False)
