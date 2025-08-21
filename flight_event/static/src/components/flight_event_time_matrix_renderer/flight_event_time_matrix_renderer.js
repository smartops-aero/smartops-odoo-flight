/** @odoo-module **/

import { Component, onWillUpdateProps, useRef, useState } from "@odoo/owl";
import { DateTimePickerPopover } from "@web/core/datetime/datetime_picker_popover";
import { formatDateTime } from "@web/core/l10n/dates";
import { useService } from "@web/core/utils/hooks";

const { DateTime } = luxon;

export class FlightEventTimeMatrixRenderer extends Component {
  static template = "flight_event.FlightEventTimeMatrixRenderer";
  static props = {
    list: Object,
    eventCodes: Array,
    timeKinds: Array,
    date: DateTime,
    onUpdate: Function,
    readonly: Boolean,
  };

  setup() {
    this.popover = useService("popover");
    this.state = useState({
      currentCell: null,
    });
    
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
   * Format the datetime value for display in the cell
   * Shows time and relative day offset (e.g., "14:30 +1")
   */
  getFormattedValue(value) {
    if (!value) {
      return "-";
    }
    
    try {
      // Format as HH:mm
      let formatted = formatDateTime(value, { format: "HH:mm" });
      
      // Add relative day if different from base date
      if (this.props.date && value) {
        const dayDiff = Math.floor(
          value.startOf("day").diff(this.props.date.startOf("day"), "days").days
        );
        if (dayDiff !== 0) {
          formatted += ` ${dayDiff > 0 ? '+' : ''}${dayDiff}`;
        }
      }
      
      return formatted;
    } catch (error) {
      console.error("Error formatting date:", error);
      return "-";
    }
  }

  /**
   * Open the date picker popover for a specific cell
   */
  openPicker(eventCode, timeKind, event) {
    if (this.props.readonly) {
      return;
    }
    
    const target = event.target;
    const currentValue = this.matrix[eventCode.code][timeKind.key].value;
    
    // Create a close function for the popover
    const close = () => {
      if (this.popoverCloser) {
        this.popoverCloser();
        this.popoverCloser = null;
      }
    };
    
    // Open the popover with DateTimePicker
    this.popoverCloser = this.popover.add(
      target,
      DateTimePickerPopover,
      {
        pickerProps: {
          value: currentValue || this.props.date || DateTime.local(),
          type: "datetime",
          onSelect: (value) => {
            this.updateCell(timeKind, eventCode, value);
            close();
          },
        },
        close: close,
      },
      {
        popoverClass: "o_datetime_picker_popover",
      }
    );
  }

  /**
   * Update a cell value
   */
  updateCell(timeKind, eventCode, value) {
    const currentValue = this.matrix[eventCode.code][timeKind.key].value;
    
    // Only update if value changed
    if (!currentValue || !value || !currentValue.equals(value)) {
      this.matrix[eventCode.code][timeKind.key].value = value;
      this.props.onUpdate(timeKind, eventCode, value);
    }
  }
}

