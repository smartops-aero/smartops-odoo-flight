# Base Import Pipeline ETL for Odoo

## Overview

The `base_import_pipeline_etl` module provides a flexible Extract-Transform-Load (ETL) framework for importing data into Odoo models from various data sources. The module implements a batch processing approach to efficiently handle large datasets while maintaining memory efficiency.

## Architecture

The import pipeline follows a classic ETL pattern with these key components:

1. **Extract**: Read data from external sources (CSV files, APIs, etc.)
2. **Transform**: Convert and map source data to target Odoo model fields
3. **Load**: Create or update records in Odoo
4. **Post-Process**: Handle related records and complex relationships after initial import

### Key Features

- Configurable field mappings via XML or UI
- Flexible transformation options (direct, lookup, regex, etc.)
- Batch processing for memory-efficient imports
- Extensible architecture for custom data sources
- Record identification and update/create logic
- Error handling and import result logging

## Module Structure

```
base_import_pipeline_etl/
├── models/
│   ├── base_import_pipeline_etl.py       # Core ETL implementation
│   ├── base_import_pipeline_mapping.py   # Field mapping configuration
│   └── base_import_pipeline_result.py    # Import result logging
├── views/
│   └── base_import_pipeline_etl_views.xml # UI views
├── security/
│   └── ir.model.access.csv               # Access rules
└── __manifest__.py                       # Module manifest
```

## How to Use

### 1. Create an Import Pipeline

Create a pipeline record to define the target model and implementation:

```xml
<record id="my_import_pipeline" model="base.import.pipeline">
    <field name="name">My Data Import</field>
    <field name="model_id" ref="module_name.model_my_target_model" />
    <field name="implementation">my_implementation</field>
    <field name="batch_size">1000</field>
    <field name="active" eval="True" />
</record>
```

### 2. Define Field Mappings

Configure field mappings to map source fields to target model fields:

```xml
<!-- Direct field mapping -->
<record id="mapping_name" model="base.import.pipeline.mapping">
    <field name="pipeline_id" ref="my_import_pipeline"/>
    <field name="source_field">SourceFieldName</field>
    <field name="target_field">target_field_name</field>
    <field name="model_id" ref="module_name.model_my_target_model"/>
    <field name="transformation">direct</field>
    <field name="sequence">10</field>
</record>

<!-- Lookup mapping for relational fields -->
<record id="mapping_partner" model="base.import.pipeline.mapping">
    <field name="pipeline_id" ref="my_import_pipeline"/>
    <field name="source_field">PartnerName</field>
    <field name="target_field">partner_id</field>
    <field name="model_id" ref="module_name.model_my_target_model"/>
    <field name="transformation">lookup</field>
    <field name="relation_model_id" ref="base.model_res_partner"/>
    <field name="relation_field">name</field>
    <field name="lookup_fields">email,ref</field>
    <field name="sequence">20</field>
</record>

<!-- Key field for record identification -->
<record id="mapping_unique_reference" model="base.import.pipeline.mapping">
    <field name="pipeline_id" ref="my_import_pipeline"/>
    <field name="source_field">UniqueRef</field>
    <field name="target_field">reference</field>
    <field name="model_id" ref="module_name.model_my_target_model"/>
    <field name="transformation">direct</field>
    <field name="is_key_field" eval="True"/>
    <field name="sequence">5</field>
</record>
```

### 3. Extend the Pipeline for Custom Implementation

```python
from odoo import api, models

class MyImportPipeline(models.Model):
    _inherit = "base.import.pipeline"

    def _selection_implementation(self):
        selection = super()._selection_implementation()
        selection.append(("my_implementation", "My Custom Import"))
        return selection

    def _my_implementation_extract(self, file_content, **kwargs):
        """Custom extraction logic for my implementation"""
        # Process file_content and return list of dictionaries
        records = []
        # ... custom extraction logic ...
        return records
```

### 4. Create an Import Wizard

Create a wizard model and interface for users to upload data:

