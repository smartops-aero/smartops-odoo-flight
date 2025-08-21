/** @odoo-module **/

import { Component } from "@odoo/owl";
import { formatDateTime } from "@web/core/l10n/dates";
import { useDateTimePicker } from "@web/core/datetime/datetime_hook";

const { DateTime } = luxon;

export class FlightEventTimeMatrixCell extends Component {
  static template = "flight_event.FlightEventTimeMatrixCell";
  static props = {
    value: { type: [DateTime, Boolean], optional: true },
    eventCode: Object,
    timeKind: Object,
    date: DateTime,
    onUpdate: Function,
    readonly: Boolean,
  };

  setup() {
    // Setup datetime picker hook for this specific cell  
    const getPickerProps = () => {
      console.log("MatrixCell getPickerProps - this.props:", this.props);
      const value = this.props?.value || this.props?.date || DateTime.local();
      console.log("MatrixCell pickerProps - value:", value, "eventCode:", this.props?.eventCode?.code, "timeKind:", this.props?.timeKind?.key);
      return {
        value: value,
        type: "datetime",
      };
    };

    const dateTimePicker = useDateTimePicker({
      target: "cell",
      get pickerProps() {
        return getPickerProps();
      },
      onChange: (value) => {
        console.log("Cell onChange:", this.props.eventCode.code, this.props.timeKind.key, value);
        // Don't update here - let onApply handle it
      },
      onApply: (value) => {
        console.log("Cell onApply:", this.props.eventCode.code, this.props.timeKind.key, value);
        if (value) {
          this.props.onUpdate(this.props.timeKind, this.props.eventCode, value);
        }
      },
    });
    
    this.openPicker = dateTimePicker.open;
  }

  /**
   * Format the datetime value for display in the cell
   * Shows time and relative day offset (e.g., "14:30 +1")
   */
  getFormattedValue() {
    const value = this.props.value;
    console.log("MatrixCell getFormattedValue - value:", value, "type:", typeof value, "eventCode:", this.props.eventCode?.code, "timeKind:", this.props.timeKind?.key);
    
    // Check for falsy values or specifically false
    if (!value || value === false) {
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
      
      console.log("MatrixCell formatted value:", formatted);
      return formatted;
    } catch (error) {
      console.error("Error formatting date:", error, "for value:", value);
      return "-";
    }
  }

  onClick() {
    if (!this.props.readonly) {
      this.openPicker(0);
    }
  }
}