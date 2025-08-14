# SmartOps Flight Module Testing Guide

## Overview
This guide documents the testing setup, common issues, and solutions for running tests in the SmartOps Flight Odoo 18.0 modules.

## Prerequisites

1. **Environment Setup**
   - Odoo 18.0 installed at `YOUR_PATH_TO/odoo-projects/kzr-odoo`
   - PostgreSQL running with user `odoo` and password `odoo`
   - Python virtual environment activated: `source .venv/bin/activate`

2. **Database Setup**
   ```bash
   # Create test database (if not exists)
   PGPASSWORD=odoo psql -h localhost -U odoo -d postgres -c "CREATE DATABASE odoo_test_flight;"
   ```

## Running Tests

### Basic Test Command
```bash
# From the kzr-odoo directory
source .venv/bin/activate

# Run tests for flight module
python src/odoo/odoo-bin \
  --test-enable \
  --stop-after-init \
  --http-port=8071 \
  --log-level=test \
  --db_host=localhost \
  --db_user=odoo \
  --db_password=odoo \
  --addons-path=src/odoo/addons/,extra-addons/ \
  -d odoo_test_flight \
  -u flight
```

### Run Specific Test Module
```bash
# Run tests for a specific module only
python src/odoo/odoo-bin \
  --test-enable \
  --stop-after-init \
  --http-port=8071 \
  --db_host=localhost --db_user=odoo --db_password=odoo \
  --addons-path=src/odoo/addons/,extra-addons/ \
  -d odoo_test_flight \
  -i flight_aircraft_spec  # Change module name as needed
```

### Run Tests with Specific Tags
```bash
# Run tests with specific tags
python src/odoo/odoo-bin \
  --test-enable \
  --test-tags=flight_aerodrome \
  --stop-after-init \
  --http-port=8071 \
  --db_host=localhost --db_user=odoo --db_password=odoo \
  --addons-path=src/odoo/addons/,extra-addons/ \
  -d odoo_test_flight \
  -u flight
```

## Common Issues and Fixes

### 1. Field Name Mismatches

**Issue**: Tests written for older Odoo versions may use incorrect field names.

**Common Fixes Applied**:
- `country` → `country_id` (Many2one to res.country)
- `timezone` → `tz` 
- `state` field removed (not in current model)

**Example Fix**:
```python
# Before (incorrect)
'country': 'US',

# After (correct)
'country_id': cls.country_us.id,
```

### 2. Duplicate Record Conflicts

**Issue**: Demo data creates records that conflict with test data.

**Solution**: Use unique identifiers for test data that won't conflict with demo records.

**Applied Changes**:
- Aerodromes: Use `KTES`/`KTSW` instead of `KJFK`/`KLAX`
- Aircraft: Use `TEST001` instead of `N12345`
- Test data should be independent of demo data

### 3. Invalid Selection Field Values

**Issue**: Selection field values must match exactly with defined options.

**Common Fixes Applied**:
- `gear_type`: `tricycle_retractable` → `retractable_tricycle`
- `equipment_type`: `standard` → `aircraft`

**How to Check Valid Values**:
```python
# Check model definition in models/*.py files
# Look for fields.Selection definitions
gear_type = fields.Selection([
    ("retractable_tricycle", "Retractable Tricycle (RT)"),
    # ... other options
])
```

### 4. Non-existent Fields

**Issue**: Tests try to use fields that don't exist in the model.

**Example Fix**:
```python
# flight.crew.role doesn't have 'code' field
# Before (incorrect)
cls.crew_role_pilot = cls.env['flight.crew.role'].create({
    'name': 'Captain',
    'code': 'CPT',  # This field doesn't exist
})

# After (correct)
cls.crew_role_pilot = cls.env['flight.crew.role'].create({
    'name': 'Captain',
    'description': 'Pilot in Command',
})
```

### 5. Access Rights Issues

**Issue**: Test users may not have proper access rights.

**Common Error**:
```
odoo.exceptions.AccessError: You are not allowed to access 'Message subtypes' (mail.message.subtype) records.
```

