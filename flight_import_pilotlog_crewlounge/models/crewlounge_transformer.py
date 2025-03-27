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

    def flight_flight_crewlounge_transform_data(self, data_rows, headers):
        """Transform CrewLounge data to flight.flight format suitable for Odoo import.

        Args:
            data_rows: List of data rows to transform
            headers: Headers for the data rows

        Returns:
            Transformed data with headers as first row, structured for Odoo import
            with nested one2many fields.
        """
        _logger.info("Starting transformation of CrewLounge data with %d rows", len(data_rows))

        # --- Mappings from CSV Column Name (UPPERCASE) to Odoo Info ---
        # Assumes flight_pilotlog module XML IDs are loaded
        # Using placeholders like base.partner_admin for pilot, adjust as needed
        # Duration needs conversion from minutes (CSV) to hours (Odoo)

        # Placeholder for the pilot - replace with actual logic if needed
        # e.g., map PILOT1_ID=='SELF' to self.env.user.partner_id.id
        # or look up based on PILOT1_ID/PILOT1_NAME
        DEFAULT_PARTNER_XMLID = "base.partner_admin"

        TIME_CODE_MAPPING = {
            'TIME_TOTAL': ('flight_pilotlog.flight_pilot_time_code_total', 60.0), # Total Block Time
            'TIME_PIC': ('flight_pilotlog.flight_pilot_time_code_pic', 60.0),     # Pilot in Command
            'TIME_SIC': ('flight_pilotlog.flight_pilot_time_code_sic', 60.0),     # Second in Command
            'TIME_DUAL': ('flight_pilotlog.flight_pilot_time_code_dual', 60.0),    # Dual Received
            'TIME_PICUS': ('flight_pilotlog.flight_pilot_time_code_picus', 60.0),  # PIC Under Supervision
            'TIME_INSTRUCTOR': ('flight_pilotlog.flight_pilot_time_code_instructor', 60.0), # Instructor Time
            'TIME_EXAMINER': ('flight_pilotlog.flight_pilot_time_code_examiner', 60.0),  # Examiner Time
            'TIME_NIGHT': ('flight_pilotlog.flight_pilot_time_code_night', 60.0),    # Night Time
            'TIME_XC': ('flight_pilotlog.flight_pilot_time_code_xc', 60.0),       # Cross Country
            'TIME_IFR': ('flight_pilotlog.flight_pilot_time_code_ifr', 60.0),       # IFR Time (Simulated or Actual)
            'TIME_HOOD': ('flight_pilotlog.flight_pilot_time_code_hood', 60.0),     # Simulated Instrument (Hood)
            'TIME_ACTUAL': ('flight_pilotlog.flight_pilot_time_code_actual', 60.0),  # Actual Instrument (IMC)
            'TIME_RELIEF': ('flight_pilotlog.flight_pilot_time_code_relief', 60.0),  # Relief Pilot Time
            'TIME_AIR': ('flight_pilotlog.flight_pilot_time_code_air', 60.0),       # Airborne Time
            # Add other TIME_* fields if needed and corresponding codes exist in Odoo
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

                # Pilot Identification (Replace with your logic)
                # pilot1_id_csv = row[header_map.get('PILOT1_ID')] if 'PILOT1_ID' in header_map else 'UNKNOWN'
                # if pilot1_id_csv == 'SELF':
                #     partner_xml_id = 'base.partner_user_{}'.format(self.env.user.id) # Example for current user
                # else: # Look up partner by ID or Name, fallback to default
                partner_xml_id = DEFAULT_PARTNER_XMLID

                # Remarks
                remark_idx = header_map.get('REMARKS')
                if remark_idx is not None and remark_idx < len(row) and row[remark_idx]:
                    remark_text = str(row[remark_idx]).strip()
                    if remark_text:
                        remarks_data.append({
                            'id': f"remark_{flight_id}_0",
                            'partner_id': partner_xml_id,
                            'remark': remark_text
                        })

                # Times
                time_counter = 0
                for csv_col, (odoo_code_xmlid, divisor) in TIME_CODE_MAPPING.items():
                    col_idx = header_map.get(csv_col)
                    if col_idx is not None and col_idx < len(row) and row[col_idx]:
                        try:
                            duration_minutes = float(row[col_idx])
                            if duration_minutes > 0:
                                duration_hours = round(duration_minutes / divisor, 4) # Use 4 decimal places for precision
                                times_data.append({
                                    'id': f"time_{flight_id}_{time_counter}",
                                    'partner_id': partner_xml_id,
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
                                    'partner_id': partner_xml_id,
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