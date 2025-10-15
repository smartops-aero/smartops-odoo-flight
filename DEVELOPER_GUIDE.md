# SmartOps Flight - Developer Quick Reference Guide

## Quick Start

### 1. Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/smartops-aero/smartops-odoo-flight.git
cd smartops-odoo-flight
git checkout 18.0

# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Configure Odoo
echo "addons_path = $(pwd),/path/to/odoo/addons" >> odoo.conf

# Install modules
odoo -c odoo.conf -i flight_uom,flight --dev=reload
```

### 2. Creating a New Module

```bash
# Create module structure
mkdir flight_custom
cd flight_custom

# Create manifest
cat > __manifest__.py << EOF
{
    "name": "Flight Custom",
    "version": "18.0.1.0.0",
    "depends": ["flight"],
    "data": [
        "security/ir.model.access.csv",
        "views/views.xml",
    ],
}
EOF

# Create init file
echo "from . import models" > __init__.py
mkdir models views security
```

## Common Development Tasks

### Adding a New Field to Flight

```python
# flight_custom/models/flight_flight.py
from odoo import fields, models

class FlightFlight(models.Model):
    _inherit = 'flight.flight'

    custom_field = fields.Char("Custom Field")
    computed_field = fields.Float(
        "Computed Field",
        compute='_compute_computed_field',
        store=True
    )

    @api.depends('departure_id', 'arrival_id')
    def _compute_computed_field(self):
        for record in self:
            # Your computation logic
            record.computed_field = 0.0
```

### Adding a New View

```xml
<!-- flight_custom/views/views.xml -->
<odoo>
    <!-- Inherit and modify existing view -->
    <record id="flight_form_inherit" model="ir.ui.view">
        <field name="name">flight.flight.form.inherit</field>
        <field name="model">flight.flight</field>
        <field name="inherit_id" ref="flight.flight_form_view" />
        <field name="arch" type="xml">
            <field name="date" position="after">
                <field name="custom_field" />
            </field>
        </arch>
    </record>

    <!-- Create new view -->
    <record id="flight_custom_tree" model="ir.ui.view">
        <field name="name">flight.custom.tree</field>
        <field name="model">flight.flight</field>
        <field name="arch" type="xml">
            <list string="Custom Flights">
                <field name="date" />
                <field name="custom_field" />
            </list>
        </field>
    </record>
</odoo>
```

### Adding Security Access

```csv
# flight_custom/security/ir.model.access.csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_flight_custom_user,flight.custom.user,model_flight_custom,flight.group_flight_user,1,0,0,0
access_flight_custom_manager,flight.custom.manager,model_flight_custom,flight.group_flight_manager,1,1,1,1
```

### Creating a Data Sync Provider

```python
# flight_custom/models/custom_provider.py
from odoo import api, models

class CustomDataProvider(models.Model):
    _inherit = 'flight.data.provider'

    @api.model
    def _get_available_services(self):
        res = super()._get_available_services()
        res.append(('custom_api', 'Custom API'))
        return res

    def get_client(self, schedule):
        if self.service == 'custom_api':
            # Return your API client
            return CustomAPIClient(self.api_base, self.username, self.password)
        return super().get_client(schedule)

    def _receive_flight_data(self, client, schedule, **kwargs):
        if self.service == 'custom_api':
            # Implement data reception
            return client.get_flights(**kwargs)
        return super()._receive_flight_data(client, schedule, **kwargs)

    def _process_flight_data(self, client, schedule, data):
        if self.service == 'custom_api':
            # Process received data
            Flight = self.env['flight.flight']
            for item in data:
                Flight.create({
                    'date': item['date'],
                    'aircraft_id': self._find_aircraft(item['aircraft']),
                    'departure_id': self._find_aerodrome(item['departure']),
                    'arrival_id': self._find_aerodrome(item['arrival']),
                })
        return super()._process_flight_data(client, schedule, data)
```

### Adding a Website Controller

```python
# flight_custom/controllers/main.py
from odoo import http
from odoo.http import request

