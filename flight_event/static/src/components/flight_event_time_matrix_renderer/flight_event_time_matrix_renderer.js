/** @odoo-module **/

import { Component, onWillUpdateProps, useState } from "@odoo/owl";
import { formatDateTime } from "@web/core/l10n/dates";
import { useDateTimePicker } from "@web/core/datetime/datetime_hook";

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
    this.state = useState({
      pickerEventCode: null,
      pickerTimeKind: null,
    });
    
    const getPickerProps = () => {
      if (!this.state.pickerEventCode || !this.state.pickerTimeKind) {
        return { value: null, type: "datetime" };
      }
      
      const currentValue = this.matrix[this.state.pickerEventCode.code][this.state.pickerTimeKind.key].value;
      
      return {
        value: currentValue || this.props.date || DateTime.local(),
        type: "datetime",
      };
    };
    
    // Setup datetime picker hook
    const dateTimePicker = useDateTimePicker({
      target: "picker-target",
      get pickerProps() {
        return getPickerProps();
      },
      onChange: (value) => {
        console.log("onChange called with value:", value);
        // Don't update matrix here - let onApply handle the actual update
        // This is just for any UI feedback during selection
      },
      onApply: (value) => {
        console.log("onApply called with value:", value);
        console.log("Picker state:", this.state.pickerEventCode, this.state.pickerTimeKind);
        console.log("Hook state value:", this.pickerState?.value);
        
        // Get the final value from the hook's state and commit to database
        const finalValue = value || this.pickerState?.value;
        if (this.state.pickerEventCode && this.state.pickerTimeKind && finalValue) {
          console.log("Calling updateCell with:", finalValue);
          this.updateCell(this.state.pickerTimeKind, this.state.pickerEventCode, finalValue);
          // Clear picker state
          this.state.pickerEventCode = null;
          this.state.pickerTimeKind = null;
        } else {
          console.log("onApply: Missing required data for updateCell");
        }
      },
    });
    
    // Subscribe to the hook's state
    this.pickerState = useState(dateTimePicker.state);
    this.openPicker = dateTimePicker.open;
    
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
  openPickerForCell(eventCode, timeKind) {
    if (this.props.readonly) {
      return;
    }
    
    // Set up picker context - getPickerProps() will read from this
    this.state.pickerEventCode = eventCode;
    this.state.pickerTimeKind = timeKind;
    
    // Open the picker (uses the hook's open method)
    this.openPicker(0);
  }

  /**
   * Update a cell value
   */
  updateCell(timeKind, eventCode, value) {
    console.log("updateCell called with:", { timeKind: timeKind.key, eventCode: eventCode.code, value });
    
    const currentValue = this.matrix[eventCode.code][timeKind.key].value;
    console.log("Current matrix value:", currentValue);
    
    // Only update if value changed
    if (!currentValue || !value || !currentValue.equals(value)) {
      console.log("Value changed, updating matrix and calling onUpdate");
      this.matrix[eventCode.code][timeKind.key].value = value;
      this.props.onUpdate(timeKind, eventCode, value);
    } else {
      console.log("Value unchanged, skipping update");
    }
  }
}

