/** @odoo-module **/

import { user } from "@web/core/user";

const { DateTime } = luxon;

/**
 * Get timezone abbreviation for display.
 * Prefers named abbreviations (EST, CET) over numeric offsets.
 * Falls back to "UTC+X" format for consistency.
 *
 * @param {String} tz - IANA timezone name
 * @returns {String} Timezone abbreviation (e.g., "EST", "UTC+4")
 */
export function getTimezoneAbbreviation(tz) {
  if (!tz || tz === "local") {
    return DateTime.local().toFormat("ZZZZ") || "Local";
  }

  const dt = DateTime.local().setZone(tz);
  const abbr = dt.toFormat("ZZZZ");

  // If it's a named abbreviation (like EST, CET), use it
  // Otherwise convert GMT+X to UTC+X for consistency
  if (abbr && !abbr.startsWith("GMT") && !abbr.startsWith("UTC")) {
    return abbr;
  }

  // Return UTC+X format
  const offset = dt.toFormat("Z");
  return `UTC${offset}`;
}

/**
 * Hook to get user's selected timezone and its display label.
 * Uses user.tz from context (set by timezone switcher or user settings).
 *
 * @returns {Object} { userTz, tzLabel }
 *   - userTz: IANA timezone name (e.g., "America/New_York") or "local" as fallback
 *   - tzLabel: Timezone abbreviation for display (e.g., "EST", "UTC+4")
 */
export function useUserTimezone() {
  return {
    /**
     * Get the user's selected timezone
     * @returns {String} IANA timezone name or "local"
     */
    get userTz() {
      return user.tz || "local";
    },

    /**
     * Get timezone abbreviation for column headers
     * @returns {String} Timezone abbreviation (e.g., "CET", "UTC+4")
     */
    get tzLabel() {
      return getTimezoneAbbreviation(user.tz);
    },
  };
}
