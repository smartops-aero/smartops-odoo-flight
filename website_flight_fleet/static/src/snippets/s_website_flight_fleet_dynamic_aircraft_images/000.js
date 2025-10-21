/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import DynamicSnippetCarousel from "@website/snippets/s_dynamic_snippet_carousel/000";

const DynamicSnippetAircraftImages = DynamicSnippetCarousel.extend({
  selector: ".s_website_flight_fleet_dynamic_aircraft_images",

  /**
   * Method to be overridden in child components in order to provide a search
   * domain if needed.
   * @override
   * @private
   */
  _getSearchDomain() {
    const searchDomain = this._super.apply(this, arguments);
    const aircraftId = parseInt(this.$el.get(0).dataset.filterByAircraftId, 10);
    const categoryId = parseInt(this.$el.get(0).dataset.filterByCategoryId, 10);

    if (aircraftId && aircraftId !== -1) {
      searchDomain.push(["aircraft_id", "=", aircraftId]);
    }
    if (categoryId && categoryId !== -1) {
      searchDomain.push(["category_id", "=", categoryId]);
    }
    return searchDomain;
  },
});

publicWidget.registry.dynamic_aircraft_images = DynamicSnippetAircraftImages;

export default DynamicSnippetAircraftImages;
