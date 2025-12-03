import logging

import pytz

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class TimezoneSwitcherController(http.Controller):
    """Controller for timezone switching operations."""

    @http.route("/web/timezone/switch", type="json", auth="user")
    def switch_timezone(self, timezone):
        """
        Switch the current user's display timezone.

        This updates the session context with the new timezone without
        modifying the user record or any database values.

        :param str timezone: IANA timezone name (e.g., 'America/New_York')
        :return: dict with success status and session info
        """
        # Validate timezone
        if timezone not in pytz.all_timezones_set:
            return {
                "success": False,
                "error": f"Invalid timezone: {timezone}",
                "available_timezones": sorted(pytz.common_timezones),
            }

        # Update session context
        # This is the key: we modify the rendering context, not the database
        request.session.context = dict(request.session.context or {})
        request.session.context["tz"] = timezone

        # Force session save to ensure persistence
        request.session.touch()

        _logger.info(
            "User %s switched display timezone to %s",
            request.env.user.login,
            timezone,
        )

        return {
            "success": True,
            "timezone": timezone,
            "user_context": request.session.context,
        }

    @http.route("/web/timezone/reset", type="json", auth="user")
    def reset_timezone(self):
        """
        Reset to user's default timezone.

        Removes the tz override from session context, falling back to
        the user's configured timezone (res.users.tz).

        :return: dict with success status and default timezone
        """
        # Remove tz from session context
        if request.session.context and "tz" in request.session.context:
            request.session.context = dict(request.session.context)
            del request.session.context["tz"]
            # Force session save to ensure persistence
            request.session.touch()

        # Get user's default timezone
        user_tz = request.env.user.tz or "UTC"

        _logger.info(
            "User %s reset display timezone to default: %s",
            request.env.user.login,
            user_tz,
        )

        return {
            "success": True,
            "timezone": user_tz,
            "user_context": request.session.context,
        }

    @http.route("/web/timezone/current", type="json", auth="user")
    def get_current_timezone(self):
        """
        Get the current display timezone.

        Returns the active timezone from session context, falling back to
        user's default timezone if no override exists.

        :return: dict with current timezone info
        """
        # Check session context first (override)
        session_tz = (
            request.session.context.get("tz") if request.session.context else None
        )

        # Fall back to user's default
        user_tz = request.env.user.tz or "UTC"

        current_tz = session_tz or user_tz

        # is_override is True only if session has a tz AND it differs from user's default
        is_override = bool(session_tz) and session_tz != user_tz

        return {
            "timezone": current_tz,
            "is_override": is_override,
            "user_default": user_tz,
            "session_context": request.session.context,
        }

    @http.route("/web/timezone/list", type="json", auth="user")
    def list_timezones(self, common_only=True):
        """
        Get list of available timezones.

        :param bool common_only: If True, return only common timezones (default: True)
        :return: dict with timezone lists
        """
        if common_only:
            timezones = sorted(pytz.common_timezones)
        else:
            timezones = sorted(pytz.all_timezones)

        # Group by region for better UX
        grouped = {}
        for tz in timezones:
            parts = tz.split("/", 1)
            region = parts[0] if len(parts) > 1 else "Other"
            if region not in grouped:
                grouped[region] = []
            grouped[region].append(tz)

        return {
            "timezones": timezones,
            "grouped": grouped,
            "count": len(timezones),
        }
