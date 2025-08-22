/** @odoo-module **/

import { Component, onWillUpdateProps } from "@odoo/owl";
import { FlightEventTimeMatrixCell } from "@flight_event/components/flight_event_time_matrix_cell/flight_event_time_matrix_cell";

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
    this._updateProps(this.props);
    onWillUpdateProps((newProps) => this._updateProps(newProps));
  }

  /**
   * @param {Object} newProps
   */
  _updateProps(newProps) {
    this.timeKinds = newProps.timeKinds;
    this.eventCodes = newProps.eventCodes;

    const records = newProps.list?.records || [];
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
          this.timeKinds.map((timeKind) => [timeKind.key, { value: false }])
        ),
      ])
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

    return value !== undefined ? value : false;
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
