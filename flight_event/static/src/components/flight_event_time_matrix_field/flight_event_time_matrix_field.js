/** @odoo-module **/

import { Component, onWillRender, onWillStart, useState } from "@odoo/owl";
import { FlightEventTimeMatrixRenderer } from "@flight_event/components/flight_event_time_matrix_renderer/flight_event_time_matrix_renderer";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";

import { useUserTimezone } from "@web_tz_switcher/hooks/use_user_timezone";

/**
 * Field widget for displaying and editing flight event times in a matrix format.
 * Manages the relationship between flight events (e.g., takeoff, landing) and their time kinds (actual/scheduled).
 *
 * The widget displays a grid where:
 * - Rows represent event codes (takeoff, landing, etc.)
 * - Columns represent time kinds (Actual, Scheduled), each with Local and UTC sub-columns
 * - Cells contain datetime values with relative day offset display
 *
 * @extends Component
 */
export class FlightEventTimeMatrixField extends Component {
  static template = "flight_event.FlightEventTimeMatrixField";
  static props = { ...standardFieldProps };
  static components = { FlightEventTimeMatrixRenderer };

  setup() {
    this.orm = useService("orm");
    this.notification = useService("notification");
    this.timezone = useUserTimezone();

    this.eventCodes = [];

    this.state = useState({
      date: null,
    });

    if (this.props.name && this.props.record.activeFields) {
      this.activeField = this.props.record.activeFields[this.props.name];
    }

    this.timeKinds = [
      { key: "A", label: "Actual" },
      { key: "S", label: "Scheduled" },
    ];

    onWillStart(async () => {
      this.eventCodes = await this.orm.searchRead(
        "flight.event.code",
        [],
        ["id", "code", "name"]
      );
    });

    onWillRender(() => {
      this.state.date = this.props.record.data.date;
    });
  }

  get userTz() {
    return this.timezone.userTz;
  }

  get localTzLabel() {
    return this.timezone.tzLabel;
  }

  /**
   * @returns {Object} The One2many field value containing flight.event.time records
   */
  get list() {
    return this.props.record.data[this.props.name];
  }

  /**
   * Commits a datetime value change to the database.
   * Either updates an existing flight.event.time record or creates a new one.
   *
   * @param {Object} timeKind - Time kind object with key ('A' or 'S') and label
   * @param {Object} eventCode - Event code object with id, code, and name
   * @param {luxon.DateTime} value - The new datetime value
   */
  async commitChange(timeKind, eventCode, value) {
    if (!value) {
      return;
    }

    if (!this.list) {
      return;
    }

    const matchingRecords = this.list.records.filter(
      (record) =>
        record.data.time_kind === timeKind.key &&
        record.data.code_id[0] === eventCode.id
    );

    if (matchingRecords.length === 1) {
      await matchingRecords[0].update({ time: value });
    } else if (matchingRecords.length === 0) {
      const record = await this.list.addNewRecord({
        mode: "edit",
      });
      const values = {
        time: value,
        time_kind: timeKind.key,
        code_id: [eventCode.id, eventCode.code],
        flight_id: this.props.record.id || this.props.record.resId,
      };
      await record.update(values);
      this.render();
    } else {
      await this.notification.add(
        "Multiple records found for the same event code and time kind",
        { type: "danger" }
      );
      return;
    }
  }
}

export const flightEventTimeMatrixField = {
  component: FlightEventTimeMatrixField,
  displayName: "Flight Event Time Matrix",
  supportedTypes: ["one2many"],
};

registry
  .category("fields")
  .add("flight_event_time_matrix", flightEventTimeMatrixField);
