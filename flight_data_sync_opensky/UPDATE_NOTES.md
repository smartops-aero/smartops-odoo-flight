# Update Notes

## After Installation

If you installed the module before the label fixes, you need to upgrade both modules:

1. **Upgrade flight_data_sync module**:
   ```bash
   # Via Odoo UI:
   Settings → Apps → Search "Flight Data Sync" → Upgrade
   
   # Or via command line:
   odoo-bin -c odoo.conf -d your_database -u flight_data_sync
   ```

2. **Upgrade flight_data_sync_opensky module**:
   ```bash
   # Via Odoo UI:
   Settings → Apps → Search "Flight Data Sync - OpenSky Network" → Upgrade
   
   # Or via command line:
   odoo-bin -c odoo.conf -d your_database -u flight_data_sync_opensky
   ```

## Fixed Issues

- Added proper field labels for API Base URL, Username, and Password
- Fixed view inheritance for OpenSky Network information panel
- All fields now display with proper labels in the form view

## Verify the Fix

After upgrading, open a Flight Data Provider form:
- Navigate to: Flights → Configuration → Data Providers
- Create or edit a provider
- Verify that "API Base URL", "Username", and "Password" fields have visible labels
- When selecting "OpenSky Network" as the service, you should see an info panel
