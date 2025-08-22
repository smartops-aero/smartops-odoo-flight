/** @odoo-module */

import { JsonField, jsonField } from "@web/views/fields/jsonb/jsonb";
import { registry } from "@web/core/registry";

/**
 * Extended JSON field widget with pretty formatting
 * Extends Odoo's default jsonb widget to provide nice JSON formatting
 */
export class FlightJsonField extends JsonField {
  static template = "flight_json_widget.FlightJsonField";

  get formattedValue() {
    const value = this.props.record.data[this.props.name];
    if (!value) {
      return "";
    }

    try {
      // Pretty format JSON with 2-space indentation
      return JSON.stringify(value, null, 2);
    } catch (error) {
      // Fallback to original formatting if there's an error
      return JSON.stringify(value);
    }
  }
}

export const flightJsonField = {
  ...jsonField,
  component: FlightJsonField,
  displayName: "Pretty JSON",
};

// Register the new widget with the same name for consistency
registry.category("fields").add("flight_json", flightJsonField);
