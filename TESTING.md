# SmartOps Flight Module Testing

## Quick Start

### Prerequisites
- Odoo 18.0 installed at `/path/to/kzr-odoo`
- PostgreSQL running with user `odoo` and password `odoo`
- Python virtual environment activated: `source .venv/bin/activate`

### Run All Tests
```bash
# Use the test runner script
./run_tests.sh
```

### Run Specific Module Tests
```bash
# From the kzr-odoo directory
source .venv/bin/activate

# Run all flight module tests
python src/odoo/odoo-bin --test-enable --stop-after-init --http-port=8071 \
  --db_host=localhost --db_user=odoo --db_password=odoo \
  --addons-path=src/odoo/addons/,extra-addons/ \
  -d odoo_test_flight -u flight
```

## Test Commands

### Database Management
```bash
# Create test database (first time only)
PGPASSWORD=odoo psql -h localhost -U odoo -d postgres -c "CREATE DATABASE odoo_test_flight;"

# Reset database (if needed)
PGPASSWORD=odoo psql -h localhost -U odoo -d postgres -c "DROP DATABASE IF EXISTS odoo_test_flight;"
PGPASSWORD=odoo psql -h localhost -U odoo -d postgres -c "CREATE DATABASE odoo_test_flight;"
```

### Run Tests with Tags (Recommended)

**Why use tags?** Without tags, Odoo runs ALL tests from ALL installed modules in the database. Tags limit execution to only the tests you specify.

| Method | Tests Run | Time | Use Case |
|--------|-----------|------|----------|
| With tags | Only tagged tests (12-44) | 5-10 seconds | ✅ Development |
| Without tags | ALL tests from ALL modules (69+) | 5-10 minutes | ❌ Full system validation only |

**Example**: Running `flight_uom` module:
- With `--test-tags=flight_uom`: **12 tests** (only flight_uom tests)
- Without tags: **69 tests** (flight_uom + all other module tests in the database)

```bash
# Fast: Run only flight_uom tests (12 tests)
python src/odoo/odoo-bin --test-enable --stop-after-init --http-port=8071 \
  --test-tags=flight_uom \
  --db_host=localhost --db_user=odoo --db_password=odoo \
  --addons-path=src/odoo/addons/,extra-addons/ \
  -d odoo_test_flight -u flight_uom

# Multiple modules
--test-tags=flight_uom,flight_number

# All flight modules  
--test-tags=flight
```

## Test Coverage

### Current Module Status

| Module | Status | Tests | Notes |
|--------|--------|-------|-------|
| flight | ✅ **ALL PASSING** | 44/44 tests passing | Core module - fully working |
| flight_uom | ✅ **ALL PASSING** | 12/12 tests passing | Fixed calculation precision issues ✅ |
| flight_number | ✅ **ALL PASSING** | 12/12 tests passing | Fixed model references and API compatibility ✅ |
| flight_event | ✅ **ALL PASSING** | 12/12 tests passing | Comprehensive test coverage restored ✅ |
| flight_portal | ✅ **ALL PASSING** | 13/13 tests passing | Portal access functionality working ✅ |
| flight_aircraft_spec | ✅ **ALL PASSING** | 9/9 tests passing | Fixed XML view error and test logic issues ✅ |
| flight_data_sync | ✅ **ALL PASSING** | 8/8 tests passing | Fixed migration issues and test models ✅ |
| website_flight_fleet | ✅ **ALL PASSING** | 13/13 tests passing | Website integration working ✅ |

### Available Test Tags

| Tag | Module | Tests | Purpose |
|-----|---------|-------|---------|
| `flight` | flight | 44 tests | Core flight functionality |
| `flight_uom` | flight_uom | 12 tests | Aviation units of measurement |
| `flight_number` | flight_number | 12 tests | Flight numbering system |
| `flight_aerodrome` | flight | ~9 tests | Airport/aerodrome tests only |
| `flight_aircraft` | flight | ~10 tests | Aircraft model tests only |
| `flight_crew` | flight | ~7 tests | Crew management tests only |
| `flight_security` | flight | 8 tests | Security and access control |

