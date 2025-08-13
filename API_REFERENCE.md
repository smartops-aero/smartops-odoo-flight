# SmartOps Flight - API Reference Documentation

## Table of Contents
1. [Core Models](#core-models)
2. [Model Methods](#model-methods)
3. [Computed Fields](#computed-fields)
4. [Constraints & Validations](#constraints--validations)
5. [Controller APIs](#controller-apis)
6. [JavaScript Components](#javascript-components)
7. [Wizards & Actions](#wizards--actions)
8. [Hooks & Extensions](#hooks--extensions)

## Core Models

### flight.flight

**Description**: Core flight record model for managing flight operations

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `date` | Date | Yes | Scheduled flight date |
| `aircraft_id` | Many2one(flight.aircraft) | Yes | Aircraft assignment |
| `departure_id` | Many2one(flight.aerodrome) | Yes | Departure aerodrome |
| `arrival_id` | Many2one(flight.aerodrome) | Yes | Arrival aerodrome |
| `crew_ids` | One2many(flight.crew) | No | Assigned crew members |
| `locked` | Boolean | No | Lock status (default: False) |
| `event_time_ids` | One2many(flight.event.time) | No | Flight events |
| `phase_duration_ids` | One2many(flight.phase.duration) | No | Phase durations |

**Inheritance**: 
- `mail.thread` - Messaging and tracking
- `mail.activity.mixin` - Activity management
- `flight.lock.mixin` - Locking functionality

### flight.aircraft

**Description**: Aircraft registry and management

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `registration` | Char | Yes | Aircraft registration number (unique) |
| `model_id` | Many2one(flight.aircraft.model) | No | Aircraft model |
| `operator_id` | Many2one(res.partner) | No | Operating company |
| `sn` | Char | No | Serial number |
| `dom` | Date | No | Date of manufacture |
| `equipment_type` | Selection | Yes | Equipment classification |
| `mtow` | Float | No | Maximum takeoff weight |
| `weight_uom_id` | Many2one(uom.uom) | Yes | Weight unit of measure |
| `spec_ids` | One2many(flight.aircraft.spec) | No | Aircraft specifications |
| `website_published` | Boolean | No | Website visibility |

**Inheritance**:
- `mail.thread` - Messaging and tracking
- `mail.activity.mixin` - Activity management  
- `avatar.mixin` - Avatar functionality

### flight.aerodrome

**Description**: Aerodrome/Airport database

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `icao` | Char | Yes | ICAO identifier (unique) |
| `iata` | Char | No | IATA identifier |
| `lid` | Char | No | FAA identifier |
| `name` | Char | No | Airport name |
| `city` | Char | No | City location |
| `municipality` | Char | No | Municipality |
| `country_id` | Many2one(res.country) | No | Country |
| `elevation` | Integer | No | Elevation in feet |
| `tz` | Selection | No | Timezone |
| `latitude` | Float(10,7) | No | GPS latitude |
| `longitude` | Float(10,7) | No | GPS longitude |

**Inheritance**:
- `mail.thread` - Messaging and tracking

### flight.crew

**Description**: Crew member assignments

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `flight_id` | Many2one(flight.flight) | Yes | Associated flight |
| `partner_id` | Many2one(res.partner) | Yes | Crew member |
| `role_id` | Many2one(flight.crew.role) | Yes | Crew role |
| `sequence` | Integer | No | Display order |

### flight.aircraft.model

**Description**: Aircraft model definitions

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | Char | Yes | Model name |
| `make_id` | Many2one(flight.aircraft.make) | No | Manufacturer |
| `class_id` | Many2one(flight.aircraft.class) | No | Aircraft class |
| `engine_type` | Selection | No | Engine type |
| `gear_type` | Selection | No | Landing gear type |
| `code` | Char | No | ICAO type code |
| `tag_ids` | Many2many(flight.aircraft.model.tag) | No | Model tags |

### flight.event.code

**Description**: Flight event type definitions

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | Char | Yes | Event code (unique) |
| `name` | Char | Yes | Event name |
| `description` | Char | No | Event description |
| `sequence` | Integer | No | Display order |
| `start_phase_ids` | One2many(flight.phase) | No | Phases started by this event |
| `end_phase_ids` | One2many(flight.phase) | No | Phases ended by this event |

### flight.event.time

**Description**: Flight event time records

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `flight_id` | Many2one(flight.flight) | Yes | Associated flight |
| `code_id` | Many2one(flight.event.code) | Yes | Event type |
| `time_kind` | Selection | Yes | Time type (A/S/R/T/E) |
| `time` | Datetime | No | Event timestamp |
| `display_time` | Char | Computed | Formatted time display |
| `history_ids` | One2many(flight.event.time.history) | No | Change history |

**Time Kinds**:
- `A` - Actual
- `S` - Scheduled
- `R` - Requested
- `T` - Target
- `E` - Estimated

## Model Methods

### flight.flight Methods

```python
def name_get(self):
    """Generate display name for flight record
    
    Returns:
        list: [(id, "date / registration: DEP - ARR")]
    
    Example:
        "2024-01-15 / N12345: KJFK - KLAX"
    """

def toggle_locked(self):
    """Toggle flight lock status
    
    Prevents modifications when locked.
    Requires single record (ensure_one).
    
    Returns:
        None
    """

@api.onchange('aircraft_id')
def _onchange_aircraft_id(self):
    """Auto-populate departure from last arrival
    
    When aircraft changes and departure is empty,
    sets departure to aircraft's last known location.
    
    Returns:
        None
    """
```

### flight.aircraft Methods

```python
def name_get(self):
    """Generate display name using registration
    
    Returns:
        list: [(id, registration)]
    """

@api.constrains('registration')
def _check_registration_unique(self):
    """Ensure aircraft registration is unique
    
    Raises:
        ValidationError: If duplicate registration found
    """
```

### flight.aerodrome Methods

```python
@api.depends('icao', 'iata')
def _compute_display_name(self):
    """Compute aerodrome display name
    
    Format: "ICAO(IATA) - Name" or "ICAO - Name"
    
    Example:
        "KJFK(JFK) - John F Kennedy International"
    """

@api.model
def _name_search(self, name, args=None, operator='ilike', 
                 limit=100, name_get_uid=None):
    """Search aerodromes by ICAO or IATA code
    
    Args:
        name: Search string
        operator: Search operator
        limit: Result limit
    
    Returns:
        list: Record IDs matching search
    """
```

### flight.event.time Methods

```python
def write(self, vals):
    """Override write to track time changes
    
    Only allows updating 'time' field.
    Creates history record for changes.
    
    Args:
        vals: Dictionary of values to update
    
    Raises:
        UserError: If attempting to modify non-time fields
    
    Returns:
        bool: Write result
    """

@api.model_create_multi
def create(self, vals_list):
    """Create event times and auto-generate phase durations
    
    Args:
        vals_list: List of value dictionaries
    
    Returns:
        recordset: Created records
    """

def _create_phase_durations(self, new_events):
    """Automatically create phase duration records
    
    Links start and end events for phase tracking.
    Prevents duplicate phase durations.
    
    Args:
        new_events: Newly created event records
    
    Returns:
        None
    """

def action_view_time_changes(self):
    """Open history of time changes
    
    Returns:
        dict: Action dictionary for history window
    """
```

### flight.data.provider Methods

```python
def get_client(self, schedule):
    """Get API client for provider
    
    Hook method for service-specific implementation.
    
    Args:
        schedule: Sync schedule record
    
    Returns:
        object: API client instance
    
    Raises:
        NotImplementedError: If not overridden
    """

def _sync(self, schedule):
    """Execute sync process
    
    Orchestrates receive, process, prepare, send flow.
    
    Args:
        schedule: Sync schedule record
    
    Returns:
        None
    """

def receive_data(self, schedule, **kwargs):
    """Receive data from external source
    
    Args:
        schedule: Sync schedule
        kwargs: Additional parameters
    
    Returns:
        dict: Received data
    """

def process_data(self, schedule, data):
    """Process received data
    
    Args:
        schedule: Sync schedule
        data: Data to process
    
    Returns:
        None
    """

def prepare_data(self, schedule, **kwargs):
    """Prepare data for sending
    
    Args:
        schedule: Sync schedule
        kwargs: Additional parameters
    
    Returns:
        dict: Prepared data
    """

def send_data(self, schedule, data, **kwargs):
    """Send data to external system
    
    Args:
        schedule: Sync schedule
        data: Data to send
        kwargs: Additional parameters
    
    Returns:
        None
    """
```

## Computed Fields

### flight.event.time Computed Fields

```python
@api.depends('time', 'flight_id.date')
def _compute_display_time(self):
    """Compute formatted time display
    
    Format: HH:MM with day offset if different from flight date
    Examples:
        "14:30" - Same day
        "02:15 (+1)" - Next day
        "23:45 (-1)" - Previous day
    """

@api.depends('time_kind', 'code_id.code', 'display_time')
def _compute_display_name(self):
    """Compute full event display name
    
    Format: "{time_kind}{code}T {display_time}"
    Example: "AOFFT 14:30"
    """
```

### flight.phase.duration Computed Fields

```python
@api.depends('start_event_id.time', 'end_event_id.time')
def _compute_duration(self):
    """Calculate phase duration in minutes
    
    Returns time difference between start and end events.
    """

@api.depends('duration')
def _compute_duration_display(self):
    """Format duration for display
    
    Format: "Xh Ym" or "Ym"
    Examples:
        "2h 30m"
        "45m"
    """
```

## Constraints & Validations

### SQL Constraints

```python
# flight.aircraft
_sql_constraints = [
    ('registration_unique', 'unique(registration)', 
     'Aircraft with this registration number already exists!'),
]

# flight.aerodrome
_sql_constraints = [
    ('icao_unique', 'unique(icao)', 
     'Aerodrome with this ICAO already exists!'),
]

# flight.event.code
_sql_constraints = [
    ('code_unique', 'unique(code)', 
     'The event code must be unique!'),
]
```

### Python Constraints

```python
# flight.data.sync.schedule
@api.constrains('kwargs')
def _check_kwargs(self):
    """Validate kwargs field contains valid Python dictionary
    
    Raises:
        ValidationError: If kwargs is not valid Python dict
    """

# flight.event.time
def write(self, vals):
    """Constraint: Only 'time' field can be modified
    
    Raises:
        UserError: If attempting to modify other fields
    """
```

## Controller APIs

### Website Flight Fleet Controllers

```python
@http.route(['/fleet', '/fleet/page/<int:page>'], 
            type='http', auth='public', website=True, sitemap=True)
def fleet(self, page=1, model=None, search=None, **post):
    """Public fleet listing page
    
    Args:
        page (int): Page number for pagination
        model (flight.aircraft.model): Filter by model
        search (str): Search term
    
    Returns:
        str: Rendered HTML template
    
    Template: website_flight_fleet.page_fleet
    """

@http.route(['/aircraft/<model("flight.aircraft"):aircraft>'],
            type='http', auth='public', website=True)
def aircraft_detail(self, aircraft, **kwargs):
    """Aircraft detail page
    
    Args:
        aircraft (flight.aircraft): Aircraft record
    
    Returns:
        str: Rendered HTML template
    
    Template: website_flight_fleet.page_aircraft_detail
    """

@http.route(['/flight/aircraft/images'], 
            type='json', auth='public', website=True)
def get_aircraft_images(self, category_id=None, aircraft_id=None):
    """AJAX endpoint for aircraft images
    
    Args:
        category_id (int): Filter by category
        aircraft_id (int): Filter by aircraft
    
    Returns:
        dict: {
            'images': [{
                'id': int,
                'name': str,
                'description': str,
                'category': str,
                'aircraft': str
            }]
        }
    """
```

### Flight Portal Controllers

```python
@http.route(['/my/flights', '/my/flights/page/<int:page>'],
            type='http', auth='user', website=True)
def portal_my_flights(self, page=1, sortby=None, **kw):
    """Portal flights listing
    
    Args:
        page (int): Page number
        sortby (str): Sort field
    
    Returns:
        str: Rendered portal template
    
    Access: Portal users only
    """

@http.route(['/my/flights/<int:flight_id>'],
            type='http', auth='user', website=True)
def portal_flight_detail(self, flight_id, **kw):
    """Portal flight detail view
    
    Args:
        flight_id (int): Flight record ID
    
    Returns:
        str: Rendered detail template
    
    Access: Portal users with flight access
    """
```

## JavaScript Components

### Flight Event Time Matrix Component

```javascript
/** @odoo-module **/
import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class FlightEventTimeMatrixField extends Component {
    static template = "flight_event.TimeMatrixField";
    static props = standardFieldProps;
    
    setup() {
        // Initialize component
        this.events = this.props.value || [];
    }
    
    onEventClick(event) {
        // Handle event click
        this.env.services.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'flight.event.time',
            res_id: event.id,
            views: [[false, 'form']],
            target: 'new',
        });
    }
}

// Register the field
registry.category("fields").add("flight_event_time_matrix", FlightEventTimeMatrixField);
```

### Relative DateTime Picker

```javascript
/** @odoo-module **/
import { DateTimeField } from "@web/views/fields/datetime/datetime_field";

export class RelativeDateTimePicker extends DateTimeField {
    static template = "flight_event.RelativeDateTimePicker";
    
    get relativeTime() {
        // Calculate relative time from flight date
        const flightDate = this.props.record.data.flight_id.date;
        const eventTime = this.props.value;
        // ... calculation logic
        return formattedRelativeTime;
    }
}
```

### Dynamic Aircraft Images Snippet

```javascript
/** @odoo-module **/
import publicWidget from '@web/public/public_widget';

publicWidget.registry.DynamicAircraftImages = publicWidget.Widget.extend({
    selector: '.s_website_flight_fleet_dynamic_aircraft_images',
    
    start: function () {
        this._loadImages();
        return this._super.apply(this, arguments);
    },
    
    _loadImages: function () {
        const categoryId = this.$el.data('category-id');
        const aircraftId = this.$el.data('aircraft-id');
        
        this._rpc({
            route: '/flight/aircraft/images',
            params: {
                category_id: categoryId,
                aircraft_id: aircraftId,
            },
        }).then(result => {
            this._renderImages(result.images);
        });
    },
    
    _renderImages: function (images) {
        // Render image gallery
        const $container = this.$('.images-container');
        images.forEach(img => {
            $container.append(`
                <div class="aircraft-image">
                    <img src="/web/image/flight.aircraft.image/${img.id}/image" 
                         alt="${img.name}" />
                    <p>${img.description}</p>
                </div>
            `);
        });
    }
});
```

## Wizards & Actions

### Flight Data Sync Wizard

```python
class FlightDataSyncWizard(models.TransientModel):
    _name = 'flight.data.sync.wizard'
    _description = 'Flight Data Sync Wizard'
    
    provider_id = fields.Many2one(
        'flight.data.provider',
        string='Provider',
        required=True
    )
    
    schedule_ids = fields.Many2many(
        'flight.data.sync.schedule',
        string='Schedules to Sync'
    )
    
    def action_sync(self):
        """Execute selected sync schedules
        
        Returns:
            dict: Action to close wizard
        """
        for schedule in self.schedule_ids:
            schedule.provider_id._sync(schedule)
        
        return {'type': 'ir.actions.act_window_close'}
```

### Server Actions

```xml
<!-- Scheduled Action for Data Sync -->
<record id="ir_cron_flight_data_sync" model="ir.cron">
    <field name="name">Flight Data Sync</field>
    <field name="model_id" ref="model_flight_data_provider"/>
    <field name="state">code</field>
    <field name="code">model.run_scheduled_syncs()</field>
    <field name="interval_number">1</field>
    <field name="interval_type">hours</field>
    <field name="numbercall">-1</field>
</record>
```

## Hooks & Extensions

### Service Provider Hooks

```python
@api.model
def _get_available_services(self):
    """Hook to register new sync services
    
    Override in custom modules to add services.
    
    Returns:
        list: [(service_code, service_name)]
    
    Example:
        return super()._get_available_services() + [
            ('my_service', 'My Service'),
        ]
    """

@api.model
def _get_available_sync_models(self):
    """Hook to register syncable models
    
    Returns:
        list: [(model_name, display_name)]
    
    Example:
        return super()._get_available_sync_models() + [
            ('my.model', 'My Model'),
        ]
    """
```

### Data Processing Hooks

```python
def _receive_flight_data(self, client, schedule, **kwargs):
    """Hook to implement flight data reception
    
    Override in service-specific module.
    
    Args:
        client: API client instance
        schedule: Sync schedule record
        kwargs: Additional parameters
    
    Returns:
        dict: Received data
    
    Example:
        data = client.get_flights(
            date_from=kwargs.get('date_from'),
            date_to=kwargs.get('date_to')
        )
        return data
    """

def _process_flight_data(self, client, schedule, data):
    """Hook to process received flight data
    
    Args:
        client: API client
        schedule: Sync schedule
        data: Data to process
    
    Example:
        Flight = self.env['flight.flight']
        for flight_data in data:
            Flight.create({
                'date': flight_data['date'],
                'aircraft_id': self._get_aircraft(flight_data['aircraft']),
                # ...
            })
    """
```

### Website Snippet Hooks

```javascript
/** @odoo-module **/
// Hook for custom snippet options
import options from '@web_editor/js/editor/snippets.options';

options.registry.FlightFleetOptions = options.Class.extend({
    /**
     * Hook called when snippet is dropped
     */
    onBuilt: function () {
        this._super();
        // Custom initialization
    },
    
    /**
     * Hook for option changes
     */
    _setCategory: function (previewMode, value) {
        this.$target.attr('data-category-id', value);
        if (!previewMode) {
            this._refreshImages();
        }
    },
});
```

## Error Handling

### Standard Error Types

```python
from odoo.exceptions import UserError, ValidationError, AccessError

# User-facing errors
raise UserError(_("Flight cannot be modified when locked"))

# Validation errors
raise ValidationError(_("Invalid ICAO code format"))

# Access control errors
raise AccessError(_("You don't have permission to modify this flight"))
```

### API Error Responses

```python
# Controller error handling
try:
    aircraft = request.env['flight.aircraft'].browse(aircraft_id)
    if not aircraft.exists():
        return request.not_found()
except AccessError:
    return request.forbidden()
```

## Testing Utilities

### Test Base Class

```python
from odoo.tests import TransactionCase

class FlightTestBase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Create test data
        cls.aircraft = cls.env['flight.aircraft'].create({
            'registration': 'TEST-001',
            'model_id': cls.env.ref('flight.aircraft_model_demo').id,
        })
        
        cls.aerodrome_dep = cls.env['flight.aerodrome'].create({
            'icao': 'TEST1',
            'name': 'Test Airport 1',
        })
    
    def create_flight(self, **values):
        """Helper to create test flights"""
        defaults = {
            'date': fields.Date.today(),
            'aircraft_id': self.aircraft.id,
            'departure_id': self.aerodrome_dep.id,
            'arrival_id': self.aerodrome_arr.id,
        }
        defaults.update(values)
        return self.env['flight.flight'].create(defaults)
```

## Performance Considerations

### Query Optimization

```python
# Use search_read for better performance
flights = self.env['flight.flight'].search_read(
    [('date', '>=', date_from)],
    ['date', 'aircraft_id', 'departure_id', 'arrival_id'],
    limit=100
)

# Use read_group for aggregations
flight_counts = self.env['flight.flight'].read_group(
    [('date', '>=', date_from)],
    ['aircraft_id'],
    ['aircraft_id'],
)

# Use SQL for complex queries
self.env.cr.execute("""
    SELECT 
        f.id,
        f.date,
        ac.registration,
        dep.icao as departure,
        arr.icao as arrival
    FROM flight_flight f
    JOIN flight_aircraft ac ON f.aircraft_id = ac.id
    JOIN flight_aerodrome dep ON f.departure_id = dep.id
    JOIN flight_aerodrome arr ON f.arrival_id = arr.id
    WHERE f.date >= %s
    ORDER BY f.date DESC
    LIMIT 100
""", (date_from,))
results = self.env.cr.dictfetchall()
```

### Caching Strategies

```python
from odoo.tools import ormcache

class FlightAerodrome(models.Model):
    _name = 'flight.aerodrome'
    
    @api.model
    @ormcache('icao')
    def _get_aerodrome_by_icao(self, icao):
        """Cached aerodrome lookup"""
        return self.search([('icao', '=', icao)], limit=1)
    
    def write(self, vals):
        # Clear cache on write
        if 'icao' in vals:
            self._get_aerodrome_by_icao.clear_cache(self)
        return super().write(vals)
```

---

*API Reference Version: 18.0.1.0.0*
*Last Updated: 2025-08-13*