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
 *
 * @extends Component
 */
export class FlightTimeInputCell extends Component {
  static template = "flight_event.FlightTimeInputCell";
  static props = {
    value: { type: [DateTime, Boolean], optional: true },
    eventCode: { type: Object, optional: true }, // Can be Object (matrix) or String (summary)
    timeKind: { type: Object, optional: true }, // Can be Object (matrix) or String (summary)
    date: DateTime,
    onUpdate: Function,
    readonly: Boolean,
    // Optional: function to handle Tab navigation (for summary widget column isolation)
    onTabNavigation: { type: Function, optional: true },
  };

  setup() {
    this.inputRef = useRef("time-input");
    this.notification = useService("notification");

    // Track input value and editing state
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

    /**
     * Handler for datetime updates from picker.
     * Used by both onChange and onApply to avoid duplication.
     * @param {DateTime} value - The selected datetime value
     */
    const handleDateTimeUpdate = (value) => {
      if (value) {
        this.props.onUpdate(this.props.timeKind, this.props.eventCode, value);
      }
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
      onChange: handleDateTimeUpdate,
      onApply: handleDateTimeUpdate,
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
          value.startOf("day").diff(this.props.date.startOf("day"), "days")
            .days,
        );
        if (dayDiff !== 0) {
          formatted += ` ${dayDiff > 0 ? "+" : ""}${dayDiff}`;
        }
      }

      return formatted;
    } catch {
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
    const match = inputValue.match(
      /^(\d{1,2}):(\d{2})(?:\s+([+-]\d+))?(?:\s+([A-Z]{2,5}))?$/i,
    );

    if (!match) {
      return null;
    }

    const [, hours, minutes, dayOffset, timezone] = match;

    // Validate time values
    const h = parseInt(hours, 10);
    const m = parseInt(minutes, 10);
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
          { zone: timezone.toUpperCase() },
        );

        // Check if timezone is valid
        if (!date.isValid) {
          return null;
        }
      } catch {
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
      date = date.plus({ days: parseInt(dayOffset, 10) });
    }

    return date.isValid ? date : null;
  }

  /**
   * Handle input field blur - parse and update value
   * @param {Event} ev - The blur event
   */
  onInputBlur(ev) {
    const inputValue = ev.target.value.trim();

    // Clear editing state
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
   * @param {KeyboardEvent} ev - The keydown event
   */
  onInputKeydown(ev) {
    if (ev.key === "Enter") {
      ev.preventDefault();
      // Parse and apply the value
      const inputValue = ev.target.value.trim();
      if (inputValue) {
        const parsed = this.parseRelativeTime(inputValue);
        if (parsed) {
          this.props.onUpdate(
            this.props.timeKind,
            this.props.eventCode,
            parsed,
          );
          this.state.isUserEditing = false;
        }
      }
      // Blur closes the picker automatically
      ev.target.blur();
    } else if (ev.key === "Escape") {
      ev.preventDefault();
      // Revert to original value
      this.state.inputValue = this.getFormattedValue();
      ev.target.blur();
    } else if (ev.key === "Tab" && this.props.onTabNavigation) {
      // Let the parent handle Tab navigation if needed (e.g., summary widget column isolation)
      const handled = this.props.onTabNavigation(
        ev,
        this.props.timeKind,
        this.props.eventCode,
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
    this.state.isUserEditing = true;
    this.state.inputValue = ev.target.value;
  }

  /**
   * Handle focus - select text for easy editing
   * @param {FocusEvent} ev - The focus event
   */
  onInputFocus(ev) {
    if (!this.props.readonly) {
      ev.target.select();
    }
  }

  /**
   * Handle picker button click - open the datetime picker
   */
  onPickerClick() {
    if (!this.props.readonly) {
      this.openPicker();
    }
  }
}
