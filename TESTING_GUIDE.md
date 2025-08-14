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

## Module Test Status

| Module | Status | Tests | Notes |
|--------|--------|-------|-------|
| flight | ✅ **ALL PASSING** | 44/44 tests passing | Core module - fully working |
| flight_uom | ✅ **ALL PASSING** | 12/12 tests passing | Fixed calculation precision issues ✅ |
| flight_number | ✅ **ALL PASSING** | 12/12 tests passing | Fixed model references and API compatibility ✅ |
| flight_event | ❌ **SETUP ERROR** | 0/0 tests (1 error) | Dependency or setup issue |
| flight_portal | ❌ **SETUP ERROR** | 0/1 tests (1 error) | Dependency or setup issue |
| flight_aircraft_spec | 🚫 **WON'T INSTALL** | Module failed to install | XML view error with `active_id` field |
| flight_data_sync | 📝 **NO TESTS** | No test files found | Module has no test cases |
| website_flight_fleet | 📝 **NO TESTS** | No test results | Module may have no/empty tests |

## Available Test Tags

| Tag | Module | Tests | Purpose |
|-----|---------|-------|---------|
| `flight` | flight | 44 tests | Core flight functionality |
| `flight_uom` | flight_uom | 12 tests | Aviation units of measurement |
| `flight_number` | flight_number | 12 tests | Flight numbering system |
| `flight_aerodrome` | flight | ~9 tests | Airport/aerodrome tests only |
| `flight_aircraft` | flight | ~10 tests | Aircraft model tests only |
| `flight_crew` | flight | ~7 tests | Crew management tests only |

**Pro tip:** Use specific tags during development for faster feedback!

## Test Structure

```
flight/
├── tests/
│   ├── __init__.py
│   ├── common.py           # Common test setup
│   ├── test_aerodrome.py   # Aerodrome tests (@tagged 'flight_aerodrome')
│   ├── test_aircraft.py    # Aircraft tests (@tagged 'flight_aircraft') 
│   ├── test_crew.py        # Crew tests (@tagged 'flight_crew')
│   ├── test_flight.py      # Flight tests (@tagged 'flight')
│   └── test_security.py    # Security tests (@tagged 'flight')
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

## Testing Summary (2025-08-14)

### ✅ **Major Success: Core Flight Module**
- **44/44 tests passing** for the main `flight` module
- All critical functionality (flights, aircraft, aerodromes, crew) working perfectly
- Comprehensive test coverage across all models

### 📊 **Overall Module Health**
- **3/8 modules fully working** (flight: 44/44, flight_uom: 12/12, flight_number: 12/12) = **68 total tests passing** ✅
- **2/8 modules have structural issues** (need development work)
- **3/8 modules lack proper tests** (need test coverage)

### 🔧 **Key Issues Identified**
1. **flight_aircraft_spec**: XML view bug prevents module installation
2. **flight_event, flight_portal**: Dependency or setup configuration issues
3. ✅ ~~**flight_number**: Test methods reference non-existent models~~ **FIXED**
4. **flight_data_sync, website_flight_fleet**: Missing or incomplete test suites

### 🎯 **Development Priorities**
1. **High**: Fix flight_aircraft_spec XML view issue (`active_id` error)
2. **Medium**: Add proper test coverage for modules without tests
3. ✅ ~~**Low**: Fine-tune calculation precision in flight_uom tests~~ **COMPLETED**

## Next Steps

1. ✅ **COMPLETED**: Test all flight modules and identify issues
2. ✅ **COMPLETED**: Fix flight_number test failures  
3. **Priority 1**: Fix flight_aircraft_spec XML view error
4. **Priority 2**: Add test coverage for flight_data_sync and website_flight_fleet
5. **Priority 3**: Set up CI/CD pipeline for automated testing

## References

- [Odoo 18.0 Testing Documentation](https://www.odoo.com/documentation/18.0/developer/reference/backend/testing.html)

---
*Last Updated: 2025-08-14*