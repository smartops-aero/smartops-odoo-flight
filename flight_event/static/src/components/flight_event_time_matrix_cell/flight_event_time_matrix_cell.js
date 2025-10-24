/** @odoo-module **/

import { Component, onWillRender, useRef, useState } from "@odoo/owl";
import { formatDateTime } from "@web/core/l10n/dates";
import { useDateTimePicker } from "@web/core/datetime/datetime_hook";
import { useService } from "@web/core/utils/hooks";

const { DateTime } = luxon;

/**
 * Individual cell component for the flight event time matrix.
 * Each cell manages its own datetime picker and displays formatted time with relative day offset.
 * Supports typed input with formats: "HH:mm", "HH:mm +/-D", "HH:mm TZ"
 *
 * @extends Component
 */
export class FlightEventTimeMatrixCell extends Component {
  static template = "flight_event.FlightEventTimeMatrixCell";
  static props = {
    value: { type: [DateTime, Boolean], optional: true },
    eventCode: Object,
    timeKind: Object,
    date: DateTime,
    onUpdate: Function,
    readonly: Boolean,
  };

  setup() {
    this.inputRef = useRef("time-input");
    this.notification = useService("notification");
    this.state = useState({
      inputValue: "",
      isFocused: false,
      isUserEditing: false, // Track if user is actively typing
    });

    const getPickerProps = () => {
      const value = this.props?.value || this.props?.date || DateTime.local();
      return {
        value: value,
        type: "datetime",
      };
    };

    /**
     * Individual datetime picker for this cell.
     * Updates immediately on change for UX, similar to 16.0 behavior.
     */
    const dateTimePicker = useDateTimePicker({
      target: "time-input",
      get pickerProps() {
        return getPickerProps();
      },
      onChange: (value) => {
        // Update immediately when user selects a date/time
        if (value) {
          this.props.onUpdate(this.props.timeKind, this.props.eventCode, value);
        }
      },
      onApply: (value) => {
        // Also handle Apply button click
        if (value) {
          this.props.onUpdate(this.props.timeKind, this.props.eventCode, value);
        }
      },
    });

    this.openPicker = dateTimePicker.open;

    /**
     * Sync display value with props on every render
     * Similar to Odoo's DateTimeField pattern (datetime_field.js:160)
     */
    onWillRender(() => {
      if (!this.state.isUserEditing) {
        this.state.inputValue = this.getFormattedValue();
      }
    });
  }

  /**
   * Formats datetime for display with relative day offset.
   * @returns {String} Formatted time like "14:30" or "14:30 +1" for next day
   */
  getFormattedValue() {
    const value = this.props.value;

    if (!value || value === false) {
      return "";
    }

    try {
      let formatted = formatDateTime(value, { format: "HH:mm" });

      if (this.props.date && value) {
        const dayDiff = Math.floor(
          value.startOf("day").diff(this.props.date.startOf("day"), "days").days
        );
        if (dayDiff !== 0) {
          formatted += ` ${dayDiff > 0 ? "+" : ""}${dayDiff}`;
        }
      }

      return formatted;
    } catch (error) {
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
   * @param {String} inputValue - User typed input
   * @returns {DateTime|null} Parsed DateTime or null if invalid
   */
  parseRelativeTime(inputValue) {
    if (!inputValue || inputValue.trim() === "") {
      return null;
    }

    // Match: HH:mm [+/-D] [TIMEZONE]
    const match = inputValue.match(/^(\d{1,2}):(\d{2})(?:\s+([+-]\d+))?(?:\s+([A-Z]{2,5}))?$/i);

    if (!match) {
      return null;
    }

    const [, hours, minutes, dayOffset, timezone] = match;

    // Validate time values
    const h = parseInt(hours);
    const m = parseInt(minutes);
    if (h < 0 || h > 23 || m < 0 || m > 59) {
      return null;
    }

    let date = this.props.date || DateTime.local();

    // Create datetime with timezone if specified
    if (timezone) {
      try {
        date = DateTime.fromObject(
          {
            year: date.year,
            month: date.month,
            day: date.day,
            hour: h,
            minute: m,
            second: 0,
            millisecond: 0,
          },
          { zone: timezone.toUpperCase() }
        );

        // Check if timezone is valid
        if (!date.isValid) {
          return null;
        }
      } catch (error) {
        return null;
      }
    } else {
      // No timezone - use local
      date = date.set({
        hour: h,
        minute: m,
        second: 0,
        millisecond: 0,
      });
    }

    // Apply day offset if specified
    if (dayOffset) {
      date = date.plus({ days: parseInt(dayOffset) });
    }

    return date.isValid ? date : null;
  }

  /**
   * Handle input field blur - parse and update value
   */
  onInputBlur(ev) {
    const inputValue = ev.target.value.trim();

    // Clear editing and focus state
    this.state.isFocused = false;
    this.state.isUserEditing = false;

    // If empty, clear the value
    if (!inputValue) {
      this.props.onUpdate(this.props.timeKind, this.props.eventCode, false);
      return;
    }

    const parsed = this.parseRelativeTime(inputValue);
    if (parsed) {
      this.props.onUpdate(this.props.timeKind, this.props.eventCode, parsed);
    } else {
      // Invalid input - revert to previous value
      this.state.inputValue = this.getFormattedValue();
      this.notification.add("Invalid time format. Use: HH:mm or HH:mm +1", {
        type: "warning",
      });
    }
  }

  /**
   * Handle input field keydown
   */
  onInputKeydown(ev) {
    if (ev.key === "Enter") {
      ev.preventDefault();
      ev.target.blur(); // Trigger blur to parse
    } else if (ev.key === "Escape") {
      ev.preventDefault();
      // Revert to original value
      this.state.inputValue = this.getFormattedValue();
      ev.target.blur();
    }
  }

  /**
   * Handle input field change - update state and mark as editing
   */
  onInputChange(ev) {
    this.state.isUserEditing = true;
    this.state.inputValue = ev.target.value;
  }

  /**
   * Handle focus - auto-open picker and select text
   */
  onInputFocus(ev) {
    if (!this.props.readonly) {
      // Update focus state to show calendar icon
      this.state.isFocused = true;

      // Select all text for easy editing
      ev.target.select();

      // Auto-open the datetime picker
      this.openPicker();
    }
  }
}
