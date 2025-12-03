/** @odoo-module **/

import { Component, onWillRender, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

import { useUserTimezone } from "../../hooks/use_user_timezone";
import { FlightTimeInputCell } from "../flight_time_input_cell/flight_time_input_cell";

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
 * Wrapper component for FlightTimeInputCell that handles
 * Tab navigation within the same time kind column.
 */
class FlightTimeSummaryCell extends Component {
  static template = "flight_event.FlightTimeSummaryCell";
  static components = { FlightTimeInputCell };
  static props = {
    value: { type: [DateTime, Boolean], optional: true },
    eventCode: String,
    timeKind: String,
    date: DateTime,
    onUpdate: Function,
    readonly: Boolean,
    displayTz: { type: String, optional: true },
    displayOnly: { type: Boolean, optional: true },
  };

  /**
   * Handle Tab navigation to stay within the same time kind column.
   * @param {KeyboardEvent} ev - The keydown event
   * @param {String} timeKind - Current time kind
   * @param {String} eventCode - Current event code
   * @returns {Boolean} True if navigation was handled
   */
  onTabNavigation(ev, timeKind, eventCode) {
    const currentIndex = EVENT_SEQUENCE.indexOf(eventCode);
    const direction = ev.shiftKey ? -1 : 1;
    const nextIndex = currentIndex + direction;

    if (nextIndex >= 0 && nextIndex < EVENT_SEQUENCE.length) {
      // Find the next input element in the same time kind column (local timezone only)
      const container = ev.target.closest(".flight-time-summary");
      const nextEventCode = EVENT_SEQUENCE[nextIndex];
      // Only navigate to editable (non-UTC) cells
      const selector = `input[data-time-kind="${timeKind}"][data-event-code="${nextEventCode}"]:not([data-display-tz="UTC"])`;
      const nextInput = container?.querySelector(selector);
      if (nextInput) {
        nextInput.focus();
        return true;
      }
    }
    return false;
  }
}

/**
 * Flight Time Summary Widget
 *
 * Displays event times in a compact visual format with real-time duration calculations.
 * Shows Actual and Scheduled times in separate columns, each with Local and UTC sub-columns.
 *
 * Layout:
 *         ACTUAL                    SCHEDULED
 *       Local   UTC               Local   UTC
 * OB    17:57  16:57  ─┐ Block   17:45  16:45  ─┐ Block
 * TO    18:05  17:05  ─┼─┐ FLT   17:55  16:55  ─┼─┐ FLT
 * LD    19:15  18:15  ─┼─┘ 1:10  19:05  18:05  ─┼─┘ 1:10
 * IB    19:22  18:22  ─┘   1:25  19:15  18:15  ─┘   1:30
 */
export class FlightTimeSummary extends Component {
  static template = "flight_event.FlightTimeSummary";
  static props = { ...standardFieldProps };
  static components = { FlightTimeSummaryCell };

  setup() {
    this.orm = useService("orm");
    this.notification = useService("notification");
    this.timezone = useUserTimezone();

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

  get userTz() {
    return this.timezone.userTz;
  }

  get localTzLabel() {
    return this.timezone.tzLabel;
  }

  get list() {
    return this.props.record.data[this.props.name];
  }

  _updateMatrix() {
    const records = this.list?.records || [];

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

      if (
        eventCode &&
        this.matrix[timeKind] &&
        this.matrix[timeKind][eventCode]
      ) {
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
      if (value === false) {
        await cellData.record.update({ time: false });
      } else {
        await cellData.record.update({ time: value });
      }
    } else if (value) {
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
