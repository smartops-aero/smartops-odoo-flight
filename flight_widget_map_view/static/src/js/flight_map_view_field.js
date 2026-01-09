/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, onMounted, onPatched } from "@odoo/owl";

export class FlightMapViewField extends Component {
  static template = "flight_widget_map_view.FlightMapViewField";
  static props = {
    ...standardFieldProps,
    height: { type: String, optional: true },
    width: { type: String, optional: true },
    animate: { type: Boolean, optional: true },
  };

  setup() {
    this.mapId = `map_${Math.random().toString(36).substring(2, 11)}`;

    onMounted(() => {
      this._setupMap();
    });

    onPatched(() => {
      this._updateMapData();
    });
  }

  get mapStyle() {
    // Get dimensions from widget props (passed as options in the view)
    const height = this.props.height || "400px";
    const width = this.props.width || "400px";
    return `height: ${height}; width: ${width};`;
  }

  get mapData() {
    try {
      const value = this.props.record.data[this.props.name];
      const parsed =
        typeof value === "string" ? JSON.parse(value || "{}") : value || {};
      return parsed;
    } catch (e) {
      console.warn(
        "Invalid map data JSON:",
        e,
        "Raw value:",
        this.props.record.data[this.props.name]
      );
      return {};
    }
  }

  _setupMap() {
    // Ensure Leaflet is loaded
    if (typeof window.L === "undefined") {
      console.error("Leaflet library not loaded");
      return;
    }

    // Skip if map already exists
    if (this.map) {
      return;
    }

    this._initializeMap();
  }

  _updateMapData() {
    if (this.map) {
      this._renderMapData();
    } else {
      this._setupMap();
    }
  }

