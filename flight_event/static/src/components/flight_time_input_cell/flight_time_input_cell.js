/** @odoo-module **/

import { Component, onWillRender, useRef, useState } from "@odoo/owl";
import { formatDateTime } from "@web/core/l10n/dates";
import { useDateTimePicker } from "@web/core/datetime/datetime_hook";
import { useService } from "@web/core/utils/hooks";

const { DateTime } = luxon;

/**
 * Shared time input cell component for flight event time entry.
 * Used by both FlightEventTimeMatrix and FlightTimeSummary widgets.
 *
 * Features:
 * - Time parsing with day offset support (e.g., "14:30 +1" for next day)
 * - Timezone support in input (e.g., "14:30 UTC")
 * - Datetime picker integration via clock icon button
 * - Keyboard navigation (Enter to save, Escape to cancel)
 * - Display timezone override for showing times in different timezones
 *
 * @extends Component
 */
export class FlightTimeInputCell extends Component {
  static template = "flight_event.FlightTimeInputCell";
  static props = {
    value: { type: [DateTime, Boolean], optional: true },
    eventCode: { type: Object, optional: true },
    timeKind: { type: Object, optional: true },
    date: DateTime,
    onUpdate: Function,
    readonly: Boolean,
    onTabNavigation: { type: Function, optional: true },
    // Optional: timezone to display the time in (e.g., "UTC", "Europe/Paris")
    // If not set, uses the value's original timezone
    displayTz: { type: String, optional: true },
    // Optional: if true, this cell is display-only (shows converted time but doesn't edit)
    displayOnly: { type: Boolean, optional: true },
  };

  setup() {
    this.inputRef = useRef("time-input");
    this.notification = useService("notification");

    this.state = useState({
      inputValue: "",
      isUserEditing: false,
    });

    const getPickerProps = () => {
      const value = this.props?.value || this.props?.date || DateTime.local();
      return {
        value: value,
        type: "datetime",
      };
    };

    const handleDateTimeUpdate = (value) => {
      if (value && !this.props.displayOnly) {
        this.props.onUpdate(this.props.timeKind, this.props.eventCode, value);
      }
    };

    const dateTimePicker = useDateTimePicker({
      target: "time-input",
      get pickerProps() {
        return getPickerProps();
      },
      onChange: handleDateTimeUpdate,
      onApply: handleDateTimeUpdate,
    });

    this.openPicker = dateTimePicker.open;

    onWillRender(() => {
      if (!this.state.isUserEditing) {
        this.state.inputValue = this.getFormattedValue();
      }
    });
  }

  /**
   * Gets the display value, optionally converted to the display timezone.
   * @returns {DateTime|false} The value in the display timezone
   */
  getDisplayValue() {
    const value = this.props.value;
    if (!value || value === false) {
      return false;
    }

    if (this.props.displayTz) {
      // Convert to UTC first to get the correct instant, then to target timezone
      return value.toUTC().setZone(this.props.displayTz);
    }
    return value;
  }

  /**
   * Formats datetime for display with relative day offset.
   * @returns {String} Formatted time like "14:30" or "14:30 +1" for next day
   */
  getFormattedValue() {
    const displayValue = this.getDisplayValue();

    if (!displayValue || displayValue === false) {
      return "";
    }

    try {
      // Use formatDateTime with explicit timezone to prevent it from
      // converting back to user's local timezone
      const tzOption = this.props.displayTz ? { tz: this.props.displayTz } : {};
      let formatted = formatDateTime(displayValue, {
        format: "HH:mm",
        ...tzOption,
      });

      // Calculate day offset relative to the flight date
      // The flight date is a calendar date (no time), so we compare calendar days
      if (this.props.date && displayValue) {
        // Get the flight date's calendar day (year, month, day)
        const flightYear = this.props.date.year;
        const flightMonth = this.props.date.month;
        const flightDay = this.props.date.day;

        // Get the display value's calendar day in its display timezone
        const displayYear = displayValue.year;
        const displayMonth = displayValue.month;
        const displayDay = displayValue.day;

        // Create comparable dates (just the calendar date, ignoring time)
        const flightDate = DateTime.fromObject({
          year: flightYear,
          month: flightMonth,
          day: flightDay,
        });
        const displayDate = DateTime.fromObject({
          year: displayYear,
          month: displayMonth,
          day: displayDay,
        });

        const dayDiff = Math.floor(displayDate.diff(flightDate, "days").days);
        if (dayDiff !== 0) {
          formatted += ` ${dayDiff > 0 ? "+" : ""}${dayDiff}`;
        }
      }

      return formatted;
    } catch (error) {
      console.warn("FlightTimeInputCell: Failed to format time value", error);
      return "";
    }
  }

