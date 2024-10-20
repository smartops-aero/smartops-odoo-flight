/** @odoo-module **/

import { Component, onWillUpdateProps } from "@odoo/owl";
import { RelativeDateTimePicker } from "@flight_event/components/relative_datetimepicker/relative_datetimepicker";
import { areDateEquals, formatDateTime } from "@web/core/l10n/dates";

const { DateTime } = luxon;

export class FlightEventTimeMatrixRenderer extends Component {
  setup() {
    this._updateProps(this.props);
    onWillUpdateProps((newProps) => this._updateProps(newProps));
  }

  _updateProps(newProps) {
    this.timeKinds = newProps.timeKinds;
    this.eventCodes = newProps.eventCodes;
    this.matrix = this._getMatrix(newProps.list.records);
  }

  _getMatrix(records = this.list.records) {
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
      // data.code_id[1] is the event code
      const eventCode = record.data.code_id[1];
      const timeKind = record.data.time_kind;
      if (matrix[eventCode] && matrix[eventCode][timeKind] !== undefined) {
        matrix[eventCode][timeKind].value = record.data.time;
        matrix[eventCode][timeKind].record = record;
      }
    });

    return matrix;
  }

  update(timeKind, eventCode, value) {
    if (
      !areDateEquals(this.matrix[eventCode.code][timeKind.key].value, value)
    ) {
      this.matrix[eventCode.code][timeKind.key].value = value;
      this.props.onUpdate(timeKind, eventCode, value);
    }
  }
}

FlightEventTimeMatrixRenderer.components = { RelativeDateTimePicker };
FlightEventTimeMatrixRenderer.template =
  "flight_event.FlightEventTimeMatrixRenderer";

FlightEventTimeMatrixRenderer.props = {
  list: Object,
  eventCodes: Array,
  timeKinds: Array,
  date: DateTime,
  onUpdate: Function,
  readonly: Boolean,
};
