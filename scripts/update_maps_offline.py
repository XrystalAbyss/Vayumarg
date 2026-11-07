"""Clean and update initMaps and populateIssueTimes in index.html."""

import re
from pathlib import Path

p = Path("src/vayumarg/ui/index.html")
text = p.read_text(encoding="utf-8")

# Offline coastline definition
offline_geo_code = """      // Simplified North Indian Ocean Coastline for Offline Mode
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

# Replace initMaps using regex
init_maps_pat = r"function initMaps\(\)\s*\{[\s\S]*?\}\s*\}"
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
text, count = re.subn(init_maps_pat, new_init_maps, text, count=1)
print(f"Replaced initMaps: {count} times")

# Replace populateIssueTimes using regex
pop_time_pat = (
    r"function populateIssueTimes\(\)\s*\{[\s\S]*?select\.selectedIndex = targetIdx - 1;\s*\}"
)
new_pop_time = """function populateIssueTimes() {
        const select = document.getElementById('forecast-issue-select');
        select.innerHTML = '';
        const obs = state.currentObservations;

        if (!obs || obs.length < 2) return;

        // Populate valid historical issue points (needing at least 2 prior points)
        obs.forEach((o, idx) => {
          if (idx < 1) return;
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
        }
      }"""
text, count2 = re.subn(pop_time_pat, new_pop_time, text, count=1)
print(f"Replaced populateIssueTimes: {count2} times")

p.write_text(text, encoding="utf-8")
Path("frontend/dist/index.html").write_text(text, encoding="utf-8")
print(f"Written {len(text)} bytes to index.html and frontend/dist/index.html")
