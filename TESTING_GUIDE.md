# SmartOps Flight Module Testing Guide

## Quick Start

### Prerequisites
- Odoo 18.0 installed at `/path/to/kzr-odoo`
- PostgreSQL running with user `odoo` and password `odoo`
- Python virtual environment activated: `source .venv/bin/activate`

### Run Tests
```bash
# From the kzr-odoo directory
source .venv/bin/activate

# Run all flight module tests
python src/odoo/odoo-bin --test-enable --stop-after-init --http-port=8071 \
  --db_host=localhost --db_user=odoo --db_password=odoo \
  --addons-path=src/odoo/addons/,extra-addons/ \
  -d odoo_test_flight -u flight
```

### Database Management
```bash
# Create test database (first time only)
PGPASSWORD=odoo psql -h localhost -U odoo -d postgres -c "CREATE DATABASE odoo_test_flight;"

# Reset database (if needed)
PGPASSWORD=odoo psql -h localhost -U odoo -d postgres -c "DROP DATABASE IF EXISTS odoo_test_flight;"
PGPASSWORD=odoo psql -h localhost -U odoo -d postgres -c "CREATE DATABASE odoo_test_flight;"
```

## Test Commands

### Run Specific Module Tests
```bash
# Run tests for specific module
python src/odoo/odoo-bin --test-enable --stop-after-init --http-port=8071 \
  --db_host=localhost --db_user=odoo --db_password=odoo \
  --addons-path=src/odoo/addons/,extra-addons/ \
  -d odoo_test_flight -i flight_aircraft_spec
```

### Run Tests with Tags
```bash
# Run specific test tags
python src/odoo/odoo-bin --test-enable --stop-after-init --http-port=8071 \
  --test-tags=flight_aerodrome \
  --db_host=localhost --db_user=odoo --db_password=odoo \
  --addons-path=src/odoo/addons/,extra-addons/ \
  -d odoo_test_flight -u flight
```

## Module Test Status

| Module | Status | Tests |
|--------|--------|-------|
| flight | ✅ **ALL PASSING** | 44/44 tests passing |
| flight_aircraft_spec | 🔄 Pending | Not tested yet |
| flight_data_sync | 🔄 Pending | Not tested yet |
| flight_event | 🔄 Pending | Not tested yet |
| flight_number | 🔄 Pending | Not tested yet |
| flight_portal | 🔄 Pending | Not tested yet |
| flight_uom | 🔄 Pending | Not tested yet |
| website_flight_fleet | 🔄 Pending | Not tested yet |

## Test Structure

```
flight/
├── tests/
│   ├── __init__.py
│   ├── common.py           # Common test setup
│   ├── test_aerodrome.py   # Aerodrome tests
│   ├── test_aircraft.py    # Aircraft tests
│   ├── test_crew.py        # Crew tests
│   ├── test_flight.py      # Flight tests
│   └── test_security.py    # Security tests
```

## Debugging

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
... 2>&1 | grep -E "(failed|error\(s\)|tests when loading)"
```

## Next Steps

1. Test remaining modules (flight_aircraft_spec, flight_event, etc.)
2. Set up CI/CD pipeline for automated testing
3. Add performance tests for large datasets

## References

- [Odoo 18.0 Testing Documentation](https://www.odoo.com/documentation/18.0/developer/reference/backend/testing.html)

---
*Last Updated: 2025-08-14*