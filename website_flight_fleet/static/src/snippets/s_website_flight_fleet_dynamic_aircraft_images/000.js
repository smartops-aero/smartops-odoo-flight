odoo.define('website_flight_fleet.dynamic_aircraft_images', function (require) {
    'use strict';

    const publicWidget = require('web.public.widget');
    const DynamicSnippet = require('website.s_dynamic_snippet');

    const DynamicSnippetAircraftImages = DynamicSnippet.extend({
        selector: '.s_website_flight_fleet_dynamic_aircraft_images',
        disabledInEditableMode: false,
        /**
         * @override
         */
        init: function () {
            this._super.apply(this, arguments);
            this.template_key = 'website_flight_fleet.s_website_flight_fleet_dynamic_aircraft_images';
        },

        /**
         * @override
         */
        _getQWebRenderOptions: function () {
            console.log('_getQWebRenderOptions - this.data:', this.data);
            if (Array.isArray(this.data)) {
                console.log('First item:', this.data[0]);
                if (this.data[0] && typeof this.data[0] === 'object') {
                    console.log('First item properties:', Object.keys(this.data[0]));
                    if (this.data[0]._record) {
                        console.log('First item _record:', this.data[0]._record);
                    }
                }
            }
            return Object.assign(
                this._super.apply(this, arguments),
                {
                    interval: parseInt(this.$target[0].dataset.carouselInterval || 5000),
                    uniqueId: 'aircraftCarousel_' + this.uniqueId,
                }
            );
        },

        /**
         * @override
         */
        _fetchData: async function () {
            console.log('Before _fetchData');
            await this._super.apply(this, arguments);
            console.log('After _fetchData - this.data:', this.data);
        },
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