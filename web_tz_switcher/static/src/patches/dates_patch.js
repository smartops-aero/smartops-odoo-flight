/** @odoo-module **/

import { user } from "@web/core/user";
import * as dates from "@web/core/l10n/dates";

/**
 * Patch formatDateTime to use user.tz as default timezone.
 *
 * By default, Odoo's formatDateTime uses Luxon's "default" zone which is
 * the browser's local timezone. This patch makes it respect user.context.tz
 * so the timezone switcher can actually change how dates are displayed.
 */
const originalFormatDateTime = dates.formatDateTime;

dates.formatDateTime = function (value, options = {}) {
  // If no explicit tz option provided and user has a timezone set, use it
  if (!options.tz && user.tz) {
    options = { ...options, tz: user.tz };
  }
  return originalFormatDateTime.call(this, value, options);
};
