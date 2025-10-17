/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.websiteFleet = publicWidget.Widget.extend({
  selector: ".o_website_fleet",
  events: {
    "click .js_search_button": "_onSearchClick",
  },

  _onSearchClick: function (ev) {
    ev.preventDefault();
    const $form = $(ev.currentTarget).closest("form");
    const term = $form.find('input[name="search"]').val();
    window.location = "/fleet?search=" + encodeURIComponent(term);
  },
});

export default publicWidget.registry.websiteFleet;
