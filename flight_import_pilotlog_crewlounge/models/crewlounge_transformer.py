# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class FlightImportPIlotlogTransformer(models.Model):
    _inherit = "flight.import.pilotlog.transformer"

    @api.model
    def _get_available_implementations(self):
        """Add CrewLounge to available implementations"""
        implementations = super(FlightImportPIlotlogTransformer, self)._get_available_implementations()
        return implementations + [('crewlounge', 'CrewLounge Format')]

    # Helper function to round duration values consistently
    def _round_duration(self, value, decimals=4):
        """Round duration values to a consistent number of decimal places."""
        return round(value, decimals)

    def _standardize_aircraft_name(self, name):
        """Standardize aircraft name capitalization.
        
        Converts names to title case (first letter of each word capitalized).
        
        Args:
            name: The name string to standardize
            
        Returns:
            Properly capitalized name string
        """
        if not name:
            return name
        return name.title()

    def _create_full_model_name(self, make_name, model_name, variant=''):
        """Helper method to create a standardized full model name.
        
        Args:
            make_name: The aircraft make name
            model_name: The aircraft model name
            variant: Optional variant name
            
        Returns:
            A formatted full model name string
        """
        # Standardize capitalization
        make_name = self._standardize_aircraft_name(make_name)
        
        full_model_name = f"{make_name} {model_name}"
        if variant:
            full_model_name += f" {variant}"
        return full_model_name.strip()

    def flight_flight_crewlounge_transform_data(self, data_rows, headers, import_wizard=None):
        """Transform CrewLounge data to flight.flight format suitable for Odoo import.

        Args:
            data_rows: List of data rows to transform
            headers: Headers for the data rows
            import_wizard: The import wizard record containing configuration like base_pilot_id

        Returns:
            Transformed data with headers as first row, structured for Odoo import
            with nested one2many fields.
        """
        _logger.info("Starting CrewLounge data transformation for %d rows", len(data_rows))

        TIME_CODE_MAPPING = {
            'TIME_TOTAL': 'flight_pilotlog.flight_pilot_time_code_total',     # Total Block Time
            'TIME_PIC': 'flight_pilotlog.flight_pilot_time_code_pic',         # Pilot in Command
            'TIME_SIC': 'flight_pilotlog.flight_pilot_time_code_sic',         # Second in Command
            'TIME_DUAL': 'flight_pilotlog.flight_pilot_time_code_dual',       # Dual Instruction Received
            'TIME_PICUS': 'flight_pilotlog.flight_pilot_time_code_picus',     # PICUS Time
            'TIME_INSTRUCTOR': 'flight_pilotlog.flight_pilot_time_code_instructor', # Instructor Time
            'TIME_EXAMINER': 'flight_pilotlog.flight_pilot_time_code_examiner',    # Examiner Time
            'TIME_NIGHT': 'flight_pilotlog.flight_pilot_time_code_night',     # Night Time
            'TIME_XC': 'flight_pilotlog.flight_pilot_time_code_xc',           # Cross Country
            'TIME_IFR': 'flight_pilotlog.flight_pilot_time_code_ifr',         # IFR Time (Simulated or Actual)
            'TIME_HOOD': 'flight_pilotlog.flight_pilot_time_code_hood',       # Simulated Instrument (Hood)
            'TIME_ACTUAL': 'flight_pilotlog.flight_pilot_time_code_actual',   # Actual Instrument (IMC)
            'TIME_RELIEF': 'flight_pilotlog.flight_pilot_time_code_relief',   # Relief Pilot Time
            'TIME_AIR': 'flight_pilotlog.flight_pilot_time_code_air',         # Airborne Time
            # Add other TIME_* fields if needed and corresponding codes exist in Odoo
        }

        # Special format fields
        TIME_FORMAT_MAPPING = {
            'TIME_AIR': 'HH:MM',  # Airborne Time is in HH:MM format
        }

        EVENT_CODE_MAPPING = {
            'TO_DAY': 'flight_pilotlog.flight_pilot_event_code_to_day',       # Takeoff Day
            'TO_NIGHT': 'flight_pilotlog.flight_pilot_event_code_to_night',     # Takeoff Night
            'LDG_DAY': 'flight_pilotlog.flight_pilot_event_code_ldg_day',      # Landing Day
            'LDG_NIGHT': 'flight_pilotlog.flight_pilot_event_code_ldg_night',    # Landing Night
            'LIFT': 'flight_pilotlog.flight_pilot_event_code_lift',         # Lift (e.g., winch launch) - if applicable
            'HOLDING': 'flight_pilotlog.flight_pilot_event_code_holding',    # Holding Pattern
            # Add other event fields if needed and corresponding codes exist
        }

        # --- Define the Full Transformed Headers ---
        transformed_headers = [
            'id', 'date', 'aircraft_id/registration', 'departure_id/icao', 'arrival_id/icao',
            'remark_ids/id', 'remark_ids/partner_id/id', 'remark_ids/remark',
            'pilot_time_ids/id', 'pilot_time_ids/partner_id/id', 'pilot_time_ids/code_id/id', 'pilot_time_ids/duration',
            'pilot_event_ids/id', 'pilot_event_ids/partner_id/id', 'pilot_event_ids/event_code_id/id', 'pilot_event_ids/count'
        ]

        # Create a mapping of original headers (uppercase) to their indices
        header_map = {}
        if headers:
            for idx, col in enumerate(headers):
                header_map[col.upper()] = idx
            _logger.debug("Created header map: %s", header_map)

        transformed_data = [transformed_headers]
        skipped_rows = 0

        # Process each row of the original data
        for idx, row in enumerate(data_rows):
            # Skip header row if present in data_rows (robust check)
            if headers and idx == 0 and len(row) == len(headers) and all(str(row[i]).upper() == str(headers[i]).upper() for i in range(len(headers))):
                continue

            # Skip empty rows
            if not row or all(not cell for cell in row):
                skipped_rows += 1
                continue

            # Make sure row has a minimum number of elements based on mapped headers
            min_cols_needed = 1 # At least one column expected
            if header_map:
                 min_cols_needed = max(header_map.values()) + 1
            if len(row) < min_cols_needed:
                _logger.warning("Row %d has insufficient columns (%d found, %d expected based on headers), skipping", idx + 1, len(row), min_cols_needed)
                skipped_rows += 1
                continue

            # --- Extract Basic Flight Data ---
            flight_id = f"flight_import_{idx:03d}"
            date_str = ''
            aircraft_reg = ''
            departure = ''
            arrival = ''

            try:
                # Date
                date_idx = header_map.get('PILOTLOG_DATE')
                if date_idx is not None and date_idx < len(row) and row[date_idx]:
                    try:
                        # Try parsing different common date formats if needed
                        date_str = datetime.strptime(str(row[date_idx]), '%d-%m-%Y').strftime('%Y-%m-%d')
                    except (ValueError, TypeError) as e:
                         _logger.warning("Row %d: Failed to parse date '%s': %s. Skipping date.", idx + 1, row[date_idx] if date_idx < len(row) else 'N/A', e)

                # Aircraft Registration
                reg_idx = header_map.get('AC_REG')
                if reg_idx is not None and reg_idx < len(row):
                    aircraft_reg = str(row[reg_idx] or '').strip()

                # Departure Aerodrome
                dep_idx = header_map.get('AF_DEP')
                if dep_idx is not None and dep_idx < len(row):
                    departure = str(row[dep_idx] or '').strip().upper()

                # Arrival Aerodrome
                arr_idx = header_map.get('AF_ARR')
                if arr_idx is not None and arr_idx < len(row):
                    arrival = str(row[arr_idx] or '').strip().upper()

                # Basic validation
                if not date_str or not aircraft_reg or not departure or not arrival:
                    _logger.warning("Row %d: Missing essential flight data (Date, Reg, Dep, Arr). Skipping row.", idx + 1)
                    skipped_rows += 1
                    continue

                # --- Extract Related Data ---
                remarks_data = []
                times_data = []
                events_data = []

                # Determine the partner to use
                if import_wizard and import_wizard.base_pilot_id:
                    # For Odoo imports, use the database ID directly
                    partner_ref = import_wizard.base_pilot_id.id
                    _logger.info("Using partner ID: %s", partner_ref)
                else:
                    partner_ref = self.env.user.partner_id.id
                    _logger.info("Using current user's partner ID: %s", partner_ref)

                # Remarks
                remark_idx = header_map.get('REMARKS')
                if remark_idx is not None and remark_idx < len(row) and row[remark_idx]:
                    remark_text = str(row[remark_idx]).strip()
                    if remark_text:
                        remarks_data.append({
                            'id': f"remark_{flight_id}_0",
                            'partner_id': partner_ref,
                            'remark': remark_text
                        })

                # Times
                time_counter = 0
                for csv_col, odoo_code_xmlid in TIME_CODE_MAPPING.items():
                    col_idx = header_map.get(csv_col)
                    if col_idx is not None and col_idx < len(row) and row[col_idx]:
                        try:
                            # Check if this field has a special format
                            special_format = TIME_FORMAT_MAPPING.get(csv_col)
                            
                            if special_format == 'HH:MM':
                                # Handle HH:MM format (e.g., "0:12", "0:16")
                                time_str = str(row[col_idx]).strip()
                                if ':' in time_str:
                                    hours, minutes = time_str.split(':')
                                    duration_hours = self._round_duration(float(hours) + float(minutes) / 60.0)
                                else:
                                    # Fallback to treating as minutes if not in HH:MM format
                                    duration_hours = self._round_duration(float(time_str) / 60.0)
                            else:
                                # Standard processing for minute values
                                duration_minutes = float(row[col_idx])
                                duration_hours = self._round_duration(duration_minutes / 60.0)
                            _logger.info("TIME DURATION")
                            _logger.info(duration_hours)
                            if duration_hours > 0:
                                times_data.append({
                                    'id': f"time_{flight_id}_{time_counter}",
                                    'partner_id': partner_ref,
                                    'code_id': odoo_code_xmlid,
                                    'duration': duration_hours
                                })
                                time_counter += 1
                        except (ValueError, TypeError) as e:
                            _logger.warning("Row %d: Invalid value '%s' for time column '%s': %s. Skipping time entry.", idx + 1, row[col_idx], csv_col, e)

                # Events
                event_counter = 0
                for csv_col, odoo_code_xmlid in EVENT_CODE_MAPPING.items():
                    col_idx = header_map.get(csv_col)
                    if col_idx is not None and col_idx < len(row) and row[col_idx]:
                        try:
                            count = int(float(row[col_idx])) # Use float first for potential decimals like '1.0'
                            if count > 0:
                                events_data.append({
                                    'id': f"event_{flight_id}_{event_counter}",
                                    'partner_id': partner_ref,
                                    'code_id': odoo_code_xmlid,
                                    'count': count
                                })
                                event_counter += 1
                        except (ValueError, TypeError) as e:
                             _logger.warning("Row %d: Invalid value '%s' for event column '%s': %s. Skipping event entry.", idx + 1, row[col_idx], csv_col, e)

                # --- Construct Output Rows ---
                num_remarks = len(remarks_data)
                num_times = len(times_data)
                num_events = len(events_data)
                max_lines = max(1, num_remarks, num_times, num_events) # Need at least 1 row for the flight
                first_remark_id, first_remark_partner, first_remark_text = '', '', ''
                if num_remarks > 0:
                    first_remark_id = remarks_data[0]['id']
                    first_remark_partner = remarks_data[0]['partner_id']
                    first_remark_text = remarks_data[0]['remark']
                for i in range(max_lines):
                    remark_id, remark_partner, remark_text = '', '', ''
                     # Check if it's the last iteration AND remarks exist in the original data
                    if num_remarks > 0 and i == max_lines - 1:
                        remark_id = first_remark_id
                        remark_partner = first_remark_partner
                        remark_text = first_remark_text


                    time_id, time_partner, time_code, time_duration = '', '', '', ''
                    if i < num_times:
                        time_id = times_data[i]['id']
                        time_partner = times_data[i]['partner_id']
                        time_code = times_data[i]['code_id']
                        time_duration = times_data[i]['duration'] # Float

                    event_id, event_partner, event_code, event_count = '', '', '', ''
                    if i < num_events:
                        event_id = events_data[i]['id']
                        event_partner = events_data[i]['partner_id']
                        event_code = events_data[i]['code_id']
                        event_count = events_data[i]['count'] # Int

                    # --- Convert numeric types to string for CSV output ---
                    time_duration_str = str(time_duration) if time_duration != '' else ''
                    event_count_str = str(event_count) if event_count != '' else ''
                    # --- End Conversion ---


                    # --- Correction: Repeat main record required fields on ALL lines ---
                    # No longer clear these fields for i > 0
                    current_flight_id = flight_id
                    current_date = str(date_str)         # Always include
                    current_aircraft = str(aircraft_reg) # Always include
                    current_dep = str(departure)         # Always include
                    current_arr = str(arrival)           # Always include
                    # --- End Correction ---

                    transformed_row = [
                        current_flight_id, current_date, current_aircraft, current_dep, current_arr,
                        str(remark_id), str(remark_partner), str(remark_text), # Ensure strings
                        str(time_id), str(time_partner), str(time_code), time_duration_str, # Use string version
                        str(event_id), str(event_partner), str(event_code), event_count_str # Use string version
                    ]
                    transformed_data.append(transformed_row)

            except Exception as e:
                _logger.error("Error processing row %d: %s. Row data: %s. Skipping row.", idx + 1, e, row, exc_info=True)
                skipped_rows += 1
                continue # Skip to the next row on unexpected errors

        _logger.info("Transformation complete. Generated %d data rows (excluding header). Skipped %d rows.", len(transformed_data) - 1, skipped_rows)
        if skipped_rows > 0:
             _logger.warning("%d rows were skipped due to errors or missing essential data. Please check logs.", skipped_rows)

        return transformed_data

    def flight_aircraft_crewlounge_transform_data(self, data_rows, headers, import_wizard=None):
        """Transform CrewLounge data to flight.aircraft format suitable for Odoo import.

        Args:
            data_rows: List of data rows to transform
            headers: Headers for the data rows
            import_wizard: The import wizard record containing configuration

        Returns:
            Transformed data with headers as first row, structured for Odoo import
        """
        _logger.info("Starting CrewLounge data transformation for aircraft: %d rows", len(data_rows))

        # Define the transformed headers for aircraft import
        transformed_headers = [
            'id', 'registration', 'operator_id', 'model_id'
        ]

        # Create a mapping of original headers (uppercase) to their indices
        header_map = {}
        if headers:
            for idx, col in enumerate(headers):
                header_map[col.upper()] = idx
            _logger.debug("Created header map: %s", header_map)

        transformed_data = [transformed_headers]
        skipped_rows = 0
        processed_aircraft = set()  # Track unique aircraft to avoid duplicates

        # Process each row of the original data
        for idx, row in enumerate(data_rows):
            # Skip header row if present in data_rows
            if headers and idx == 0 and len(row) == len(headers) and all(str(row[i]).upper() == str(headers[i]).upper() for i in range(len(headers))):
                continue

            # Skip empty rows
            if not row or all(not cell for cell in row):
                skipped_rows += 1
                continue

            # Make sure row has a minimum number of elements based on mapped headers
            min_cols_needed = 1  # At least one column expected
            if header_map:
                min_cols_needed = max(header_map.values()) + 1
            if len(row) < min_cols_needed:
                _logger.warning("Row %d has insufficient columns (%d found, %d expected based on headers), skipping", 
                               idx + 1, len(row), min_cols_needed)
                skipped_rows += 1
                continue

            try:
                # --- Extract Aircraft Registration ---
                reg_idx = header_map.get('AC_REG')
                if reg_idx is None or reg_idx >= len(row) or not row[reg_idx]:
                    _logger.warning("Row %d: Missing aircraft registration. Skipping row.", idx + 1)
                    skipped_rows += 1
                    continue

                aircraft_reg = str(row[reg_idx]).strip()
                
                # Skip if we've already processed this aircraft
                if aircraft_reg in processed_aircraft:
                    _logger.info("Skipping duplicate aircraft registration: %s", aircraft_reg)
                    continue
                
                processed_aircraft.add(aircraft_reg)

                # --- Extract Aircraft Make/Model ---
                make_idx = header_map.get('AC_MAKE')
                model_idx = header_map.get('AC_MODEL')
                variant_idx = header_map.get('AC_VARIANT')
                
                # Extract values with fallbacks
                make_name = str(row[make_idx]).strip() if make_idx is not None and make_idx < len(row) and row[make_idx] else ''
                model_name = str(row[model_idx]).strip() if model_idx is not None and model_idx < len(row) and row[model_idx] else ''
                variant = str(row[variant_idx]).strip() if variant_idx is not None and variant_idx < len(row) and row[variant_idx] else ''
                
                full_model_name = self._create_full_model_name(make_name, model_name, variant)
                
                # --- Extract Operator ---
                operator_idx = header_map.get('OPERATOR')
                operator_name = str(row[operator_idx]).strip() if operator_idx is not None and operator_idx < len(row) and row[operator_idx] else ''
                
                # Create the transformed row
                aircraft_id = f"aircraft_import_{aircraft_reg.replace('-', '_')}"
                
                transformed_row = [
                    aircraft_id,        # id
                    aircraft_reg,       # registration
                    operator_name,      # operator_id (name lookup)
                    full_model_name     # model_id (name lookup)
                ]
                
                transformed_data.append(transformed_row)

            except Exception as e:
                _logger.error("Error processing row %d: %s. Row data: %s. Skipping row.", 
                             idx + 1, e, row, exc_info=True)
                skipped_rows += 1
                continue  # Skip to the next row on unexpected errors

        _logger.info("Aircraft transformation complete. Generated %d data rows (excluding header). Skipped %d rows.", 
                    len(transformed_data) - 1, skipped_rows)
        if skipped_rows > 0:
            _logger.warning("%d rows were skipped due to errors or missing essential data. Please check logs.", 
                           skipped_rows)

        return transformed_data

    def flight_aircraft_make_crewlounge_transform_data(self, data_rows, headers, import_wizard=None):
        """Transform CrewLounge data to flight.aircraft.make format.
        
        Extracts unique aircraft makes from the data.
        """
        _logger.info("Starting CrewLounge data transformation for aircraft makes: %d rows", len(data_rows))
        
        # Define headers for make import
        transformed_headers = ['id', 'name']
        
        # Create a mapping of original headers to their indices
        header_map = {}
        if headers:
            for idx, col in enumerate(headers):
                header_map[col.upper()] = idx
        
        transformed_data = [transformed_headers]
        processed_makes = set()  # Track unique makes
        
        # Process each row to extract unique makes
        for idx, row in enumerate(data_rows):
            # Skip header row if present
            if headers and idx == 0 and len(row) == len(headers):
                continue
                
            # Skip empty rows
            if not row or all(not cell for cell in row):
                continue
                
            try:
                # Extract make
                make_idx = header_map.get('AC_MAKE')
                if make_idx is None or make_idx >= len(row) or not row[make_idx]:
                    continue
                    
                make_name = str(row[make_idx]).strip()
                # Standardize capitalization
                make_name = self._standardize_aircraft_name(make_name)
                
                if not make_name or make_name in processed_makes:
                    continue
                    
                processed_makes.add(make_name)
                
                # Create unique ID for the make
                make_id = f"make_{make_name.lower().replace(' ', '_')}"
                
                transformed_data.append([make_id, make_name])
                
            except Exception as e:
                _logger.error("Error processing make in row %d: %s", idx + 1, e)
                continue
                
        _logger.info("Aircraft make transformation complete. Generated %d unique makes.", len(transformed_data) - 1)
        return transformed_data
        
    def flight_aircraft_model_crewlounge_transform_data(self, data_rows, headers, import_wizard=None):
        """Transform CrewLounge data to flight.aircraft.model format.
        
        Extracts unique aircraft models from the data with references to makes and classes.
        """
        _logger.info("Starting CrewLounge data transformation for aircraft models: %d rows", len(data_rows))
        
        # Define headers for model import
        transformed_headers = [
            'id', 'name', 'make_id', 'class_id', 'engine_type', 'gear_type'
        ]
        
        # Create a mapping of original headers to their indices
        header_map = {}
        if headers:
            for idx, col in enumerate(headers):
                header_map[col.upper()] = idx
        
        # Engine type mapping
        engine_type_mapping = {
            'Piston': 'piston',
            'Turboprop': 'turboprop',
            'Turbofan': 'turbofan',
            'Turbojet': 'turbojet',
            'Turboshaft': 'turboshaft',
            'Electric': 'electric',
        }
        
        transformed_data = [transformed_headers]
        processed_models = set()  # Track unique models
        
        # Process each row to extract unique models
        for idx, row in enumerate(data_rows):
            # Skip header row if present
            if headers and idx == 0 and len(row) == len(headers):
                continue
                
            # Skip empty rows
            if not row or all(not cell for cell in row):
                continue
                
            try:
                # Extract make, model, variant
                make_idx = header_map.get('AC_MAKE')
                model_idx = header_map.get('AC_MODEL')
                variant_idx = header_map.get('AC_VARIANT')
                engine_type_idx = header_map.get('AC_ENGTYPE')
                tailwheel_idx = header_map.get('AC_TAILWHEEL')
                
                # Skip if missing essential data
                if (make_idx is None or make_idx >= len(row) or not row[make_idx] or
                    model_idx is None or model_idx >= len(row) or not row[model_idx]):
                    continue
                    
                make_name = str(row[make_idx]).strip()
                model_name = str(row[model_idx]).strip()
                variant = str(row[variant_idx]).strip() if variant_idx is not None and variant_idx < len(row) and row[variant_idx] else ''
                
                full_model_name = self._create_full_model_name(make_name, model_name, variant)
                
                # Skip if already processed
                if full_model_name in processed_models:
                    continue
                    
                processed_models.add(full_model_name)
                
                # Extract engine type and count
                engine_type_idx = header_map.get('AC_ENGTYPE')
                engine_type = str(row[engine_type_idx]).strip() if engine_type_idx is not None and engine_type_idx < len(row) and row[engine_type_idx] else ''
                odoo_engine_type = engine_type_mapping.get(engine_type, '')
                
                # Extract engine count (Single/Multi)
                engines_idx = header_map.get('AC_ENGINES')
                engine_count = str(row[engines_idx]).strip() if engines_idx is not None and engines_idx < len(row) and row[engines_idx] else ''
                is_multi_engine = engine_count.lower() == 'multi'
                
                # Check if seaplane
                sea_idx = header_map.get('AC_SEA')
                is_seaplane = False
                if sea_idx is not None and sea_idx < len(row) and row[sea_idx]:
                    is_seaplane = str(row[sea_idx]).strip().upper() in ('TRUE', 'YES', '1')
                
                # Determine gear type
                tailwheel_idx = header_map.get('AC_TAILWHEEL')
                is_tailwheel = False
                if tailwheel_idx is not None and tailwheel_idx < len(row):
                    is_tailwheel = str(row[tailwheel_idx]).strip().upper() in ('TRUE', 'YES', '1')
                    
                gear_type = 'fixed_tailwheel' if is_tailwheel else 'fixed_tricycle'
                
                # Map to the correct class ID based on aircraft category and characteristics
                # Map class IDs to display names
                class_display_names = {
                    'class_airplane_mes': 'Multi-Engine Sea',
                    'class_airplane_mel': 'Multi-Engine Land',
                    'class_airplane_ses': 'Single-Engine Sea',
                    'class_airplane_sel': 'Single-Engine Land',
                    'class_rotorcraft_helicopter': 'Helicopter',
                    'class_rotorcraft_gyroplane': 'Gyroplane',
                    'class_glider': 'Glider',
                    'class_lighter_than_air_balloon': 'Balloon',
                    'class_lighter_than_air_airship': 'Airship',
                    'class_powered_lift': 'Powered Lift',
                    'class_powered_parachute': 'Powered Parachute',
                    'class_weight_shift_control': 'Weight Shift Control'
                }
                
                class_id = ''
                if is_multi_engine and is_seaplane:
                    class_id = class_display_names['class_airplane_mes']  # Multi-Engine Sea
                elif is_multi_engine:
                    class_id = class_display_names['class_airplane_mel']  # Multi-Engine Land
                elif is_seaplane:
                    class_id = class_display_names['class_airplane_ses']  # Single-Engine Sea
                else:
                    class_id = class_display_names['class_airplane_sel']  # Single-Engine Land
                
                # Create IDs for references
                make_id = self._standardize_aircraft_name(make_name)
                model_id = f"model_{make_name.lower().replace(' ', '_')}_{model_name.lower().replace(' ', '_')}"
                
                transformed_data.append([
                    model_id,
                    full_model_name,
                    make_id,
                    class_id,
                    odoo_engine_type,
                    gear_type
                ])
                
            except Exception as e:
                _logger.error("Error processing model in row %d: %s", idx + 1, e)
                continue
                
        _logger.info("Aircraft model transformation complete. Generated %d unique models.", len(transformed_data) - 1)
        return transformed_data