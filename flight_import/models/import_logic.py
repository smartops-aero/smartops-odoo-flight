import csv
import io
import base64
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class FlightDataImporter(models.AbstractModel):
    _name = "flight.data.importer"
    _description = "Flight Data Importer"

    @api.model
    def import_csv_data(self, file_content, config_id):
        """
        Import CSV data using the specified configuration
        
        :param file_content: CSV file content (base64 encoded)
        :param config_id: ID of import configuration to use
        :return: Import statistics
        """
        config = self.env["flight.import.config"].browse(config_id)
        if not config:
            raise UserError(_("Import configuration not found"))
            
        # Decode file content
        try:
            csv_data = base64.b64decode(file_content).decode("utf-8")
        except Exception as e:
            raise UserError(_("Could not decode file content: %s") % str(e))
            
        # Parse CSV
        try:
            csv_file = io.StringIO(csv_data)
            reader = csv.reader(csv_file, delimiter=config.csv_delimiter or ",", quotechar=config.csv_quotechar or '"')
            
            # Get headers
            if config.csv_has_header:
                headers = next(reader)
            else:
                # If no headers, create dummy headers (column1, column2, etc.)
                first_row = next(reader)
                headers = [f"column{i+1}" for i in range(len(first_row))]
                # Reset the reader to include the first row
                csv_file.seek(0)
                reader = csv.reader(csv_file, delimiter=config.csv_delimiter or ",", quotechar=config.csv_quotechar or '"')
                if config.csv_has_header:
                    next(reader)  # Skip header row again
            
            # Convert rows to dictionaries
            rows = []
            for row in reader:
                # Skip empty rows
                if not any(cell.strip() for cell in row):
                    continue
                    
                # Convert to dictionary
                row_dict = {}
                for i, value in enumerate(row):
                    if i < len(headers):
                        row_dict[headers[i]] = value.strip()
                rows.append(row_dict)
                
            # Perform the import
            return self._import_data_rows(rows, config)
        except Exception as e:
            _logger.exception("Error importing CSV data")
            raise UserError(_("Error importing CSV data: %s") % str(e))

    @api.model
    def _import_data_rows(self, rows, config):
        """
        Import data rows using the specified configuration
        
        :param rows: List of dictionaries with data
        :param config: Import configuration
        :return: Import statistics
        """
        # Initialize tracking dictionaries and statistics
        created_records = {}
        stats = {
            "processed": 0,
            "created": {},
            "updated": {},
            "errors": []
        }
        
        # Get utility model for transformations
        utils = self.env["flight.import.utils"]
        
        # Get ordered model mappings
        model_mappings = config.model_mappings.sorted("sequence")
        
        # Process each row
        for row_idx, row in enumerate(rows, 1):
            try:
                # Process each model in sequence
                flight = False
                
                for mapping in model_mappings:
                    record = self._process_model_mapping(mapping, row, created_records, utils)
                    
                    # If this is a flight record, save it for later use
                    if mapping.target_model == "flight.flight" and record:
                        flight = record
                
                if flight:
                    # Get pilot
                    pilot = utils.get_pilot_from_row(row, config)
                    
                    if pilot:
                        # Create pilot times
                        self._create_pilot_times(flight, row, config.time_mappings, pilot, utils)
                        
                        # Create pilot events
                        self._create_pilot_events(flight, row, config.event_mappings, pilot, utils)
                        
                        # Create remark if present
                        if config.remark_field and row.get(config.remark_field):
                            self._create_pilot_remark(flight, row[config.remark_field], pilot)
                    else:
                        stats['errors'].append({
                            'row': row_idx,
                            'error': "No pilot found for this row and no default pilot configured"
                        })
                
                stats["processed"] += 1
            except Exception as e:
                _logger.exception(f"Error processing row {row_idx}")
                stats["errors"].append({
                    "row": row_idx,
                    "error": str(e)
                })
        
        # Compile statistics
        for model, records in created_records.items():
            model_name = model.split(".")[-1]
            stats["created"][model_name] = len([r for r in records.values() if r.get("created")])
            stats["updated"][model_name] = len([r for r in records.values() if not r.get("created")])
        
        return stats

    @api.model
    def _process_model_mapping(self, mapping, row, created_records, utils):
        """
        Process a single model mapping for a data row
        
        :param mapping: Model mapping configuration
        :param row: Data row
        :param created_records: Dictionary of already created records
        :param utils: Utility model for transformations
        :return: Created or updated record
        """
        # Check if required fields are missing
        missing_required = False
        for fm in mapping.field_mappings:
            if fm.required and not row.get(fm.source_field):
                missing_required = True
                break
                
        if missing_required and mapping.skip_if_required_missing:
            return False
            
        # Build lookup domain
        lookup_fields = mapping.lookup_fields.split(",") if mapping.lookup_fields else []
        domain = []
        
        for field in lookup_fields:
            field = field.strip()
            mapping_entry = self.env["flight.import.field.mapping"].search([
                ("model_mapping_id", "=", mapping.id),
                ("target_field", "=", field)
            ], limit=1)
            
            if mapping_entry and row.get(mapping_entry.source_field):
                source_value = row[mapping_entry.source_field]
                
                # Apply transformation if needed
                if mapping_entry.transform:
                    transform = self.env["flight.import.transform.method"].search([
                        ("config_id", "=", mapping.config_id.id),
                        ("name", "=", mapping_entry.transform)
                    ], limit=1)
                    
                    if transform:
                        method_parts = transform.method.split(".")
                        if len(method_parts) == 2:
                            model_name, method_name = method_parts
                            source_value = getattr(utils, method_name)(source_value)
                
                # Handle relation fields
                if mapping_entry.relation and mapping_entry.relation_field:
                    relation_record = created_records.get(mapping_entry.relation, {}).get(source_value)
                    if relation_record:
                        domain.append((field, "=", relation_record["record"].id))
                else:
                    domain.append((field, "=", source_value))
            
        # Look for existing record
        record = False
        if domain:
            record = self.env[mapping.target_model].search(domain, limit=1)
        
        # Build values for create/update
        values = {}
        
        for fm in mapping.field_mappings:
            source_value = row.get(fm.source_field)
            
            # Use default value if source is empty
            if not source_value and fm.default_value:
                source_value = fm.default_value
                
            if source_value or fm.default_value:
                # Apply transformation if needed
                if fm.transform:
                    _logger.info(f"Applying transformation {fm.transform} to value {source_value}")
                    transform = self.env["flight.import.transform.method"].search([
                        ("config_id", "=", mapping.config_id.id),
                        ("name", "=", fm.transform)
                    ], limit=1)
                    
                    if transform:
                        _logger.info(f"Found transform method: {transform.method}")
                        method_parts = transform.method.split(".")
                        method_name = method_parts.pop()  # Get the last part (method name)
                        model_name = ".".join(method_parts)  # Join the rest as the model name
                        try:
                            # This is the important change - we're directly calling the method on the utils object
                            # that was passed to the function, rather than trying to find the model
                            # Use the model name to get the correct model
                            model_obj = self.env[model_name]
                            transformed_value = getattr(model_obj, method_name)(source_value)
                            source_value = transformed_value
                        except Exception as e:
                            _logger.error(f"Error applying transformation: {e}")
                            # Apply fallback
                            if fm.target_field == 'aircraft_category':
                                source_value = 'airplane'  # Hardcoded fallback
                    else:
                        _logger.warning(f"Transform method '{fm.transform}' not found for config_id {mapping.config_id.id}")
                        # Apply a default fallback for known fields
                        if fm.target_field == 'aircraft_category':
                            _logger.info("Applying hardcoded fallback for aircraft_category")
                            if str(source_value).lower() in ['aeroplane', 'airplane']:
                                source_value = 'airplane'
                
                # Handle relation fields
                if fm.relation:
                    relation_value = False
                    
                    if fm.relation_field:
                        # Find related record from cache
                        relation_record = created_records.get(fm.relation, {}).get(source_value)
                        if relation_record:
                            relation_value = relation_record["record"].id
                        else:
                            # Try to find existing record
                            relation_record = self.env[fm.relation].search([(fm.relation_field, "=", source_value)], limit=1)
                            if relation_record:
                                relation_value = relation_record.id
                    
                    if relation_value:
                        values[fm.target_field] = relation_value
                else:
                    values[fm.target_field] = source_value
        
        # Create or update the record
        created = False
        if values:
            if not record:
                record = self.env[mapping.target_model].create(values)
                created = True
            else:
                record.write(values)
            
            # Track the created/updated record
            if mapping.target_model not in created_records:
                created_records[mapping.target_model] = {}
                
            # Use the appropriate key for tracking
            if mapping.source_model == "aerodrome":
                key = row.get("AF_DEP") or row.get("AF_ARR")
            elif mapping.source_model == "aircraft":
                key = row.get("AC_REG")
            elif mapping.source_model == "aircraft_make":
                key = row.get("AC_MAKE")
            elif mapping.source_model == "aircraft_model":
                key = row.get("AC_MODEL")
            else:
                key = f"{mapping.source_model}_{len(created_records[mapping.target_model]) + 1}"
                
            created_records[mapping.target_model][key] = {
                "record": record,
                "created": created
            }
        
        return record

    @api.model
    def _create_pilot_times(self, flight, row, time_mappings, pilot, utils):
        """
        Create pilot time records for the flight
        
        :param flight: Flight record
        :param row: Data row
        :param time_mappings: Time mappings configuration
        :param pilot: Pilot record
        :param utils: Utility model for transformations
        """
        PilotTime = self.env["flight.pilot.time"]
        
        for mapping in time_mappings:
            time_value = row.get(mapping.source_field)
            if not time_value:
                continue
                
            # Convert to float
            time_float = utils.convert_to_float(time_value)
            
            # Skip if zero
            if time_float <= 0:
                continue
                
            # Convert to hours if needed
            if mapping.convert_to_hours and mapping.divisor:
                time_float = time_float / mapping.divisor
                
            # Check for existing record
            existing = PilotTime.search([
                ("flight_id", "=", flight.id),
                ("partner_id", "=", pilot.id),
                ("code_id", "=", mapping.time_code_id.id)
            ], limit=1)
            
            if existing:
                existing.write({"duration": time_float})
            else:
                PilotTime.create({
                    "flight_id": flight.id,
                    "partner_id": pilot.id,
                    "code_id": mapping.time_code_id.id,
                    "duration": time_float
                })

    @api.model
    def _create_pilot_events(self, flight, row, event_mappings, pilot, utils):
        """
        Create pilot event records for the flight
        
        :param flight: Flight record
        :param row: Data row
        :param event_mappings: Event mappings configuration
        :param pilot: Pilot record
        :param utils: Utility model for transformations
        """
        PilotEvent = self.env["flight.pilot.event"]
        
        for mapping in event_mappings:
            event_value = row.get(mapping.source_field)
            if not event_value:
                continue
                
            # Convert to integer
            try:
                count = int(event_value)
            except (ValueError, TypeError):
                count = 0
                
            # Skip if zero
            if count <= 0:
                continue
                
            # Check for existing record
            existing = PilotEvent.search([
                ("flight_id", "=", flight.id),
                ("partner_id", "=", pilot.id),
                ("event_code_id", "=", mapping.event_code_id.id)
            ], limit=1)
            
            # Parse datetime for the event
            datetime_val = utils.parse_datetime(
                row.get("PILOTLOG_DATE"),
                row.get("TIME_DEP") or row.get("TIME_TO")
            )
            
            if existing:
                existing.write({
                    "count": count,
                    "datetime": datetime_val
                })
            else:
                PilotEvent.create({
                    "flight_id": flight.id,
                    "partner_id": pilot.id,
                    "event_code_id": mapping.event_code_id.id,
                    "count": count,
                    "datetime": datetime_val
                })

    @api.model
    def _create_pilot_remark(self, flight, remark, pilot):
        """
        Create pilot remark record for the flight
        
        :param flight: Flight record
        :param remark: Remark text
        :param pilot: Pilot record
        """
        PilotRemark = self.env["flight.pilot.remark"]
        
        # Check for existing record
        existing = PilotRemark.search([
            ("flight_id", "=", flight.id),
            ("partner_id", "=", pilot.id)
        ], limit=1)
        
        if existing:
            existing.write({"remark": remark})
        else:
            PilotRemark.create({
                "flight_id": flight.id,
                "partner_id": pilot.id,
                "remark": remark
            })