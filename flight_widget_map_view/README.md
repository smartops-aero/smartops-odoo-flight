# Flight Map View Widget

Interactive map widget for Odoo 18.0 with route visualization and animation capabilities.

## Overview

Advanced mapping widget that provides geographic visualization capabilities with route display, path animations, and real-time updates. Built on Leaflet.js with GSAP animations for smooth, professional map interactions.

## Features

- **Interactive Maps**: Leaflet-based widget with OpenStreetMap tiles
- **Route Visualization**: Display paths between multiple points
- **Path Animation**: GSAP-powered smooth route animations
- **Coordinate Support**: Multiple formats (decimal, DMS, arcseconds)
- **Custom Markers**: Configurable icons and styles
- **Responsive Design**: Adapts to different layouts
- **Real-time Updates**: Dynamic updates based on field changes

## Installation

### Prerequisites

- Odoo 18.0
- Modern web browser with JavaScript enabled

### Steps

1. Copy module to Odoo addons directory
2. Update apps list
3. Install "Flight Widget - Map View"

## Usage

### Basic Implementation

1. **In your Python model:**

```python
from odoo import models, fields

class YourModel(models.Model):
    _name = 'your.model'
    _inherit = 'map.path.mixin'

    map_data = fields.Text('Map Data')
```

2. **In your XML view:**

```xml
<field name="map_data" widget="flight_map_view" />
```

### Map Data Format

The widget expects JSON data with this structure:

```json
{
  "paths": [
    {
      "from": { "lat": 43.238949, "lng": 76.889709 },
      "to": { "lat": 25.252829, "lng": 55.364471 },
      "label": "Route Name"
    }
  ],
  "markers": [
    {
      "lat": 43.238949,
      "lng": 76.889709,
      "label": "Location Name",
      "icon": "custom-icon-url"
    }
  ]
}
```

## Technical Details

### Dependencies

- **Leaflet.js 1.9.x**: Map rendering engine
- **GSAP 3.x**: Animation library
- **OpenStreetMap**: Default tile provider

### Widget Options

- `zoom`: Initial zoom level (default: 5)
- `center`: Initial center coordinates
- `animate`: Enable/disable animations
- `duration`: Animation duration in seconds

### Coordinate Formats Supported

- Decimal degrees: `43.238949`
- DMS: `43°14'20.2"N`
- Arcseconds: `155800` (converted automatically)

## API Reference

### MapPathMixin

Provides helper methods for map data handling:

- `_compute_map_data()`: Generate map data from model fields
- `_get_coordinates()`: Extract coordinates from records
- `_format_path_data()`: Format path data for widget

### Events

The widget triggers these events:

- `map:loaded`: Map initialization complete
- `map:path_drawn`: Path animation complete
- `map:marker_clicked`: Marker click event

## Customization

### Custom Tile Providers

```javascript
// In your custom JS
const customTiles = "https://{s}.your-tiles.com/{z}/{x}/{y}.png";
```

### Custom Markers

```javascript
const customIcon = L.icon({
  iconUrl: "/module/static/icon.png",
  iconSize: [32, 32],
});
```

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance

- Optimized for up to 100 markers
- Smooth animations up to 20 paths
- Lazy loading for tile data

## Troubleshooting

### Map not displaying

- Check browser console for errors
- Verify Leaflet CSS is loaded
- Ensure container has height

### Animation issues

- Verify GSAP is loaded
- Check browser compatibility
- Review animation duration settings

## License

LGPL-3

## Author

Apexive Solutions LLC

- Website: https://www.apexive.com/

## Version

18.0.1.0.0 - Initial release for Odoo 18.0
