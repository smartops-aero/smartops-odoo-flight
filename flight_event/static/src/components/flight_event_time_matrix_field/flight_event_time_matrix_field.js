/** @odoo-module **/

import { Component, onWillStart, onWillUpdateProps, useState } from "@odoo/owl";
import { FlightEventTimeMatrixRenderer } from "@flight_event/components/flight_event_time_matrix_renderer/flight_event_time_matrix_renderer";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";

export class FlightEventTimeMatrixField extends Component {
  static template = "flight_event.FlightEventTimeMatrixField";
  static props = { ...standardFieldProps };
  static components = { FlightEventTimeMatrixRenderer };

  setup() {
    this.orm = useService("orm");
    this.notification = useService("notification");

    // Initialize eventCodes as empty array to prevent undefined errors
    this.eventCodes = [];

    this.state = useState({
      date: this.props.record.data.date,
    });

    // Check if props.name exists before using it
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

    onWillUpdateProps((nextProps) => {
      this.state.date = nextProps.record.data.date;
    });
  }

  getList() {
    // Access the One2many field data from the record
    const fieldValue = this.props.record.data[this.props.name];
    return fieldValue;
  }

  get list() {
    return this.getList();
  }

  async commitChange(timeKind, eventCode, value) {
    if (!value) return;

    const matchingRecords = this.list.records.filter(
      (record) =>
        record.data.time_kind === timeKind.key &&
        record.data.code_id[0] === eventCode.id
    );
    if (matchingRecords.length === 1) {
      await matchingRecords[0].update({ time: value });
    } else if (matchingRecords.length === 0) {
      const record = await this.list.addNew({
        mode: "edit",
      });
      const values = {
        time: value,
        time_kind: timeKind.key,
        code_id: [eventCode.id, eventCode.code],
        flight_id: this.props.record.id || this.props.record.resId,
      };
      await record.update(values);
    } else {
      await this.notification.add(
        "Multiple records found for the same event code and time kind",
        { type: "danger" }
      );
      return;
    }
    // No need to call setDirty - the record update handles this automatically
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
