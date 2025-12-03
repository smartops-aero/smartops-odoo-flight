/** @odoo-module **/

import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { rpc } from "@web/core/network/rpc";

/**
 * Timezone Switcher Service
 *
 * Manages timezone switching for display purposes without modifying database.
 * Integrates with Odoo's user context and triggers view re-rendering.
 */
export const timezoneSwitcherService = {
  dependencies: ["action", "notification"],

  start(env, { action, notification }) {
    const STORAGE_KEY = "web_tz_switcher.current_tz";

    /**
     * Get current active timezone info.
     * Priority: session context > localStorage > user default
     *
     * @returns {Promise<Object>} - { timezone, isOverride, userDefault }
     */
    async function getCurrentTimezone() {
      try {
        const result = await rpc("/web/timezone/current");
        return {
          timezone: result.timezone,
          isOverride: result.is_override,
          userDefault: result.user_default,
        };
      } catch (error) {
        console.error("Failed to get current timezone:", error);
        return {
          timezone: user.context.tz || "UTC",
          isOverride: false,
          userDefault: user.context.tz || "UTC",
        };
      }
    }

    /**
     * Switch to a new timezone.
     * Updates session context and triggers view reload.
     *
     * @param {String} timezone - IANA timezone name (e.g., 'America/New_York')
     * @returns {Promise<Boolean>} - Success status
     */
    async function switchTimezone(timezone) {
      if (!timezone) {
        return false;
      }

      try {
        // Call backend to update session context
        const result = await rpc("/web/timezone/switch", {
          timezone: timezone,
        });

        if (!result.success) {
          notification.add(result.error || "Failed to switch timezone", {
            type: "danger",
          });
          return false;
        }

        // Update user context (affects all datetime rendering)
        user.updateContext({ tz: timezone });

        // Store in localStorage for persistence across sessions
        try {
          localStorage.setItem(STORAGE_KEY, timezone);
        } catch (e) {
          console.warn("Failed to save timezone to localStorage:", e);
        }

        // Trigger soft reload to re-render all datetime fields with new timezone
        await action.doAction({
          type: "ir.actions.client",
          tag: "soft_reload",
        });

        notification.add(`Timezone switched to ${timezone}`, {
          type: "success",
        });

        return true;
      } catch (error) {
        console.error("Failed to switch timezone:", error);
        notification.add("Failed to switch timezone. Please try again.", {
          type: "danger",
        });
        return false;
      }
    }

    /**
     * Reset to user's default timezone.
     * Removes session override and restores user's configured timezone.
     *
     * @returns {Promise<Boolean>} - Success status
     */
    async function resetTimezone() {
      try {
        const result = await rpc("/web/timezone/reset");

        if (!result.success) {
          notification.add("Failed to reset timezone", {
            type: "danger",
          });
          return false;
        }

        // Update user context to user's default
        user.updateContext({ tz: result.timezone });

        // Clear localStorage
        try {
          localStorage.removeItem(STORAGE_KEY);
        } catch (e) {
          console.warn("Failed to clear timezone from localStorage:", e);
        }

        // Trigger soft reload to re-render all datetime fields with new timezone
        await action.doAction({
          type: "ir.actions.client",
          tag: "soft_reload",
        });

        notification.add(`Timezone reset to ${result.timezone}`, {
          type: "info",
        });

        return true;
      } catch (error) {
        console.error("Failed to reset timezone:", error);
        notification.add("Failed to reset timezone. Please try again.", {
          type: "danger",
        });
        return false;
      }
    }

    /**
     * Get list of available timezones.
     *
     * @param {Boolean} commonOnly - Return only common timezones
     * @returns {Promise<Object>} - Timezone lists (flat and grouped)
     */
    async function listTimezones(commonOnly = true) {
      try {
        return await rpc("/web/timezone/list", {
          common_only: commonOnly,
        });
      } catch (error) {
        console.error("Failed to fetch timezones:", error);
        return {
          timezones: [],
          grouped: {},
          count: 0,
        };
      }
    }

    /**
     * Initialize timezone from localStorage on startup.
     * Restores user's last selected timezone if available.
     */
    async function initialize() {
      try {
        const storedTz = localStorage.getItem(STORAGE_KEY);
        if (storedTz && storedTz !== user.context.tz) {
          // Silently restore stored timezone
          await rpc("/web/timezone/switch", {
            timezone: storedTz,
          });
          user.updateContext({ tz: storedTz });
        }
      } catch (e) {
        console.warn("Failed to initialize timezone from storage:", e);
      }
    }

    // Initialize on service start
    initialize();

    return {
      getCurrentTimezone,
      switchTimezone,
      resetTimezone,
      listTimezones,
    };
  },
};

registry.category("services").add("timezone_switcher", timezoneSwitcherService);