  /**
   * Parses user input in formats:
   * - "HH:mm" → Same day at specified time
   * - "HH:mm +D" → D days in future
   * - "HH:mm -D" → D days in past
   * - "HH:mm TZ" → Specified time in timezone
   * - "HH:mm +D TZ" → Combined offset and timezone
   *
   * When displayTz is set, input is interpreted in that timezone.
   *
   * @param {String} inputValue - User typed input
   * @returns {DateTime|null} Parsed DateTime or null if invalid
   */
  parseRelativeTime(inputValue) {
    if (!inputValue || inputValue.trim() === "") {
      return null;
    }

    const match = inputValue.match(
      /^(\d{1,2}):(\d{2})(?:\s+([+-]\d+))?(?:\s+([A-Z]{2,5}))?$/i
    );

    if (!match) {
      return null;
    }

    const [, hours, minutes, dayOffset, timezone] = match;

    const h = parseInt(hours, 10);
    const m = parseInt(minutes, 10);
    if (h < 0 || h > 23 || m < 0 || m > 59) {
      return null;
    }

    // Use explicit timezone from input, or displayTz (user's selected timezone), or browser local
    // This ensures times entered are interpreted in the displayed timezone
    const parseZone =
      timezone?.toUpperCase() || this.props.displayTz || "local";
    const baseDate = this.props.date || DateTime.local();

    // Extract the calendar date from the base date
    // The flight date field is a Date (not DateTime), so it represents a calendar date
    // We need to use the date as-is regardless of timezone
    const year = baseDate.year;
    const month = baseDate.month;
    const day = baseDate.day;

    let date;
    try {
      date = DateTime.fromObject(
        {
          year,
          month,
          day,
          hour: h,
          minute: m,
          second: 0,
          millisecond: 0,
        },
        { zone: parseZone }
      );

      if (!date.isValid) {
        return null;
      }
    } catch (error) {
      console.warn("FlightTimeInputCell: Failed to parse time input", error);
      return null;
    }

    if (dayOffset) {
      date = date.plus({ days: parseInt(dayOffset, 10) });
    }

    return date.isValid ? date : null;
  }

  /**
   * Handle input field blur - parse and update value
   * @param {Event} ev - The blur event
   */
  onInputBlur(ev) {
    // Display-only cells don't process input
    if (this.props.displayOnly) {
      this.state.isUserEditing = false;
      this.state.inputValue = this.getFormattedValue();
      return;
    }

    // Only process if user was actually editing
    // This prevents re-parsing the display value (e.g., "17:50 -1") on blur
    if (!this.state.isUserEditing) {
      return;
    }

    const inputValue = ev.target.value.trim();
    this.state.isUserEditing = false;

    if (!inputValue) {
      this.props.onUpdate(this.props.timeKind, this.props.eventCode, false);
      return;
    }

    const parsed = this.parseRelativeTime(inputValue);
    if (parsed) {
      this.props.onUpdate(this.props.timeKind, this.props.eventCode, parsed);
    } else {
      this.state.inputValue = this.getFormattedValue();
      this.notification.add("Invalid time format. Use: HH:mm or HH:mm +1", {
        type: "warning",
      });
    }
  }

  /**
   * Handle input field keydown
   * @param {KeyboardEvent} ev - The keydown event
   */
  onInputKeydown(ev) {
    // Display-only cells don't process keyboard input for editing
    if (this.props.displayOnly) {
      if (ev.key === "Tab" && this.props.onTabNavigation) {
        const handled = this.props.onTabNavigation(
          ev,
          this.props.timeKind,
          this.props.eventCode
        );
        if (handled) {
          ev.preventDefault();
        }
      }
      return;
    }

    if (ev.key === "Enter") {
      ev.preventDefault();
      const inputValue = ev.target.value.trim();
      if (inputValue) {
        const parsed = this.parseRelativeTime(inputValue);
        if (parsed) {
          this.props.onUpdate(
            this.props.timeKind,
            this.props.eventCode,
            parsed
          );
          this.state.isUserEditing = false;
        }
      }
      ev.target.blur();
    } else if (ev.key === "Escape") {
      ev.preventDefault();
      this.state.inputValue = this.getFormattedValue();
      ev.target.blur();
    } else if (ev.key === "Tab" && this.props.onTabNavigation) {
      const handled = this.props.onTabNavigation(
        ev,
        this.props.timeKind,
        this.props.eventCode
      );
      if (handled) {
        ev.preventDefault();
      }
    }
  }

  /**
   * Handle input field change - update state and mark as editing
   * @param {Event} ev - The input event
   */
  onInputChange(ev) {
    if (!this.props.displayOnly) {
      this.state.isUserEditing = true;
      this.state.inputValue = ev.target.value;
    }
  }

  /**
   * Handle focus - select text for easy editing
   * @param {FocusEvent} ev - The focus event
   */
  onInputFocus(ev) {
    if (!this.props.readonly && !this.props.displayOnly) {
      ev.target.select();
    }
  }

  /**
   * Handle picker button click - open the datetime picker
   */
  onPickerClick() {
    if (!this.props.readonly && !this.props.displayOnly) {
      this.openPicker();
    }
  }

  /**
   * Check if picker button should be shown
   * @returns {Boolean}
   */
  get showPickerButton() {
    return !this.props.readonly && !this.props.displayOnly;
  }

  /**
   * Check if the input should be readonly
   * @returns {Boolean}
   */
  get isReadonly() {
    return this.props.readonly || this.props.displayOnly;
  }

  /**
   * Get tooltip text explaining input format
   * @returns {String}
   */
  get inputTooltip() {
    if (this.props.displayOnly) {
      return this.props.displayTz ? `Time in ${this.props.displayTz}` : "";
    }
    const tz = this.props.displayTz || "local";
    return `Enter time in ${tz}\n` +
      `Format: HH:mm, HH:mm ±D, or HH:mm TZ\n` +
      `Examples: 14:30, 02:15 +1, 23:45 -1 UTC`;
  }
}
