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
    _inherit = ["flight.import.wizard.mixin", "pilot.import.helper"]

    # Field mappings
    date_field = fields.Char("Date Field", default="PILOTLOG_DATE")
    flight_number_field = fields.Char("Flight Number Field", default="FLIGHTNUMBER")
    departure_field = fields.Char("Departure Field", default="AF_DEP")
    arrival_field = fields.Char("Arrival Field", default="AF_ARR")
    aircraft_reg_field = fields.Char("Aircraft Registration Field", default="AC_REG")
    aircraft_make_field = fields.Char("Aircraft Make Field", default="AC_MAKE")
    aircraft_model_field = fields.Char("Aircraft Model Field", default="AC_MODEL")
    remarks_field = fields.Char("Remarks Field", default="REMARKS")
    flight_time_field = fields.Char("Flight Time Field", default="TIME_TOTAL")
    is_simulator_field = fields.Char("Is Simulator Field", default="AC_ISSIM")
    
    # Additional pilot time fields
    pic_time_field = fields.Char("PIC Time Field", default="TIME_PIC")
    sic_time_field = fields.Char("SIC Time Field", default="TIME_SIC")
    dual_time_field = fields.Char("Dual Time Field", default="TIME_DUAL")
    instructor_time_field = fields.Char("Instructor Time Field", default="TIME_INSTRUCTOR")
    night_time_field = fields.Char("Night Time Field", default="TIME_NIGHT")
    ifr_time_field = fields.Char("IFR Time Field", default="TIME_IFR")
    capacity_field = fields.Char("Pilot Capacity Field", default="CAPACITY")
    
    # Pilot 1 fields
    pilot1_id_field = fields.Char("Pilot 1 ID Field", default="PILOT1_ID")
    pilot1_name_field = fields.Char("Pilot 1 Name Field", default="PILOT1_NAME")
    pilot1_phone_field = fields.Char("Pilot 1 Phone Field", default="PILOT1_PHONE")
    pilot1_email_field = fields.Char("Pilot 1 Email Field", default="PILOT1_EMAIL")
    
    # Pilot 2 fields
    pilot2_id_field = fields.Char("Pilot 2 ID Field", default="PILOT2_ID")
    pilot2_name_field = fields.Char("Pilot 2 Name Field", default="PILOT2_NAME")
    pilot2_phone_field = fields.Char("Pilot 2 Phone Field", default="PILOT2_PHONE")
    pilot2_email_field = fields.Char("Pilot 2 Email Field", default="PILOT2_EMAIL")
    
    # Pilot 3 fields
    pilot3_id_field = fields.Char("Pilot 3 ID Field", default="PILOT3_ID")
    pilot3_name_field = fields.Char("Pilot 3 Name Field", default="PILOT3_NAME")
    pilot3_phone_field = fields.Char("Pilot 3 Phone Field", default="PILOT3_PHONE")
    pilot3_email_field = fields.Char("Pilot 3 Email Field", default="PILOT3_EMAIL")
    
    # Pilot 4 fields
    pilot4_id_field = fields.Char("Pilot 4 ID Field", default="PILOT4_ID")
    pilot4_name_field = fields.Char("Pilot 4 Name Field", default="PILOT4_NAME")
    pilot4_phone_field = fields.Char("Pilot 4 Phone Field", default="PILOT4_PHONE")
    pilot4_email_field = fields.Char("Pilot 4 Email Field", default="PILOT4_EMAIL")
    
    # Import lines
    line_ids = fields.One2many("flight.import.line", "wizard_id", string="Import Lines")
    
    def action_preview(self):
        """Parse CSV file and prepare data for preview."""
        self.ensure_one()
        
        # Check if file is uploaded
        if not self.csv_file:
            raise UserError(_("Please upload a CSV file."))
            
        # Clear existing lines
        self.line_ids.unlink()
        
        # Parse CSV file
        try:
            # Decode file content
            csv_data = base64.b64decode(self.csv_file)
            csv_file = io.StringIO(csv_data.decode("utf-8"))
            reader = csv.DictReader(csv_file, delimiter=self.delimiter)
            
            # Create import lines
            for row in reader:
                self._create_import_line(row)
                
            # Validate lines
            self._validate_lines()
            
            # Update state
            self.state = "preview"
            
            # Return view
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
        raw_flight_time = row.get(self.flight_time_field, "")
        raw_is_simulator = row.get(self.is_simulator_field, "")
        
        # Extract pilot time data
        raw_pic_time = row.get(self.pic_time_field, "")
        raw_sic_time = row.get(self.sic_time_field, "")
        raw_dual_time = row.get(self.dual_time_field, "")
        raw_instructor_time = row.get(self.instructor_time_field, "")
        raw_night_time = row.get(self.night_time_field, "")
        raw_ifr_time = row.get(self.ifr_time_field, "")
        raw_capacity = row.get(self.capacity_field, "")
        
        # Extract pilot data
        # Pilot 1
        raw_pilot1_id = row.get(self.pilot1_id_field, "")
        raw_pilot1_name = row.get(self.pilot1_name_field, "")
        raw_pilot1_phone = row.get(self.pilot1_phone_field, "")
        raw_pilot1_email = row.get(self.pilot1_email_field, "")
        
        # Pilot 2
        raw_pilot2_id = row.get(self.pilot2_id_field, "")
        raw_pilot2_name = row.get(self.pilot2_name_field, "")
        raw_pilot2_phone = row.get(self.pilot2_phone_field, "")
        raw_pilot2_email = row.get(self.pilot2_email_field, "")
        
        # Pilot 3
        raw_pilot3_id = row.get(self.pilot3_id_field, "")
        raw_pilot3_name = row.get(self.pilot3_name_field, "")
        raw_pilot3_phone = row.get(self.pilot3_phone_field, "")
        raw_pilot3_email = row.get(self.pilot3_email_field, "")
        
        # Pilot 4
        raw_pilot4_id = row.get(self.pilot4_id_field, "")
        raw_pilot4_name = row.get(self.pilot4_name_field, "")
        raw_pilot4_phone = row.get(self.pilot4_phone_field, "")
        raw_pilot4_email = row.get(self.pilot4_email_field, "")
        
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
        
        # Process pilot times
        pic_time = 0.0
        if raw_pic_time:
            try:
                pic_time = float(raw_pic_time)
            except ValueError:
                pass
                
        sic_time = 0.0
        if raw_sic_time:
            try:
                sic_time = float(raw_sic_time)
            except ValueError:
                pass
                
        dual_time = 0.0
        if raw_dual_time:
            try:
                dual_time = float(raw_dual_time)
            except ValueError:
                pass
                
        instructor_time = 0.0
        if raw_instructor_time:
            try:
                instructor_time = float(raw_instructor_time)
            except ValueError:
                pass
                
        night_time = 0.0
        if raw_night_time:
            try:
                night_time = float(raw_night_time)
            except ValueError:
                pass
                
        ifr_time = 0.0
        if raw_ifr_time:
            try:
                ifr_time = float(raw_ifr_time)
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
            "raw_flight_time": raw_flight_time,
            "raw_is_simulator": raw_is_simulator,
            "raw_pic_time": raw_pic_time,
            "raw_sic_time": raw_sic_time,
            "raw_dual_time": raw_dual_time,
            "raw_instructor_time": raw_instructor_time,
            "raw_night_time": raw_night_time,
            "raw_ifr_time": raw_ifr_time,
            "raw_capacity": raw_capacity,
            "date": date,
            "flight_number": raw_flight_number,
            "remarks": raw_remarks,
            "flight_time": flight_time,
            "is_simulator": is_simulator,
            "pic_time": pic_time,
            "sic_time": sic_time,
            "dual_time": dual_time,
            "instructor_time": instructor_time,
            "night_time": night_time,
            "ifr_time": ifr_time,
            "capacity": raw_capacity,
            "pilot1_id": raw_pilot1_id,
            "pilot1_name": raw_pilot1_name,
            "pilot1_phone": raw_pilot1_phone,
            "pilot1_email": raw_pilot1_email,
            "pilot2_id": raw_pilot2_id,
            "pilot2_name": raw_pilot2_name,
            "pilot2_phone": raw_pilot2_phone,
            "pilot2_email": raw_pilot2_email,
            "pilot3_id": raw_pilot3_id,
            "pilot3_name": raw_pilot3_name,
            "pilot3_phone": raw_pilot3_phone,
            "pilot3_email": raw_pilot3_email,
            "pilot4_id": raw_pilot4_id,
            "pilot4_name": raw_pilot4_name,
            "pilot4_phone": raw_pilot4_phone,
            "pilot4_email": raw_pilot4_email,
        })
    
    def _validate_lines(self):
        """Validate import lines."""
        for line in self.line_ids:
            errors = []
            
            # Validate date
            if not line.date:
                errors.append(_("Invalid date format"))
            
            # Validate flight number
            if not line.flight_number:
                errors.append(_("Flight number is required"))
            
            # Validate departure and arrival
            if not line.raw_departure:
                errors.append(_("Departure is required"))
            
            if not line.raw_arrival:
                errors.append(_("Arrival is required"))
            
            # Validate aircraft
            if not line.raw_aircraft_reg:
                errors.append(_("Aircraft registration is required"))
            
            # Validate flight time
            if line.flight_time <= 0:
                errors.append(_("Flight time must be positive"))
            
            # Validate pilot data
            if not line.pilot1_name and not line.pilot2_name:
                errors.append(_("At least one pilot is required"))
            
            # Validate pilot time entries
            total_pilot_time = line.pic_time + line.sic_time + line.dual_time + line.instructor_time
            if total_pilot_time <= 0:
                errors.append(_("At least one pilot time entry is required"))
            
            # Set state based on validation
            if errors:
                line.state = "invalid"
                line.error = "\n".join(errors)
            else:
                # Check for existing flight
                existing = self.env["flight.flight"].search([
                    ("date", "=", line.date),
                    ("number", "=", line.flight_number),
                    ("is_simulator", "=", line.is_simulator),
                ], limit=1)
                
                if existing:
                    line.state = "conflict"
                    line.error = _("Flight already exists")
                else:
                    line.state = "valid"
    
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
    
    def _get_or_create_aerodrome(self, code):
        """Get or create aerodrome by code."""
        if not code:
            return False
            
        # Search for existing aerodrome
        aerodrome = self.env["flight.aerodrome"].search([
            ("code", "=ilike", code),
            "|", ("company_id", "=", self.env.company.id), ("company_id", "=", False)
        ], limit=1)
        
        if aerodrome:
            return aerodrome
            
        # Create new aerodrome
        return self.env["flight.aerodrome"].create({
            "code": code.upper(),
            "name": code.upper(),
            "company_id": self.env.company.id,
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
    
    def action_import(self):
        """Import valid lines."""
        # Check if there are valid lines
        valid_lines = self.line_ids.filtered(lambda l: l.state == "valid")
        if not valid_lines:
            raise UserError(_("No valid lines to import."))
        
        # Import lines
        imported_count = 0
        error_count = 0
        
        for line in valid_lines:
            try:
                # Get or create aircraft
                aircraft = self._get_or_create_aircraft(line)
                
                # Get or create departure and arrival aerodromes
                departure = self._get_or_create_aerodrome(line.raw_departure)
                arrival = self._get_or_create_aerodrome(line.raw_arrival)
                
                # Create flight
                flight = self.env["flight.flight"].create({
                    "date": line.date,
                    "number": line.flight_number,
                    "departure_id": departure.id,
                    "arrival_id": arrival.id,
                    "aircraft_id": aircraft.id,
                    "duration": line.flight_time,
                    "is_simulator": line.is_simulator,
                    "remarks": line.remarks,
                })
                
                # Process pilot data
                self.process_pilot_data(flight, line)
                
                # Update line
                line.write({
                    "state": "imported",
                    "flight_id": flight.id,
                })
                
                imported_count += 1
            except Exception as e:
                # Update line with error
                line.write({
                    "state": "invalid",
                    "error": str(e),
                })
                error_count += 1
        
        # Show result message
        message = _("Import completed: %s flights imported, %s errors.") % (
            imported_count,
            error_count,
        )
        
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Import Result"),
                "message": message,
                "sticky": False,
                "type": "success" if error_count == 0 else "warning",
            },
        }
