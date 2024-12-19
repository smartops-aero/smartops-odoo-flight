/** @odoo-module */
import options from 'web_editor.snippets.options';

options.registry.WebsiteFlightFleetDynamicCarousel = options.Class.extend({
    start() {
        this._super(...arguments);
        this.updateUI();
    },

    updateUI() {
        const aircraft_id = this.$target.data('aircraft-id') || '0';
        const category_id = this.$target.data('category-id') || '0';
        
        this.$el.find(`[data-select-aircraft="${aircraft_id}"]`).addClass('active');
        this.$el.find(`[data-select-category="${category_id}"]`).addClass('active');
    },

    async selectDataset(previewMode, value, params) {
        const type = params.datasetType;
        const currentTarget = this.$target[0];

        if (type === 'aircraft') {
            this.$target.attr('data-aircraft-id', params.value);
        } else if (type === 'category') {
            this.$target.attr('data-category-id', params.value);
        }

        if (!previewMode) {
            const aircraft_id = this.$target.attr('data-aircraft-id');
            const category_id = this.$target.attr('data-category-id');

            if (aircraft_id !== '0' && category_id !== '0') {
                await this._rpc({
                    route: '/flight/aircraft/images',
                    params: { aircraft_id, category_id },
                }).then(data => {
                    if (data.images?.length) {
                        this._updateCarousel(currentTarget, data);
                        this.$target.find('.editor-message').addClass('d-none');
                        this.$target.find('.dynamic-carousel-container').removeClass('d-none');
                    }
                });
            }
        }
    },

    _updateCarousel(target, data) {
        if (!data.images?.length) return;

        const $carousel = $(target).find('.s_website_flight_fleet_carousel');
        const $inner = $carousel.find('.carousel-inner');
        const $indicators = $carousel.find('.carousel-indicators');

        $inner.empty();
        $indicators.empty();

        data.images.forEach((image, index) => {
            $indicators.append($('<li>', {
                'data-bs-target': '#' + $carousel.attr('id'),
                'data-bs-slide-to': index,
                'class': index === 0 ? 'active' : ''
            }));

            $inner.append($('<div>', {
                'class': `carousel-item oe_img_bg o_bg_img_center${index === 0 ? ' active' : ''}`,
                'data-name': 'Slide',
                'style': `background-image: url(/web/image/flight.aircraft.image/${image.id}/image)`
            }));
        });
    }
});

export default {
    WebsiteFlightFleetDynamicCarousel: options.registry.WebsiteFlightFleetDynamicCarousel,
};