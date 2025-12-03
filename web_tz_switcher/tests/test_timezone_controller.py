from odoo.tests import tagged
from odoo.tests.common import HttpCase


@tagged("post_install", "-at_install")
class TestTimezoneController(HttpCase):
    """Test timezone switching controller endpoints."""

    def test_switch_timezone_valid(self):
        """Test switching to a valid timezone."""
        result = self.url_open(
            "/web/timezone/switch",
            data={"params": {"timezone": "America/New_York"}},
            headers={"Content-Type": "application/json"},
        ).json()

        self.assertTrue(result["result"]["success"])
        self.assertEqual(result["result"]["timezone"], "America/New_York")

    def test_switch_timezone_invalid(self):
        """Test switching to an invalid timezone."""
        result = self.url_open(
            "/web/timezone/switch",
            data={"params": {"timezone": "Invalid/Timezone"}},
            headers={"Content-Type": "application/json"},
        ).json()

        self.assertFalse(result["result"]["success"])
        self.assertIn("error", result["result"])

    def test_reset_timezone(self):
        """Test resetting to user's default timezone."""
        # First switch to a different timezone
        self.url_open(
            "/web/timezone/switch",
            data={"params": {"timezone": "Europe/London"}},
            headers={"Content-Type": "application/json"},
        )

        # Then reset
        result = self.url_open(
            "/web/timezone/reset",
            data={"params": {}},
            headers={"Content-Type": "application/json"},
        ).json()

        self.assertTrue(result["result"]["success"])
        # Should be user's default or UTC
        self.assertIn(result["result"]["timezone"], [self.env.user.tz or "UTC", "UTC"])

    def test_get_current_timezone(self):
        """Test getting current timezone info."""
        result = self.url_open(
            "/web/timezone/current",
            data={"params": {}},
            headers={"Content-Type": "application/json"},
        ).json()

        self.assertIn("timezone", result["result"])
        self.assertIn("is_override", result["result"])
        self.assertIn("user_default", result["result"])

    def test_list_timezones_common(self):
        """Test listing common timezones."""
        result = self.url_open(
            "/web/timezone/list",
            data={"params": {"common_only": True}},
            headers={"Content-Type": "application/json"},
        ).json()

        self.assertIn("timezones", result["result"])
        self.assertIn("grouped", result["result"])
        self.assertGreater(result["result"]["count"], 0)
        # Check some common timezones are present
        self.assertIn("America/New_York", result["result"]["timezones"])
        self.assertIn("Europe/London", result["result"]["timezones"])

    def test_list_timezones_all(self):
        """Test listing all timezones."""
        result = self.url_open(
            "/web/timezone/list",
            data={"params": {"common_only": False}},
            headers={"Content-Type": "application/json"},
        ).json()

        # All timezones should include more than common
        result_common = self.url_open(
            "/web/timezone/list",
            data={"params": {"common_only": True}},
            headers={"Content-Type": "application/json"},
        ).json()

        self.assertGreaterEqual(
            result["result"]["count"], result_common["result"]["count"]
        )

    def test_session_persistence(self):
        """Test that timezone persists in session."""
        # Switch timezone
        self.url_open(
            "/web/timezone/switch",
            data={"params": {"timezone": "Asia/Tokyo"}},
            headers={"Content-Type": "application/json"},
        )

        # Get current timezone
        result = self.url_open(
            "/web/timezone/current",
            data={"params": {}},
            headers={"Content-Type": "application/json"},
        ).json()

        # Should still be Asia/Tokyo
        self.assertEqual(result["result"]["timezone"], "Asia/Tokyo")
        self.assertTrue(result["result"]["is_override"])

    def test_timezone_override_flag(self):
        """Test that override flag is set correctly."""
        # Get current (should be user default, no override)
        result = self.url_open(
            "/web/timezone/current",
            data={"params": {}},
            headers={"Content-Type": "application/json"},
        ).json()

        initial_override = result["result"]["is_override"]

        # Switch to different timezone
        self.url_open(
            "/web/timezone/switch",
            data={"params": {"timezone": "Pacific/Auckland"}},
            headers={"Content-Type": "application/json"},
        )

        # Check override flag
        result = self.url_open(
            "/web/timezone/current",
            data={"params": {}},
            headers={"Content-Type": "application/json"},
        ).json()

        self.assertTrue(result["result"]["is_override"])

        # Reset
        self.url_open(
            "/web/timezone/reset",
            data={"params": {}},
            headers={"Content-Type": "application/json"},
        )

        # Check override flag is cleared
        result = self.url_open(
            "/web/timezone/current",
            data={"params": {}},
            headers={"Content-Type": "application/json"},
        ).json()

        self.assertEqual(result["result"]["is_override"], initial_override)
