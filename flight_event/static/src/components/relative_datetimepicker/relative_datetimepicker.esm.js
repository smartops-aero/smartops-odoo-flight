/** @odoo-module **/

import {
  formatDateTime,
  luxonToMoment,
  parseDateTime,
} from "@web/core/l10n/dates";
import { DateTimePicker } from "@web/core/datepicker/datepicker";

const { DateTime } = luxon;

function wrapError(fn, defaultValue) {
  return (...args) => {
    const result = [defaultValue, null];
    try {
      result[0] = fn(...args);
    } catch (_err) {
      result[1] = _err;
    }
    return result;
  };
}

export class RelativeDateTimePicker extends DateTimePicker {
  setup() {
    this.baseDate = this.props.baseDate;
    super.setup();
  }

  onWillUpdateProps(nextProps) {
    this.baseDate = nextProps.baseDate;
    super.onWillUpdateProps(nextProps);
  }

  initFormat() {
    this.isLocal = true;
  }

  bootstrapDateTimePicker(commandOrParams) {
    if (typeof commandOrParams === "object") {
      if (this.baseDate) {
        commandOrParams.defaultDate = luxonToMoment(this.baseDate);
      }
    }
    super.bootstrapDateTimePicker(commandOrParams);
  }

  formatValue(value, options) {
    if (!value) {
      return ["", false];
    }

    let [formattedValue, error] = wrapError(formatDateTime, "")(value, options);

    if (
      !error &&
      formattedValue !== "" &&
      this.baseDate &&
      options.format.includes("%R")
    ) {
      const deltaDays = value
        .startOf("day")
        .diff(this.baseDate.startOf("day"), "days").days;
      if (deltaDays !== 0) {
        const relativeDay = deltaDays > 0 ? `+${deltaDays}` : `${deltaDays}`;
        formattedValue = formattedValue.replace("%R", relativeDay);
      } else {
        formattedValue = formattedValue.replace("%R", "");
      }
    }

    return [formattedValue, error];
  }

  parseValue(value, options) {
    const [timeString, deltaDays, timezone] = value.split(
      /\s*(?:([+-]\d+)|([A-Z]{3,4}))\s*$/
    );

    let parsedDate = this.baseDate || DateTime.local();
    const [hours, minutes] = timeString.split(":").map(Number);

    if (!isNaN(hours) && !isNaN(minutes)) {
      if (timezone) {
        parsedDate = DateTime.fromObject(
          {
            year: parsedDate.year,
            month: parsedDate.month,
            day: parsedDate.day,
            hour: hours,
            minute: minutes,
          },
          { zone: timezone }
        );
      } else {
        parsedDate = parsedDate.set({
          hours,
          minutes,
          seconds: 0,
          milliseconds: 0,
        });
      }

      if (deltaDays) {
        parsedDate = parsedDate.plus({ days: parseInt(deltaDays, 10) });
      }
    } else {
      return wrapError(parseDateTime, false)(value, options);
    }

    return [parsedDate, false];
  }
}

RelativeDateTimePicker.template = "web.DatePicker";

RelativeDateTimePicker.props = {
  ...DateTimePicker.props,
  baseDate: { type: DateTime, optional: true },
};

RelativeDateTimePicker.defaultProps = {
  ...DateTimePicker.defaultProps,
  sideBySide: true,
  format: "HH:mm %R",
  defaultFormat: "YYYY-MM-DD HH:mm",
  buttons: {
    showToday: true,
    showClear: true,
    showClose: true,
  },
};
