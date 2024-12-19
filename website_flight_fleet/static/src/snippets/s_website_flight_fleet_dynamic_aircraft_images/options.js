odoo.define('website_flight_fleet.s_website_flight_fleet_dynamic_aircraft_images_options', function (require) {
    'use strict';

    const options = require('web_editor.snippets.options');
    const dynamicSnippetOptions = require('website.s_dynamic_snippet_options');

    const dynamicSnippetAircraftImagesOptions = dynamicSnippetOptions.extend({
        init() {
            this._super.apply(this, arguments);
            this.modelNameFilter = 'flight.aircraft.image';
            this.aircrafts = {};
            this.categories = {};
        },

        async _renderCustomXML(uiFragment) {
            await this._super.apply(this, arguments);
            await this._renderAircraftSelector(uiFragment);
            await this._renderCategorySelector(uiFragment);
        },

        async _fetchAircrafts() {
            return await this._rpc({
                model: 'flight.aircraft',
                method: 'search_read',
                kwargs: {
                    domain: [['website_published', '=', true]],
                    fields: ['id', 'website_display_name'],
                },
            });
        },

        async _fetchCategories() {
            return await this._rpc({
                model: 'flight.aircraft.image.category',
                method: 'search_read',
                kwargs: {
                    domain: [['active', '=', true]],
                    fields: ['id', 'name'],
                },
            });
        },

        async _renderAircraftSelector(uiFragment) {
            const aircraftsList = await this._fetchAircrafts();
            this.aircrafts = {};
            for (const aircraft of aircraftsList) {
                this.aircrafts[aircraft.id] = aircraft;
            }
            const selector = uiFragment.querySelector('[data-name="aircraft_opt"]');
            return this._renderSelectUserValueWidgetButtons(selector, this.aircrafts);
        },

        async _renderCategorySelector(uiFragment) {
            const categoriesList = await this._fetchCategories();
            this.categories = {};
            for (const category of categoriesList) {
                this.categories[category.id] = category;
            }
            const selector = uiFragment.querySelector('[data-name="category_opt"]');
            return this._renderSelectUserValueWidgetButtons(selector, this.categories);
        },
    });

    options.registry.dynamic_snippet_aircraft_images = dynamicSnippetAircraftImagesOptions;
    return dynamicSnippetAircraftImagesOptions;
});