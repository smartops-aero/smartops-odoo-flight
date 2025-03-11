# Copyright 2024 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).
import base64
import csv
import io
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class FlightImport(models.TransientModel):
    """Wizard for importing flights from CSV file."""

    _name = "flight.import"
    _description = "Flight Import Wizard"
    _inherit = "flight.import.wizard.mixin"

    # Field mappings
    date_field = fields.Char("Date Field", default="PILOTLOG_DATE")
    flight_number_field = fields.Char("Flight Number Field", default="FLIGHTNUMBER")
    departure_field = fields.Char("Departure Field", default="AF_DEP")
    arrival_field = fields.Char("Arrival Field", default="AF_ARR")
    aircraft_reg_field = fields.Char("Aircraft Registration Field", default="AC_REG")
    aircraft_make_field = fields.Char("Aircraft Make Field", default="AC_MAKE")
    aircraft_model_field = fields.Char("Aircraft Model Field", default="AC_MODEL")
    remarks_field = fields.Char("Remarks Field", default="REMARKS")
    pilot1_field = fields.Char("Pilot 1 Field", default="PILOT1_NAME")
    pilot2_field = fields.Char("Pilot 2 Field", default="PILOT2_NAME")
    flight_time_field = fields.Char("Flight Time Field", default="TIME_TOTAL")
    is_simulator_field = fields.Char("Is Simulator Field", default="AC_ISSIM")
    
    # Import lines
    line_ids = fields.One2many("flight.import.line", "wizard_id", string="Import Lines")
    
    def action_preview(self):
        """Parse CSV file and prepare data for preview."""
        self.ensure_one()
        
        # Clear existing lines
        self.line_ids.unlink()
        
        if not self.csv_file:
            raise UserError(_("Please upload a CSV file."))
        
        # Read CSV file
        try:
            csv_data = base64.b64decode(self.csv_file)
            csv_file = io.StringIO(csv_data.decode("utf-8"))
            reader = csv.DictReader(csv_file, delimiter=self.delimiter)
            
            # Process each row
            for row in reader:
                self._create_import_line(row)
                
            # Validate lines
            self._validate_lines()
            
            # Update state
            self.state = "preview"
            
            return {
                "type": "ir.actions.act_window",
                "res_model": self._name,
                "res_id": self.id,
                "view_mode": "form",
                "target": "new",
            }
            
        except Exception as e:
            raise UserError(_("Error parsing CSV file: %s") % str(e))
    
    def _create_import_line(self, row):
        """Create import line from CSV row."""
        # Extract raw values
        raw_date = row.get(self.date_field, "")
        raw_flight_number = row.get(self.flight_number_field, "")
        raw_departure = row.get(self.departure_field, "")
        raw_arrival = row.get(self.arrival_field, "")
        raw_aircraft_reg = row.get(self.aircraft_reg_field, "")
        raw_aircraft_make = row.get(self.aircraft_make_field, "")
        raw_aircraft_model = row.get(self.aircraft_model_field, "")
        raw_remarks = row.get(self.remarks_field, "")
        raw_pilot1 = row.get(self.pilot1_field, "")
        raw_pilot2 = row.get(self.pilot2_field, "")
        raw_flight_time = row.get(self.flight_time_field, "")
        raw_is_simulator = row.get(self.is_simulator_field, "")
        
        # Process date
        date = False
        if raw_date:
            try:
                date = datetime.strptime(raw_date, "%d-%m-%Y").date()
            except ValueError:
                pass
        
        # Process flight time
        flight_time = 0.0
        if raw_flight_time:
            try:
                flight_time = float(raw_flight_time)
            except ValueError:
                pass
        
        # Process is_simulator
        is_simulator = False
        if raw_is_simulator and raw_is_simulator.upper() == "TRUE":
            is_simulator = True
        
        # Create line
        return self.env["flight.import.line"].create({
            "wizard_id": self.id,
            "raw_date": raw_date,
            "raw_flight_number": raw_flight_number,
            "raw_departure": raw_departure,
            "raw_arrival": raw_arrival,
            "raw_aircraft_reg": raw_aircraft_reg,
            "raw_aircraft_make": raw_aircraft_make,
            "raw_aircraft_model": raw_aircraft_model,
            "raw_remarks": raw_remarks,
            "raw_pilot1": raw_pilot1,
            "raw_pilot2": raw_pilot2,
            "raw_flight_time": raw_flight_time,
            "raw_is_simulator": raw_is_simulator,
            "date": date,
            "flight_number": raw_flight_number,
            "remarks": raw_remarks,
            "flight_time": flight_time,
            "is_simulator": is_simulator,
        })
    
    def _validate_lines(self):
        """Validate import lines and set appropriate states."""
        for line in self.line_ids:
            # Process aircraft
            if line.raw_aircraft_reg:
                aircraft = self._get_or_create_aircraft(line)
                if aircraft:
                    line.aircraft_id = aircraft.id
            
            # Process departure aerodrome
            if line.raw_departure:
                departure = self._get_or_create_aerodrome(line.raw_departure)
                if departure:
                    line.departure_id = departure.id
            
            # Process arrival aerodrome
            if line.raw_arrival:
                arrival = self._get_or_create_aerodrome(line.raw_arrival)
                if arrival:
                    line.arrival_id = arrival.id
            
            # Validate required fields
            errors = []
            if not line.date:
                errors.append(_("Invalid or missing date"))
            if not line.aircraft_id:
                errors.append(_("Invalid or missing aircraft"))
            if not line.departure_id:
                errors.append(_("Invalid or missing departure aerodrome"))
            if not line.arrival_id:
                errors.append(_("Invalid or missing arrival aerodrome"))
            
            # Set state based on validation
            if errors:
                line.status = "invalid"
                line.message = "\n".join(errors)
            else:
                # Check for existing flight
                existing = self.env["flight.flight"].search([
                    ("date", "=", line.date),
                    ("aircraft_id", "=", line.aircraft_id.id),
                    ("departure_id", "=", line.departure_id.id),
                    ("arrival_id", "=", line.arrival_id.id),
                ], limit=1)
                
                if existing:
                    line.status = "conflict"
                    line.message = _("Flight already exists")
                    line.to_import = False
                else:
                    line.status = "valid"
                    line.to_import = True
    
    def _get_or_create_aircraft(self, line):
        """Get or create aircraft based on import line data."""
        if not line.raw_aircraft_reg:
            return False
        
        # Search for existing aircraft
        aircraft = self.env["flight.aircraft"].search([
            ("registration", "=", line.raw_aircraft_reg)
        ], limit=1)
        
        if aircraft:
            return aircraft
        
        # Create new aircraft if not found
        model_id = self._get_or_create_model(line)
        
        return self.env["flight.aircraft"].create({
            "registration": line.raw_aircraft_reg,
            "model_id": model_id,
            "equipment_type": "aircraft" if not line.is_simulator else "ffs",
        })
    
    def _get_or_create_model(self, line):
        """Get or create aircraft model."""
        if not line.raw_aircraft_model:
            return False
            
        # Get make and model number using separate methods
        make = self._get_make_from_model(line.raw_aircraft_make, line.raw_aircraft_model)
        model_number = self._get_model_number(line.raw_aircraft_model)
        
        # Check for existing model
        model = self.env["flight.aircraft.model"].search([
            ("name", "=", model_number)
        ], limit=1)
        
        if model:
            return model.id
            
        # Create new model
        make_id = self._get_or_create_make(make) if make else False
        
        model_vals = {
            "name": model_number,
            "make_id": make_id,
        }
        
        # Remove False values to use model defaults
        model_vals = {k: v for k, v in model_vals.items() if v is not False}
        
        model = self.env["flight.aircraft.model"].create(model_vals)
        return model.id
    
    def _get_make_from_model(self, make_str, model_str):
        """Identify aircraft manufacturer from make or model string."""
        if make_str and isinstance(make_str, str) and make_str.strip():
            return make_str.strip()
            
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
        """Match a model prefix against known manufacturer prefixes."""
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
        """Match a model string against known manufacturer patterns."""
        import re
        
        # Common manufacturer patterns
        manufacturer_patterns = [
            # Format: (pattern, manufacturer_name)
            (r'^A[0-9]{1,3}', 'Airbus'),
            (r'^B[0-9]{1,3}', 'Boeing'),
            (r'^C[0-9]{1,3}', 'Cessna'),
            (r'^PA[0-9]{1,2}', 'Piper'),
            (r'^P[0-9]{1,2}[A-Z]', 'Piper'),
            (r'^BE[0-9]{1,3}', 'Beechcraft'),
            (r'^CE[0-9]{1,3}', 'Cessna'),
            (r'^ATR[0-9]{1,2}', 'ATR'),
            (r'^F[0-9]{1,3}', 'Fokker'),
            (r'^G[0-9]{1,3}', 'Gulfstream'),
            (r'^SR[0-9]{1,2}', 'Cirrus'),
            (r'^E[0-9]{1,3}', 'Embraer'),
            (r'^ERJ[0-9]{1,3}', 'Embraer'),
            (r'^CRJ[0-9]{1,3}', 'Bombardier'),
            (r'^CL[0-9]{1,3}', 'Bombardier'),
            (r'^DHC[0-9]{1,2}', 'De Havilland Canada'),
            (r'^DO[0-9]{1,3}', 'Dornier'),
            (r'^PC[0-9]{1,2}', 'Pilatus'),
            (r'^LJ[0-9]{1,2}', 'Learjet'),
            (r'^DA[0-9]{1,2}', 'Diamond Aircraft'),
            (r'^TB[0-9]{1,2}', 'Socata'),
            (r'^BN[0-9]{1,2}', 'Britten-Norman'),
            (r'^YAK[0-9]{1,2}', 'Yakovlev'),
            (r'^Z[0-9]{1,3}', 'Zlin'),
            (r'^MD[0-9]{1,2}', 'McDonnell Douglas'),
            (r'^DC[0-9]{1,2}', 'Douglas'),
            (r'^M20', 'Mooney'),
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
        """Extract model number from model string."""
        if not model_str or not isinstance(model_str, str):
            return model_str
            
        # Clean the model string
        model = model_str.strip()
        
        # Default to the original string
        return model
    
    def _get_or_create_make(self, make):
        """Get or create aircraft make."""
        if not make:
            return False
            
        # Search for existing make
        make_obj = self.env["flight.aircraft.make"].search([
            ("name", "=", make)
        ], limit=1)
        
        if make_obj:
            return make_obj.id
            
        # Create new make
        make_obj = self.env["flight.aircraft.make"].create({
            "name": make
        })
        
        return make_obj.id
    
    def _get_or_create_aerodrome(self, icao):
        """Get or create aerodrome by ICAO code."""
        if not icao:
            return False
            
        # Search for existing aerodrome
        aerodrome = self.env["flight.aerodrome"].search([
            ("icao", "=", icao)
        ], limit=1)
        
        if aerodrome:
            return aerodrome
            
        # Create new aerodrome
        return self.env["flight.aerodrome"].create({
            "name": icao,  # Use ICAO as name for now
            "icao": icao,
        })
    
    def action_import(self):
        """Import valid flights."""
        self.ensure_one()
        
        # Import only valid and selected lines
        valid_lines = self.line_ids.filtered(lambda l: l.status == "valid" and l.to_import)
        
        for line in valid_lines:
            # Create flight
            flight = self.env["flight.flight"].create({
                "date": line.date,
                "aircraft_id": line.aircraft_id.id,
                "departure_id": line.departure_id.id,
                "arrival_id": line.arrival_id.id,
            })
            
            # Update line state
            line.write({
                "result": "created",
            })
        
        # Update skipped lines
        skipped_lines = self.line_ids.filtered(lambda l: l.status == "valid" and not l.to_import)
        skipped_lines.write({"result": "skipped"})
        
        # Update wizard state
        self.state = "import"
        
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
