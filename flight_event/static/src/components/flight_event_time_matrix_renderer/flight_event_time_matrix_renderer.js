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
    records.forEach((record) => {
      // Data.code_id[1] is the event code
      const eventCode = record.data.code_id[1];
      const timeKind = record.data.time_kind;
      
      if (matrix[eventCode] && matrix[eventCode][timeKind] !== undefined) {
        matrix[eventCode][timeKind].value = record.data.time;
        matrix[eventCode][timeKind].record = record;
      }
    });

    return matrix;
  }

  /**
   * Safely get the cell value for a specific event code and time kind
   */
  getCellValue(eventCode, timeKind) {
    if (!this.matrix) {
      return false;
    }
    
    const cellData = this.matrix[eventCode.code]?.[timeKind.key];
    const value = cellData?.value;
    
    return value !== undefined ? value : false;
  }

  /**
   * Handle cell update from MatrixCell component
   */
  onCellUpdate(timeKind, eventCode, value) {
    // Update the matrix and propagate to parent
    this.matrix[eventCode.code][timeKind.key].value = value;
    this.props.onUpdate(timeKind, eventCode, value);
  }
}

