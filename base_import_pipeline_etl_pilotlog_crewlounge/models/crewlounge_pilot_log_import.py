from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CrewLoungePilotLogImport(models.Model):
    _name = "crewlounge.pilot.log.import"
    _inherit = "base.import.pipeline.etl"
    _description = "CrewLounge Pilot Log Import"
    
    @api.model
    def _get_available_implementations(self):
        """Add pilotlog_crewlounge implementation to available implementations"""
        implementations = super()._get_available_implementations()
        implementations.append(('pilotlog_crewlounge', 'CrewLounge Pilot Log'))
        return implementations
    
    def pilotlog_crewlounge_extract(self, file_content, filename=None):
        """Extract data from CrewLounge Pilot Log CSV file"""
        return self._extract_from_csv(file_content, filename)
    
    def pilotlog_crewlounge_transform(self, extracted_data):
        """Transform data from CrewLounge Pilot Log format using field mappings"""
        if not extracted_data:
            return []
            
        transformed_data = []
        
        # Group mappings by model
        mappings_by_model = {}
        for mapping in self.mapping_ids:
            if mapping.model not in mappings_by_model:
                mappings_by_model[mapping.model] = []
            mappings_by_model[mapping.model].append(mapping)
        
        # Transform each record
        for record in extracted_data:
            transformed_record = {
                'flight.aerodrome.departure': {},
                'flight.aerodrome.arrival': {},
                'flight.aircraft': {},
                'flight.flight': {},
            }
            
            # Apply transformations for each model
            for model, mappings in mappings_by_model.items():
                for mapping in mappings:
                    if mapping.source_field in record:
                        value = record[mapping.source_field]
                        
                        # Apply transformation
                        transformed_value = self._apply_field_transformations(
                            mapping.source_field, 
                            value, 
                            mapping.transformation, 
                            mapping.transformation_options
                        )
                        
                        # Store the transformed value in the appropriate model section
                        if model == 'flight.aerodrome' and mapping.field_type == 'source':
                            # Use the context field to determine if it's departure or arrival
                            if mapping.context == 'departure':
                                transformed_record['flight.aerodrome.departure'][mapping.target_field] = transformed_value
                            elif mapping.context == 'arrival':
                                transformed_record['flight.aerodrome.arrival'][mapping.target_field] = transformed_value
                            elif mapping.context == 'both':
                                transformed_record['flight.aerodrome.departure'][mapping.target_field] = transformed_value
                                transformed_record['flight.aerodrome.arrival'][mapping.target_field] = transformed_value
                        else:
                            transformed_record[model][mapping.target_field] = transformed_value
            
            transformed_data.append(transformed_record)
            
        return transformed_data
    
    def pilotlog_crewlounge_load(self, transformed_data):
        """Load transformed data into flight models"""
        if not transformed_data:
            return {'created': [], 'errors': ['No data to import']}
        
        flights = []
        created_aerodromes = []
        created_aircraft = []
        errors = []
        
        for record in transformed_data:
            try:
                # Create or find departure aerodrome
                departure_data = record['flight.aerodrome.departure']
                if departure_data and departure_data.get('icao'):
                    departure = self._get_or_create_aerodrome(departure_data)
                    if departure not in created_aerodromes:
                        created_aerodromes.append(departure)
                else:
                    departure = False
                
                # Create or find arrival aerodrome
                arrival_data = record['flight.aerodrome.arrival']
                if arrival_data and arrival_data.get('icao'):
                    arrival = self._get_or_create_aerodrome(arrival_data)
                    if arrival not in created_aerodromes:
                        created_aerodromes.append(arrival)
                else:
                    arrival = False
                
                # Create or find aircraft
                aircraft_data = record['flight.aircraft']
                if aircraft_data and aircraft_data.get('registration'):
                    aircraft = self._get_or_create_aircraft(aircraft_data)
                    if aircraft not in created_aircraft:
                        created_aircraft.append(aircraft)
                else:
                    aircraft = False
                
                # Create flight
                flight_data = record['flight.flight']
                if departure and arrival and aircraft:
                    flight_vals = {
                        'date': flight_data.get('date'),
                        'aircraft_id': aircraft.id,
                        'departure_id': departure.id,
                        'arrival_id': arrival.id,
                    }
                    flight = self.env['flight.flight'].create(flight_vals)
                    flights.append(flight)
            except Exception as e:
                errors.append(str(e))
        
        return {
            'created': flights,
            'errors': errors,
            # Additional data for more detailed logging
            'flights': flights,
            'aerodromes': created_aerodromes,
            'aircraft': created_aircraft,
        }
    
    def _get_or_create_aerodrome(self, aerodrome_data):
        """Find or create an aerodrome"""
        icao = aerodrome_data.get('icao')
        if not icao:
            raise UserError(_("ICAO code is required for aerodrome"))
        
        return self._get_or_create_record(
            'flight.aerodrome',
            [('icao', '=', icao)],
            {
                'name': aerodrome_data.get('name', icao),
                'icao': icao,
            }
        )
    
    def _get_or_create_aircraft(self, aircraft_data):
        """Find or create an aircraft"""
        registration = aircraft_data.get('registration')
        if not registration:
            raise UserError(_("Registration is required for aircraft"))
        
        return self._get_or_create_record(
            'flight.aircraft',
            [('registration', '=', registration)],
            {
                'registration': registration,
            }
        )
