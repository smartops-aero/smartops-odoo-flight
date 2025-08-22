/** @odoo-module **/

import { Component } from "@odoo/owl";
import { formatDateTime } from "@web/core/l10n/dates";
import { useDateTimePicker } from "@web/core/datetime/datetime_hook";

const { DateTime } = luxon;

/**
 * Individual cell component for the flight event time matrix.
 * Each cell manages its own datetime picker and displays formatted time with relative day offset.
 *
 * @extends Component
 */
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
    const getPickerProps = () => {
      const value = this.props?.value || this.props?.date || DateTime.local();
      return {
        value: value,
        type: "datetime",
      };
    };

    /**
     * Individual datetime picker for this cell.
     * Uses onApply instead of onChange to prevent auto-closing.
     */
    const dateTimePicker = useDateTimePicker({
      target: "cell",
      get pickerProps() {
        return getPickerProps();
      },
      onChange: (value) => {
        // Intentionally empty - we handle updates in onApply
      },
      onApply: (value) => {
        if (value) {
          this.props.onUpdate(this.props.timeKind, this.props.eventCode, value);
        }
      },
    });

    this.openPicker = dateTimePicker.open;
  }

  /**
   * Formats datetime for display with relative day offset.
   * @returns {string} Formatted time like "14:30" or "14:30 +1" for next day
   */
  getFormattedValue() {
    const value = this.props.value;

    if (!value || value === false) {
      return "-";
    }

    try {
      let formatted = formatDateTime(value, { format: "HH:mm" });

      if (this.props.date && value) {
        const dayDiff = Math.floor(
          value.startOf("day").diff(this.props.date.startOf("day"), "days").days
        );
        if (dayDiff !== 0) {
          formatted += ` ${dayDiff > 0 ? "+" : ""}${dayDiff}`;
        }
      }

      return formatted;
    } catch (error) {
      return "-";
    }
  }

  onClick() {
    if (!this.props.readonly) {
      this.openPicker(0);
    }
  }
}
