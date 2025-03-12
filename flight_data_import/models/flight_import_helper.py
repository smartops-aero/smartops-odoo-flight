# Copyright 2025 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).

from odoo import api, models


class FlightImportHelper(models.AbstractModel):
    """Helper model for flight.flight data imports.
    
    This model provides common functionality for flight.flight data imports,
    """
    _name = "flight.import.helper"
    _description = "Flight Import Helper"

    @api.model
    def _import_speeddict(self):
        """Pre-fetch commonly used data to improve import performance."""
        speeddict = {
            "aircraft": {},
            "pilots": {},
            "aerodromes": {},
        }
        # Pre-fetch aircraft by registration
        aircraft = self.env["flight.aircraft"].search_read(
            [], ["name", "id", "registration"]
        )
        for ac in aircraft:
            if ac.get("registration"):
                speeddict["aircraft"][ac["registration"]] = ac["id"]
            if ac.get("name"):
                speeddict["aircraft"][ac["name"]] = ac["id"]

        # Pre-fetch aerodromes by ICAO and IATA codes
        aerodromes = self.env["flight.aerodrome"].search_read(
            [], ["name", "id", "code", "icao_code", "iata_code"]
        )
        for ad in aerodromes:
            if ad.get("code"):
                speeddict["aerodromes"][ad["code"]] = ad["id"]
            if ad.get("icao_code"):
                speeddict["aerodromes"][ad["icao_code"]] = ad["id"]
            if ad.get("iata_code"):
                speeddict["aerodromes"][ad["iata_code"]] = ad["id"]
            if ad.get("name"):
                speeddict["aerodromes"][ad["name"]] = ad["id"]

        # First, get pilots from flight crew records
        pilot_partners = self.env["flight.crew"].search([]).mapped("partner_id")
        
        # Then, get a reasonable number of additional partners that might be pilots
        # This is a heuristic approach - we look for partners that might be individuals
        additional_partners = self.env["res.partner"].search([
            ("is_company", "=", False),
            ("id", "not in", pilot_partners.ids if pilot_partners else [0]),
        ], limit=1000)  # Limit to avoid performance issues
        
        # Combine both sets of partners
        all_potential_pilots = pilot_partners + additional_partners
        
        if all_potential_pilots:
            pilots = self.env["res.partner"].search_read(
                [("id", "in", all_potential_pilots.ids)], 
                ["name", "id", "email"]
            )
            for pilot in pilots:
                if pilot.get("email"):
                    speeddict["pilots"][pilot["email"]] = pilot["id"]
                # Don't index by name as it's not reliable for matching
        
        return speeddict

    @api.model
    def _import_update_hook(self, record_vals, speeddict, record_type="flight"):
        """Hook for extending the import process.
        
        This method is designed to be inherited by specific import modules to
        customize the import process for different record types.
        
        Args:
            record_vals (dict): Values for creating/updating a record
            speeddict (dict): Dictionary with pre-fetched data
            record_type (str): Type of record being imported (flight, aircraft, pilot)
            
        Returns:
            dict: Updated record values
        """
        if record_type == "flight":
            return self._flight_import_update_hook(record_vals, speeddict)
        elif record_type == "aircraft":
            return self._aircraft_import_update_hook(record_vals, speeddict)
        elif record_type == "pilot":
            return self._pilot_import_update_hook(record_vals, speeddict)
        return record_vals

    @api.model
    def _flight_import_update_hook(self, flight_vals, speeddict):
        """Hook for extending the flight import process."""
        # Match aircraft by registration
        if flight_vals.get("aircraft_reg"):
            aircraft_reg = flight_vals["aircraft_reg"].upper()
            if aircraft_reg in speeddict["aircraft"]:
                flight_vals["aircraft_id"] = speeddict["aircraft"][aircraft_reg]
        
        # Match departure and arrival aerodromes
        if flight_vals.get("departure_code"):
            dep_code = flight_vals["departure_code"].upper()
            if dep_code in speeddict["aerodromes"]:
                flight_vals["departure_id"] = speeddict["aerodromes"][dep_code]
                
        if flight_vals.get("arrival_code"):
            arr_code = flight_vals["arrival_code"].upper()
            if arr_code in speeddict["aerodromes"]:
                flight_vals["arrival_id"] = speeddict["aerodromes"][arr_code]
        
        return flight_vals

    @api.model
    def _aircraft_import_update_hook(self, aircraft_vals, speeddict):
        """Hook for extending the aircraft import process."""
        # Add any aircraft-specific import logic here
        return aircraft_vals

    @api.model
    def _pilot_import_update_hook(self, pilot_vals, speeddict):
        """Hook for extending the pilot import process."""
        # Add any pilot-specific import logic here
        return pilot_vals

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
    
    @api.model
    def find_or_create_aircraft(self, vals, update_if_exists=True):
        """Find or create an aircraft record.
        
        This method looks for an existing aircraft by registration.
        If found and update_if_exists is True, it updates the record.
        Otherwise, it creates a new aircraft record.
        
        Args:
            vals (dict): Values for creating/updating an aircraft
            update_if_exists (bool): Whether to update existing records
            
        Returns:
            int: ID of the aircraft record
        """
        Aircraft = self.env["flight.aircraft"]
        
        # Try to find by registration
        if vals.get("registration"):
            aircraft = Aircraft.search([
                ("registration", "=ilike", vals["registration"])
            ], limit=1)
            
            if aircraft:
                if update_if_exists:
                    aircraft.write(vals)
                return aircraft.id
        
        # Create new aircraft
        return Aircraft.create(vals).id
    
    @api.model
    def find_or_create_pilot(self, pilot_vals, speeddict=None, update_existing=True):
        """Find or create a pilot.
        
        Args:
            pilot_vals (dict): Pilot values
            speeddict (dict, optional): Pre-fetched data for faster lookups
            update_existing (bool, optional): Whether to update existing records
            
        Returns:
            int: Pilot ID
        """
        if not pilot_vals:
            return False
            
        # Try to find pilot in speeddict by email
        if speeddict and speeddict.get("pilots") and pilot_vals.get("email"):
            if pilot_vals["email"] in speeddict["pilots"]:
                return speeddict["pilots"][pilot_vals["email"]]
        
        # Try to find pilot by email only
        domain = []
        if pilot_vals.get("email"):
            domain = [("email", "=", pilot_vals["email"])]
            
        if domain:
            pilot = self.env["res.partner"].search(domain, limit=1)
            if pilot:
                # Update existing pilot if requested
                if update_existing:
                    pilot.write(pilot_vals)
                return pilot.id
        
        # Create new pilot
        return self.env["res.partner"].create(pilot_vals).id
