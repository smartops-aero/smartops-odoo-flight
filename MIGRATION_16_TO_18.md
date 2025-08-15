# Migration Guide: Odoo 16.0 to 18.0

This document outlines all the changes required when migrating SmartOps Flight modules from Odoo 16.0 to 18.0.

## Table of Contents
- [Core API Changes](#core-api-changes)
- [View and UI Changes](#view-and-ui-changes)
- [Security and Access Control](#security-and-access-control)
- [Module-Specific Changes](#module-specific-changes)
- [Testing](#testing)
- [Complete Breaking Changes Checklist](#complete-breaking-changes-checklist)

## Core API Changes

### 1. Display Name Implementation

**Odoo 16.0 (Deprecated):**
```python
def name_get(self):
    result = []
    for record in self:
        name = f"{record.field1} - {record.field2}"
        result.append((record.id, name))
    return result
```

**Odoo 18.0 (New):**
```python
@api.depends('field1', 'field2')  # List all fields used in display name
def _compute_display_name(self):
    for record in self:
        record.display_name = f"{record.field1} - {record.field2}"
```

**Affected Models:**
- `flight.flight`
- `flight.aircraft` 
- `flight.aerodrome`
- `flight.number`

### 2. ir.cron Field Changes

The `ir.cron` model has removed deprecated fields:

**Removed Fields:**
- `numbercall` - No longer supported
- `doall` - No longer supported

**Migration Required:**
Remove these fields from any `ir.cron` data XML files.

## View and UI Changes

### 1. Chatter Widget

**Odoo 16.0 (Deprecated):**
```xml
<div class="oe_chatter">
    <field name="message_follower_ids" options="{'post_refresh': 'recipients'}"/>
    <field name="activity_ids"/>
    <field name="message_ids"/>
</div>
```

**Odoo 18.0 (New):**
```xml
<chatter />
```

The new `<chatter />` tag automatically includes all messaging functionality.

**Affected Views:**
- All form views with chatter functionality
- `flight_views.xml`
- `aircraft_views.xml`
- `aerodrome_views.xml`

### 2. Website Components

#### Slug Function Import

**Odoo 16.0 (Deprecated):**
```python
from odoo.addons.http_routing.models.ir_http import slug
# Use: slug(record)
```

**Odoo 18.0 (New):**
```python
def _compute_website_url(self):
    IrHttp = self.env['ir.http']
    for record in self:
        record.website_url = f"/path/{IrHttp._slug(record)}"
```

#### XML Structure Changes

**Website snippet paths changed:**
- `snippet_feature` → `snippet_structure`

## Security and Access Control

### Record Rules with Website Module

When `website_flight_fleet` module is installed, it adds domain rules that restrict access based on `website_published` field:

```xml
<record id="website_aircraft_user" model="ir.rule">
    <field name="domain_force">
        ['|', ('website_published', '=', True), ('create_uid', '=', user.id)]
    </field>
    <field name="groups" eval="[(4, ref('flight.group_flight_user'))]"/>
</record>
```

**Important:** Tests must account for this by:
1. Setting `website_published = True` on test records
2. Or creating records with the test user
3. Or checking for field existence: `if 'website_published' in self.env['model']._fields:`

## Module-Specific Changes

### flight_data_sync

**ir.cron configuration updates:**
- Removed `numbercall` field
- Removed `doall` field
- Updated to use new scheduling syntax

### website_flight_fleet

**Model changes:**
- Added `website_published` field to `flight.aircraft`
- Updated slug generation to use `IrHttp._slug()`
- Fixed xpath selectors for website templates

**Controller changes:**
- Updated domain filters to check `website_published`
- Modified slug handling in routes

### flight_portal

No significant changes required for 18.0 migration.

### flight_number

**Display name:**
- Migrated from `name_get()` to `_compute_display_name()`
- Added proper field dependencies

## Testing

### Test Updates Required

1. **Replace name_get() calls:**
```python
# Old
name = record.name_get()[0][1]

# New
name = record.display_name
```

2. **Handle website_published field:**
```python
# Check if field exists (when website module installed)
if 'website_published' in self.env['flight.aircraft']._fields:
    vals['website_published'] = True
```

3. **Update test data:**
- Remove deprecated fields from test data
- Add required fields for new constraints

### Running Tests

```bash
# Run all tests with the updated test runner
./run_tests.sh

# Run specific module tests
source .venv/bin/activate
odoo-bin --test-enable --stop-after-init --test-tags=module_name -d test_db -u module_name
```

## Code Quality

### Ruff Configuration

Project now uses Python 3.11+ with ruff for linting:

```bash
# Full cleanup command
ruff format . && ruff check . --fix --unsafe-fixes
```

Configuration in `.ruff.toml`:
```toml
target-version = "py311"
```

## Common Migration Issues and Solutions

### Issue 1: AccessError in Tests
**Cause:** Website module adds domain rules
**Solution:** Set `website_published = True` on test records

### Issue 2: AttributeError: 'Model' object has no attribute 'name_get'
**Cause:** Method deprecated in Odoo 18.0
**Solution:** Use `display_name` field instead

### Issue 3: ValueError: Invalid field 'numbercall' on model 'ir.cron'
**Cause:** Field removed in Odoo 18.0
**Solution:** Remove field from XML data files

### Issue 4: ImportError: cannot import name 'slug'
**Cause:** Function moved to IrHttp model
**Solution:** Use `self.env['ir.http']._slug(record)`

### Issue 5: Chatter not displaying correctly
**Cause:** Old verbose chatter syntax deprecated
**Solution:** Replace with simple `<chatter />` tag

## Files Modified During Migration

### Manifest Files
- All `__manifest__.py` files updated to version 18.0.1.0.0

### View Files Updated for tree→list
- flight/views/*.xml
- flight_aircraft_spec/views/*.xml
- flight_data_sync/views/*.xml
- flight_data_sync/wizard/*.xml
- flight_event/views/*.xml
- flight_number/views/*.xml
- website_flight_fleet/views/*.xml

### Python Files Updated
- flight_data_sync/models/flight_data_provider.py
- flight_event/models/flight_event.py

### Configuration Files
- .ruff.toml (Python 3.11 target)
- .pre-commit-config.yaml (Python 3.11, Node 18)
- CLAUDE.md (Updated documentation)

## Known Non-Critical Issues

### Warnings That Don't Affect Functionality
1. **ESLint warnings in relative_datetimepicker.js** (prefer-const)
2. **Website template warning about oe_structure class**

These warnings don't affect functionality and can be addressed in future updates.

## Best Practices for Future Development

1. **Always use `_compute_display_name()`** for record display names
2. **Use `<chatter />`** tag for messaging functionality
3. **Check for optional fields** when modules might not be installed
4. **Use Python 3.11+ features** where appropriate
5. **Run ruff before committing** to ensure code quality
6. **Test with all modules installed** to catch integration issues

## Complete Breaking Changes Checklist

### 1. Tree → List View Rename (MANDATORY)

**Error you'll see:** `ValueError: Wrong value for ir.ui.view.type: 'tree'`

#### A. XML View Roots
```xml
<!-- Before (16.0) -->
<tree editable="bottom">
    <field name="name"/>
</tree>

<!-- After (18.0) -->
<list editable="bottom">
    <field name="name"/>
</list>
```

#### B. Inline x2many Subviews
```xml
<!-- Before -->
<field name="line_ids">
    <tree editable="bottom">
        <field name="product_id"/>
    </tree>
</field>

<!-- After -->
<field name="line_ids">
    <list editable="bottom">
        <field name="product_id"/>
    </list>
</field>
```

#### C. Actions (ir.actions.act_window)
```xml
<!-- Before -->
<field name="view_mode">tree,form</field>

<!-- After -->
<field name="view_mode">list,form</field>
```

#### D. Python Action Dictionaries
```python
# Before
return {
    'type': 'ir.actions.act_window',
    'views': [(view_id, 'tree'), (False, 'form')],
    'view_mode': 'tree,form',
}

# After
return {
    'type': 'ir.actions.act_window',
    'views': [(view_id, 'list'), (False, 'form')],
    'view_mode': 'list,form',
}
```

#### E. Context Keys
```xml
<!-- Before -->
<field name="line_ids" context="{'tree_view_ref': 'module.view_id'}"/>

<!-- After -->
<field name="line_ids" context="{'list_view_ref': 'module.view_id'}"/>
```

#### F. XPath in Inherited Views
```xml
<!-- Before -->
<xpath expr="//tree/field[@name='date']" position="after">

<!-- After -->
<xpath expr="//list/field[@name='date']" position="after">
```

#### G. Remove Explicit Type Field
```xml
<!-- Before -->
<record id="view_id" model="ir.ui.view">
    <field name="type">tree</field>  <!-- REMOVE THIS -->
    <field name="arch" type="xml">
        ...
    </field>
</record>

<!-- After -->
<record id="view_id" model="ir.ui.view">
    <!-- Type is inferred from root tag -->
    <field name="arch" type="xml">
        ...
    </field>
</record>
```

### 2. attrs and states Attributes Removed (MANDATORY)

**Error you'll see:** `Since 17.0, the "attrs" and "states" attributes are no longer used.`

#### A. Field Modifiers
```xml
<!-- Before (16.0) -->
<field name="departure_id" attrs="{'invisible': [('locked','=',True)]}"/>
<field name="arrival_id" attrs="{'readonly': [('state','in',('done','cancel'))]}"/>
<field name="pilot_id" attrs="{'required': [('type','=','commercial')]}"/>

<!-- After (18.0) -->
<field name="departure_id" invisible="locked"/>
<field name="arrival_id" readonly="state in ('done','cancel')"/>
<field name="pilot_id" required="type == 'commercial'"/>
```

#### B. Complex Conditions
```xml
<!-- Before: Polish notation with | and & -->
attrs="{'invisible': ['|', ('a','=',1), ('b','=',2)]}"
attrs="{'readonly': ['&', ('x','!=',0), ('y','=',False)]}"

<!-- After: Python expressions -->
invisible="(a == 1) or (b == 2)"
readonly="(x != 0) and (not y)"
```

#### C. Button States
```xml
<!-- Before -->
<button name="action_confirm" states="draft,sent" string="Confirm"/>

<!-- After -->
<button name="action_confirm" string="Confirm" invisible="state not in ('draft','sent')"/>
```

#### D. Page/Group Visibility
```xml
<!-- Before -->
<page name="settings" attrs="{'invisible': [('is_company','=',False)]}">

<!-- After -->
<page name="settings" invisible="not is_company">
```

#### E. List Column Visibility
```xml
<!-- Before (in list/tree views) -->
<field name="amount" attrs="{'column_invisible': [('parent.type','=','service')]}"/>

<!-- After -->
<field name="amount" column_invisible="parent.type == 'service'"/>
```

#### F. Domain Syntax Conversion Table
| 16.0 Domain | 18.0 Expression |
|-------------|-----------------|
| `('x','=',1)` | `x == 1` |
| `('x','!=',1)` | `x != 1` |
| `('x','>',1)` | `x > 1` |
| `('x','>=',1)` | `x >= 1` |
| `('x','<',1)` | `x < 1` |
| `('x','<=',1)` | `x <= 1` |
| `('x','in',['a','b'])` | `x in ['a','b']` |
| `('x','not in',['a','b'])` | `x not in ['a','b']` |
| `('x','=',True)` | `x` |
| `('x','=',False)` | `not x` |
| `('x','like','%test%')` | `'test' in x` |

### 3. QWeb Changes

#### t-raw Deprecated
```xml
<!-- Before -->
<t t-raw="html_content"/>

<!-- After -->
<t t-out="Markup(html_content)"/>
```

In Python, ensure:
```python
from markupsafe import Markup
# Pass Markup(content) when you need unescaped HTML
```

### 4. Quick Sed Commands for Batch Migration

```bash
# 1. Replace tree tags with list
find . -name "*.xml" -exec sed -i 's/<tree>/<list>/g' {} \;
find . -name "*.xml" -exec sed -i 's/<\/tree>/<\/list>/g' {} \;
find . -name "*.xml" -exec sed -i 's/<tree /<list /g' {} \;

# 2. Update view_mode in actions
find . -name "*.xml" -exec sed -i 's/view_mode">tree/view_mode">list/g' {} \;
find . -name "*.xml" -exec sed -i 's/view_mode">tree,/view_mode">list,/g' {} \;

# 3. Update Python files
find . -name "*.py" -exec sed -i "s/'tree'/'list'/g" {} \;
find . -name "*.py" -exec sed -i 's/"tree"/"list"/g' {} \;

# 4. Update context keys
find . -name "*.xml" -exec sed -i 's/tree_view_ref/list_view_ref/g' {} \;

# Note: attrs and states require manual conversion due to complex logic
```

### 5. Manual Conversion Required

The following changes require manual review and conversion:

1. **attrs attributes** - Convert domain syntax to Python expressions
2. **states attributes** - Convert to invisible/readonly expressions
3. **Complex domain logic** - Polish notation (|, &) to Python (or, and)
4. **Optional fields** - Review column_invisible vs invisible in lists
5. **Inherited views** - Update XPath expressions targeting tree elements

### 6. Manifest Changes

#### A. Version Update
```python
# __manifest__.py
{
    'version': '18.0.1.0.0',  # Update from 16.0.x.x.x
    ...
}
```

#### B. Assets Declaration (Important!)
```python
# Before (16.0) - might use old patterns
{
    'data': [
        'views/assets.xml',  # Old way with templates
    ],
}

# After (18.0) - use assets key
{
    'assets': {
        'web.assets_backend': [
            'module_name/static/src/js/**/*.js',
            'module_name/static/src/xml/**/*.xml',
            'module_name/static/src/scss/**/*.scss',
        ],
        'web.assets_frontend': [
            'module_name/static/src/frontend/**/*.js',
            'module_name/static/src/frontend/**/*.scss',
        ],
    },
}
```

#### C. Data Files Order
Ensure views are loaded before menus that reference them:
```python
'data': [
    'security/security.xml',
    'security/ir.model.access.csv',
    'views/model_views.xml',  # Views first
    'views/menu_views.xml',   # Menus after
],
```

### 7. JavaScript/OWL Changes

#### A. Module Declaration
```javascript
// Use ES module format with Odoo module marker
/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
```

#### B. Registry Pattern for Extensions
```javascript
// Register custom fields
registry.category("fields").add("custom_field", CustomFieldComponent);

// Register actions
registry.category("actions").add("custom_action", CustomActionComponent);

// Register services
registry.category("services").add("custom_service", customService);
```

### 8. Website-Specific Changes

#### A. Snippet Structure Rename
```xml
<!-- Before -->
<xpath expr="//div[@id='snippet_feature']" position="inside">

<!-- After -->
<xpath expr="//div[@id='snippet_structure']" position="inside">
```

#### B. New Page Templates (18.0 feature)
```python
# In __manifest__.py for website modules
{
    'new_page_templates': [
        {
            'id': 'website_flight_fleet.fleet_page',
            'name': 'Fleet Page',
            'template': 'website_flight_fleet.fleet_page_template',
        }
    ],
}
```

### 9. ORM Deprecations

#### A. _flush_search() Removed
```python
# Before (16.0)
self._flush_search()  # Deprecated

# After (18.0)
# Removed - flushing handled automatically by execute_query()
```

#### B. Modifiers Attribute (Do NOT use)
```xml
<!-- NEVER manually set modifiers -->
<field name="field" modifiers="{}"/>  <!-- DON'T DO THIS -->

<!-- Always use direct attributes -->
<field name="field" invisible="condition" readonly="other_condition"/>
```

### 10. Environment Requirements

- Python 3.10+ (recommended 3.11+)
- PostgreSQL 12+
- Node.js with rtlcss (`npm install -g rtlcss`)
- wkhtmltopdf 0.12.6 (for PDF reports)

## References

- [Odoo 18.0 Release Notes](https://www.odoo.com/documentation/18.0/developer/releases.html)
- [Odoo 18.0 API Reference](https://www.odoo.com/documentation/18.0/developer/reference.html)
- [OWL Framework v2 Documentation](https://www.odoo.com/documentation/18.0/developer/reference/frontend/owl.html)
- [Odoo Forum: Tree to List Migration](https://www.odoo.com/forum/help-1/odoo-18-tree-to-list)