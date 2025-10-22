#!/bin/bash

# Flight Module Test Runner Script
#
# Usage:
#   ./run_tests.sh                                    # Run all module tests
#   ./run_tests.sh flight                             # Run specific module
#   ./run_tests.sh "flight,flight_uom"                # Run multiple modules
#   ./run_tests.sh flight my_test_db                  # Custom database name
#   ./run_tests.sh flight my_test_db 8071             # Custom database and port
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ODOO_PATH="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
FLIGHT_BASE_PATH="$SCRIPT_DIR"

# Activate venv
source "$ODOO_PATH/venv/bin/activate"

# Auto-discover modules with tests directories
discover_test_modules() {
    local modules=()
    for dir in "$SCRIPT_DIR"/*/; do
        if [ -d "${dir}tests" ]; then
            local module_name=$(basename "$dir")
            modules+=("$module_name")
        fi
    done
    # Join array with commas
    echo "$(IFS=,; echo "${modules[*]}")"
}

# Default values - auto-discover all modules with tests
DEFAULT_MODULES=$(discover_test_modules)
MODULE="${1:-$DEFAULT_MODULES}"
TEST_DB="${2:-odoo_test_flight}"
PORT="${3:-8071}"

echo "Running tests for: $MODULE"
echo "Test database: $TEST_DB"
echo "Port: $PORT"

# Run the test directly with proper tag format
python3 "$ODOO_PATH/src/odoo/odoo-bin" \
  -d "$TEST_DB" \
  --db_host=localhost \
  --db_user=odoo \
  --db_password=odoo \
  --addons-path="$ODOO_PATH/src/odoo/addons,$FLIGHT_BASE_PATH" \
  -i "$MODULE" \
  --test-enable \
  --test-tags="$MODULE" \
  --stop-after-init \
  --http-port="$PORT" \
  --log-level=test
