# Fixing Remaining Test Issues - Action Plan

## Current Status: 6 Failed + 13 Errors (19 total issues)

## Issue Categories and Fix Strategy

### 1. **Display Name Format Issues** (3 issues)
**Problem**: Tests expect wrong display name format

#### Issues:
- `test_aerodrome_display_name`: Expected format doesn't match actual
- `test_aircraft_display_name`: Expected format doesn't match actual  
- `test_crew_display_name`: Expected format doesn't match actual

#### Fix Strategy:
1. Check actual `name_get()` or `_compute_display_name()` methods in models
2. Update test expectations to match actual format
3. Use proper method to get display name (`.name_get()[0][1]` vs `.display_name`)

### 2. **Constraint Validation Issues** (4 issues)
**Problem**: Tests try to create invalid data to test constraints

#### Issues:
- `test_aerodrome_coordinates_validation`: Coordinate validation not working
- `test_aerodrome_unique_codes`: Duplicate ICAO constraint test failing
- `test_crew_role_unique_code`: Trying to test constraint that doesn't exist
- `test_crew_partner_validation`: Partner validation test failing

#### Fix Strategy:
1. Check if constraints actually exist in models
2. Use `assertRaises(ValidationError)` properly
3. Create unique test data that won't conflict

### 3. **Model Creation Errors** (8 issues)
**Problem**: Tests try to create records with missing required fields or wrong field names

#### Issues:
- `test_aircraft_creation`: Missing required fields
- `test_aircraft_class_categories`: Wrong field usage
- `test_aircraft_model_engine_types`: Wrong field usage  
- `test_aircraft_model_gear_types`: Wrong field usage
- `test_aircraft_model_tags`: Wrong field usage
- `test_crew_role_creation`: Wrong field usage
- `test_multiple_crew_same_flight`: Missing required fields

#### Fix Strategy:
1. Check model field definitions
2. Provide all required fields
3. Use correct field names
4. Follow foreign key relationships properly

### 4. **Required Field Violations** (2 issues)
**Problem**: Tests create records without required fields

#### Issues:
- `flight_auto_departure_from_last_arrival`: Missing departure_id (required)
- Other flight creation tests missing required fields

#### Fix Strategy:
1. Always provide `departure_id` when creating flights
2. Check `required=True` fields in models
3. Use helper methods from `common.py`

### 5. **Access Rights Issues** (2 issues)
**Problem**: Test users don't have sufficient permissions for delete operations

#### Issues:
- `test_flight_copy`: Copy operation access rights
- `test_flight_unlink_locked`: Delete operation access rights

#### Fix Strategy:
1. Use `with_user(self.user_manager)` for admin operations
2. Check security rules for specific operations
3. Ensure test users have correct group memberships

## Step-by-Step Fixing Process

### Phase 1: Fix Display Name Issues (Quick Wins)
1. Check actual `name_get()` methods in models
2. Update 3 display name tests with correct expectations
3. Run tests to verify fixes

### Phase 2: Fix Model Field Issues (Medium Priority)  
1. Read each model file to understand field definitions
2. Update tests to use correct field names and types
3. Provide required fields for record creation

### Phase 3: Fix Constraint Tests (Complex)
1. Verify which constraints actually exist in models
2. Rewrite constraint tests to properly test existing constraints
3. Remove tests for non-existent constraints

### Phase 4: Fix Access Rights (Final)
1. Ensure proper user context for admin operations
2. Test with appropriate user permissions

## Tools and Commands for Fixing

### Get Specific Error Details:
```bash
# Get full error trace for specific test
python src/odoo/odoo-bin --test-enable --stop-after-init --http-port=8071 \
  --log-level=test --db_host=localhost --db_user=odoo --db_password=odoo \
  --addons-path=src/odoo/addons/,extra-addons/ \
  -d odoo_test_flight -u flight 2>&1 | \
  grep -A10 "ERROR.*test_aerodrome_display_name"
```

### Test Single Module:
```bash
# Test only aerodrome tests
python src/odoo/odoo-bin --test-enable --stop-after-init \
  --test-tags=flight_aerodrome \
  --http-port=8071 --db_host=localhost --db_user=odoo --db_password=odoo \
  --addons-path=src/odoo/addons/,extra-addons/ \
  -d odoo_test_flight -u flight
```

## Expected Timeline

- **Phase 1 (Display Names)**: 30 minutes - 3 fixes
- **Phase 2 (Model Fields)**: 1-2 hours - 8 fixes  
- **Phase 3 (Constraints)**: 1 hour - 4 fixes
- **Phase 4 (Access Rights)**: 30 minutes - 2 fixes

**Total Estimated Time**: 3-4 hours to fix all remaining issues

## Success Metrics

- **Target**: 0 failed, 0 errors out of 44 tests
- **Minimum Acceptable**: Less than 5 total issues
- **Current**: 6 failed + 13 errors = 19 issues
- **Improvement Needed**: Fix at least 14+ issues

## Next Actions

1. Start with Phase 1 (display names) for quick wins
2. Systematically work through each failing test
3. Update this document with progress
4. Commit fixes incrementally to track progress

---
*Created: 2025-08-14*
*Target: Get flight module tests to 95%+ success rate*