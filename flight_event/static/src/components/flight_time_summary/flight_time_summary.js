/** @odoo-module **/

import { Component, onWillRender, onWillStart, useRef, useState } from "@odoo/owl";

import { formatDateTime } from "@web/core/l10n/dates";
import { registry } from "@web/core/registry";
import { useDateTimePicker } from "@web/core/datetime/datetime_hook";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

const { DateTime } = luxon;

/**
 * Event codes in sequence order for the summary display.
 * These are the standard aviation event codes.
 */
const EVENT_SEQUENCE = ["OB", "TO", "LD", "IB"];

/**
 * Labels for each event code
 */
const EVENT_LABELS = {
  OB: "Off Blocks",
  TO: "Take Off",
  LD: "Landing",
  IB: "In Blocks",
};

/**
 * Time input cell component for individual time entry.
 * Handles keyboard navigation to stay within the same time kind column.
 */
class FlightTimeSummaryCell extends Component {
  static template = "flight_event.FlightTimeSummaryCell";
  static props = {
    value: { type: [DateTime, Boolean], optional: true },
    eventCode: String,
    timeKind: String,
    date: DateTime,
    onUpdate: Function,
    readonly: Boolean,
    inputRef: { type: String, optional: true },
  };

  setup() {
    this.inputRef = useRef(this.props.inputRef || "time-input");
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
      if (value) {
        this.props.onUpdate(this.props.timeKind, this.props.eventCode, value);
      }
    };

    const dateTimePicker = useDateTimePicker({
      target: this.props.inputRef || "time-input",
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

    let date = this.props.date || DateTime.local();

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

        if (!date.isValid) {
          return null;
        }
      } catch (error) {
        return null;
      }
    } else {
      date = date.set({
        hour: h,
        minute: m,
        second: 0,
        millisecond: 0,
      });
    }

    if (dayOffset) {
      date = date.plus({ days: parseInt(dayOffset, 10) });
    }

    return date.isValid ? date : null;
  }

  /**
   * Handle input blur event - parse and update value
   * @param {Event} ev - The blur event
   */
  onInputBlur(ev) {
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
   * Handle keyboard navigation.
   * Tab/Shift+Tab moves to next/prev cell in the SAME column (same time kind).
   */
  onInputKeydown(ev) {
    if (ev.key === "Enter") {
      ev.preventDefault();
      ev.target.blur();
    } else if (ev.key === "Escape") {
      ev.preventDefault();
      this.state.inputValue = this.getFormattedValue();
      ev.target.blur();
    } else if (ev.key === "Tab") {
      // Find the next input in the same column
      const currentIndex = EVENT_SEQUENCE.indexOf(this.props.eventCode);
      const direction = ev.shiftKey ? -1 : 1;
      const nextIndex = currentIndex + direction;

      if (nextIndex >= 0 && nextIndex < EVENT_SEQUENCE.length) {
        ev.preventDefault();
        // Find the next input element in the same time kind column
        const container = ev.target.closest(".flight-time-summary");
        const nextInputName = `input-${this.props.timeKind}-${EVENT_SEQUENCE[nextIndex]}`;
        const nextInput = container?.querySelector(`input[name="${nextInputName}"]`);
        if (nextInput) {
          nextInput.focus();
        }
      }
      // If at boundary, let default Tab behavior happen (move to other column or next field)
    }
  }

  onInputChange(ev) {
    this.state.isUserEditing = true;
    this.state.inputValue = ev.target.value;
  }

  onInputFocus(ev) {
    if (!this.props.readonly) {
      ev.target.select();
      this.openPicker();
    }
  }
}

/**
 * Flight Time Summary Widget
 *
 * Displays event times in a compact visual format with real-time duration calculations.
 * Shows Actual and Scheduled times in separate columns with block/flight time indicators.
 *
 * Layout:
 *       ACTUAL              SCHEDULED
 * OB    17:57  ─┐ Block    17:45  ─┐ Block
 * TO    18:05  ─┼─┐ Flight 17:55  ─┼─┐ Flight
 * LD    19:15  ─┼─┘ 1:10   19:05  ─┼─┘ 1:10
 * IB    19:22  ─┘   1:25   19:15  ─┘   1:30
 */
export class FlightTimeSummary extends Component {
  static template = "flight_event.FlightTimeSummary";
  static props = { ...standardFieldProps };
  static components = { FlightTimeSummaryCell };

  setup() {
    this.orm = useService("orm");
    this.notification = useService("notification");

    this.eventCodes = [];
    this.eventCodeMap = {};

    this.state = useState({
      date: null,
    });

    if (this.props.name && this.props.record.activeFields) {
      this.activeField = this.props.record.activeFields[this.props.name];
    }

    onWillStart(async () => {
      const codes = await this.orm.searchRead(
        "flight.event.code",
        [["code", "in", EVENT_SEQUENCE]],
        ["id", "code", "name"]
      );
      this.eventCodes = codes;
      this.eventCodeMap = Object.fromEntries(codes.map((c) => [c.code, c]));
    });

    onWillRender(() => {
      this.state.date = this.props.record.data.date;
      this._updateMatrix();
    });
  }

