/** @odoo-module **/

import { Component, onWillUpdateProps } from "@odoo/owl";
import { FlightEventTimeMatrixCell } from "@flight_event/components/flight_event_time_matrix_cell/flight_event_time_matrix_cell";

const { DateTime } = luxon;

export class FlightEventTimeMatrixRenderer extends Component {
  static template = "flight_event.FlightEventTimeMatrixRenderer";
  static components = { FlightEventTimeMatrixCell };
  static props = {
    list: Object,
    eventCodes: Array,
    timeKinds: Array,
    date: DateTime,
    onUpdate: Function,
    readonly: Boolean,
  };

  setup() {
    this._updateProps(this.props);
    onWillUpdateProps((newProps) => this._updateProps(newProps));
  }

  _updateProps(newProps) {
    this.timeKinds = newProps.timeKinds;
    this.eventCodes = newProps.eventCodes;
    
    // Handle case where list might be null/undefined
    const records = newProps.list?.records || [];
    console.log("_updateProps - newProps.list:", newProps.list);
    console.log("_updateProps - records:", records);
    console.log("_updateProps - records length:", records.length);
    
    if (records.length > 0) {
      console.log("Sample record:", records[0]);
      console.log("Sample record data:", records[0].data);
    }
    
    this.matrix = this._getMatrix(records);
  }

  _getMatrix(records = []) {
    // Initialize the matrix using map and fill
    const matrix = Object.fromEntries(
      this.eventCodes.map((eventCode) => [
        eventCode.code,
        Object.fromEntries(
          this.timeKinds.map((timeKind) => [timeKind.key, { value: false }])
        ),
      ])
    );

    // Fill the matrix with actual values from records
    console.log("_getMatrix processing", records.length, "records");
    records.forEach((record, index) => {
      // Data.code_id[1] is the event code
      const eventCode = record.data.code_id[1];
      const timeKind = record.data.time_kind;
      const time = record.data.time;
      
      console.log(`Record ${index}:`, {
        eventCode,
        timeKind, 
        time,
        timeType: typeof time,
        isDateTime: time instanceof DateTime
      });
      
      if (matrix[eventCode] && matrix[eventCode][timeKind] !== undefined) {
        matrix[eventCode][timeKind].value = record.data.time;
        matrix[eventCode][timeKind].record = record;
        console.log(`Set matrix[${eventCode}][${timeKind}] =`, record.data.time);
      } else {
        console.log(`Skipped record - eventCode: ${eventCode}, timeKind: ${timeKind} not found in matrix`);
      }
    });

    return matrix;
  }

  /**
   * Safely get the cell value for a specific event code and time kind
   */
  getCellValue(eventCode, timeKind) {
    console.log("getCellValue called for:", eventCode.code, timeKind.key);
    console.log("Matrix exists:", !!this.matrix);
    console.log("full matrix:" , this.matrix);
    
    if (!this.matrix) {
      console.log("Matrix not initialized yet");
      return false;
    }
    
    const cellData = this.matrix[eventCode.code]?.[timeKind.key];
    console.log("Cell data:", cellData);
    
    // Return the actual value (which could be DateTime or false)
    // Don't convert to false if it's a valid DateTime
    const value = cellData?.value;
    console.log("Returning value:", value, "Type:", typeof value, "Is DateTime:", value instanceof DateTime);
    
    return value !== undefined ? value : false;
  }

  /**
   * Handle cell update from MatrixCell component
   */
  onCellUpdate(timeKind, eventCode, value) {
    console.log("Matrix renderer onCellUpdate:", { timeKind: timeKind.key, eventCode: eventCode.code, value });
    
    // Update the matrix and propagate to parent
    this.matrix[eventCode.code][timeKind.key].value = value;
    this.props.onUpdate(timeKind, eventCode, value);
  }
}

