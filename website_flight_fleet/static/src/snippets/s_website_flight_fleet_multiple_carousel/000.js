odoo.define("website_flight_fleet.multiple_carousel", function (require) {
  const publicWidget = require("web.public.widget");

  publicWidget.registry.WebsiteFlightFleetMultipleCarousel =
    publicWidget.Widget.extend({
      selector: ".s_website_flight_fleet_multiple_carousel",

      start: function () {
        this._super.apply(this, arguments);
        this._initializeCarousel();
        return this;
      },

      destroy: function () {
        this._stopAutoSlide();
        this._super.apply(this, arguments);
      },

      _initializeCarousel: function () {
        const carousel = this.el.querySelector(".multiple-cards-carousel");
        const carouselInner = carousel.querySelector(".carousel-inner");
        const items = carousel.querySelectorAll(".carousel-item");

        this.carousel = carousel;
        // Store the carousel ID
        this.carouselId = carousel.id;
        this.carouselInner = carouselInner;
        this.items = items;
        this.currentIndex = 0;
        this.isAnimating = false;

        // Get interval from data attribute or default to 5 seconds
        const interval = parseFloat(carousel.dataset.interval || "5") * 1000;
        this.interval = interval;

        // Initialize indicators
        this._updateIndicators();

        // Initialize auto-sliding
        this._startAutoSlide();

        // Update item width based on viewport
        this._updateItemWidth();

        // Navigation buttons
        carousel
          .querySelector(".carousel-control-next")
          .addEventListener("click", () => {
            this._stopAutoSlide();
            this._slideNext();
            this._startAutoSlide();
          });

        carousel
          .querySelector(".carousel-control-prev")
          .addEventListener("click", () => {
            this._stopAutoSlide();
            this._slidePrev();
            this._startAutoSlide();
          });

        // Handle mouse interactions
        carouselInner.addEventListener("mouseenter", () =>
          this._stopAutoSlide()
        );
        carouselInner.addEventListener("mouseleave", () =>
          this._startAutoSlide()
        );

        // Handle window resize
        window.addEventListener("resize", () => this._updateItemWidth());

        // Update navigation buttons
        this._updateNavigationButtons();

        // Observe DOM changes to update indicators when slides are added/removed
        this._observeSlideChanges();
      },

      _observeSlideChanges: function () {
        const observer = new MutationObserver(() => {
          this.items = this.carousel.querySelectorAll(".carousel-item");
          this._updateIndicators();
          this._updateNavigationButtons();
        });

        observer.observe(this.carouselInner, {
          // Watch for changes to child elements
          childList: true,
          // Watch for changes in descendants
          subtree: true,
        });
      },

      _updateIndicators: function () {
        const indicatorsContainer = this.carousel.querySelector(
          ".carousel-indicators"
        );
        if (!indicatorsContainer) return;

        // Clear existing indicators
        indicatorsContainer.innerHTML = "";

        // Create new indicators based on number of slides
        Array.from(this.items).forEach((_, index) => {
          const indicator = document.createElement("li");
          indicator.setAttribute("data-bs-target", `#${this.carouselId}`);
          indicator.setAttribute("data-bs-slide-to", index.toString());
          if (index === this.currentIndex) {
            indicator.classList.add("active");
          }

          // Add click handler
          indicator.addEventListener("click", () => {
            this._stopAutoSlide();
            this._slideTo(index);
            this._startAutoSlide();
          });

          indicatorsContainer.appendChild(indicator);
        });
      },

      _slideTo: function (index) {
        if (this.isAnimating || index === this.currentIndex) return;

        this.isAnimating = true;
        this.currentIndex = index;
        this._smoothScroll();

        // Update indicators
        const indicators = this.carousel.querySelectorAll(
          ".carousel-indicators li"
        );
        indicators.forEach((indicator, i) => {
          indicator.classList.toggle("active", i === index);
        });
      },

      _startAutoSlide: function () {
        if (this.autoSlideTimer) {
          clearInterval(this.autoSlideTimer);
        }
        this.autoSlideTimer = setInterval(() => {
          this._slideNext();
        }, this.interval);
      },

      _stopAutoSlide: function () {
        if (this.autoSlideTimer) {
          clearInterval(this.autoSlideTimer);
          this.autoSlideTimer = null;
        }
      },

      _updateItemWidth: function () {
        const viewportWidth = window.innerWidth;
        const itemsPerView =
          viewportWidth >= 992 ? 3 : viewportWidth >= 768 ? 2 : 1;
        this.itemWidth = this.carouselInner.offsetWidth / itemsPerView;
      },

      _slideNext: function () {
        if (this.isAnimating) return;

        const maxIndex = this.items.length - 1;
        if (this.currentIndex < maxIndex) {
          this.currentIndex++;
        } else {
          this.currentIndex = 0;
        }

        this.isAnimating = true;
        this._smoothScroll();
        this._updateIndicators();
      },

      _slidePrev: function () {
        if (this.isAnimating) return;

        if (this.currentIndex > 0) {
          this.currentIndex--;
        } else {
          this.currentIndex = this.items.length - 1;
        }

        this.isAnimating = true;
        this._smoothScroll();
        this._updateIndicators();
      },

      _smoothScroll: function () {
        this.carouselInner.scrollTo({
          left: this.currentIndex * this.itemWidth,
          behavior: "smooth",
        });

        // Update buttons and reset animation flag after transition
        setTimeout(() => {
          this.isAnimating = false;
          this._updateNavigationButtons();
          // Match transition duration from CSS
        }, 500);
      },

      _updateNavigationButtons: function () {
        const prevButton = this.carousel.querySelector(
          ".carousel-control-prev"
        );
        const nextButton = this.carousel.querySelector(
          ".carousel-control-next"
        );

        prevButton.style.display = this.currentIndex <= 0 ? "none" : "flex";
        nextButton.style.display =
          this.currentIndex >= this.items.length - 1 ? "none" : "flex";
      },
    });

  return publicWidget.registry.WebsiteFlightFleetMultipleCarousel;
});
