# Copyright 2024 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).

from odoo import api, fields, models


class PilotImportHelper(models.AbstractModel):
    """Helper model for pilot data import."""

    _name = "pilot.import.helper"
    _description = "Pilot Import Helper"

    @api.model
    def get_or_create_pilot(self, pilot_name, pilot_phone=False, pilot_email=False):
        """Get or create pilot by name, with optional phone and email."""
        if not pilot_name or pilot_name == "SELF":
            # Use the current user's partner as the pilot
            return self.env.user.partner_id
            
        # Search for existing pilot
        domain = [
            ("name", "=ilike", pilot_name),
            "|", ("company_id", "=", self.env.company.id), ("company_id", "=", False)
        ]
        
        pilot = self.env["res.partner"].search(domain, limit=1)
        
        if pilot:
            # Update phone and email if provided and not already set
            vals = {}
            if pilot_phone and not pilot.phone:
                vals['phone'] = pilot_phone
            if pilot_email and not pilot.email:
                vals['email'] = pilot_email
            
            if vals:
                pilot.write(vals)
            
            return pilot
            
        # Create new pilot
        return self.env["res.partner"].create({
            "name": pilot_name,
            "phone": pilot_phone if pilot_phone else False,
            "email": pilot_email if pilot_email else False,
            "company_id": self.env.company.id,
        })

    @api.model
    def create_pilot_time_entries(self, flight, pilot, time_data):
        """Create pilot time entries for a flight."""
        time_entries = []
        
        # Map time codes to values
        time_mapping = [
            ("pic", time_data.get("pic_time", 0.0)),
            ("sic", time_data.get("sic_time", 0.0)),
            ("dual", time_data.get("dual_time", 0.0)),
            ("instr", time_data.get("instructor_time", 0.0)),
            ("night", time_data.get("night_time", 0.0)),
            ("ifr", time_data.get("ifr_time", 0.0)),
        ]
        
        # Create time entries for each non-zero time value
        for code_name, duration in time_mapping:
            if duration > 0:
                # Get time code
                time_code = self.env["flight.pilot.time.code"].search([
                    ("code", "=", code_name)
                ], limit=1)
                
                if not time_code:
                    continue
                
                # Create time entry
                time_entry = self.env["flight.pilot.time"].create({
                    "flight_id": flight.id,
                    "partner_id": pilot.id,
                    "code_id": time_code.id,
                    "duration": duration,
                })
                
                time_entries.append(time_entry)
        
        return time_entries

    @api.model
    def create_pilot_events(self, flight, pilot, capacity=False):
        """Create pilot events for a flight based on capacity."""
        events = []
        
        # Determine event code based on capacity
        event_code_name = "TO_DAY"  # Default event code
        
        if capacity:
            # Map capacity to event code
            capacity_mapping = {
                "PIC": "TO_DAY",
                "SIC": "TO_DAY",
                "DUAL": "TO_DAY",
                "INSTRUCTOR": "TO_DAY",
                "EXAMINER": "TO_DAY",
                "OBSERVER": "TO_DAY",
            }
            
            if capacity.upper() in capacity_mapping:
                event_code_name = capacity_mapping[capacity.upper()]
        
        # Get event code
        event_code = self.env["flight.pilot.event.code"].search([
            ("code", "=", event_code_name)
        ], limit=1)
        
        if not event_code:
            return events
        
        # Create event
        event = self.env["flight.pilot.event"].create({
            "flight_id": flight.id,
            "partner_id": pilot.id,
            "event_code_id": event_code.id,
            "datetime": fields.Datetime.now(),
        })
        
        events.append(event)
        
        return events

    @api.model
    def create_pilot_remark(self, flight, pilot, remarks):
        """Create pilot remark for a flight."""
        if not remarks:
            return False
            
        # Check if flight.pilot.remark model exists
        if not self.env['ir.model'].search([('model', '=', 'flight.pilot.remark')]):
            return False
            
        return self.env["flight.pilot.remark"].create({
            "flight_id": flight.id,
            "partner_id": pilot.id,
            "remarks": remarks,
        })
        
    @api.model
    def process_pilot_data(self, flight, line):
        """Process all pilot data for a flight import line."""
        # Process pilot 1
        if line.pilot1_name:
            pilot1 = self.get_or_create_pilot(line.pilot1_name, line.pilot1_phone, line.pilot1_email)
            if pilot1:
                # Create time entries
                time_data = {
                    "pic_time": line.pic_time,
                    "dual_time": line.dual_time,
                    "instructor_time": line.instructor_time,
                    "night_time": line.night_time,
                    "ifr_time": line.ifr_time,
                }
                self.create_pilot_time_entries(flight, pilot1, time_data)
                
                # Create events
                self.create_pilot_events(flight, pilot1, line.capacity)
                
                # Create remarks
                if line.remarks:
                    self.create_pilot_remark(flight, pilot1, line.remarks)
        
        # Process pilot 2
        if line.pilot2_name:
            pilot2 = self.get_or_create_pilot(line.pilot2_name, line.pilot2_phone, line.pilot2_email)
            if pilot2:
                # Create time entries
                time_data = {
                    "sic_time": line.sic_time,
                    "night_time": line.night_time,
                    "ifr_time": line.ifr_time,
                }
                self.create_pilot_time_entries(flight, pilot2, time_data)
                
                # Create events
                self.create_pilot_events(flight, pilot2, "SIC")
        
        # Process pilot 3
        if line.pilot3_name:
            pilot3 = self.get_or_create_pilot(line.pilot3_name, line.pilot3_phone, line.pilot3_email)
            if pilot3:
                # Create events only
                self.create_pilot_events(flight, pilot3, "OBSERVER")
        
        # Process pilot 4
        if line.pilot4_name:
            pilot4 = self.get_or_create_pilot(line.pilot4_name, line.pilot4_phone, line.pilot4_email)
            if pilot4:
                # Create events only
                self.create_pilot_events(flight, pilot4, "OBSERVER")
                
        return True