class FlightCustomController(http.Controller):

    @http.route('/flight/custom', type='http', auth='public', website=True)
    def custom_page(self, **kwargs):
        flights = request.env['flight.flight'].sudo().search(
            [('date', '>=', fields.Date.today())],
            limit=10
        )

        values = {
            'flights': flights,
        }

        return request.render('flight_custom.custom_page_template', values)

    @http.route('/api/flight/custom', type='json', auth='public')
    def api_endpoint(self, date_from=None, date_to=None):
        domain = []
        if date_from:
            domain.append(('date', '>=', date_from))
        if date_to:
            domain.append(('date', '<=', date_to))

        flights = request.env['flight.flight'].sudo().search_read(
            domain,
            ['date', 'aircraft_id', 'departure_id', 'arrival_id'],
            limit=100
        )

        return {'flights': flights}
```

### Creating an OWL Component

```javascript
/** @odoo-module **/
import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class FlightCustomWidget extends Component {
  static template = "flight_custom.Widget";
  static props = {
    flightId: Number,
    readonly: { type: Boolean, optional: true },
  };

  setup() {
    this.orm = useService("orm");
    this.action = useService("action");
    this.flightData = null;

    onWillStart(async () => {
      await this.loadFlightData();
    });
  }

  async loadFlightData() {
    const result = await this.orm.read(
      "flight.flight",
      [this.props.flightId],
      ["date", "aircraft_id", "departure_id", "arrival_id"]
    );
    this.flightData = result[0];
  }

  onFlightClick() {
    this.action.doAction({
      type: "ir.actions.act_window",
      res_model: "flight.flight",
      res_id: this.props.flightId,
      views: [[false, "form"]],
      target: "current",
    });
  }
}

// Register as field widget
registry.category("fields").add("flight_custom_widget", FlightCustomWidget);
```

## Testing

### Writing Unit Tests

```python
# flight_custom/tests/test_custom.py
from odoo.tests import TransactionCase
from odoo import fields

