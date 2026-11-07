"""Harden src/vayumarg/ui/index.html with local offline Leaflet assets,
SVG/GeoJSON coastline fallback, canonical benchmark auto-selection, and scientific wording corrections.
"""

from pathlib import Path

ui_file = Path("src/vayumarg/ui/index.html")
text = ui_file.read_text(encoding="utf-8")

# 1. Replace remote Leaflet CDN with local assets
text = text.replace(
    '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>',
    '<link rel="stylesheet" href="/ui/vendor/leaflet/leaflet.css" />',
)
text = text.replace(
    '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>',
    '<script src="/ui/vendor/leaflet/leaflet.js"></script>',
)

# 2. Correct scientific wording in UI
text = text.replace("Gust Averaged", "1-Min Sustained")
text = text.replace("Minimum Core Eye Temp", "Min Brightness Temp (Sensor Clamp: ~180 K)")
text = text.replace("<th>Uncertainty</th>", "<th>Nominal Buffer</th>")
text = text.replace(
    "±${p.uncertainty_radius_km} km cone", "±${p.uncertainty_radius_km} km illustrative envelope"
)
text = text.replace(
    "Super Cyclone AMPHAN (2020)",
    "Cyclone AMPHAN (2020) — Peak: Super Cyclone / Image Fix: ESCS (95 kt)",
)
text = text.replace("Super Cyclone • Convection", "Convective Analytics • Sensor LUT Calibration")
text = text.replace("Arabian Sea • Forecast", "Arabian Sea • Geodesic Forecast")
text = text.replace(
    "Scientific Data Governance", "Scientific Data Governance • Honest Label Quarantine"
)
text = text.replace(
    "Multi-Horizon Validation", "Multi-Horizon Validation • Pre-Landfall Acceleration"
)

# 3. Add local offline coastline and map fallback
offline_geo_code = """
      // Simplified North Indian Ocean Coastline for Offline Mode
      const NIO_COASTLINE = {
        "type": "FeatureCollection",
        "features": [
          {
            "type": "Feature",
            "properties": {"name": "Indian Subcontinent Coastline & Basin Boundary"},
            "geometry": {
              "type": "Polygon",
              "coordinates": [[
                [68.5, 23.8], [70.0, 23.0], [70.2, 22.3], [69.0, 22.4], [69.1, 21.6], [70.3, 20.9], [72.1, 21.1], [72.8, 21.6],
                [72.8, 19.5], [73.0, 18.9], [73.3, 16.5], [74.2, 14.8], [74.8, 13.3], [75.8, 11.2], [76.3, 9.9], [77.5, 8.1],
                [78.1, 8.8], [79.3, 9.3], [79.9, 10.3], [79.8, 11.8], [80.3, 13.1], [80.2, 14.9], [81.8, 15.8], [82.3, 17.0],
                [83.3, 17.7], [85.0, 19.5], [86.9, 20.8], [87.5, 21.6], [88.2, 21.7], [89.1, 21.8], [90.5, 22.0], [91.8, 22.3],
                [92.5, 20.8], [93.5, 19.8], [94.3, 18.2], [94.8, 16.0], [96.2, 16.8], [98.2, 16.5], [98.5, 12.0], [99.0, 8.0],
                [95.0, 5.0], [80.0, 5.0], [60.0, 5.0], [55.0, 15.0], [58.0, 23.0], [62.0, 25.2], [66.5, 24.8], [68.5, 23.8]
              ]]
            }
          },
          {
            "type": "Feature",
            "properties": {"name": "Sri Lanka"},
            "geometry": {
              "type": "Polygon",
              "coordinates": [[
                [79.8, 9.8], [80.5, 9.8], [81.3, 8.6], [81.8, 7.5], [81.3, 6.0], [80.6, 5.9], [79.8, 6.9], [79.8, 8.5], [79.8, 9.8]
              ]]
            }
          }
        ]
      };

      function addOfflineBasemap(mapInstance) {
        L.geoJSON(NIO_COASTLINE, {
          style: {
            color: '#334155',
            weight: 1.5,
            fillColor: '#131b2e',
            fillOpacity: 0.65
          }
        }).addTo(mapInstance);

        for (let lat = 5; lat <= 30; lat += 5) {
          L.polyline([[lat, 50], [lat, 100]], { color: '#1e293b', weight: 0.8, dashArray: '2, 4' }).addTo(mapInstance);
        }
        for (let lon = 55; lon <= 95; lon += 5) {
          L.polyline([[5, lon], [30, lon]], { color: '#1e293b', weight: 0.8, dashArray: '2, 4' }).addTo(mapInstance);
        }

        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
          attribution: '&copy; OpenStreetMap, &copy; CARTO',
          maxZoom: 12,
          errorTileUrl: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256"><rect width="256" height="256" fill="%230d1527"/><path d="M0,0 L256,0 M0,256 L256,256 M0,0 L0,256 M256,0 L256,256" stroke="%231e293b" stroke-width="0.5"/></svg>'
        }).addTo(mapInstance);
      }
"""

