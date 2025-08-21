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
    console.log("commitChange called with:", { 
      timeKind: timeKind.key, 
      eventCode: eventCode.code, 
      eventCodeId: eventCode.id,
      value 
    });

    if (!value) {
      console.log("commitChange: No value provided, returning");
      return;
    }

    if (!this.list) {
      console.warn('One2many field not yet initialized');
      return;
    }

    console.log("commitChange: Searching for matching records...");
    const matchingRecords = this.list.records.filter(
      (record) =>
        record.data.time_kind === timeKind.key &&
        record.data.code_id[0] === eventCode.id
    );
    
    console.log("commitChange: Found", matchingRecords.length, "matching records");
    
    if (matchingRecords.length === 1) {
      console.log("commitChange: Updating existing record");
      await matchingRecords[0].update({ time: value });
      console.log("commitChange: Record updated successfully");
    } else if (matchingRecords.length === 0) {
      console.log("commitChange: Creating new record");
      // Use the correct method name
      const record = await this.list.addNewRecord({
        mode: "edit",
      });
      const values = {
        time: value,
        time_kind: timeKind.key,
        code_id: [eventCode.id, eventCode.code],
        flight_id: this.props.record.id || this.props.record.resId,
      };
      console.log("commitChange: Setting values on new record:", values);
      await record.update(values);
      console.log("commitChange: New record created and updated successfully");
      
      // Force UI update by triggering a re-render
      this.render();
    } else {
      console.log("commitChange: Multiple records found, showing error");
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