  _initializeMap() {
    // Wait for DOM to be ready
    setTimeout(() => {
      const mapElement = document.getElementById(this.mapId);
      if (!mapElement) {
        console.warn("Map element not found, ID:", this.mapId);
        return;
      }

      try {
        // Initialize Leaflet map
        this.map = L.map(this.mapId, {
          center: [0, 0],
          zoom: 2,
          scrollWheelZoom: true,
        });

        // Add OpenStreetMap tiles
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution: "© OpenStreetMap contributors",
        }).addTo(this.map);

        // Render map data
        this._renderMapData();
      } catch (error) {
        console.error("Error initializing map:", error);
      }
    }, 200);
  }

  _renderMapData() {
    if (!this.map) return;

    const data = this.mapData;

    // Clear existing layers
    this.map.eachLayer((layer) => {
      if (layer !== this.map._layers[Object.keys(this.map._layers)[0]]) {
        this.map.removeLayer(layer);
      }
    });

    // Render paths
    if (data.paths && Array.isArray(data.paths)) {
      data.paths.forEach((path) => this._renderPath(path));
    }

    // Render markers
    if (data.markers && Array.isArray(data.markers)) {
      data.markers.forEach((marker) => this._renderMarker(marker));
    }

    // Fit bounds to show all elements
    this._fitMapBounds(data);
  }

  _renderPath(pathData) {
    if (!pathData.points || !Array.isArray(pathData.points)) return;

    const options = pathData.options || {};
    const polylineOptions = {
      color: options.color || "#3388ff",
      weight: options.weight || 3,
      opacity: options.opacity || 1.0,
    };

    if (options.dashArray) {
      polylineOptions.dashArray = options.dashArray;
    }

    const polyline = L.polyline(pathData.points, polylineOptions);
    polyline.addTo(this.map);

    // Add animation if: view allows it (animate !== false) AND path requests it
    const viewAllowsAnimation = this.props.animate !== false;
    const pathRequestsAnimation = options.animated;
    if (viewAllowsAnimation && pathRequestsAnimation) {
      this._animatePath(polyline, options);
    }
  }

  _renderMarker(markerData) {
    if (!markerData.position || !Array.isArray(markerData.position)) return;

    const options = markerData.options || {};
    let marker;

    // Create custom icon from map data
    if (options.icon) {
      let customIcon;

      // Check if it's a file path/URL
      if (options.icon.startsWith("/") || options.icon.startsWith("http")) {
        customIcon = L.icon({
          iconUrl: options.icon,
          iconSize: [24, 24],
          iconAnchor: [12, 12],
        });
      } else {
        // Treat as HTML content (FontAwesome, emoji, or custom HTML)
        customIcon = L.divIcon({
          html: options.icon,
          iconSize: options.iconSize || [28, 28],
          iconAnchor: options.iconAnchor || [14, 14],
          className: options.iconClass || "",
        });
      }

      marker = L.marker(markerData.position, { icon: customIcon });
    } else {
      marker = L.marker(markerData.position);
    }

    if (options.popup) {
      marker.bindPopup(options.popup);
    }

    if (options.label) {
      marker.bindTooltip(options.label, {
        permanent: true,
        direction: "bottom",
      });
    }

    marker.addTo(this.map);
  }

  _animatePath(polyline, options) {
    if (!options.animations || !Array.isArray(options.animations)) return;

    // Create animated marker
    const animatedMarker = this._createAnimatedMarker(options);
    animatedMarker.addTo(this.map);

    // Use GSAP for animations with initial state
    this._createGSAPTimeline(
      animatedMarker,
      options.animations,
      options.loop,
      options.initialState
    );
  }

  _createAnimatedMarker(options) {
    const icon = L.divIcon({
      html: options.markerHtml || "✈️",
      iconSize: options.markerSize || [16, 16],
      iconAnchor: options.markerAnchor || [8, 8],
      className: options.markerClass || "",
    });

    const initialPos = options.initialPosition || [0, 0];
    const marker = L.marker(initialPos, { icon });

    // Initialize for GSAP animation
    marker._animationData = {
      element: null,
      position: initialPos,
    };

    return marker;
  }

  _createGSAPTimeline(marker, animations, loop = false, initialState = {}) {
    // Wait for marker element to be available
    setTimeout(() => {
      const element = marker.getElement();
      if (!element) {
        console.warn("Marker element not found!");
        return;
      }

      // Check GSAP availability
      if (typeof gsap === "undefined") {
        console.error("GSAP not loaded!");
        return;
      }

      // Set initial state from Python configuration
      const defaultInitialState = {
        opacity: 1,
        scale: 1,
        rotation: 0,
      };
      gsap.set(element, { ...defaultInitialState, ...initialState });

      // Create GSAP timeline
      const timeline = gsap.timeline({
        repeat: loop ? -1 : 0,
        repeatDelay: 0.5,
      });

      // Build timeline with proper cumulative timing
      let timelinePosition = 0;

      animations.forEach((animation) => {
        const {
          duration = 1,
          delay = 0,
          properties = {},
          easing = "power2.inOut",
        } = animation;

        // Convert properties to GSAP format
        const gsapProps = this._convertPropertiesToGSAP(marker, properties);
        gsapProps.duration = duration;
        gsapProps.ease = easing;

        // Add delay to current timeline position
        timelinePosition += delay;

        // Add animation at current timeline position
        timeline.to(element, gsapProps, timelinePosition);

        // Move timeline position forward by animation duration for next animation
        timelinePosition += duration;
      });
    }, 100);
  }

  _convertPropertiesToGSAP(marker, properties) {
    const gsapProps = {};

    for (const [property, config] of Object.entries(properties)) {
      const value = typeof config === "object" ? config.to : config;

      switch (property) {
        case "opacity":
          gsapProps.opacity = value;
          break;
        case "scale":
          gsapProps.scale = value;
          break;
        case "rotation":
          gsapProps.rotation = value;
          break;
        case "position":
          if (Array.isArray(value) && value.length === 2) {
            // Custom position animation using simple progress tracking
            const startPos = marker.getLatLng();
            const targetLat = value[0];
            const targetLng = value[1];

            // Calculate the visual angle for rotation
            const startProjected = this.map.latLngToContainerPoint([
              startPos.lat,
              startPos.lng,
            ]);
            const endProjected = this.map.latLngToContainerPoint([
              targetLat,
              targetLng,
            ]);
            const screenAngleRad = Math.atan2(
              endProjected.y - startProjected.y,
              endProjected.x - startProjected.x
            );
            const screenAngleDeg = screenAngleRad * (180 / Math.PI);

            // Use onUpdate callback with this.progress() for position interpolation
            gsapProps.onUpdate = function () {
              const progress = this.progress();
              const lat = startPos.lat + (targetLat - startPos.lat) * progress;
              const lng = startPos.lng + (targetLng - startPos.lng) * progress;

              // Update marker position
              marker.setLatLng([lat, lng]);

              // Update plane rotation (apply to img element to avoid conflicts)
              const element = marker.getElement();
              if (element) {
                const img = element.querySelector("img");
                if (img) {
                  img.style.transform = `rotate(${screenAngleDeg}deg)`;
                }
              }
            };
          }
          break;
      }
    }

    return gsapProps;
  }

  _fitMapBounds(data) {
    const bounds = [];

    // Collect all points
    if (data.paths) {
      data.paths.forEach((path) => {
        if (path.points) {
          bounds.push(...path.points);
        }
      });
    }

    if (data.markers) {
      data.markers.forEach((marker) => {
        if (marker.position) {
          bounds.push(marker.position);
        }
      });
    }

    if (bounds.length > 0) {
      this.map.fitBounds(bounds, { padding: [10, 10] });
    }
  }
}

export const flightMapViewField = {
  component: FlightMapViewField,
  displayName: "Flight Map View",
  supportedTypes: ["json"],
  extractProps: ({ options }) => ({
    height: options.height,
    width: options.width,
    animate: options.animate,
  }),
};

// Register the widget
registry.category("fields").add("flight_map_view", flightMapViewField);