old_init_maps = """    function initMaps() {
        // 1. Explorer Map
        if (typeof L !== 'undefined') {
          state.mapExplorer = L.map('map-explorer', { zoomControl: true }).setView([18.0, 75.0], 5);
          L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; OpenStreetMap, &copy; CARTO',
            maxZoom: 12
          }).addTo(state.mapExplorer);

          // 2. Forecast Map
          state.mapForecast = L.map('map-forecast', { zoomControl: true }).setView([18.0, 75.0], 5);
          L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; OpenStreetMap, &copy; CARTO',
            maxZoom: 12
          }).addTo(state.mapForecast);
        }
      }"""

new_init_maps = (
    offline_geo_code
    + """
    function initMaps() {
        if (typeof L !== 'undefined') {
          state.mapExplorer = L.map('map-explorer', { zoomControl: true }).setView([18.0, 75.0], 5);
          addOfflineBasemap(state.mapExplorer);

          state.mapForecast = L.map('map-forecast', { zoomControl: true }).setView([18.0, 75.0], 5);
          addOfflineBasemap(state.mapForecast);
        }
      }"""
)

if old_init_maps in text:
    text = text.replace(old_init_maps, new_init_maps)
else:
    print("[WARN] old_init_maps not matched exactly, checking pattern")

# 4. Canonical issue time selection
old_pop_time = """      // Offer issue times starting from index 2 up to length - 1
        obs.forEach((o, idx) => {
          if (idx < 1) return; // Need at least 2 historical points
          const opt = document.createElement('option');
          opt.value = o.iso_time;
          const timeStr = o.iso_time.replace('T', ' ').slice(0, 16);
          opt.textContent = `Fix #${idx+1} [${timeStr} UTC] (${o.latitude}°N, ${o.longitude}°E) - ${o.wind_speed_knots || '-'} kt`;
          select.appendChild(opt);
        });

        // Default issue time: approximately 40% through lifecycle for good forecast demo
        const targetIdx = Math.max(1, Math.min(obs.length - 3, Math.floor(obs.length * 0.4)));
        select.selectedIndex = targetIdx - 1;"""

new_pop_time = """      // Offer issue times starting from index 2 up to length - 1
        obs.forEach((o, idx) => {
          if (idx < 1) return; // Need at least 2 historical points
          const opt = document.createElement('option');
          opt.value = o.iso_time;
          const timeStr = (o.iso_time || '').replace('T', ' ').slice(0, 16);
          opt.textContent = `Fix #${idx+1} [${timeStr} UTC] (${o.latitude}°N, ${o.longitude}°E) - ${o.wind_speed_knots || '-'} kt`;
          select.appendChild(opt);
        });

        // Auto-select canonical benchmark issue time if present
        let canonicalIdx = -1;
        if (state.selectedStorm === 'BIPARJOY') {
          canonicalIdx = obs.findIndex(o => (o.iso_time || '').includes('2023-06-11T06:00'));
        } else if (state.selectedStorm === 'AMPHAN') {
          canonicalIdx = obs.findIndex(o => (o.iso_time || '').includes('2020-05-18T00:00'));
        } else if (state.selectedStorm === 'REMAL') {
          canonicalIdx = obs.findIndex(o => (o.iso_time || '').includes('2024-05-25T12:00'));
        } else if (state.selectedStorm === 'DANA') {
          canonicalIdx = obs.findIndex(o => (o.iso_time || '').includes('2024-10-23T12:00'));
        }

        if (canonicalIdx >= 1) {
          select.selectedIndex = canonicalIdx - 1;
        } else {
          const targetIdx = Math.max(1, Math.min(obs.length - 3, Math.floor(obs.length * 0.4)));
          select.selectedIndex = targetIdx - 1;
        }"""

if old_pop_time in text:
    text = text.replace(old_pop_time, new_pop_time)
else:
    print("[WARN] old_pop_time not matched exactly, checking pattern")

ui_file.write_text(text, encoding="utf-8")
print(f"Updated {ui_file} ({len(text)} chars)")

# Also overwrite frontend/dist/index.html so both are 100% in sync
dist_file = Path("frontend/dist/index.html")
dist_file.write_text(text, encoding="utf-8")
print(f"Synced {dist_file}")
