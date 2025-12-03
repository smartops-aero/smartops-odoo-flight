{
    "name": "Web Timezone Switcher",
    "version": "18.0.1.0.0",
    "category": "Web",
    "summary": "Real-time timezone switching for display without database updates",
    "description": """
Web Timezone Switcher
=====================

Provides a systray dropdown to switch display timezone in real-time without
updating the database.

Features:
---------
* Systray dropdown with IANA timezone selector
* Session-based timezone storage (doesn't modify user record)
* Automatic re-rendering of datetime fields
* Falls back to user's default timezone
* Works with all standard Odoo datetime widgets
* Timezone preference persists across page loads
* Optional localStorage fallback for better UX

Technical:
----------
* Uses Odoo's context mechanism (tz parameter)
* All database times remain in UTC
* Only affects rendering/display
* Patches formatDateTime to use user.tz instead of browser timezone
* Triggers selective re-rendering of current view via soft_reload

Perfect for:
------------
* Aviation operations spanning multiple timezones
* Global teams working across regions
* Support staff handling international customers
* Any business requiring multi-timezone visibility
    """,
    "author": "Apexive Solutions LLC",
    "website": "https://apexive.com",
    "license": "LGPL-3",
    "depends": ["web"],
    "data": [
        "security/ir.model.access.csv",
        "data/timezone_data.xml",
        "views/webclient_templates.xml",
    ],
    "assets": {
        "web.assets_backend": [
            # Patches must load first to override core functions
            "web_tz_switcher/static/src/patches/*.js",
            # Hooks (shared utilities)
            "web_tz_switcher/static/src/hooks/*.js",
            # Services
            "web_tz_switcher/static/src/services/timezone_service.js",
            # Components
            "web_tz_switcher/static/src/components/timezone_switcher_menu/*.js",
            "web_tz_switcher/static/src/components/timezone_switcher_menu/*.xml",
            "web_tz_switcher/static/src/components/timezone_switcher_menu/*.scss",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
