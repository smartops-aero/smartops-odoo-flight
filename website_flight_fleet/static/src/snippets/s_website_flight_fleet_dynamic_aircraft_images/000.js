odoo.define('website_flight_fleet.dynamic_aircraft_images', function (require) {
    'use strict';

    const publicWidget = require('web.public.widget');
    const DynamicSnippetCarousel = require('website.s_dynamic_snippet_carousel');

    const DynamicSnippetAircraftImages = DynamicSnippetCarousel.extend({
        selector: '.s_website_flight_fleet_dynamic_aircraft_images',
        

        /**
         * Method to be overridden in child components in order to provide a search
         * domain if needed.
         * @override
         * @private
         */
        _getSearchDomain() {
            const searchDomain = this._super.apply(this, arguments);
            const aircraftId = parseInt(this.$el.get(0).dataset.filterByAircraftId);
            const categoryId = parseInt(this.$el.get(0).dataset.filterByCategoryId);
            
            if (aircraftId && aircraftId !== -1) {
                searchDomain.push(['aircraft_id', '=', aircraftId]);
            }
            if (categoryId && categoryId !== -1) {
                searchDomain.push(['category_id', '=', categoryId]);
            }
            return searchDomain;
        },
    });

    publicWidget.registry.dynamic_aircraft_images = DynamicSnippetAircraftImages;
    return DynamicSnippetAircraftImages;
});