## Detailed Test Coverage

### 1. Flight Base Module (`flight/tests/`)

**test_flight.py**: Core flight operations (9 test methods)
- Flight creation and validation
- Display name generation
- Lock/unlock functionality
- Crew assignment
- Auto departure from last arrival
- Multi-record operations
- Search filters and grouping
- Flight duplication
- Locked flight deletion constraints

**test_aircraft.py**: Aircraft management (8 test methods)
- Aircraft creation and validation
- Model/make relationships
- Registration uniqueness
- Operator assignment
- Weight unit handling
- Multi-aircraft operations
- Search functionality
- Constraint validation

**test_aerodrome.py**: Airport operations (9 test methods)
- Aerodrome creation
- Coordinate validation
- ICAO/IATA code uniqueness
- Timezone handling
- Elevation management
- Country relationships
- Search capabilities
- Flight associations

**test_crew.py**: Crew management (7 test methods)
- Crew role creation
- Flight assignment
- Role validation
- Partner constraints
- Multiple crew per flight
- Role hierarchy
- Assignment constraints

**test_security.py**: Access control (8 test methods)
- User group hierarchy
- Flight CRUD permissions
- Aircraft access rights
- Aerodrome permissions
- Lock/unlock permissions
- Group inheritance
- Portal restrictions

### 2. Aircraft Specifications Module (`flight_aircraft_spec/tests/`)

**test_aircraft_spec.py**: Specification management (9 test methods)
- Spec category creation
- Value type handling (bool, float, text)
- UOM conversions
- Unique constraints
- Sequence ordering
- Category relationships
- Validation rules
- Search capabilities
- Data integrity

### 3. Data Sync Module (`flight_data_sync/tests/`)

**test_data_sync.py**: External data synchronization (8 test methods)
- Provider configuration
- Sync service testing
- Error handling
- Configuration validation
- Service type management
- Integration testing
- Data consistency
- Sync logging

### 4. Event Module (`flight_event/tests/`)

**test_flight_event.py**: Event tracking (12 test methods)
- Event type creation
- Severity levels
- Status workflow
- Impact assessment
- Flight associations
- Event categories
- Timeline tracking
- Resolution management
- Event hierarchies
- Notification systems
- Reporting capabilities
- Data archival

### 5. Flight Number Module (`flight_number/tests/`)

**test_flight_number.py**: Flight number management (12 test methods)
- Prefix creation and validation
- Number format handling
- Display name generation
- Search functionality
- Flight integration
- Multiple prefix support
- Empty prefix handling
- Domain searches
- Edge case testing
- Performance optimization
- Bulk operations
- Validation constraints

### 6. Portal Module (`flight_portal/tests/`)

**test_flight_portal.py**: Portal access (13 test methods)
- Portal user permissions
- Flight sharing mechanisms
- Document access control
- Read-only constraints
- Flight history access
- Notification preferences
- Security boundaries
- User isolation
- Data visibility rules
- Permission inheritance
- Access logging
- Session management
- Integration testing

### 7. UOM Module (`flight_uom/tests/`)

**test_flight_uom.py**: Aviation units (12 test methods)
- Nautical mile conversions
- Altitude calculations
- Fuel consumption metrics
- Weight/balance computations
- Speed conversions
- Flight level handling
- Precision testing
- Rounding behavior
- Unit compatibility
- Conversion accuracy
- Performance metrics
- International standards

### 8. Website Fleet Module (`website_flight_fleet/tests/`)

**test_website_flight_fleet.py**: Fleet display (13 test methods)
- Publishing control
- Category filtering
- Website visibility
- Image management
- SEO metadata
- Responsive display
- Aircraft categorization
- Public access control
- Search engine optimization
- URL generation
- Template rendering
- Cache management
- Performance optimization

## Test Structure

