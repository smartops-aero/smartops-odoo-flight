# SmartOps Flight Module Test Documentation

## Overview
Comprehensive test suite for all SmartOps Flight modules following Odoo 18.0 testing best practices.

## Test Coverage

### 1. Flight Base Module (`flight/tests/`)
- **test_flight.py**: Core flight operations (12 test methods)
  - Flight creation and validation
  - Date/time calculations
  - Status management
  - Lock/unlock functionality
  - Flight duplication
  - Route validation

- **test_aircraft.py**: Aircraft management (11 test methods)
  - Aircraft creation
  - Model/make relationships
  - Registration validation
  - Operator assignment
  - Aircraft categories
  - Maintenance tracking

- **test_aerodrome.py**: Airport operations (9 test methods)
  - Aerodrome creation
  - Coordinate validation
  - ICAO/IATA codes
  - Timezone handling
  - Elevation management

- **test_crew.py**: Crew management (8 test methods)
  - Crew role creation
  - Flight assignment
  - Role validation
  - Partner constraints

- **test_security.py**: Access control (8 test methods)
  - User group hierarchy
  - CRUD permissions
  - Lock permissions
  - Model-specific access

### 2. Aircraft Specifications Module (`flight_aircraft_spec/tests/`)
- **test_aircraft_spec.py**: Specification management (9 test methods)
  - Spec category creation
  - Value type handling (bool, float, text)
  - UOM conversions
  - Unique constraints
  - Sequence ordering

### 3. Data Sync Module (`flight_data_sync/tests/`)
- **test_data_sync.py**: External data synchronization (12 test methods)
  - API configuration
  - Sync logging
  - Queue management
  - Field mapping
  - Error recovery
  - Batch processing

### 4. Event Module (`flight_event/tests/`)
- **test_flight_event.py**: Event tracking (12 test methods)
  - Event type creation
  - Severity levels
  - Status workflow
  - Impact assessment
  - Recurring events
  - Resolution tracking

### 5. Flight Number Module (`flight_number/tests/`)
- **test_flight_number.py**: Flight number management (12 test methods)
  - Airline creation
  - Number format validation
  - Codeshare flights
  - Seasonal schedules
  - Capacity allocation
  - International/domestic classification

### 6. Portal Module (`flight_portal/tests/`)
- **test_flight_portal.py**: Portal access (12 test methods)
  - Portal user permissions
  - Flight sharing
  - Document access
  - Read-only constraints
  - Flight history
  - Notification preferences

### 7. UOM Module (`flight_uom/tests/`)
- **test_flight_uom.py**: Aviation units (12 test methods)
  - Nautical mile conversions
  - Altitude calculations
  - Fuel consumption
  - Weight/balance
  - Speed conversions
  - Flight level handling

### 8. Website Fleet Module (`website_flight_fleet/tests/`)
- **test_website_flight_fleet.py**: Fleet display (12 test methods)
  - Publishing control
  - Category filtering
  - Charter availability
  - Image management
  - SEO metadata
  - Responsive display

## Running Tests

### Run All Tests
```bash
./run_tests.sh
```

### Run Specific Module Tests
```bash
# Run tests for a specific module
python odoo-bin -d test_db --test-enable --test-tags=flight -i flight

# Run with specific tags
python odoo-bin -d test_db --test-enable --test-tags=flight_security -i flight
```

### Test Tags
Each test class is tagged for selective execution:
- `post_install`: Run after module installation
- `-at_install`: Skip during installation
- Module-specific tags: `flight`, `flight_aircraft_spec`, etc.

## Test Database Setup
Tests use `TransactionCase` which:
- Creates a fresh transaction for each test
- Automatically rolls back changes
- Ensures test isolation

## Test Data Management
Each test module includes:
- `setUpClass()`: Creates shared test data
- Individual test methods: Test specific functionality
- Proper cleanup via transaction rollback

## Assertions Used
- `assertTrue/assertFalse`: Boolean checks
- `assertEqual/assertNotEqual`: Value comparisons
- `assertIn/assertNotIn`: Collection membership
- `assertRaises`: Exception handling
- `assertAlmostEqual`: Float comparisons

## Coverage Metrics
- **Total Test Methods**: 101
- **Modules Covered**: 8/8 (100%)
- **Core Models Tested**: 25+
- **Security Groups**: 4
- **Access Rules**: 20+

## Best Practices Followed
1. **Odoo 18.0 Standards**: Using latest testing framework
2. **Isolation**: Each test is independent
3. **Comprehensive**: Tests cover CRUD + business logic
4. **Tagged**: Proper tagging for test organization
5. **Documented**: Clear test descriptions
6. **Error Cases**: Tests both success and failure paths

## Common Test Patterns

### Model Creation Test
```python
def test_01_model_creation(self):
    """Test model creation and validation"""
    record = self.env['model.name'].create({
        'field': 'value'
    })
    self.assertTrue(record.id)
    self.assertEqual(record.field, 'value')
```

### Permission Test
```python
def test_02_access_rights(self):
    """Test access rights"""
    with self.assertRaises(AccessError):
        record.with_user(self.portal_user).write({'field': 'value'})
```

### Workflow Test
```python
def test_03_workflow(self):
    """Test status workflow"""
    record.status = 'draft'
    record.action_confirm()
    self.assertEqual(record.status, 'confirmed')
```

## Continuous Integration
The test suite is designed for CI/CD integration:
- Exit code 0 on success
- Exit code 1 on failure
- Detailed logging to `test_results.log`
- Database cleanup after tests

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure all module dependencies are installed
2. **Database Errors**: Check PostgreSQL is running
3. **Permission Errors**: Run with appropriate user permissions
4. **Tag Errors**: Verify test tags match module names

### Debug Mode
Run tests with debug logging:
```bash
python odoo-bin -d test_db --test-enable --log-level=debug -i module_name
```

## Future Enhancements
- [ ] Performance benchmarks
- [ ] Load testing
- [ ] API endpoint tests
- [ ] JavaScript/OWL component tests
- [ ] Selenium UI tests