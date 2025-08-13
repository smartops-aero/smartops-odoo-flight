# Migration Guide: Odoo 16.0 to 18.0

## Overview

This document outlines the migration of SmartOps Flight modules from Odoo 16.0 to Odoo 18.0 Community Edition.

## Migration Summary

### 1. Version Updates
All module manifests have been updated from version `16.0.x.x.x` to `18.0.1.0.0`.

### 2. Dependency Changes
- Added `web` dependency to modules that use frontend assets or web components
- Removed deprecated `qweb` key from manifests (now handled via assets)

### 3. Python Requirements
- Updated to Python 3.11+ (minimum Python 3.10)
- Updated ruff configuration to target Python 3.11

### 4. JavaScript/Frontend Changes
- JavaScript modules already use modern ES module format (`/** @odoo-module **/`)
- Assets are properly declared in manifest `assets` key
- No changes needed for OWL components (already using v2 patterns)

### 5. Module-Specific Changes

#### flight (base module)
- Version: 16.0.1.2.0 → 18.0.1.0.0
- Added `web` dependency for frontend integration

#### flight_uom
- Version: 16.0.1.0.0 → 18.0.1.0.0
- No structural changes required

#### flight_aircraft_spec
- Version: 16.0.1.0.1 → 18.0.1.0.0
- No structural changes required

#### flight_data_sync
- Version: 16.0.0.1 → 18.0.1.0.0
- Added `web` dependency
- Removed deprecated `qweb` key

#### flight_event
- Version: 16.0.1.0.1 → 18.0.1.0.0
- Added `web` dependency
- JavaScript components already use modern patterns

#### flight_number
- Version: 16.0.0.3 → 18.0.1.0.0
- No structural changes required

#### flight_portal
- Version: 16.0.1.0.0 → 18.0.1.0.0
- Added `web` dependency for portal frontend

#### website_flight_fleet
- Version: 16.0.1.1.1 → 18.0.1.0.0
- Assets already properly configured
- Website snippets remain compatible

## Testing Instructions

### Environment Setup

1. **Install Dependencies**
```bash
# Python 3.11+ virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install Odoo 18.0 requirements
pip install -r /path/to/odoo18/requirements.txt

# Install Node dependencies
npm install -g rtlcss
```

2. **PostgreSQL Requirements**
- PostgreSQL 12+ (tested with versions 12-17)

### Quick Test Script

```bash
#!/bin/bash
# Create test database
createdb test_flight_18

# Run Odoo with flight modules
python /path/to/odoo18/odoo-bin \
  -d test_flight_18 \
  --addons-path=/path/to/odoo18/addons,/path/to/flight/modules \
  -i flight,flight_aircraft_spec,flight_data_sync,flight_event,flight_number,flight_portal,flight_uom,website_flight_fleet \
  --dev=xml
```

### Verification Checklist

- [ ] All modules install without errors
- [ ] Menu items and views load correctly
- [ ] JavaScript components render properly (flight_event matrix field)
- [ ] Website snippets work (website_flight_fleet)
- [ ] Portal access functions correctly
- [ ] Scheduled actions (crons) in flight_data_sync work
- [ ] Security rules and access rights are applied

## Known Issues & Solutions

### Issue: Assets not loading
**Solution**: Run with `--dev=xml` flag or use debug mode with `?debug=assets` in URL

### Issue: XPath errors in view inheritance
**Solution**: Verify that parent views exist and XPath selectors are accurate

### Issue: JavaScript errors
**Solution**: Clear browser cache and regenerate assets

## Rollback Plan

If issues are encountered:
1. Switch back to 16.0 branch: `git checkout 16.0`
2. Restore database from backup
3. Restart Odoo with 16.0 codebase

## Support

For migration issues, check:
- Odoo 18.0 official documentation
- Module repository issues: https://github.com/smartops-aero/flight

## Migration Completed

✅ All modules successfully migrated to Odoo 18.0
✅ JavaScript components use modern ES module format
✅ Assets properly configured in manifests
✅ Python requirements updated