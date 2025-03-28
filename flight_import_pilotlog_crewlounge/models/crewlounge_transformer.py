import logging
from datetime import datetime
# Removed typing imports as they are not used without hints
# from typing import List, Dict, Any, Tuple, Optional, Set

from odoo import api, models, fields
from odoo.tools import float_round

_logger = logging.getLogger(__name__)

# --- Constants for CrewLounge Import ---

# Mapping from CrewLounge CSV headers (uppercase) to Odoo XML IDs for Time Codes
CREWLOUNGE_TIME_CODE_MAPPING = {
    "TIME_TOTAL": "flight_pilotlog.flight_pilot_time_code_total",
    "TIME_PIC": "flight_pilotlog.flight_pilot_time_code_pic",
    "TIME_SIC": "flight_pilotlog.flight_pilot_time_code_sic",
    "TIME_DUAL": "flight_pilotlog.flight_pilot_time_code_dual",
    "TIME_PICUS": "flight_pilotlog.flight_pilot_time_code_picus",
    "TIME_INSTRUCTOR": "flight_pilotlog.flight_pilot_time_code_instructor",
    "TIME_EXAMINER": "flight_pilotlog.flight_pilot_time_code_examiner",
    "TIME_NIGHT": "flight_pilotlog.flight_pilot_time_code_night",
    "TIME_XC": "flight_pilotlog.flight_pilot_time_code_xc",
    "TIME_IFR": "flight_pilotlog.flight_pilot_time_code_ifr",
    "TIME_HOOD": "flight_pilotlog.flight_pilot_time_code_hood",
    "TIME_ACTUAL": "flight_pilotlog.flight_pilot_time_code_actual",
    "TIME_RELIEF": "flight_pilotlog.flight_pilot_time_code_relief",
    "TIME_AIR": "flight_pilotlog.flight_pilot_time_code_air",
}

# CrewLounge CSV headers (uppercase) that require special time format parsing (HH:MM)
CREWLOUNGE_TIME_HHMM_FORMAT_HEADERS = {"TIME_AIR"}

# Mapping from CrewLounge CSV headers (uppercase) to Odoo XML IDs for Event Codes
CREWLOUNGE_EVENT_CODE_MAPPING = {
    "TO_DAY": "flight_pilotlog.flight_pilot_event_code_to_day",
    "TO_NIGHT": "flight_pilotlog.flight_pilot_event_code_to_night",
    "LDG_DAY": "flight_pilotlog.flight_pilot_event_code_ldg_day",
    "LDG_NIGHT": "flight_pilotlog.flight_pilot_event_code_ldg_night",
    "LIFT": "flight_pilotlog.flight_pilot_event_code_lift",
    "HOLDING": "flight_pilotlog.flight_pilot_event_code_holding",
}

# Headers for the transformed flight.flight data structure expected by Odoo import
FLIGHT_TRANSFORMED_HEADERS = [
    "id", "date", "aircraft_id", "departure_id",
    "arrival_id", "remark_ids/id", "remark_ids/partner_id/.id",
    "remark_ids/remark", "pilot_time_ids/id", "pilot_time_ids/partner_id/.id",
    "pilot_time_ids/code_id/id", "pilot_time_ids/duration",
    "pilot_event_ids/id", "pilot_event_ids/partner_id/.id",
    "pilot_event_ids/event_code_id/id", "pilot_event_ids/count",
]

# Headers for the transformed flight.aircraft data structure
AIRCRAFT_TRANSFORMED_HEADERS = ["id", "registration", "operator_id", "model_id"]

# Headers for the transformed flight.aircraft.make data structure
MAKE_TRANSFORMED_HEADERS = ["id", "name"]

# Headers for the transformed flight.aircraft.model data structure
MODEL_TRANSFORMED_HEADERS = [
    "id", "name", "make_id", "class_id", "engine_type", "gear_type"
]

# Mapping for Aircraft Model Engine Types
ENGINE_TYPE_MAPPING = {
    "Piston": "piston",
    "Turboprop": "turboprop",
    "Turbofan": "turbofan",
    "Turbojet": "turbojet",
    "Turboshaft": "turboshaft",
    "Electric": "electric",
}

