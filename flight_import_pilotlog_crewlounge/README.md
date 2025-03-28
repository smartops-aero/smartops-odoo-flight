# Flight Import PilotLog CrewLounge Module

## Overview
The Flight Import PilotLog CrewLounge module extends the Flight Import PilotLog functionality with specific features for importing pilot logbook data from CrewLounge. This specialized module provides pre-configured mappings and transformations tailored for CrewLounge export formats, simplifying the import process for users of this platform.

## Key Features
- **CrewLounge-Specific Mappings**: Pre-configured field mappings for CrewLounge export formats
- **Custom Transformations**: Specialized data transformations for CrewLounge-specific data formats
- **Simplified Import Process**: Streamlined workflow for CrewLounge data imports
- **Data Validation**: Built-in validation rules specific to CrewLounge data structures
- **Default Templates**: Ready-to-use import templates for common CrewLounge export scenarios

## Module Components
- **CrewLounge Transformers**: Specialized transformation handlers for CrewLounge data
- **Default Mappings**: XML data files defining standard CrewLounge to Odoo field mappings
- **Import Templates**: Pre-configured templates for different CrewLounge export formats
- **Validation Rules**: CrewLounge-specific validation to ensure data integrity

## Integration
This module integrates with:
- Flight Import PilotLog module for core import functionality
- Flight module for aircraft and flight data models
- Flight PilotLog module for storing imported pilot log data

## Technical Details
- **Dependencies**: flight_import_pilotlog, flight_pilotlog
- **Implementation**: Extends flight_import_pilotlog with CrewLounge-specific features
- **Data Structure**: Compatible with standard CrewLounge CSV export formats

## Usage Instructions
1. Navigate to the Flight Import section in your Odoo instance
2. Select the CSV file exported from CrewLounge
3. Choose the appropriate CrewLounge template from the dropdown
4. Assign pilots using the enhanced pilot selection dropdown
5. Preview and validate the data
6. Complete the import process

## Support
For questions or support regarding this module, please contact your system administrator or the module maintainer.

---

This module is part of the SmartOps Odoo Flight suite of applications.