**Solution**: Ensure test users have appropriate groups:
```python
cls.user_manager = cls.env['res.users'].create({
    'name': 'Flight Manager',
    'login': 'flight_manager',
    'email': 'manager@flight.test',
    'groups_id': [(6, 0, [
        cls.env.ref('flight.group_flight_manager').id,
        cls.env.ref('base.group_user').id,  # Add Internal User group
    ])]
})
```

## Test Structure

### Module Test Files
```
flight/
├── tests/
│   ├── __init__.py
│   ├── common.py           # Common test setup class
│   ├── test_aerodrome.py   # Aerodrome model tests
│   ├── test_aircraft.py    # Aircraft model tests
│   ├── test_crew.py        # Crew model tests
│   ├── test_flight.py      # Flight model tests
│   └── test_security.py    # Access rights tests
```

### Test Class Structure
```python
from odoo.tests import tagged
from .common import FlightCommon

@tagged('post_install', '-at_install', 'flight_aerodrome')
class TestAerodrome(FlightCommon):
    """Test cases for flight.aerodrome model"""
    
    def test_01_aerodrome_creation(self):
        """Test aerodrome creation with all fields"""
        # Test implementation
```

## Best Practices

1. **Use Unique Test Data**: Avoid conflicts with demo data by using unique identifiers
2. **Check Field Definitions**: Always verify field names and types in model definitions
3. **Test Isolation**: Each test should be independent and not rely on other tests
4. **Proper Tagging**: Use appropriate tags for test organization
5. **Error Handling**: Test both success and failure cases

## Debugging Tips

### Get Detailed Error Output
```bash
# Use --log-level=debug for verbose output
python src/odoo/odoo-bin \
  --test-enable \
  --stop-after-init \
  --http-port=8071 \
  --log-level=debug \
  --db_host=localhost --db_user=odoo --db_password=odoo \
  --addons-path=src/odoo/addons/,extra-addons/ \
  -d odoo_test_flight \
  -u flight 2>&1 | tee test_output.log
```

### Filter Test Output
```bash
# Get only test results
... | grep -E "(ERROR|FAIL|OK|test_)"

# Get test summary
... | grep -E "Ran |tests in|OK|FAILED"
```

## Files Modified During Migration

The following files were updated to fix test issues:

1. **flight/tests/common.py**
   - Fixed country field: `country` → `country_id`
   - Changed airports to unique test codes (KTES, KTSW)
   - Fixed aircraft registration (TEST001)
   - Fixed equipment_type: `standard` → `aircraft`
   - Fixed gear_type: `tricycle_retractable` → `retractable_tricycle`
   - Removed non-existent `code` field from crew roles

2. **flight/tests/test_aerodrome.py**
   - Updated field names to match model
   - Fixed ICAO codes to use test airports
   - Changed `country` to `country_id`
   - Changed `timezone` to `tz`

3. **flight/tests/test_flight.py**
   - Updated expected display name to use TEST001 registration
   - Updated ICAO codes in expected values

## Module Test Status

| Module | Status | Notes |
|--------|--------|-------|
| flight | Partially Working | 44 tests run, some access rights issues |
| flight_aircraft_spec | Pending | Needs testing |
| flight_data_sync | Pending | Needs testing |
| flight_event | Pending | Needs testing |
| flight_number | Pending | Needs testing |
| flight_portal | Pending | Needs testing |
| flight_uom | Pending | Needs testing |
| website_flight_fleet | Pending | Needs testing |

## Next Steps

1. Fix remaining access rights issues in test users
2. Run and fix tests for other modules
3. Add proper group assignments for test users
4. Update any remaining deprecated assertions
5. Create CI/CD pipeline for automated testing

## References

- [Odoo 18.0 Testing Documentation](https://www.odoo.com/documentation/18.0/developer/reference/backend/testing.html)
- [Odoo Test Framework Guide](https://www.odoo.com/documentation/18.0/developer/reference/backend/testing.html#writing-tests)

---
*Last Updated: 2025-08-14*
*Tested with Odoo 18.0*