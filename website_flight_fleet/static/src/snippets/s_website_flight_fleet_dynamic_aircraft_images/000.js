odoo.define('website_flight_fleet.dynamic_aircraft_images', function (require) {
    'use strict';

    const publicWidget = require('web.public.widget');
    const DynamicSnippet = require('website.s_dynamic_snippet');

    const DynamicSnippetAircraftImages = DynamicSnippet.extend({
        selector: '.s_website_flight_fleet_dynamic_aircraft_images',
        disabledInEditableMode: false,

        _getSearchDomain() {
            const searchDomain = this._super.apply(this, arguments);
            const aircraftId = parseInt(this.$el.get(0).dataset.aircraftId);
            const categoryId = parseInt(this.$el.get(0).dataset.categoryId);
            
            if (aircraftId > 0) {
                searchDomain.push(['aircraft_id', '=', aircraftId]);
            }
            if (categoryId > 0) {
                searchDomain.push(['category_id', '=', categoryId]);
            }
            return searchDomain;
        },
    });

    publicWidget.registry.dynamic_aircraft_images = DynamicSnippetAircraftImages;
    return DynamicSnippetAircraftImages;
});