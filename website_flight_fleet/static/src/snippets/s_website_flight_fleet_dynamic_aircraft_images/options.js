odoo.define('website_flight_fleet.dynamic_aircraft_images_options', function (require) {
    'use strict';

    const options = require('web_editor.snippets.options');
    const dynamicSnippetOptions = require('website.s_dynamic_snippet_options');

    const dynamicSnippetAircraftImagesOptions = dynamicSnippetOptions.extend({
        init() {
            this._super.apply(this, arguments);
            this.modelNameFilter = 'flight.aircraft.image';
            this.aircrafts = {};
            this.categories = {};
            
            console.log("Initializing dynamic aircraft images snippet options");
        },

        /**
         * @override
         */
        onBuilt() {
            this._super(...arguments);
            this.$target[0].dataset['snippet'] = 's_website_flight_fleet_dynamic_aircraft_images';
        },

        /**
         * @override
         */
        async _fetchDynamicFilters() {
            await this._super.apply(this, arguments);
            await this._fetchAircrafts();
            await this._fetchCategories();
        },

        /**
         * @override
         */
        async _renderCustomXML(uiFragment) {
            await this._super.apply(this, arguments);
            await this._renderAircraftSelector(uiFragment);
            await this._renderCategorySelector(uiFragment);
        },

        async _fetchAircrafts() {
            try {
                console.log('Fetching aircrafts...');
                const result = await this._rpc({
                    model: 'flight.aircraft',
                    method: 'search_read',
                    fields: ['id', 'website_display_name'],
                    domain: [],
                });
                this.aircrafts = result.reduce((acc, aircraft) => {
                    acc[aircraft.id] = aircraft;
                    return acc;
                }, {});
            } catch (error) {
                console.error('Error fetching aircrafts:', error);
            }
        },

        async _fetchCategories() {
            try {
                const result = await this._rpc({
                    model: 'flight.aircraft.image.category',
                    method: 'search_read',
                    fields: ['id', 'name'],
                    domain: [],
                });
                this.categories = result.reduce((acc, category) => {
                    acc[category.id] = category;
                    return acc;
                }, {});
            } catch (error) {
                console.error('Error fetching categories:', error);
            }
        },

        async _renderAircraftSelector(uiFragment) {
            const aircraftSelect = uiFragment.querySelector('[data-name="aircraft_opt"]');
            if (aircraftSelect && Object.keys(this.aircrafts).length) {
                for (const [id, aircraft] of Object.entries(this.aircrafts)) {
                    const button = document.createElement('we-button');
                    button.dataset.selectDataAttribute = id;
                    button.textContent = aircraft.website_display_name;
                    aircraftSelect.appendChild(button);
                }
            }
        },

        async _renderCategorySelector(uiFragment) {
            const categorySelect = uiFragment.querySelector('[data-name="category_opt"]');
            if (categorySelect && Object.keys(this.categories).length) {
                for (const [id, category] of Object.entries(this.categories)) {
                    const button = document.createElement('we-button');
                    button.dataset.selectDataAttribute = id;
                    button.textContent = category.name;
                    categorySelect.appendChild(button);
                }
            }
        },

        /**
         * @override
         */
        _setOptionsDefaultValues: function () {
            this._setOptionValue('filterByAircraftId', -1);
            this._setOptionValue('filterByCategoryId', -1);
            this._setOptionValue('carouselInterval', '5000');
            this._super.apply(this, arguments);
        },
    });

    options.registry.dynamic_snippet_aircraft_images = dynamicSnippetAircraftImagesOptions;
    return dynamicSnippetAircraftImagesOptions;
});