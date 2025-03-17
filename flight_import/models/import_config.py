
# flight_import/models/import_config.py
from odoo import api, fields, models


class FlightImportConfig(models.Model):
    _name = "flight.import.config"
    _description = "Flight Import Configuration"

    name = fields.Char(required=True)
    description = fields.Text()
    active = fields.Boolean(default=True)
    
    # Model mappings for creating/finding records
    model_mappings = fields.One2many(
        "flight.import.model.mapping", "config_id", string="Model Mappings"
    )
    
    # Mappings for pilot times
    time_mappings = fields.One2many(
        "flight.import.time.mapping", "config_id", string="Pilot Time Mappings"
    )
    
    # Mappings for pilot events
    event_mappings = fields.One2many(
        "flight.import.event.mapping", "config_id", string="Pilot Event Mappings"
    )
    
    # Field to use for remarks
    remark_field = fields.Char(string="Remarks Field")
    
    # Transformation methods
    transform_methods = fields.One2many(
        "flight.import.transform.method", "config_id", string="Transform Methods"
    )
    
    # Default pilot to use if not specified in import
    default_pilot_id = fields.Many2one("res.partner", string="Default Pilot")
    
    # CSV configuration
    csv_has_header = fields.Boolean(string="CSV Has Header", default=True)
    csv_delimiter = fields.Char(string="CSV Delimiter", default=",")
    csv_quotechar = fields.Char(string="CSV Quote Character", default='"')
    
    # Date format for parsing
    date_format = fields.Char(string="Date Format", default="%d-%m-%Y")


class FlightImportModelMapping(models.Model):
    _name = "flight.import.model.mapping"
    _description = "Flight Import Model Mapping"
    _order = "sequence, id"

    config_id = fields.Many2one("flight.import.config", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    
    source_model = fields.Char(required=True, help="Logical name of the source model (e.g. 'aircraft')")
    target_model = fields.Char(required=True, help="Technical name of the Odoo model (e.g. 'flight.aircraft')")
    
    # Field mappings for this model
    field_mappings = fields.One2many(
        "flight.import.field.mapping", "model_mapping_id", string="Field Mappings"
    )
    
    # Field(s) to use for looking up existing records
    lookup_fields = fields.Char(
        help="Comma-separated list of fields to use when looking up existing records"
    )
    
    # Whether to skip this model if a required field is missing
    skip_if_required_missing = fields.Boolean(
        default=True, help="Skip creating this model if a required field is missing"
    )
    
    def action_view_field_mappings(self):
        """Open the field mappings form for this model mapping"""
        self.ensure_one()
        return {
            "name": f"Field Mappings for {self.source_model}",
            "type": "ir.actions.act_window",
            "res_model": "flight.import.field.mapping",
            "view_mode": "tree",
            "domain": [("model_mapping_id", "=", self.id)],
            "context": {"default_model_mapping_id": self.id},
            "target": "current",
        }


class FlightImportFieldMapping(models.Model):
    _name = "flight.import.field.mapping"
    _description = "Flight Import Field Mapping"
    _order = "sequence, id"

    model_mapping_id = fields.Many2one(
        "flight.import.model.mapping", required=True, ondelete="cascade"
    )
    sequence = fields.Integer(default=10)
    
    source_field = fields.Char(required=True, help="Field name in the imported data")
    target_field = fields.Char(required=True, help="Field name in the Odoo model")
    
    # Whether this field is required
    required = fields.Boolean(default=False)
    
    # For relational fields
    relation = fields.Char(help="Technical name of the related model (e.g. 'flight.aircraft.make')")
    relation_field = fields.Char(help="Field name in the related model for lookup")
    
    # Transformation method to apply to the field value
    transform = fields.Char(help="Name of the transformation method to apply")
    
    # Default value if source field is empty
    default_value = fields.Char(help="Default value if source field is empty")


class FlightImportTimeMapping(models.Model):
    _name = "flight.import.time.mapping"
    _description = "Flight Import Pilot Time Mapping"
    _order = "sequence, id"

    config_id = fields.Many2one("flight.import.config", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    
    source_field = fields.Char(required=True, help="Field name in the imported data")
    time_code_id = fields.Many2one(
        "flight.pilot.time.code", required=True, string="Pilot Time Code"
    )
    
    # Whether to convert the time value (e.g., minutes to hours)
    convert_to_hours = fields.Boolean(default=True, help="Convert time value to hours")
    divisor = fields.Float(default=60.0, help="Divisor to convert to hours (e.g. 60 for minutes)")


class FlightImportEventMapping(models.Model):
    _name = "flight.import.event.mapping"
    _description = "Flight Import Pilot Event Mapping"
    _order = "sequence, id"

    config_id = fields.Many2one("flight.import.config", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    
    source_field = fields.Char(required=True, help="Field name in the imported data")
    event_code_id = fields.Many2one(
        "flight.pilot.event.code", required=True, string="Pilot Event Code"
    )


class FlightImportTransformMethod(models.Model):
    _name = "flight.import.transform.method"
    _description = "Flight Import Transform Method"

    config_id = fields.Many2one("flight.import.config", required=True, ondelete="cascade")
    name = fields.Char(required=True, help="Name of the transformation method")
    method = fields.Char(
        required=True, 
        help="Method to call (e.g. 'import_utils.parse_date')"
    )
    description = fields.Text()