```
flight/
├── tests/
│   ├── __init__.py
│   ├── common.py           # Common test setup and utilities
│   ├── test_aerodrome.py   # Aerodrome tests (@tagged 'flight_aerodrome')
│   ├── test_aircraft.py    # Aircraft tests (@tagged 'flight_aircraft') 
│   ├── test_crew.py        # Crew tests (@tagged 'flight_crew')
│   ├── test_flight.py      # Flight tests (@tagged 'flight')
│   └── test_security.py    # Security tests (@tagged 'flight_security')
```

## Debugging and Troubleshooting

### Verbose Output
```bash
# Get detailed test output
python src/odoo/odoo-bin --test-enable --stop-after-init --http-port=8071 \
  --log-level=test --db_host=localhost --db_user=odoo --db_password=odoo \
  --addons-path=src/odoo/addons/,extra-addons/ \
  -d odoo_test_flight -u flight
```

### Filter Output
```bash
# Filter for errors only
... 2>&1 | grep -E "(ERROR|FAIL)"

# Get summary only
... 2>&1 | grep -E "(failed|error\\(s\\)|tests when loading)"
```

### Common Issues

1. **Import Errors**: Ensure all module dependencies are installed
2. **Database Errors**: Check PostgreSQL is running
3. **Permission Errors**: Run with appropriate user permissions
4. **Tag Errors**: Verify test tags match module names
5. **Port Conflicts**: Use different ports with `--http-port=8071`

### Debug Mode
```bash
python src/odoo/odoo-bin --test-enable --stop-after-init \
  --log-level=debug --test-tags=module_name \
  -d test_db -u module_name
```

## Test Patterns and Best Practices

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

## Test Database Management

Tests use `TransactionCase` which:
- Creates a fresh transaction for each test
- Automatically rolls back changes
- Ensures test isolation
- Provides consistent test environment

Each test module includes:
- `setUpClass()`: Creates shared test data
- Individual test methods: Test specific functionality
- Proper cleanup via transaction rollback

## Assertions Reference

- `assertTrue/assertFalse`: Boolean checks
- `assertEqual/assertNotEqual`: Value comparisons
- `assertIn/assertNotIn`: Collection membership
- `assertRaises`: Exception handling
- `assertAlmostEqual`: Float comparisons
- `assertGreater/assertLess`: Numeric comparisons

## Coverage Metrics

- **Total Test Methods**: 123
- **Modules Covered**: 8/8 (100%)
- **Core Models Tested**: 25+
- **Security Groups**: 4
- **Access Rules**: 20+
- **Test Success Rate**: 123/123 (100%)

## Continuous Integration

The test suite is designed for CI/CD integration:
- Exit code 0 on success
- Exit code 1 on failure
- Detailed logging to `test_results.log`
- Database cleanup after tests
- Parallel test execution support

## Migration Testing

### Post-Migration Validation
```bash
# Test all modules after migration
./run_tests.sh

# Verify specific migration changes
python src/odoo/odoo-bin --test-enable --test-tags=flight_security \
  -d test_db -u flight
```

### Migration-Specific Tests
- Display name functionality (name_get → _compute_display_name)
- Security rule compatibility with website modules
- View rendering with new chatter syntax
- Tree → List view functionality

## Performance Testing

### Benchmark Commands
```bash
# Time test execution
time python src/odoo/odoo-bin --test-enable --stop-after-init \
  --test-tags=flight -d test_db -u flight

# Memory usage monitoring
/usr/bin/time -v python src/odoo/odoo-bin --test-enable \
  --test-tags=flight -d test_db -u flight
```

## Future Enhancements

- [ ] Performance benchmarks
- [ ] Load testing scenarios
- [ ] API endpoint testing
- [ ] JavaScript/OWL component tests
- [ ] Selenium UI automation
- [ ] Integration test suite
- [ ] Code coverage reporting
- [ ] Test data factories

## References

- [Odoo 18.0 Testing Documentation](https://www.odoo.com/documentation/18.0/developer/reference/backend/testing.html)
- [Python unittest Documentation](https://docs.python.org/3/library/unittest.html)
- [PostgreSQL Testing Best Practices](https://www.postgresql.org/docs/current/regress.html)

---
*Last Updated: 2025-08-15*