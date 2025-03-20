import logging

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class BaseImportPipeline(models.Model):
    _inherit = "base.import.pipeline"

    def _selection_implementation(self):
        selection = super()._selection_implementation()
        selection.append(("crewlounge", "Flight Import - CrewLounge"))
        return selection

    def _crewlounge_extract(
        self, file_content, filename=None, csv_delimiter=",", **kwargs
    ):
        """Extract data from CrewLounge CSV file"""
        if not file_content:
            raise UserError(_("No file content provided"))

        # Use the CSV extraction helper method
        return self.env["base.import.pipeline"]._extract_from_csv(
            file_content, filename, delimiter=csv_delimiter
        )

    def _prepare_update_values(self, target_model, record, values):
        """Override to handle special case for flight.event.time model updates
        
        For flight.event.time, we only want to update the time field
        to respect the constraint in the write method
        """
        if target_model == "flight.event.time" and "time" in values:
            # Only keep the time field for flight.event.time model
            return {"time": values["time"]}
        
        # For all other models, use the standard implementation
        return super()._prepare_update_values(target_model, record, values)

    def _bulk_update_post_process_records(self, target_model, update_groups, post_result):
        """Override to handle special case for flight.event.time model
        
        The flight.event.time model's write method requires a singleton record
        when comparing the current time with new time. We need to process each
        record individually for this model.
        """
        if target_model == "flight.event.time":
            # Process flight.event.time records one by one
            for group_info in update_groups.values():
                if group_info["records"]:
                    try:
                        # Update each record individually
                        for record in group_info["records"]:
                            record.write(group_info["values"])
                            post_result["post_updated"].append(record.id)
                    except Exception as e:
                        error_msg = f"Error updating {target_model} records: {str(e)}"
                        post_result["post_errors"].append(error_msg)
                        _logger.error(error_msg)
                        _logger.error("Stack trace: %s", traceback.format_exc())
        else:
            # For all other models, use the standard bulk implementation
            super()._bulk_update_post_process_records(target_model, update_groups, post_result)


