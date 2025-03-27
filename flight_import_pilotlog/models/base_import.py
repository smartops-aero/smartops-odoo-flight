import itertools
import logging
import operator

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.base_import.models.base_import import ImportValidationError

_logger = logging.getLogger(__name__)


class ImportExtended(models.TransientModel):
    _inherit = "base_import.import"

    transformer_id = fields.Many2one(
        "flight.import.pilotlog.transformer",
        string="Data Transformer",
        help="Transformer to use for data conversion",
    )

    base_pilot_id = fields.Many2one(
        "res.partner",
        string="Base Pilot",
        help="Default pilot to use for imported flights",
    )

    @api.model
    def update_transformation_preview(self, id):
        """Log and skip transformation for now"""
        record = self.browse(id)

        if record.res_model != "flight.flight":
            return {"status": "success"}

        try:
            if not record.file:
                _logger.warning("No file data found for record ID: %s", id)
                return {"status": "error", "message": "No file data available"}

            _logger.info(
                "File found for record ID: %s, proceeding with original data", id
            )
            return {"status": "success"}
        except Exception as e:
            _logger.exception("Error in update_transformation_preview: %s", e)
            return {"status": "error", "message": str(e)}

    def parse_preview(self, options, count=10):
        """Follow base parse_preview pattern with optional transformation"""
        self.ensure_one()

        if not self.transformer_id:
            return super(ImportExtended, self).parse_preview(options, count)
        else:
            try:
                fields_tree = self.get_fields_tree(self.res_model)
                file_length, rows = self._read_file(options)
                if file_length <= 0:
                    raise UserError(_("Import file has no content or is corrupt"))

                # Apply transformation if transformer is selected
                if self.transformer_id:
                    # Extract headers if present
                    original_headers = []
                    if options.get("has_headers") and rows:
                        original_headers = rows[0]

                    # Transform the data using the selected transformer
                    rows = self.transformer_id.transform_data(
                        rows, original_headers, self
                    )

                    # Force has_headers to True for transformed data
                    options = dict(options)
                    options["has_headers"] = True

                # Continue with standard processing, same as base implementation
                preview = rows[:count]

                # Get file headers
                if options.get("has_headers") and preview:
                    # We need the header types before matching columns to fields
                    headers = preview.pop(0)
                    header_types = self._extract_headers_types(
                        headers, preview, options
                    )
                else:
                    header_types, headers = {}, []

                # Get matches: the ones already selected by the user or propose a new matching.
                matches = {}
                # If user checked to the advanced mode, we re-parse the file but we keep the mapping "as is".
                # No need to make another mapping proposal
                if options.get("keep_matches") and options.get("fields"):
                    for index, match in enumerate(options.get("fields", [])):
                        if match:
                            matches[index] = match.split("/")
                elif options.get("has_headers"):
                    matches = self._get_mapping_suggestions(
                        headers, header_types, fields_tree
                    )
                    # remove header_name for matches keys as tuples are no supported in json.
                    # and remove distance from suggestion (keep only the field path) as not used at client side.
                    matches = {
                        header_key[0]: suggestion["field_path"]
                        for header_key, suggestion in matches.items()
                        if suggestion
                    }

                # compute if we should activate advanced mode or not:
                # if was already activated of if file contains "relational fields".
                if options.get("keep_matches"):
                    advanced_mode = options.get("advanced")
                else:
                    # Check is label contain relational field
                    from odoo import models

                    has_relational_header = any(
                        len(models.fix_import_export_id_paths(col)) > 1
                        for col in headers
                    )
                    # Check is matches fields have relational field
                    has_relational_match = any(
                        len(match) > 1 for field, match in matches.items() if match
                    )
                    advanced_mode = has_relational_header or has_relational_match

                # Take first non null values for each column to show preview to users.
                column_example = []
                if preview and preview[0]:  # Ensure we have data to process
                    for column_index, _unused in enumerate(preview[0]):
                        vals = []
                        for record in preview:
                            if record[column_index]:
                                vals.append(
                                    "%s%s"
                                    % (
                                        record[column_index][:50],
                                        "..." if len(record[column_index]) > 50 else "",
                                    )
                                )
                            if len(vals) == 5:
                                break
                        column_example.append(
                            vals
                            or [
                                ""
                            ]  # blank value if no example have been found at all for the current column
                        )

                # Batch management
                batch = False
                batch_cutoff = options.get("limit")
                if batch_cutoff:
                    if count > batch_cutoff:
                        batch = len(preview) > batch_cutoff
                    else:
                        batch = bool(
                            next(
                                itertools.islice(rows, batch_cutoff - count, None), None
                            )
                        )

                result = {
                    "fields": fields_tree,
                    "matches": matches or False,
                    "headers": headers or False,
                    "header_types": list(header_types.values())
                    if header_types
                    else False,
                    "preview": column_example,
                    "options": options,
                    "advanced_mode": advanced_mode,
                    "debug": self.user_has_groups("base.group_no_one"),
                    "batch": batch,
                    "file_length": file_length,
                }

                # Add transformation info if applicable
                if self.transformer_id:
                    result["transformer_id"] = {
                        "id": self.transformer_id.id,
                        "name": self.transformer_id.name,
                    }
                    result["is_transformed"] = bool(self.transformer_id)

                # Add base_pilot_id if available
                if self.base_pilot_id:
                    result["base_pilot_id"] = {
                        "id": self.base_pilot_id.id,
                        "name": self.base_pilot_id.name,
                    }

                return result

            except Exception as error:
                _logger.exception("Error during parsing preview: %s", error)
                preview = None
                if self.file_type == "text/csv" and self.file:
                    preview = self.file[:1024].decode("iso-8859-1")
                return {
                    "error": str(error),
                    "preview": preview,
                    "transformer_id": {
                        "id": self.transformer_id.id,
                        "name": self.transformer_id.name,
                    }
                    if self.transformer_id
                    else False,
                    "base_pilot_id": {
                        "id": self.base_pilot_id.id,
                        "name": self.base_pilot_id.name,
                    }
                    if self.base_pilot_id
                    else False,
                }

    def execute_import(self, fields, columns, options, dryrun=False):
        """Log and delegate to parent method"""
        self.ensure_one()  # Ensure singleton
        try:
            result = super(ImportExtended, self).execute_import(
                fields, columns, options, dryrun
            )
            _logger.info("Import executed successfully, result: %s", result)
            return result
        except Exception as e:
            _logger.exception("Error in execute_import: %s", e)
            raise

    @api.model
    def _convert_import_data(self, fields, options):
        """Override to apply transformation before conversion"""
        # Apply transformation if transformer is selected
        if self.transformer_id:
            # Read the original file data
            file_length, rows_to_import = self._read_file(options)

            # Extract headers if present
            original_headers = []
            if options.get("has_headers") and rows_to_import:
                original_headers = rows_to_import[0]

            # Transform the data using the selected transformer
            transformed_rows = self.transformer_id.transform_data(
                rows_to_import, original_headers, self
            )

            # Now continue with the standard processing, but using our transformed data
            # Get indices for non-empty fields
            indices = [index for index, field in enumerate(fields) if field]
            if not indices:
                raise ImportValidationError(
                    _("You must configure at least one field to import")
                )

            # If only one index, itemgetter will return an atom rather than a 1-tuple
            if len(indices) == 1:
                mapper = lambda row: [row[indices[0]]]
            else:
                mapper = operator.itemgetter(*indices)

            # Get only list of actually imported fields
            import_fields = [f for f in fields if f]

            # Skip the header row from the transformed data
            rows_to_process = (
                transformed_rows[1:] if options.get("has_headers") else transformed_rows
            )

            # Ensure the transformed data has the right number of columns
            if transformed_rows and len(transformed_rows[0]) != len(fields):
                _logger.warning(
                    "Transformed data has %d columns but fields has %d elements. This may cause issues.",
                    len(transformed_rows[0]),
                    len(fields),
                )

                # If the transformed data has fewer columns than fields, pad with empty strings
                if len(transformed_rows[0]) < len(fields):
                    rows_to_process = [
                        row + [""] * (len(fields) - len(row)) for row in rows_to_process
                    ]

            # Apply the mapper to extract only the fields we want
            data = [
                list(row)
                for row in map(mapper, rows_to_process)
                # don't try inserting completely empty rows
                if any(row)
            ]

            # slicing needs to happen after filtering out empty rows
            return data[options.get("skip") :], import_fields

        # For all other cases, use the standard implementation
        return super(ImportExtended, self)._convert_import_data(fields, options)