# Mapping for Aircraft Class IDs to potential Display Names (for lookup)
# Using display names as CrewLounge doesn't provide Odoo class IDs directly
CLASS_DISPLAY_NAMES = {
    "class_airplane_mes": "Multi-Engine Sea",
    "class_airplane_mel": "Multi-Engine Land",
    "class_airplane_ses": "Single-Engine Sea",
    "class_airplane_sel": "Single-Engine Land",
    "class_rotorcraft_helicopter": "Helicopter",
    "class_rotorcraft_gyroplane": "Gyroplane",
    "class_glider": "Glider",
    "class_lighter_than_air_balloon": "Balloon",
    "class_lighter_than_air_airship": "Airship",
    "class_powered_lift": "Powered Lift",
    "class_powered_parachute": "Powered Parachute",
    "class_weight_shift_control": "Weight Shift Control",
}

# --- Helper Functions (Internal) ---

def _build_header_map(headers):
    """Creates a mapping from uppercase header names to their column index."""
    header_map = {col.upper(): idx for idx, col in enumerate(headers)}
    _logger.debug("Built header map: %s", header_map)
    return header_map

def _should_skip_row(
    idx,
    row,
    headers,
    min_cols_needed,
    is_header_present_in_data=True,
):
    """Checks if a row should be skipped (header, empty, insufficient columns)."""
    # Skip header row if present in data_rows
    if is_header_present_in_data and idx == 0 and len(row) == len(headers) and \
       all(str(row[i]).upper() == str(headers[i]).upper() for i in range(len(headers))):
        return True

    # Skip empty rows
    if not row or all(not cell for cell in row):
        return True

    # Skip rows with insufficient columns
    if len(row) < min_cols_needed:
        _logger.warning(
            "Row %d has insufficient columns (%d found, %d expected based on headers), skipping",
            idx + 1, len(row), min_cols_needed
        )
        return True

    return False

def _log_skipped_rows(skipped_rows):
    """Logs a warning if any rows were skipped."""
    if skipped_rows > 0:
        _logger.warning(
            "%d rows were skipped due to errors, missing essential data, or being duplicates. "
            "Please check logs for details.", skipped_rows
        )

def _get_cell_value(row, header_map, header_name):
    """Safely retrieves and strips a cell value from a row using the header map."""
    col_idx = header_map.get(header_name.upper())
    if col_idx is not None and col_idx < len(row) and row[col_idx]:
        return str(row[col_idx]).strip()
    return None

def _parse_boolean_flag(value):
    """Parses common boolean string representations."""
    return value is not None and value.upper() in ("TRUE", "YES", "1")

