/** @odoo-module */

import options from "web_editor.snippets.options";

options.registry.WebsiteFlightFleetMultipleCarousel = options.Class.extend({
  /**
   * @override
   */
  start: function () {
    this._super.apply(this, arguments);
    this._initializeCarousel();
    return this;
  },

  /**
   * @override
   */
  onFocus: function () {
    this._refreshCarousel();
  },

  /**
   * @override
   */
  onClone: function () {
    this._assignUniqueID();
  },

  /**
   * @override
   */
  onBuilt: function () {
    this._assignUniqueID();
  },

  /**
   * @override
   */
  cleanForSave: function () {
    // Reset carousel state before save
    this.$target.find(".carousel-item").removeClass("active");
    this.$target.find(".carousel-item:first").addClass("active");
  },

  //--------------------------------------------------------------------------
  // Options
  //--------------------------------------------------------------------------

  /**
   * @see this.selectClass for parameters
   */
  addSlide: function (previewMode, widgetValue, params) {
    const $carousel = this.$target.find(".carousel-inner");
    const $clone = $carousel.find(".carousel-item:first").clone();

    // Reset the clone's content
    $clone.removeClass("active");
    $clone.find("img").attr({
      src: "/web/image/website.s_carousel_default_image_1",
      alt: "New Slide",
    });

    // Append the new slide
    $carousel.append($clone);

    // Reinitialize the carousel
    this._refreshCarousel();
  },
  /**
   * Changes the animation speed/interval and reinitializes the widget
   *
   * @param {string} previewMode
   * @param {string} value
   * @param {Object} params
   */
  updateInterval: function (previewMode, value, params) {
    // Get the widget instance
    const widget = this.$target.data("WebsiteFlightFleetMultipleCarousel");

    if (widget) {
      // Stop current auto sliding
      widget._stopAutoSlide();

      // Update the interval value
      widget.interval = parseFloat(value) * 1000;

      // Restart auto sliding with new interval
      widget._startAutoSlide();
    }
  },

  //--------------------------------------------------------------------------
  // Private
  //--------------------------------------------------------------------------

  /**
   * Initialize carousel functionality
   * @private
   */
  _initializeCarousel: function () {
    const self = this;
    this.$controls = this.$target.find(
      ".carousel-control-prev, .carousel-control-next"
    );

    // Handle navigation clicks
    this._onNavigationClick = _.throttle(
      this._handleNavigationClick.bind(this),
      500
    );
    this.$controls.on("click.carousel_opt", this._onNavigationClick);
  },

  /**
   * Refresh carousel state
   * @private
   */
  _refreshCarousel: function () {
    this._updateNavigationVisibility();
    this._updateSlidePositions();
  },

  /**
   * Assign unique ID to carousel
   * @private
   */
  _assignUniqueID: function () {
    const uniqueId = `multipleCarousel${Date.now()}`;
    this.$target.find(".multiple-cards-carousel").attr("id", uniqueId);
    this.$target
      .find("[data-bs-target]")
      .attr("data-bs-target", `#${uniqueId}`);
  },

  /**
   * Update navigation buttons visibility
   * @private
   */
  _updateNavigationVisibility: function () {
    const $items = this.$target.find(".carousel-item");
    this.$controls.toggleClass("d-none", $items.length <= 1);
  },

  /**
   * Update slide positions
   * @private
   */
  _updateSlidePositions: function () {
    const $items = this.$target.find(".carousel-item");
    let visibleSlides =
      window.innerWidth >= 992 ? 3 : window.innerWidth >= 768 ? 2 : 1;
  },

  /**
   * Handle navigation click
   * @private
   */
  _handleNavigationClick: function (ev) {
    const direction = $(ev.currentTarget).hasClass("carousel-control-prev")
      ? "prev"
      : "next";
    this._slide(direction);
  },

  /**
   * Slide the carousel
   * @private
   */
  _slide: function (direction) {
    const $items = this.$target.find(".carousel-item");
    const $active = $items.filter(".active");
    const activeIndex = $items.index($active);

    let newIndex;
    if (direction === "prev") {
      newIndex = activeIndex - 1 < 0 ? $items.length - 1 : activeIndex - 1;
    } else {
      newIndex = activeIndex + 1 >= $items.length ? 0 : activeIndex + 1;
    }

    $items.removeClass("active");
    $items.eq(newIndex).addClass("active");

    this._updateSlidePositions();
  },
});

export default {
  WebsiteFlightFleetMultipleCarousel:
    options.registry.WebsiteFlightFleetMultipleCarousel,
};
