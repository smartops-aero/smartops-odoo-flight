odoo.define("website_flight_fleet.fleet", function (require) {
  var publicWidget = require("web.public.widget");

  publicWidget.registry.websiteFleet = publicWidget.Widget.extend({
    selector: ".o_website_fleet",
    events: {
      "click .js_search_button": "_onSearchClick",
    },

    _onSearchClick: function (ev) {
      ev.preventDefault();
      var $form = $(ev.currentTarget).closest("form");
      var term = $form.find('input[name="search"]').val();
      window.location = "/fleet?search=" + encodeURIComponent(term);
    },
  });

  return publicWidget.registry.websiteFleet;
});
