/** @odoo-module */
import options from 'web_editor.snippets.options';

options.registry.WebsiteFlightFleetDynamicCarousel = options.Class.extend({
    start() {
        console.log('WebsiteFlightFleetDynamicCarousel: start() called');
        this._super(...arguments);
        this.updateUI();
    },

    updateUI() {
        console.log('WebsiteFlightFleetDynamicCarousel: updateUI() called');
        const aircraft_id = this.$target.attr('data-aircraft-id') || '0';
        const category_id = this.$target.attr('data-category-id') || '0';
        
        this.$el.find('[data-name="aircraft_opt"]').removeClass('active');
        this.$el.find('[data-name="category_opt"]').removeClass('active');
        
        this.$el.find(`[data-select-dataset="${aircraft_id}"][data-name="aircraft_opt"]`).addClass('active');
        this.$el.find(`[data-select-dataset="${category_id}"][data-name="category_opt"]`).addClass('active');
    },

    async selectDataset(previewMode, value, params) {
        console.log('selectDataset called with:', { previewMode, value, params });
        
        const optName = params.name;
        const selectedValue = value;

        if (optName === 'aircraft_opt') {
            this.$target.attr('data-aircraft-id', selectedValue);
        } else if (optName === 'category_opt') {
            this.$target.attr('data-category-id', selectedValue);
        }

        if (!previewMode) {
            const aircraft_id = this.$target.attr('data-aircraft-id');
            const category_id = this.$target.attr('data-category-id');

            if (aircraft_id !== '0' || category_id !== '0') {
                try {
                    const data = await this._rpc({
                        route: '/flight/aircraft/images',
                        params: { aircraft_id, category_id },
                    });

                    if (data.images?.length) {
                        this._updateCarousel(this.$target[0], data);
                        this.$target.find('.editor-message').addClass('d-none');
                        this.$target.find('.dynamic-carousel-container').removeClass('d-none');
                    } else {
                        this.$target.find('.editor-message').removeClass('d-none');
                        this.$target.find('.dynamic-carousel-container').addClass('d-none');
                    }
                } catch (error) {
                    console.error('Error fetching images:', error);
                }
            }
        }
        
        this.updateUI();
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

            const $item = $('<div>', {
                'class': `carousel-item oe_img_bg o_bg_img_center${index === 0 ? ' active' : ''}`,
                'data-name': 'Slide',
                'style': `background-image: url(/web/image/flight.aircraft.image/${image.id}/image)`
            });

            if (image.description) {
                $item.append($('<div>', {
                    'class': 'carousel-caption',
                    'text': image.description
                }));
            }

            $inner.append($item);
        });
    }
});

export default {
    WebsiteFlightFleetDynamicCarousel: options.registry.WebsiteFlightFleetDynamicCarousel,
};