class BaseImportPipelineMapping(models.Model):
    _inherit = "base.import.pipeline.mapping"

    def _selection_transformation(self):
        selection = super()._selection_transformation()
        selection.append(
            ("crewlounge_engine_type_mapping", "Crewlounge Engine Type Mapping")
        )
        selection.append(
            ("crewlounge_equipment_type_mapping", "Crewlounge Equipment Type Mapping")
        )
        selection.append(
            ("crewlounge_aircraft_class_mapping", "Crewlounge Aircraft Class Mapping")
        )
        selection.append(
            ("crewlounge_gear_type_mapping", "Crewlounge Gear Type Mapping")
        )
        selection.append(
            ("crewlounge_aircraft_tags_mapping", "Crewlounge Aircraft Tags Mapping")
        )
        selection.append(
            ("crewlounge_flight_event_time", "Crewlounge Flight Event Time")
        )
        return selection

    def _transform_crewlounge_engine_type_mapping(self, value):
        """Map engine type values from CrewLounge format to Odoo format"""
        if not value:
            return value

        # Normalize the input by converting to lowercase and removing extra spaces
        normalized_value = value.lower().strip()

        # Define mapping from source values to target values
        engine_type_map = {
            "piston": "piston",
            "turbine (jet-fan)": "turbofan",
            "turbine (prop-shaft)": "turboprop",
            "unpowered": "non_powered",
        }

        # Try exact match first
        if normalized_value in engine_type_map:
            return engine_type_map[normalized_value]

        # If not found, try partial matches
        for src, target in engine_type_map.items():
            if src in normalized_value:
                return target

        # For more complex cases
        if "jet" in normalized_value or "fan" in normalized_value:
            return "turbofan"
        elif "prop" in normalized_value:
            return "turboprop"
        elif "diesel" in normalized_value:
            return "diesel"
        elif "electric" in normalized_value:
            return "electric"
        elif "radial" in normalized_value:
            return "radial"
        elif "turbojet" in normalized_value:
            return "turbojet"
        elif "turboshaft" in normalized_value:
            return "turboshaft"

        # Log warning for unrecognized values
        _logger.warning("Unrecognized engine type: %s", value)

        # Return default if available, otherwise return None
        return self.default_value if self.default_value else None

    def _transform_crewlounge_equipment_type_mapping(self, value):
        """Map equipment type based on AC_ISSIM field (TRUE/FALSE)

        If AC_ISSIM is TRUE, it's a simulator (FFS)
        If AC_ISSIM is FALSE, it's an aircraft
        """
        if not value:
            return "aircraft"  # Default to aircraft if no value

        # Normalize the value
        normalized_value = str(value).strip().upper()

        # Map based on TRUE/FALSE
        if normalized_value == "TRUE":
            return "ffs"  # Full Flight Simulator
        else:
            return "aircraft"  # Default to aircraft for any other value

    def _transform_crewlounge_aircraft_class_mapping(self, value, record):
        """
        Determine aircraft class based on CSV fields:
        - AC_CLASS (Aeroplane, etc.)
        - AC_SPSE (Single Pilot Single Engine)
        - AC_SPME (Single Pilot Multi Engine)
        - AC_GLIDER (Glider)
        - AC_SEA (Seaplane)
        - AC_ENGINES (Single or Multi)

        Maps to appropriate class_id reference from flight.aircraft.class model

        Args:
            value: The value of the source field (if any)
            record: The complete record dictionary with all CSV fields
        """
        if not record:
            return None

        # Default to None if we can't determine
        class_ref = None

        # Get all relevant fields and normalize them
        ac_class = self._get_field_value(record, "AC_CLASS", "").lower().strip()
        ac_spse = self._normalize_boolean(
            self._get_field_value(record, "AC_SPSE", "FALSE")
        )
        ac_spme = self._normalize_boolean(
            self._get_field_value(record, "AC_SPME", "FALSE")
        )
        ac_glider = self._normalize_boolean(
            self._get_field_value(record, "AC_GLIDER", "FALSE")
        )
        ac_sea = self._normalize_boolean(
            self._get_field_value(record, "AC_SEA", "FALSE")
        )
        ac_engines = self._get_field_value(record, "AC_ENGINES", "").lower().strip()

        # Determine class based on fields
        if ac_glider:
            # It's a glider
            class_ref = "flight.class_glider"
        elif "aeroplane" in ac_class or "airplane" in ac_class:
            # It's an airplane, determine which type
            if ac_sea:
                # Seaplane
                if ac_engines == "multi" or ac_spme:
                    class_ref = "flight.class_airplane_mes"  # Multi-Engine Sea
                else:
                    class_ref = "flight.class_airplane_ses"  # Single-Engine Sea
            else:
                # Land plane
                if ac_engines == "multi" or ac_spme:
                    class_ref = "flight.class_airplane_mel"  # Multi-Engine Land
                else:
                    class_ref = "flight.class_airplane_sel"  # Single-Engine Land
        elif "rotorcraft" in ac_class or "helicopter" in ac_class:
            # It's a rotorcraft
            class_ref = "flight.class_rotorcraft_helicopter"
        elif "gyroplane" in ac_class or "gyrocopter" in ac_class:
            class_ref = "flight.class_rotorcraft_gyroplane"
        elif "balloon" in ac_class:
            class_ref = "flight.class_lighter_than_air_balloon"
        elif "airship" in ac_class:
            class_ref = "flight.class_lighter_than_air_airship"
        elif "powered lift" in ac_class:
            class_ref = "flight.class_powered_lift"
        elif "powered parachute" in ac_class:
            class_ref = "flight.class_powered_parachute"
        elif "weight shift" in ac_class:
            class_ref = "flight.class_weight_shift_control"

        # Default for airplanes if nothing else matches
        if not class_ref and (
            "aeroplane" in ac_class or "airplane" in ac_class or ac_class == ""
        ):
            # Default to single engine land if we can't determine specifics
            class_ref = "flight.class_airplane_sel"

        # Log warning if we couldn't determine the class
        if not class_ref:
            _logger.warning("Could not determine aircraft class for record: %s", record)
            return None

        # Convert XML ID to database ID
        try:
            class_id = self.env.ref(class_ref).id
            return class_id
        except Exception as e:
            _logger.error("Failed to resolve XML ID %s: %s", class_ref, e)
            return None

    def _transform_crewlounge_gear_type_mapping(self, value, record):
        """
        Determine aircraft gear type based on CSV fields:
        - AC_SEA (Seaplane)
        - AC_TAILWHEEL (Tailwheel aircraft)
        - AC_COMPLEX (Complex aircraft with retractable landing gear)

        Maps to appropriate gear_type selection option in flight.aircraft model

        Args:
            value: The value of the source field (if any)
            record: The complete record dictionary with all CSV fields
        """
        if not record:
            return None

        # Get all relevant fields and normalize them as booleans
        ac_sea = self._normalize_boolean(
            self._get_field_value(record, "AC_SEA", "FALSE")
        )
        ac_tailwheel = self._normalize_boolean(
            self._get_field_value(record, "AC_TAILWHEEL", "FALSE")
        )
        ac_complex = self._normalize_boolean(
            self._get_field_value(record, "AC_COMPLEX", "FALSE")
        )

        # Determine gear type based on fields using the logic provided
        if ac_sea:
            return "floats"
        elif ac_tailwheel and not ac_complex:
            return "fixed_tailwheel"
        elif ac_tailwheel and ac_complex:
            return "retractable_tailwheel"
        elif not ac_tailwheel and not ac_complex:
            return "fixed_tricycle"
        elif not ac_tailwheel and ac_complex:
            return "retractable_tricycle"

        # Default if we can't determine
        _logger.warning("Could not determine gear type for record: %s", record)
        return None

    def _transform_crewlounge_aircraft_tags_mapping(self, value, record):
        """
        Map boolean CSV fields to aircraft model tags.

        Currently maps:
        - AC_COMPLEX to 'Complex' tag
        - AC_HIGHPERF to 'High Performance' tag

        Args:
            value: The value of the source field (if any)
            record: The complete record dictionary with all CSV fields

        Returns:
            A list of tag IDs based on the boolean fields in the record
        """
        if not record:
            return False

        # Initialize empty tag list
        tag_ids = []

        # Check for Complex tag
        if self._normalize_boolean(
            self._get_field_value(record, "AC_COMPLEX", "FALSE")
        ):
            try:
                complex_tag = self.env.ref("flight.flight_aircraft_model_tag_complex")
                if complex_tag:
                    tag_ids.append(complex_tag.id)
            except Exception as e:
                _logger.error("Failed to resolve Complex tag: %s", e)

        # Check for High Performance tag
        if self._normalize_boolean(
            self._get_field_value(record, "AC_HIGHPERF", "FALSE")
        ):
            try:
                highperf_tag = self.env.ref(
                    "flight.flight_aircraft_model_tag_high_performance"
                )
                if highperf_tag:
                    tag_ids.append(highperf_tag.id)
            except Exception as e:
                _logger.error("Failed to resolve High Performance tag: %s", e)

        # Check for Pressurized tag (if such a field exists)
        if self._normalize_boolean(
            self._get_field_value(record, "AC_PRESSURIZED", "FALSE")
        ):
            try:
                pressurized_tag = self.env.ref(
                    "flight.flight_aircraft_model_tag_pressurized"
                )
                if pressurized_tag:
                    tag_ids.append(pressurized_tag.id)
            except Exception as e:
                _logger.error("Failed to resolve Pressurized tag: %s", e)

        # Return tag_ids as a command for many2many field
        # If tag_ids is empty, return False to not update the field
        return [(6, 0, tag_ids)] if tag_ids else False

    def _transform_crewlounge_flight_event_time(self, value, record=None):
        """Convert HH:MM time value to datetime by combining with flight date

        This transformation is specifically for flight event times. It:
        1. Gets the flight record from the post-processing context
        2. Takes the date from the flight record
        3. Combines it with the time value (HH:MM) from the source field

        Args:
            value: The time value (HH:MM)
            record: The complete record dictionary

        Returns:
            datetime object or False if conversion fails
        """
        if not value:
            return False

        try:
            # Get the flight record from context (in post-processing)
            flight_id = self.env.context.get("parent_record_id")
            if not flight_id:
                _logger.error(
                    "No flight_id found in context for flight_event_time transformation"
                )
                return False

            # Get the flight record
            flight = self.env["flight.flight"].browse(flight_id)
            if not flight or not flight.date:
                _logger.error(
                    "No flight record or date found for flight_id: %s", flight_id
                )
                return False

            # Get the flight date
            flight_date = flight.date

            # Parse the time string (HH:MM)
            time_str = value.strip()
            if not time_str:
                return False

            # Split hours and minutes
            time_parts = time_str.split(":")
            if len(time_parts) != 2:
                _logger.error("Invalid time format: %s", time_str)
                return False

            hours = int(time_parts[0])
            minutes = int(time_parts[1])

            # Combine flight date and time
            from datetime import datetime

            dt = datetime.combine(
                flight_date, datetime.min.time().replace(hour=hours, minute=minutes)
            )
            return dt
        except Exception as e:
            _logger.error("Error in flight_event_time transformation: %s", e)
            return False

    def _get_field_value(self, record, field_name, default=""):
        """Helper method to safely get field value from record"""
        return record.get(field_name, default)

    def _normalize_boolean(self, value):
        """Convert string boolean values to actual boolean"""
        if isinstance(value, bool):
            return value

        normalized = str(value).strip().upper()
        return normalized == "TRUE" or normalized == "1" or normalized == "YES"

    def _get_or_create_record(self, model_name, domain, values, mapping=None):
        """Override to handle special case for flight.event.time updating"""
        # Special handling for flight.event.time model - only update the time field
        if model_name == "flight.event.time" and domain:
            record = self.env[model_name].search(domain, limit=1)
            if record and "time" in values:
                # Only update the time field for existing flight.event.time records
                # This respects the constraint in the write method
                time_value = values.get("time")
                if time_value:
                    record.write({"time": time_value})
                return record

        # For all other cases, use the standard implementation
        return super()._get_or_create_record(model_name, domain, values, mapping)
