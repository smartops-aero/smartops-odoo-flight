#!/bin/bash

# Flight Module Test Runner Script
# This script runs all tests for the SmartOps Flight modules

echo "========================================="
echo "SmartOps Flight Module Test Runner"
echo "========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration - using relative paths from script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ODOO_PATH="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
VENV_PATH="$ODOO_PATH/.venv"
ADDONS_PATH="$ODOO_PATH/extra-addons"
DB_NAME="odoo_test_flight"

# Show resolved paths for verification
echo "Script location: $SCRIPT_DIR"
echo "Odoo path: $ODOO_PATH"
echo "Addons path: $ADDONS_PATH"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_PATH/bin/activate"

# Function to run tests for a specific module
run_module_tests() {
    local module=$1
    local tags=$2

    echo ""
    echo -e "${YELLOW}Testing module: $module${NC}"
    echo "----------------------------------------"

    # Run the tests using the established approach from TESTING_GUIDE.md
    "$ODOO_PATH/src/odoo/odoo-bin" \
        --test-enable \
        --stop-after-init \
        --http-port=8071 \
        --test-tags="$tags" \
        --db_host=localhost \
        --db_user=odoo \
        --db_password=odoo \
        --addons-path="$ODOO_PATH/src/odoo/addons,$ADDONS_PATH" \
        -d "$DB_NAME" \
        -u "$module" 2>&1 | tee -a test_results.log

    # Check exit status
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        echo -e "${GREEN}✓ $module tests passed${NC}"
        return 0
    else
        echo -e "${RED}✗ $module tests failed${NC}"
        return 1
    fi
}

# Initialize results
TOTAL_MODULES=0
PASSED_MODULES=0
FAILED_MODULES=()

# Using existing test database: $DB_NAME
echo "Using test database: $DB_NAME"

# Initialize results file
echo "Test Results - $(date)" > test_results.log
echo "=========================================" >> test_results.log

# Test each module
echo ""
echo "Running tests for all modules..."
echo ""

# Base flight module (44 tests expected)
if run_module_tests "flight" "flight"; then
    ((PASSED_MODULES++))
else
    FAILED_MODULES+=("flight")
fi
((TOTAL_MODULES++))

# UOM module (12 tests expected)
if run_module_tests "flight_uom" "flight_uom"; then
    ((PASSED_MODULES++))
else
    FAILED_MODULES+=("flight_uom")
fi
((TOTAL_MODULES++))

# Flight number module (12 tests expected)
if run_module_tests "flight_number" "flight_number"; then
    ((PASSED_MODULES++))
else
    FAILED_MODULES+=("flight_number")
fi
((TOTAL_MODULES++))

# Aircraft specifications module (9 tests expected)
if run_module_tests "flight_aircraft_spec" "flight_aircraft_spec"; then
    ((PASSED_MODULES++))
else
    FAILED_MODULES+=("flight_aircraft_spec")
fi
((TOTAL_MODULES++))

# Event module (12 tests expected)
if run_module_tests "flight_event" "flight_event"; then
    ((PASSED_MODULES++))
else
    FAILED_MODULES+=("flight_event")
fi
((TOTAL_MODULES++))

# Portal module (13 tests expected)
if run_module_tests "flight_portal" "flight_portal"; then
    ((PASSED_MODULES++))
else
    FAILED_MODULES+=("flight_portal")
fi
((TOTAL_MODULES++))

# Data sync module (8 tests expected)
if run_module_tests "flight_data_sync" "flight_data_sync"; then
    ((PASSED_MODULES++))
else
    FAILED_MODULES+=("flight_data_sync")
fi
((TOTAL_MODULES++))

# Website fleet module (13 tests expected)
if run_module_tests "website_flight_fleet" "website_flight_fleet"; then
    ((PASSED_MODULES++))
else
    FAILED_MODULES+=("website_flight_fleet")
fi
((TOTAL_MODULES++))

# Summary
echo ""
echo "========================================="
echo "Test Summary"
echo "========================================="
echo -e "Total modules tested: ${TOTAL_MODULES}"
echo -e "Passed: ${GREEN}${PASSED_MODULES}${NC}"
echo -e "Failed: ${RED}$((TOTAL_MODULES - PASSED_MODULES))${NC}"

if [ ${#FAILED_MODULES[@]} -gt 0 ]; then
    echo ""
    echo -e "${RED}Failed modules:${NC}"
    for module in "${FAILED_MODULES[@]}"; do
        echo -e "  - ${RED}$module${NC}"
    done
fi

# Test database cleanup skipped (using persistent test database)
echo ""
echo "Test run completed."

# Exit with appropriate code
if [ ${#FAILED_MODULES[@]} -eq 0 ]; then
    echo ""
    echo -e "${GREEN}All tests passed successfully!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}Some tests failed. Check test_results.log for details.${NC}"
    exit 1
fi