  get list() {
    return this.props.record.data[this.props.name];
  }

  _updateMatrix() {
    const records = this.list?.records || [];

    // Build matrix: { A: { OB: value, TO: value, ... }, S: { ... } }
    this.matrix = {
      A: {},
      S: {},
    };

    for (const code of EVENT_SEQUENCE) {
      this.matrix.A[code] = { value: false, record: null };
      this.matrix.S[code] = { value: false, record: null };
    }

    for (const record of records) {
      const codeObj = record.data.code_id;
      const eventCode = codeObj ? codeObj[1] : null;
      const timeKind = record.data.time_kind;

      if (eventCode && this.matrix[timeKind] && this.matrix[timeKind][eventCode]) {
        this.matrix[timeKind][eventCode] = {
          value: record.data.time,
          record: record,
        };
      }
    }
  }

  /**
   * Get the time value for a specific event and time kind
   * @param {String} timeKind - The time kind ('A' or 'S')
   * @param {String} eventCode - The event code (OB, TO, LD, IB)
   * @returns {luxon.DateTime|Boolean} The time value or false
   */
  getTimeValue(timeKind, eventCode) {
    return this.matrix?.[timeKind]?.[eventCode]?.value || false;
  }

  /**
   * Calculate duration between two events in the same time kind
   * @param {String} timeKind - The time kind ('A' or 'S')
   * @param {String} startCode - Start event code
   * @param {String} endCode - End event code
   * @returns {String} Formatted duration like "1:25" or ""
   */
  calculateDuration(timeKind, startCode, endCode) {
    const startTime = this.getTimeValue(timeKind, startCode);
    const endTime = this.getTimeValue(timeKind, endCode);

    if (!startTime || !endTime) {
      return "";
    }

    const diffMinutes = endTime.diff(startTime, "minutes").minutes;
    if (diffMinutes < 0) {
      return "";
    }

    const hours = Math.floor(diffMinutes / 60);
    const minutes = Math.round(diffMinutes % 60);
    return `${hours}:${minutes.toString().padStart(2, "0")}`;
  }

  /**
   * Get block duration (OB → IB)
   * @param {String} timeKind - The time kind ('A' or 'S')
   * @returns {String} Formatted duration
   */
  getBlockDuration(timeKind) {
    return this.calculateDuration(timeKind, "OB", "IB");
  }

  /**
   * Get flight duration (TO → LD)
   * @param {String} timeKind - The time kind ('A' or 'S')
   * @returns {String} Formatted duration
   */
  getFlightDuration(timeKind) {
    return this.calculateDuration(timeKind, "TO", "LD");
  }

  /**
   * Get taxi-out duration (OB → TO)
   * @param {String} timeKind - The time kind ('A' or 'S')
   * @returns {String} Formatted duration
   */
  getTaxiOutDuration(timeKind) {
    return this.calculateDuration(timeKind, "OB", "TO");
  }

  /**
   * Get taxi-in duration (LD → IB)
   * @param {String} timeKind - The time kind ('A' or 'S')
   * @returns {String} Formatted duration
   */
  getTaxiInDuration(timeKind) {
    return this.calculateDuration(timeKind, "LD", "IB");
  }

  /**
   * Get the event label
   * @param {String} code - The event code
   * @returns {String} Human readable label
   */
  getEventLabel(code) {
    return EVENT_LABELS[code] || code;
  }

  /**
   * Handle time update from cell
   * @param {String} timeKind - The time kind ('A' or 'S')
   * @param {String} eventCode - The event code
   * @param {luxon.DateTime|Boolean} value - The new time value
   */
  async commitChange(timeKind, eventCode, value) {
    if (!this.list) {
      return;
    }

    const eventCodeObj = this.eventCodeMap[eventCode];
    if (!eventCodeObj) {
      return;
    }

    const cellData = this.matrix[timeKind][eventCode];

    if (cellData.record) {
      // Update existing record
      if (value === false) {
        // Clear the value - we need to delete the record or set time to null
        await cellData.record.update({ time: false });
      } else {
        await cellData.record.update({ time: value });
      }
    } else if (value) {
      // Create new record
      const record = await this.list.addNewRecord({ mode: "edit" });
      await record.update({
        time: value,
        time_kind: timeKind,
        code_id: [eventCodeObj.id, eventCodeObj.code],
        flight_id: this.props.record.id || this.props.record.resId,
      });
      this.render();
    }
  }

  get eventSequence() {
    return EVENT_SEQUENCE;
  }
}

export const flightTimeSummary = {
  component: FlightTimeSummary,
  displayName: "Flight Time Summary",
  supportedTypes: ["one2many"],
};

registry.category("fields").add("flight_time_summary", flightTimeSummary);
