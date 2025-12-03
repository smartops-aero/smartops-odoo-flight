/** @odoo-module **/

import { Component, onWillRender } from "@odoo/owl";
import { FlightTimeInputCell as FlightEventTimeMatrixCell } from "@flight_event/components/flight_time_input_cell/flight_time_input_cell";

const { DateTime } = luxon;

/**
 * Renders the flight event time matrix as a table.
 * Manages the layout and data flow to individual cell components.
 *
 * @extends Component
 */
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
    // Use onWillRender to rebuild matrix on every render.
    // This ensures changes from other widgets (e.g., summary widget)
    // that share the same One2many field are reflected.
    onWillRender(() => this._rebuildMatrix());
  }

  /**
   * Rebuilds the matrix from current props.
   * Called on every render to pick up changes from shared field data.
   */
  _rebuildMatrix() {
    this.timeKinds = this.props.timeKinds;
    this.eventCodes = this.props.eventCodes;

    const records = this.props.list?.records || [];
    this.matrix = this._getMatrix(records);
  }

  /**
   * Builds a 2D matrix structure from flat records.
   * @param {Array} records
   * @returns {Object}
   */
  _getMatrix(records = []) {
    const matrix = Object.fromEntries(
      this.eventCodes.map((eventCode) => [
        eventCode.code,
        Object.fromEntries(
          this.timeKinds.map((timeKind) => [timeKind.key, { value: false }]),
        ),
      ]),
    );

    records.forEach((record) => {
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
   * @param {Object} eventCode
   * @param {Object} timeKind
   * @returns {luxon.DateTime|false}
   */
  getCellValue(eventCode, timeKind) {
    if (!this.matrix) {
      return false;
    }

    const cellData = this.matrix[eventCode.code]?.[timeKind.key];
    const value = cellData?.value;

    return value === undefined ? false : value;
  }

  /**
   * @param {Object} timeKind
   * @param {Object} eventCode
   * @param {luxon.DateTime} value
   */
  onCellUpdate(timeKind, eventCode, value) {
    this.matrix[eventCode.code][timeKind.key].value = value;
    this.props.onUpdate(timeKind, eventCode, value);
  }
}
