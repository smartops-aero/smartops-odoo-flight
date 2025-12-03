/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownGroup } from "@web/core/dropdown/dropdown_group";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { rpc } from "@web/core/network/rpc";

import { getTimezoneAbbreviation } from "../../hooks/use_user_timezone";

const { DateTime } = luxon;

/**
 * Timezone Switcher Systray Menu
 *
 * Displays a dropdown in the systray for switching display timezones.
 * Shows current timezone and provides quick access to common zones.
 */
export class TimezoneSwitcherMenu extends Component {
  static template = "web_tz_switcher.TimezoneSwitcherMenu";
  static components = { Dropdown, DropdownGroup, DropdownItem };
  static props = {};

  setup() {
    this.timezoneSwitcher = useService("timezone_switcher");

    this.state = useState({
      currentTimezone: user.context.tz || "UTC",
      isOverride: false,
      timezones: [],
      groupedTimezones: {},
      searchQuery: "",
      showAllRegions: false,
      currentTime: DateTime.now(),
    });

    onWillStart(async () => {
      await this.loadTimezones();
      await this.updateCurrentTimezone();
      // Update time every second
      setInterval(() => {
        this.state.currentTime = DateTime.now();
      }, 1000);
    });
  }

  /**
   * Load available timezones from backend.
   */
  async loadTimezones() {
    const result = await this.timezoneSwitcher.listTimezones(true);
    this.state.timezones = result.timezones || [];
    this.state.groupedTimezones = result.grouped || {};
  }

  /**
   * Update current timezone state.
   * Uses backend's is_override flag which correctly compares against user's DB timezone.
   */
  async updateCurrentTimezone() {
    try {
      const result = await rpc("/web/timezone/current");
      this.state.currentTimezone = result.timezone;
      this.state.isOverride = result.is_override;
    } catch (error) {
      console.error("Failed to get current timezone:", error);
    }
  }

  /**
   * Get display label for current timezone.
   * Shows shortened name and current time.
   */
  get currentTimezoneLabel() {
    const tz = this.state.currentTimezone;
    const parts = tz.split("/");
    const shortName = parts[parts.length - 1].replace(/_/g, " ");
    const time = this.state.currentTime.setZone(tz).toFormat("HH:mm");
    return `${shortName} (${time})`;
  }

  /**
   * Get formatted current time in selected timezone.
   */
  get currentTimeFormatted() {
    return this.state.currentTime
      .setZone(this.state.currentTimezone)
      .toFormat("HH:mm:ss");
  }

  /**
   * Get short timezone abbreviation (e.g., "EST", "PST", "UTC+4").
   */
  get currentTimezoneShort() {
    return getTimezoneAbbreviation(this.state.currentTimezone);
  }

  /**
   * Get filtered timezones based on search query.
   */
  get filteredTimezones() {
    const query = this.state.searchQuery.toLowerCase();
    if (!query) {
      return this.state.timezones;
    }
    return this.state.timezones.filter((tz) =>
      tz.toLowerCase().includes(query),
    );
  }

  /**
   * Get grouped timezones filtered by search.
   */
  get filteredGroupedTimezones() {
    const filtered = {};
    const query = this.state.searchQuery.toLowerCase();

    for (const [region, tzList] of Object.entries(
      this.state.groupedTimezones,
    )) {
      const matchingTzs = query
        ? tzList.filter((tz) => tz.toLowerCase().includes(query))
        : tzList;

      if (matchingTzs.length > 0) {
        filtered[region] = matchingTzs;
      }
    }

    return filtered;
  }

  /**
   * Get list of featured/common timezone regions.
   */
  get featuredRegions() {
    return ["America", "Europe", "Asia", "Pacific"];
  }

  /**
   * Get regions to display based on showAllRegions state.
   */
  get visibleRegions() {
    if (this.state.showAllRegions || this.state.searchQuery) {
      return Object.keys(this.filteredGroupedTimezones).sort();
    }
    return this.featuredRegions.filter(
      (region) => region in this.filteredGroupedTimezones,
    );
  }

  /**
   * Handle timezone selection.
   * @param {string} timezone - Selected IANA timezone
   */
  async onTimezoneSelect(timezone) {
    const success = await this.timezoneSwitcher.switchTimezone(timezone);
    if (success) {
      await this.updateCurrentTimezone();
    }
  }

  /**
   * Handle reset to user default timezone.
   */
  async onResetTimezone() {
    const success = await this.timezoneSwitcher.resetTimezone();
    if (success) {
      await this.updateCurrentTimezone();
    }
  }

  /**
   * Handle search input change.
   * @param {Event} ev - Input event
   */
  onSearchInput(ev) {
    this.state.searchQuery = ev.target.value;
  }

  /**
   * Clear search query.
   */
  onClearSearch() {
    this.state.searchQuery = "";
  }

  /**
   * Toggle showing all regions.
   */
  onToggleAllRegions() {
    this.state.showAllRegions = !this.state.showAllRegions;
  }

  /**
   * Format timezone display name.
   * @param {string} timezone - IANA timezone name
   * @returns {string} - Formatted display name
   */
  formatTimezoneName(timezone) {
    return timezone.replace(/_/g, " ");
  }

  /**
   * Get UTC offset for a timezone.
   * @param {string} timezone - IANA timezone name
   * @returns {string} - UTC offset (e.g., "UTC+5:30")
   */
  getTimezoneOffset(timezone) {
    const dt = DateTime.now().setZone(timezone);
    const offset = dt.offset / 60; // Convert minutes to hours
    const hours = Math.floor(Math.abs(offset));
    const minutes = Math.abs(offset) % 1 === 0 ? "00" : "30";
    const sign = offset >= 0 ? "+" : "-";
    return `UTC${sign}${hours}:${minutes}`;
  }
}

// Register in systray
export const systrayItem = {
  Component: TimezoneSwitcherMenu,
};

// sequence: 0 places it next to user menu (rightmost area)
registry
  .category("systray")
  .add("TimezoneSwitcherMenu", systrayItem, { sequence: 0 });