```python
class MyImportWizard(models.TransientModel):
    _name = "my.import.wizard"
    _description = "My Import Wizard"

    file = fields.Binary(string="File", required=True)
    filename = fields.Char(string="Filename")
    batch_size = fields.Integer(string="Batch Size", default=500)
    
    def action_import(self):
        pipeline = self.env["base.import.pipeline"].search(
            [("implementation", "=", "my_implementation")], limit=1
        )
        if not pipeline:
            raise UserError("Import pipeline not configured")
            
        file_content = base64.b64decode(self.file).decode("utf-8")
        
        result = pipeline.run_import(
            file_content=file_content,
            filename=self.filename,
            batch_size=self.batch_size
        )
        
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Import Result",
                "message": f"Created: {len(result.get('created', []))}, "
                          f"Updated: {len(result.get('updated', []))}, "
                          f"Errors: {len(result.get('errors', []))}",
                "sticky": False,
            }
        }
```

## Field Mapping Configuration

### Available Transformation Types

1. **direct**: Direct field mapping without transformation
2. **date_format**: Convert date formats (e.g., DD-MM-YYYY to YYYY-MM-DD)
3. **lookup**: Look up and link to existing records (for Many2one fields)
4. **regex**: Apply regular expressions for data cleaning/extraction
5. **parent_record_id**: Link to parent record during post-processing
6. **minutes_to_hours**: Convert minutes to hours
7. **ref_id**: Convert XML references to database IDs

### Mapping Field Descriptions

| Field | Description |
|-------|-------------|
| `pipeline_id` | Reference to the import pipeline |
| `description` | Text description about this mapping |
| `source_field` | Field name in the source data |
| `target_field` | Field name in the Odoo model |
| `model_id` | Target Odoo model |
| `model` | Related field showing the model name from model_id |
| `transformation` | Transformation type |
| `sequence` | Order in which mappings are processed |
| `is_key_field` | Field used to identify existing records |
| `is_post_process` | Field is processed after main import |
| `relation_model_id` | For lookup transformations, the related model |
| `relation_model` | Related field showing the model name from relation_model_id |
| `relation_field` | For lookups, the field to match in related model |
| `lookup_fields` | Additional fields for lookup (comma-separated) |
| `default_value` | Value to use if source field is empty |
| `regex_pattern` | For regex transformations, the pattern to match |
| `regex_replacement` | For regex, the replacement pattern |
| `context` | Context for record creation during lookups |
| `post_process_value` | Static value to use during post-processing |
| `use_context_value` | Boolean to indicate if we should use a context value |
| `context_variable_name` | Name of the context variable to use |
| `group_key` | Group key for post-processing records |

## Post-Processing

Post-processing is used for creating or updating related records after the main import is complete. This is particularly useful for handling complex relationships or dependencies between records.

### Example Post-Processing Mapping

```xml
<record id="mapping_post_process" model="base.import.pipeline.mapping">
    <field name="pipeline_id" ref="my_import_pipeline"/>
    <field name="source_field">ChildData</field>
    <field name="target_field">name</field>
    <field name="model_id" ref="module_name.model_my_child_model"/>
    <field name="transformation">direct</field>
    <field name="is_post_process" eval="True"/>
    <field name="group_key">child_record</field>
    <field name="sequence">100</field>
</record>

<record id="mapping_post_process_parent" model="base.import.pipeline.mapping">
    <field name="pipeline_id" ref="my_import_pipeline"/>
    <field name="target_field">parent_id</field>
    <field name="model_id" ref="module_name.model_my_child_model"/>
    <field name="transformation">parent_record_id</field>
    <field name="is_post_process" eval="True"/>
    <field name="group_key">child_record</field>
    <field name="sequence">110</field>
</record>
```

## Performance Considerations

- Use batch processing to manage memory usage for large imports
- Configure appropriate `batch_size` values based on record complexity
- Use key fields for efficient record identification
- Consider indexing fields used for lookups in your models

## Extending the Framework

The import pipeline framework is designed to be extended for custom data sources and transformations:

1. Add new transformation types by extending `_selection_transformation` and implementing corresponding `_transform_X` methods in `base.import.pipeline.mapping`
2. Add new implementations by extending `_selection_implementation` and implementing corresponding `_X_extract` methods in `base.import.pipeline`
3. Create specialized import wizards for specific data sources

## Troubleshooting

- Check import results in the "Import Results" tab of the pipeline
- Use `_logger.debug` statements in custom methods for debugging
- Test with small data samples before importing large datasets
- Verify field mappings match your source data structure
