import csv
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class FlightDataImporter(models.TransientModel):
    _name = 'flight.data.importer'
    _description = 'Flight Data Importer'

    # Fields for the wizard
    csv_file = fields.Binary(string="CSV File", required=True)
    self_partner_id = fields.Many2one(
        'res.partner',
        string="SELF Pilot",
        required=True,
        domain="[('is_company', '=', False)]"
    )

    def action_import(self):
        """Handle the import process with a loading state and result notification."""

        try:
            # Step 2: Perform the import
            self._perform_import()

            # Step 3: Show success message if import completes
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Import Successful',
                    'message': 'The flight data has been imported successfully.',
                    'type': 'success',  # Green notification
                    'sticky': False,    # Auto-dismisses after a few seconds
                }
            }
        except Exception as e:
            # Step 3 (alternative): Show error message if import fails
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Import Failed',
                    'message': f'An error occurred: {str(e)}',
                    'type': 'danger',   # Red notification
                    'sticky': False,
                }
            }

    def _perform_import(self):
        """Handle the import process when the 'Import' button is clicked."""
        if not self.csv_file:
            raise UserError(_("Please upload a CSV file."))
        if not self.self_partner_id:
            raise UserError(_("Please select the SELF pilot."))

        # Decode the uploaded CSV file
        try:
            csv_data = self.csv_file.decode('utf-8').splitlines()
            reader = csv.DictReader(csv_data)
        except Exception as e:
            raise UserError(_("Error reading CSV file: %s") % str(e))

        # Hardcoded configuration for mapping CSV columns to Odoo fields
        config = {
            'flight.flight': {
                'date': {'source': 'PILOTLOG_DATE', 'transform': {'type': 'date', 'format': '%d-%m-%Y'}},
                'aircraft_id': {
                    'related_model': 'flight.aircraft',
                    'search_field': 'registration',
                    'source_search': 'AC_REG',
                    'create_if_not_found': True,
                    'create_values': {
                        'registration': 'AC_REG',
                        'model_id': {
                            'related_model': 'flight.aircraft.model',
                            'search_fields': ['make_id.name', 'name'],
                            'source_search': ['AC_MAKE', 'AC_MODEL'],
                            'create_if_not_found': True,
                            'create_values': {
                                'name': 'AC_MODEL',
                                'make_id': {
                                    'related_model': 'flight.aircraft.make',
                                    'search_field': 'name',
                                    'source_search': 'AC_MAKE',
                                    'create_if_not_found': True,
                                    'create_values': {'name': 'AC_MAKE'}
                                }
                            }
                        }
                    }
                },
                'departure_id': {
                    'related_model': 'flight.aerodrome',
                    'search_field': 'icao',
                    'source_search': 'AF_DEP',
                    'create_if_not_found': True,
                    'create_values': {'icao': 'AF_DEP'}
                },
                'arrival_id': {
                    'related_model': 'flight.aerodrome',
                    'search_field': 'icao',
                    'source_search': 'AF_ARR',
                    'create_if_not_found': True,
                    'create_values': {'icao': 'AF_ARR'}
                }
            },
            'flight.pilot.time': [
                {
                    'partner_id': {'source': 'PILOT1_NAME', 'transform': {'type': 'map_pilot'}},
                    'code_id': self.env.ref('flight_pilotlog.flight_pilot_time_code_pic').id,  # Replace with your XML ID
                    'duration': {'source': 'TIME_PIC', 'transform': {'type': 'minutes_to_hours'}}
                }
            ],
            'flight.pilot.event': [
                {
                    'partner_id': {'source': 'PILOT1_NAME', 'transform': {'type': 'map_pilot'}},
                    'event_code_id': self.env.ref('flight_pilotlog.flight_pilot_event_code_to_day').id,  # Replace with your XML ID
                    'count': {'source': 'TO_DAY'}
                }
            ],
            'flight.pilot.remark': {
                'partner_id': {'source': 'PILOT1_NAME', 'transform': {'type': 'map_pilot'}},
                'remark': {'source': 'REMARKS'}
            }
        }

        # Initialize caches to improve performance
        caches = {
            'aerodrome': {},  # icao -> id
            'aircraft': {},   # registration -> id
            'make': {},       # name -> id
            'model': {},      # (make_id, name) -> id
            'pilot': {}       # name -> id
        }

        print(config)
        print(caches)

        # Process each row in the CSV
        for row in reader:
            try:
                self._process_row(row, config, caches, self.self_partner_id)
            except Exception as e:
                raise UserError(_("Error processing row: %s") % str(e))

    def _process_row(self, row, config, caches, self_partner_id):
        """Process a single row from the CSV and create related records."""
        env = self.env

        # Create flight.flight record
        flight_vals = {}
        for field, mapping in config['flight.flight'].items():
            if 'related_model' in mapping:
                flight_vals[field] = self._get_or_create_related(row, mapping, caches, env)
            else:
                flight_vals[field] = self._transform_value(row, mapping)
        flight = env['flight.flight'].create(flight_vals)

        # Create pilot time records
        for time_mapping in config.get('flight.pilot.time', []):
            partner_id = self._get_pilot_id(row, time_mapping['partner_id'], caches, self_partner_id, env)
            duration = self._transform_value(row, time_mapping['duration'])
            if duration and partner_id:
                env['flight.pilot.time'].create({
                    'flight_id': flight.id,
                    'partner_id': partner_id,
                    'code_id': time_mapping['code_id'],
                    'duration': duration
                })

        # Create pilot event records
        for event_mapping in config.get('flight.pilot.event', []):
            partner_id = self._get_pilot_id(row, event_mapping['partner_id'], caches, self_partner_id, env)
            count = int(row.get(event_mapping['count']['source'], 0))
            if count and partner_id:
                env['flight.pilot.event'].create({
                    'flight_id': flight.id,
                    'partner_id': partner_id,
                    'event_code_id': event_mapping['event_code_id'],
                    'count': count
                })

        # Create remark records
        remark_mapping = config.get('flight.pilot.remark', {})
        if remark_mapping and row.get(remark_mapping['remark']['source']):
            partner_id = self._get_pilot_id(row, remark_mapping['partner_id'], caches, self_partner_id, env)
            env['flight.pilot.remark'].create({
                'flight_id': flight.id,
                'partner_id': partner_id,
                'remark': row[remark_mapping['remark']['source']]
            })

    def _get_or_create_related(self, row, mapping, caches, env):
        """Get or create a related record (e.g., aircraft, aerodrome) based on CSV data."""
        model = mapping['related_model']
        search_field = mapping['search_field']
        search_value = row.get(mapping['source_search'], '')

        if not search_value:
            return False

        cache_key = (model, search_value)
        if cache_key in caches.get(model, {}):
            return caches[model][cache_key]

        record = env[model].search([(search_field, '=', search_value)], limit=1)
        if not record and mapping.get('create_if_not_found'):
            create_vals = {}
            for key, val in mapping['create_values'].items():
                if isinstance(val, dict) and 'related_model' in val:
                    create_vals[key] = self._get_or_create_related(row, val, caches, env)
                else:
                    create_vals[key] = row.get(val, '')
            record = env[model].create(create_vals)

        caches.setdefault(model, {})[cache_key] = record.id
        return record.id

    def _transform_value(self, row, mapping):
        """Transform a CSV value based on the specified transformation type."""
        value = row.get(mapping['source'], '')
        if not value:
            return False
        transform = mapping.get('transform', {})
        if transform.get('type') == 'date':
            try:
                return datetime.strptime(value, transform['format']).date()
            except ValueError:
                raise UserError(_("Invalid date format for %s: %s") % (mapping['source'], value))
        elif transform.get('type') == 'minutes_to_hours':
            try:
                return float(value) / 60
            except ValueError:
                raise UserError(_("Invalid time value for %s: %s") % (mapping['source'], value))
        return value

    def _get_pilot_id(self, row, mapping, caches, self_partner_id, env):
        """Map a pilot name from the CSV to a res.partner ID, using 'SELF' for the selected pilot."""
        pilot_name = row.get(mapping['source'], '')
        if not pilot_name:
            return False
        if pilot_name == 'SELF':
            return self_partner_id.id
        if pilot_name in caches['pilot']:
            return caches['pilot'][pilot_name]
        pilot = env['res.partner'].search([('name', '=', pilot_name)], limit=1)
        if not pilot:
            pilot = env['res.partner'].create({'name': pilot_name})
        caches['pilot'][pilot_name] = pilot.id
        return pilot.id