class TestFlightCustom(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create test data
        cls.aircraft = cls.env['flight.aircraft'].create({
            'registration': 'TEST-001',
        })

        cls.aerodrome = cls.env['flight.aerodrome'].create({
            'icao': 'TEST',
            'name': 'Test Airport',
        })

    def test_custom_field(self):
        """Test custom field functionality"""
        flight = self.env['flight.flight'].create({
            'date': fields.Date.today(),
            'aircraft_id': self.aircraft.id,
            'departure_id': self.aerodrome.id,
            'arrival_id': self.aerodrome.id,
            'custom_field': 'Test Value',
        })

        self.assertEqual(flight.custom_field, 'Test Value')

    def test_computed_field(self):
        """Test computed field calculation"""
        flight = self.env['flight.flight'].create({
            'date': fields.Date.today(),
            'aircraft_id': self.aircraft.id,
            'departure_id': self.aerodrome.id,
            'arrival_id': self.aerodrome.id,
        })

        # Trigger computation
        flight._compute_computed_field()

        self.assertIsNotNone(flight.computed_field)
```

### Running Tests

```bash
# Run all tests for a module
odoo -c odoo.conf --test-enable --stop-after-init -i flight_custom

# Run specific test
odoo -c odoo.conf --test-enable --stop-after-init \
     --test-tags flight_custom.test_custom

# Generate coverage report
coverage run odoo -c odoo.conf --test-enable --stop-after-init -i flight_custom
coverage report
coverage html
```

## Debugging Tips

### 1. Enable Debug Mode

```python
# In Python code
import logging
_logger = logging.getLogger(__name__)

def my_method(self):
    _logger.info("Starting my_method")
    _logger.debug(f"Processing record: {self.id}")

    try:
        # Your code
        pass
    except Exception as e:
        _logger.exception("Error in my_method")
        raise
```

### 2. Using Python Debugger

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use the modern breakpoint
breakpoint()  # Python 3.7+
```

### 3. SQL Query Logging

```bash
# Enable SQL logging
odoo -c odoo.conf --log-sql --log-level=debug
```

### 4. JavaScript Debugging

```javascript
// Use browser console
console.log("Debug info:", data);
console.table(records);

// Set breakpoint
debugger;

// Conditional breakpoint
if (condition) {
  debugger;
}
```

## Performance Optimization

### 1. Database Indexes

```python
class FlightFlight(models.Model):
    _name = 'flight.flight'

    # Add index to frequently queried fields
    date = fields.Date(index=True)
    aircraft_id = fields.Many2one('flight.aircraft', index=True)
```

### 2. Batch Operations

```python
# Bad - N queries
for record in records:
    record.write({'field': value})

# Good - 1 query
records.write({'field': value})

# Bad - Multiple creates
for data in data_list:
    self.env['model'].create(data)

# Good - Batch create
self.env['model'].create(data_list)
```

### 3. Prefetching

```python
# Bad - Causes N+1 queries
for flight in flights:
    print(flight.aircraft_id.registration)

# Good - Prefetch related records
flights.mapped('aircraft_id')  # Prefetch
for flight in flights:
    print(flight.aircraft_id.registration)
```

### 4. Use search_read

```python
# Bad - Two queries
records = self.env['model'].search([])
data = records.read(['field1', 'field2'])

# Good - One query
data = self.env['model'].search_read(
    [],
    ['field1', 'field2']
)
```

## Common Patterns

### 1. Singleton Pattern

```python
def my_method(self):
    self.ensure_one()  # Ensure single record
    # Method logic for single record
```

### 2. Context Manager

```python
with self.env.cr.savepoint():
    try:
        # Risky operations
        self.dangerous_operation()
    except Exception:
        # Rollback to savepoint
        raise
```

### 3. Computed Fields with Dependencies

```python
@api.depends('field1', 'field2.subfield')
def _compute_total(self):
    for record in self:
        record.total = record.field1 + sum(record.field2.mapped('subfield'))
```

### 4. Onchange Methods

```python
@api.onchange('aircraft_id')
def _onchange_aircraft_id(self):
    if self.aircraft_id:
        # Update related fields
        last_flight = self.aircraft_id.flight_ids[-1:]
        if last_flight:
            self.departure_id = last_flight.arrival_id
```

## Migration Guide

### Creating Migration Scripts

```python
# migrations/18.0.1.1.0/pre-migrate.py
def migrate(cr, version):
    """Pre-migration script"""
    # Add column before ORM loads
    cr.execute("""
        ALTER TABLE flight_flight
        ADD COLUMN IF NOT EXISTS new_field VARCHAR
    """)

# migrations/18.0.1.1.0/post-migrate.py
from odoo import api, SUPERUSER_ID

def migrate(cr, version):
    """Post-migration script"""
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Data migration
    flights = env['flight.flight'].search([])
    for flight in flights:
        flight.new_field = compute_value(flight)
```

## Useful Commands

### Development Commands

```bash
# Update module
odoo -c odoo.conf -u flight_custom

# Install with dependencies
odoo -c odoo.conf -i flight_custom

# Development mode with auto-reload
odoo -c odoo.conf --dev=reload,xml,qweb

# Shell access
odoo shell -c odoo.conf

# Clear assets
odoo -c odoo.conf --dev=xml,reload,qweb
```

### Code Quality

```bash
# Format Python code
ruff format .

# Lint Python code
ruff check . --fix

# Format XML/JS/CSS
npx prettier --write "**/*.{xml,js,css}"

# Run pre-commit hooks
pre-commit run --all-files
```

### Git Commands

```bash
# Create feature branch
git checkout -b 18.0-feature-name

# Commit with conventional message
git commit -m "[IMP] flight: Add custom feature

- Added new field
- Updated views
- Added tests"

# Interactive rebase
git rebase -i HEAD~3

# Cherry-pick commit
git cherry-pick commit_hash
```

## Resources

### Documentation

- [Odoo 18.0 Docs](https://www.odoo.com/documentation/18.0/)
- [OWL Framework](https://github.com/odoo/owl)
- [Python API](https://www.odoo.com/documentation/18.0/developer/reference/backend.html)

### Tools

- [Odoo.sh](https://www.odoo.sh/) - Cloud deployment
- [Runbot](http://runbot.odoo.com/) - Test instances
- [OCA Tools](https://github.com/OCA/maintainer-tools) - Module management

### Community

- [Odoo Forums](https://www.odoo.com/forum)
- [GitHub Issues](https://github.com/smartops-aero/smartops-odoo-flight/issues)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/odoo)

---

_Quick Reference Version: 18.0.1.0.0_
_Last Updated: 2025-08-13_
