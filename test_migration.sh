#!/bin/bash

# Odoo 18.0 Migration Test Script
# Usage: ./test_migration.sh /path/to/odoo18

ODOO_PATH=${1:-"./odoo"}
DB_NAME="test_flight_18_$(date +%s)"
ADDONS_PATH="$ODOO_PATH/addons,$(pwd)"

echo "========================================="
echo "Odoo 18.0 Flight Modules Migration Test"
echo "========================================="
echo ""
echo "Odoo Path: $ODOO_PATH"
echo "Test Database: $DB_NAME"
echo "Addons Path: $ADDONS_PATH"
echo ""

# Check if Odoo path exists
if [ ! -f "$ODOO_PATH/odoo-bin" ]; then
    echo "Error: odoo-bin not found at $ODOO_PATH"
    echo "Usage: $0 /path/to/odoo18"
    exit 1
fi

# Create test database
echo "Creating test database..."
createdb "$DB_NAME" || {
    echo "Error: Failed to create database $DB_NAME"
    exit 1
}

# Install all flight modules
echo ""
echo "Installing flight modules..."
python "$ODOO_PATH/odoo-bin" \
    -d "$DB_NAME" \
    --addons-path="$ADDONS_PATH" \
    -i flight,flight_aircraft_spec,flight_data_sync,flight_event,flight_number,flight_portal,flight_uom,website_flight_fleet \
    --stop-after-init \
    --log-level=warn

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS: All modules installed successfully!"
    echo ""
    echo "To run Odoo with the migrated modules:"
    echo "python $ODOO_PATH/odoo-bin -d $DB_NAME --addons-path=$ADDONS_PATH"
else
    echo ""
    echo "❌ ERROR: Module installation failed!"
    echo "Check the logs above for details."
fi

echo ""
echo "To clean up test database:"
echo "dropdb $DB_NAME"