class FlightImportPIlotlogTransformer(models.Model):
    _inherit = "flight.import.pilotlog.transformer"

    # === Implementation Registration ===

    @api.model
    def _get_available_implementations(self):
        """Add CrewLounge to available implementations."""
        implementations = super()._get_available_implementations()
        return implementations + [("crewlounge", "CrewLounge Format")]

    # === Helper Methods ===

    def _round_duration(self, value, decimals=4):
        """Round duration values consistently."""
        return float_round(value, precision_digits=decimals)

    def _standardize_aircraft_name(self, name):
        """Standardize aircraft name capitalization (Title Case)."""
        return name.title() if name else name

    def _create_full_model_name(self, make_name, model_name, variant=""):
        """Create a standardized full model name from components."""
        parts = []
        if make_name:
            parts.append(self._standardize_aircraft_name(make_name))
        if model_name:
            parts.append(model_name) # Model often contains acronyms, don't title case
        if variant:
            parts.append(variant)
        return " ".join(filter(None, parts)) # Filter ensures no extra spaces if parts are empty

    def _get_partner_ref(self, import_wizard):
        """Determine the partner ID to use for related records."""
        if import_wizard and import_wizard.pilot_id:
            return import_wizard.pilot_id.id
        # Fallback to current user's partner, though wizard context is preferred
        return self.env.user.partner_id.id

    def _parse_crewlounge_date(self, row_idx, date_str):
        """Parses CrewLounge date string (%d-%m-%Y) to Odoo format (%Y-%m-%d)."""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%d-%m-%Y").strftime("%Y-%m-%d")
        except (ValueError, TypeError) as e:
            _logger.warning(
                "Row %d: Failed to parse date '%s': %s. Skipping date.",
                row_idx + 1, date_str, e
            )
            return None

    def _parse_crewlounge_time_duration(self, row_idx, time_value, csv_col):
        """Parses CrewLounge time values (minutes or HH:MM) into duration (hours)."""
        if time_value is None: # Allow zero values if explicitly present, skip if None/empty
            return None

        try:
            if csv_col in CREWLOUNGE_TIME_HHMM_FORMAT_HEADERS:
                # Handle HH:MM format (e.g., "0:12", "1:05")
                if ":" in time_value:
                    hours, minutes = map(float, time_value.split(":", 1))
                    duration_hours = hours + minutes / 60.0
                else:
                    # Fallback: assume it might be minutes if format is wrong
                    _logger.debug("Row %d: Expected HH:MM for %s, got '%s'. Interpreting as minutes.",
                                  row_idx + 1, csv_col, time_value)
                    duration_hours = float(time_value) / 60.0
            else:
                # Standard processing for minute values
                duration_minutes = float(time_value)
                duration_hours = duration_minutes / 60.0

            return self._round_duration(duration_hours) if duration_hours > 0 else None

        except (ValueError, TypeError) as e:
            _logger.warning(
                "Row %d: Invalid value '%s' for time column '%s': %s. Skipping time entry.",
                row_idx + 1, time_value, csv_col, e
            )
            return None

    def _parse_crewlounge_event_count(self, row_idx, count_value, csv_col):
        """Parses CrewLounge event count values."""
        if count_value is None:
            return None
        try:
            # Use float first for potential decimals like '1.0', then convert to int
            count = int(float(count_value))
            return count if count > 0 else None
        except (ValueError, TypeError) as e:
            _logger.warning(
                "Row %d: Invalid value '%s' for event column '%s': %s. Skipping event entry.",
                row_idx + 1, count_value, csv_col, e
            )
            return None

    # === Flight Transformation Logic ===

    def _extract_basic_flight_data(self, row_idx, row, header_map):
        """Extracts and validates basic flight information (date, reg, dep, arr)."""
        date_str_raw = _get_cell_value(row, header_map, "PILOTLOG_DATE")
        aircraft_reg = _get_cell_value(row, header_map, "AC_REG")
        departure = _get_cell_value(row, header_map, "AF_DEP")
        arrival = _get_cell_value(row, header_map, "AF_ARR")

        date_str = self._parse_crewlounge_date(row_idx, date_str_raw)

        if not date_str or not aircraft_reg or not departure or not arrival:
            _logger.warning(
                "Row %d: Missing essential flight data (Date='%s', Reg='%s', Dep='%s', Arr='%s'). Skipping row.",
                row_idx + 1, date_str_raw, aircraft_reg, departure, arrival
            )
            return None

        return {
            "date": date_str,
            "aircraft_reg": aircraft_reg,
            "departure": departure.upper(),
            "arrival": arrival.upper(),
        }

    def _extract_flight_remarks(self, flight_id, row, header_map, partner_ref):
        """Extracts remarks for the flight."""
        remarks_data = []
        remark_text = _get_cell_value(row, header_map, "REMARKS")
        if remark_text:
            remarks_data.append({
                "id": f"remark_{flight_id}_0", # Only one remark per flight seems intended
                "partner_id": partner_ref,
                "remark": remark_text,
            })
        return remarks_data

    def _extract_flight_pilot_times(self, row_idx, flight_id, row, header_map, partner_ref):
        """Extracts pilot time entries for the flight."""
        times_data = []
        time_counter = 0
        for csv_col, odoo_code_xmlid in CREWLOUNGE_TIME_CODE_MAPPING.items():
            time_value = _get_cell_value(row, header_map, csv_col)
            duration = self._parse_crewlounge_time_duration(row_idx, time_value, csv_col)

            if duration is not None: # Check for None explicitly, 0 duration is valid but we skip it here
                times_data.append({
                    "id": f"time_{flight_id}_{time_counter}",
                    "partner_id": partner_ref,
                    "code_id": odoo_code_xmlid,
                    "duration": duration,
                })
                time_counter += 1
        return times_data

    def _extract_flight_pilot_events(self, row_idx, flight_id, row, header_map, partner_ref):
        """Extracts pilot event entries for the flight."""
        events_data = []
        event_counter = 0
        for csv_col, odoo_code_xmlid in CREWLOUNGE_EVENT_CODE_MAPPING.items():
            count_value = _get_cell_value(row, header_map, csv_col)
            count = self._parse_crewlounge_event_count(row_idx, count_value, csv_col)

            if count is not None: # Check for None explicitly
                events_data.append({
                    "id": f"event_{flight_id}_{event_counter}",
                    "partner_id": partner_ref,
                    "code_id": odoo_code_xmlid,
                    "count": count,
                })
                event_counter += 1
        return events_data

    def _build_flight_output_rows(
        self,
        flight_id,
        basic_data,
        remarks_data,
        times_data,
        events_data,
    ):
        """Constructs the multi-line output rows for a single flight for Odoo import."""
        output_rows = []
        num_remarks = len(remarks_data)
        num_times = len(times_data)
        num_events = len(events_data)
        max_lines = max(1, num_remarks, num_times, num_events)

        # Get the first (and likely only) remark details if they exist
        first_remark = remarks_data[0] if num_remarks > 0 else {}

        for i in range(max_lines):
            # --- Basic Flight Info (Repeated on all lines) ---
            current_flight_id = flight_id
            current_date = basic_data["date"]
            current_aircraft = basic_data["aircraft_reg"]
            current_dep = basic_data["departure"]
            current_arr = basic_data["arrival"]

            # --- Remark Info (Only on the last line as per original logic) ---
            remark_id, remark_partner, remark_text = "", "", ""
            if i == max_lines - 1 and num_remarks > 0: # Check index AND if remarks exist
                remark_id = first_remark.get("id", "")
                remark_partner = first_remark.get("partner_id", "")
                remark_text = first_remark.get("remark", "")

            # --- Time Info (One per line up to num_times) ---
            time_id, time_partner, time_code, time_duration = "", "", "", ""
            if i < num_times:
                time_entry = times_data[i]
                time_id = time_entry.get("id", "")
                time_partner = time_entry.get("partner_id", "")
                time_code = time_entry.get("code_id", "")
                time_duration = time_entry.get("duration", "") # Keep as float/int for now

            # --- Event Info (One per line up to num_events) ---
            event_id, event_partner, event_code, event_count = "", "", "", ""
            if i < num_events:
                event_entry = events_data[i]
                event_id = event_entry.get("id", "")
                event_partner = event_entry.get("partner_id", "")
                event_code = event_entry.get("code_id", "")
                event_count = event_entry.get("count", "") # Keep as int for now

            # --- Assemble Row (Convert numbers to string at the end) ---
            transformed_row = [
                str(current_flight_id), str(current_date), str(current_aircraft),
                str(current_dep), str(current_arr),
                str(remark_id), str(remark_partner), str(remark_text),
                str(time_id), str(time_partner), str(time_code),
                str(time_duration) if time_duration != "" else "", # String conversion
                str(event_id), str(event_partner), str(event_code),
                str(event_count) if event_count != "" else "", # String conversion
            ]
            output_rows.append(transformed_row)

        return output_rows

    def flight_flight_crewlounge_transform_data(
        self, data_rows, headers, import_wizard=None
    ):
        """Transform CrewLounge data to flight.flight format suitable for Odoo import."""
        if not headers:
            _logger.error("No headers provided for transformation. Cannot proceed.")
            return []
        if not data_rows:
            return [FLIGHT_TRANSFORMED_HEADERS] # Return headers even if no data

        header_map = _build_header_map(headers)
        min_cols_needed = max(header_map.values()) + 1 if header_map else 1
        partner_ref = self._get_partner_ref(import_wizard)

        transformed_data = [FLIGHT_TRANSFORMED_HEADERS]
        skipped_rows = 0

        for idx, row in enumerate(data_rows):
            if _should_skip_row(idx, row, headers, min_cols_needed):
                if idx > 0 and (row and any(cell for cell in row)): # Don't count header/empty rows in final warning
                     skipped_rows += 1
                continue

            try:
                flight_id = f"flight_import_{idx:03d}" # Use original index for consistent ID

                # 1. Extract Basic Data
                basic_data = self._extract_basic_flight_data(idx, row, header_map)
                if not basic_data:
                    skipped_rows += 1
                    continue

                # 2. Extract Related Data
                remarks_data = self._extract_flight_remarks(flight_id, row, header_map, partner_ref)
                times_data = self._extract_flight_pilot_times(idx, flight_id, row, header_map, partner_ref)
                events_data = self._extract_flight_pilot_events(idx, flight_id, row, header_map, partner_ref)

                # 3. Build Output Rows
                output_rows = self._build_flight_output_rows(
                    flight_id, basic_data, remarks_data, times_data, events_data
                )
                transformed_data.extend(output_rows)

            except Exception as e:
                _logger.error(
                    "Error processing row %d: %s. Row data: %s. Skipping row.",
                    idx + 1, e, row, exc_info=True
                )
                skipped_rows += 1
                continue

        _log_skipped_rows(skipped_rows)
        return transformed_data

    # === Aircraft Transformation Logic ===

    def flight_aircraft_crewlounge_transform_data(
        self, data_rows, headers, import_wizard=None
    ):
        """Transform CrewLounge data to flight.aircraft format."""
        if not headers:
             _logger.error("No headers provided for aircraft transformation.")
             return []
        if not data_rows:
            return [AIRCRAFT_TRANSFORMED_HEADERS]

        header_map = _build_header_map(headers)
        min_cols_needed = max(header_map.values()) + 1 if header_map else 1

        transformed_data = [AIRCRAFT_TRANSFORMED_HEADERS]
        skipped_rows = 0
        processed_aircraft = set() # Removed type hint Set[str]

        for idx, row in enumerate(data_rows):
            if _should_skip_row(idx, row, headers, min_cols_needed):
                if idx > 0 and (row and any(cell for cell in row)):
                     skipped_rows += 1
                continue

            try:
                # Extract Registration (Mandatory)
                aircraft_reg = _get_cell_value(row, header_map, "AC_REG")
                if not aircraft_reg:
                    _logger.warning("Row %d: Missing aircraft registration. Skipping row.", idx + 1)
                    skipped_rows += 1
                    continue

                # Skip duplicates
                if aircraft_reg in processed_aircraft:
                    continue
                processed_aircraft.add(aircraft_reg)

                # Extract Make/Model/Variant
                make_name = _get_cell_value(row, header_map, "AC_MAKE")
                model_name = _get_cell_value(row, header_map, "AC_MODEL")
                variant = _get_cell_value(row, header_map, "AC_VARIANT")
                full_model_name = self._create_full_model_name(make_name, model_name, variant)

                # Extract Operator
                operator_name = _get_cell_value(row, header_map, "OPERATOR")

                # Create ID and row
                aircraft_id = f"aircraft_import_{aircraft_reg.replace('-', '_').lower()}"
                transformed_row = [
                    aircraft_id,
                    aircraft_reg,
                    operator_name or "", # Use name for lookup, ensure string
                    full_model_name or "", # Use name for lookup, ensure string
                ]
                transformed_data.append(transformed_row)

            except Exception as e:
                _logger.error("Error processing aircraft row %d: %s. Row data: %s. Skipping row.", idx + 1, e, row, exc_info=True)
                skipped_rows += 1
                continue

        _log_skipped_rows(skipped_rows)
        return transformed_data

    # === Aircraft Make Transformation Logic ===

    def flight_aircraft_make_crewlounge_transform_data(
        self, data_rows, headers, import_wizard=None
    ):
        """Transform CrewLounge data to flight.aircraft.make format (unique makes)."""
        if not headers:
             _logger.error("No headers provided for make transformation.")
             return []
        if not data_rows:
            return [MAKE_TRANSFORMED_HEADERS]

        header_map = _build_header_map(headers)
        min_cols_needed = header_map.get('AC_MAKE', -1) + 1 if 'AC_MAKE' in header_map else 1

        transformed_data = [MAKE_TRANSFORMED_HEADERS]
        processed_makes = set() # Removed type hint Set[str]

        for idx, row in enumerate(data_rows):
            # Simplified skip check as we only care about AC_MAKE
            if idx == 0 and len(row) == len(headers): continue # Skip header
            if not row or all(not cell for cell in row): continue # Skip empty
            if len(row) < min_cols_needed: continue # Skip short rows

            try:
                make_name_raw = _get_cell_value(row, header_map, "AC_MAKE")
                if not make_name_raw:
                    continue

                make_name = self._standardize_aircraft_name(make_name_raw) or "" # Ensure string

                if not make_name or make_name in processed_makes:
                    continue
                processed_makes.add(make_name)

                make_id = f"make_{make_name.lower().replace(' ', '_').replace('-', '_')}"
                transformed_data.append([make_id, make_name])

            except Exception as e:
                _logger.error("Error processing make in row %d: %s", idx + 1, e)
                # Don't increment skipped_rows here as it's just extracting unique values
                continue

        # No skipped row log here, as we intentionally skip duplicates/blanks
        return transformed_data

    # === Aircraft Model Transformation Logic ===

    def _determine_aircraft_class_name(self, row, header_map):
        """Determine aircraft class display name based on engine count and sea capability."""
        engine_count_str = _get_cell_value(row, header_map, "AC_ENGINES")
        is_multi_engine = engine_count_str is not None and engine_count_str.lower() == "multi"

        is_seaplane = _parse_boolean_flag(_get_cell_value(row, header_map, "AC_SEA"))

        # Basic Airplane Class determination (extend if more types are needed)
        if is_multi_engine and is_seaplane:
            return CLASS_DISPLAY_NAMES.get("class_airplane_mes", "")
        elif is_multi_engine:
            return CLASS_DISPLAY_NAMES.get("class_airplane_mel", "")
        elif is_seaplane:
            return CLASS_DISPLAY_NAMES.get("class_airplane_ses", "")
        elif engine_count_str is not None: # If engine count provided, assume SEL if not multi/sea
             return CLASS_DISPLAY_NAMES.get("class_airplane_sel", "")
        else: # Cannot determine class if engine count is missing
            return ""

    def _determine_aircraft_gear_type(self, row, header_map):
        """Determine aircraft gear type based on tailwheel flag."""
        is_tailwheel = _parse_boolean_flag(_get_cell_value(row, header_map, "AC_TAILWHEEL"))
        # Crewlounge doesn't explicitly state fixed/retract, default to fixed variants
        if is_tailwheel is not None: # Only set if tailwheel info is present
            return "fixed_tailwheel" if is_tailwheel else "fixed_tricycle"
        return ""

    def flight_aircraft_model_crewlounge_transform_data(
        self, data_rows, headers, import_wizard=None
    ):
        """Transform CrewLounge data to flight.aircraft.model format (unique models)."""
        if not headers:
             _logger.error("No headers provided for model transformation.")
             return []
        if not data_rows:
            return [MODEL_TRANSFORMED_HEADERS]

        header_map = _build_header_map(headers)
        # Determine min cols based on needed headers (Make, Model at least)
        min_cols_needed = 0
        for hdr in ["AC_MAKE", "AC_MODEL"]:
             min_cols_needed = max(min_cols_needed, header_map.get(hdr, -1) + 1)
        if min_cols_needed == 0: min_cols_needed = 1 # At least 1 col needed

        transformed_data = [MODEL_TRANSFORMED_HEADERS]
        processed_models = set() # Removed type hint Set[str]

        for idx, row in enumerate(data_rows):
            # Skip header, empty, short rows
            if _should_skip_row(idx, row, headers, min_cols_needed):
                continue

            try:
                # Extract make, model, variant
                make_name_raw = _get_cell_value(row, header_map, "AC_MAKE")
                model_name = _get_cell_value(row, header_map, "AC_MODEL")
                variant = _get_cell_value(row, header_map, "AC_VARIANT")

                # Standardize Make name for consistency
                make_name = self._standardize_aircraft_name(make_name_raw)

                full_model_name = self._create_full_model_name(make_name, model_name, variant)

                # Skip if model name is empty or already processed
                if not full_model_name or full_model_name in processed_models:
                    continue
                processed_models.add(full_model_name)

                # Create Model ID
                model_id_parts = []
                if make_name: model_id_parts.append(make_name.lower().replace(' ', '_').replace('-', '_'))
                if model_name: model_id_parts.append(model_name.lower().replace(' ', '_').replace('-', '_'))
                if variant: model_id_parts.append(variant.lower().replace(' ', '_').replace('-', '_')) # Add variant for uniqueness
                model_id = f"model_{'_'.join(filter(None, model_id_parts))}"
                if not model_id_parts: model_id = f"model_import_{idx}" # Fallback ID

                # Determine related fields
                class_name = self._determine_aircraft_class_name(row, header_map)
                gear_type = self._determine_aircraft_gear_type(row, header_map)

                # Engine Type
                engine_type_raw = _get_cell_value(row, header_map, "AC_ENGTYPE")
                engine_type = ENGINE_TYPE_MAPPING.get(engine_type_raw, "") if engine_type_raw else ""

                # Assemble row for import (using names for lookups)
                transformed_row = [
                    model_id,
                    full_model_name,
                    make_name or "",        # make_id (by name)
                    class_name or "",       # class_id (by name)
                    engine_type or "",      # engine_type (selection value)
                    gear_type or "",        # gear_type (selection value)
                ]
                transformed_data.append(transformed_row)

            except Exception as e:
                _logger.error("Error processing model in row %d: %s", idx + 1, e)
                # Don't increment skipped_rows here
                continue

        # No skipped row log here
        return transformed_data