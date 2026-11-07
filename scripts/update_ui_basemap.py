import json
import re

# Read GeoJSON
with open("src/vayumarg/ui/data/nio_basemap.json", encoding="utf-8") as f:
    basemap_data = json.load(f)

basemap_json_str = json.dumps(basemap_data)

# Read index.html
with open("src/vayumarg/ui/index.html", encoding="utf-8") as f:
    content = f.read()

# 1. Update map container styling
css_target = """    #map-explorer, #map-forecast {
      width: 100%;
      height: 100%;
    }"""
css_replacement = """    #map-explorer, #map-forecast {
      width: 100%;
      height: 100%;
      background: #0B1624 !important;
    }
    .leaflet-container {
      background: #0B1624 !important;
    }
    .leaflet-control-scale-line {
      background: rgba(11, 22, 36, 0.85) !important;
      border: 1px solid #526A7D !important;
      border-top: none !important;
      color: #96A8BB !important;
      font-family: monospace !important;
      font-size: 10px !important;
      padding: 2px 6px !important;
    }"""
if css_target in content:
    content = content.replace(css_target, css_replacement)
    print("Updated CSS rules.")

# 2. Replace NIO_COASTLINE and addOfflineBasemap and initMaps
maps_setup_pattern = re.compile(
    r"// Maps Setup[\s\S]*?function initMaps\(\)\s*\{[\s\S]*?\}\s*\}", re.MULTILINE
)

new_maps_code = f"""// Maps Setup
    // Authentic Natural Earth 110m North Indian Ocean Basin GeoJSON (Keyless Offline Basemap)
    const NIO_BASEMAP_GEOJSON = {basemap_json_str};

    const BASIN_LABELS = [
      {{ name: 'ARABIAN SEA', lat: 16.5, lon: 65.0, cls: 'color:#3F556D; font-weight:700; font-size:11px; letter-spacing:0.25em;' }},
      {{ name: 'BAY OF BENGAL', lat: 14.5, lon: 88.5, cls: 'color:#3F556D; font-weight:700; font-size:11px; letter-spacing:0.25em;' }},
      {{ name: 'INDIAN OCEAN', lat: 2.0, lon: 76.0, cls: 'color:#2F445B; font-weight:600; font-size:10px; letter-spacing:0.3em;' }},
      {{ name: 'INDIA', lat: 22.0, lon: 78.5, cls: 'color:#4E6782; font-weight:600; font-size:11px; letter-spacing:0.1em;' }},
      {{ name: 'SRI LANKA', lat: 7.5, lon: 80.8, cls: 'color:#4E6782; font-size:9px; letter-spacing:0.1em;' }},
      {{ name: 'PAKISTAN', lat: 28.5, lon: 66.5, cls: 'color:#4E6782; font-size:10px; letter-spacing:0.1em;' }},
      {{ name: 'OMAN', lat: 21.5, lon: 56.5, cls: 'color:#4E6782; font-size:10px; letter-spacing:0.1em;' }},
      {{ name: 'BANGLADESH', lat: 24.0, lon: 90.2, cls: 'color:#4E6782; font-size:9px; letter-spacing:0.1em;' }},
      {{ name: 'MYANMAR', lat: 19.5, lon: 96.0, cls: 'color:#4E6782; font-size:10px; letter-spacing:0.1em;' }}
    ];

    function addOfflineBasemap(mapInstance) {{
      // 1. Authentic Land Polygons (Land: #1B2B3A, Coastline/Borders: #526A7D)
      L.geoJSON(NIO_BASEMAP_GEOJSON, {{
        style: {{
          color: '#526A7D',
          weight: 1.2,
          fillColor: '#1B2B3A',
          fillOpacity: 1.0,
          opacity: 0.9
        }},
        interactive: false
      }}).addTo(mapInstance);

      // 2. 5-degree Lat/Lon Graticule lines (#27394B)
      for (let lat = 5; lat <= 35; lat += 5) {{
        L.polyline([[lat, 40], [lat, 105]], {{ color: '#27394B', weight: 0.75, dashArray: '3, 4', interactive: false }}).addTo(mapInstance);
      }}
      for (let lon = 45; lon <= 105; lon += 10) {{
        L.polyline([[0, lon], [38, lon]], {{ color: '#27394B', weight: 0.75, dashArray: '3, 4', interactive: false }}).addTo(mapInstance);
      }}

      // 3. Static Geographic Basin Labels
      BASIN_LABELS.forEach(lbl => {{
        L.marker([lbl.lat, lbl.lon], {{
          icon: L.divIcon({{
            className: 'pointer-events-none select-none',
            html: '<div style=\"' + lbl.cls + ' white-space:nowrap; text-transform:uppercase;\">' + lbl.name + '</div>'
          }})
        }}).addTo(mapInstance);
      }});

      // 4. Metric scale control
      L.control.scale({{ imperial: false, metric: true, position: 'bottomright' }}).addTo(mapInstance);
    }}

    function initMaps() {{
      if (typeof L !== 'undefined') {{
        state.mapExplorer = L.map('map-explorer', {{ zoomControl: true, attributionControl: false }}).setView([16.0, 76.0], 5);
        addOfflineBasemap(state.mapExplorer);

        state.mapForecast = L.map('map-forecast', {{ zoomControl: true, attributionControl: false }}).setView([16.0, 76.0], 5);
        addOfflineBasemap(state.mapForecast);
      }}
    }}"""

if maps_setup_pattern.search(content):
    content = maps_setup_pattern.sub(new_maps_code, content)
    print("Updated maps setup code.")
else:
    print("Warning: maps setup pattern not found!")

# 3. Update renderMapTrack for de-cluttering
old_render_track = """      // Render Map Track
      if (state.mapExplorer && obs.length > 0) {
        if (state.trackLayer) state.mapExplorer.removeLayer(state.trackLayer);

        const latlngs = obs.map(o => [o.latitude, o.longitude]);
        const trackGroup = L.layerGroup();

        // Polyline connecting track
        L.polyline(latlngs, {
          color: '#38bdf8',
          weight: 3,
          opacity: 0.85
        }).addTo(trackGroup);

        // Individual fix markers
        obs.forEach((o, idx) => {
          const color = getCatColor(o.imd_category);
          const circle = L.circleMarker([o.latitude, o.longitude], {
            radius: 5,
            fillColor: color,
            color: '#fff',
            weight: 1,
            opacity: 1,
            fillOpacity: 0.9
          });

          circle.bindPopup(`
            <div style="font-size:12px; line-height:1.4;">
              <strong>${state.selectedStorm} Fix #${idx+1}</strong><br>
              <strong>Time (UTC):</strong> ${o.iso_time.replace('T', ' ').slice(0, 16)}<br>
              <strong>Position:</strong> ${o.latitude.toFixed(2)}°N, ${o.longitude.toFixed(2)}°E<br>
              <strong>IMD Wind (3-min):</strong> ${o.imd_wind_speed_knots || 'N/A'} kts<br>
              <strong>JTWC Wind (1-min):</strong> ${o.jtwc_wind_speed_knots || 'N/A'} kts<br>
              <strong>Pressure:</strong> ${o.central_pressure_hpa || 'N/A'} hPa<br>
              <strong>Category:</strong> ${o.imd_category}
            </div>
          `);
          circle.addTo(trackGroup);
        });

        trackGroup.addTo(state.mapExplorer);
        state.trackLayer = trackGroup;
        state.mapExplorer.fitBounds(L.polyline(latlngs).getBounds(), { padding: [30, 30] });
      }"""

new_render_track = """      // Render Map Track (Intelligent De-cluttering)
      if (state.mapExplorer && obs.length > 0) {
        if (state.trackLayer) state.mapExplorer.removeLayer(state.trackLayer);

        const latlngs = obs.map(o => [o.latitude, o.longitude]);
        const trackGroup = L.layerGroup();

        // Continuous Polyline (#65C4D6)
        L.polyline(latlngs, {
          color: '#65C4D6',
          weight: 2.5,
          opacity: 0.9
        }).addTo(trackGroup);

        // Distinct Start (Genesis), End (Final), and Micro-markers for intermediate points
        obs.forEach((o, idx) => {
          const color = getCatColor(o.imd_category);
          const isStart = idx === 0;
          const isEnd = idx === obs.length - 1;
          const timeStr = o.iso_time ? o.iso_time.replace('T', ' ').slice(0, 16) : '';

          let marker;
          if (isStart) {
            marker = L.circleMarker([o.latitude, o.longitude], {
              radius: 6,
              fillColor: '#10B981',
              color: '#F5F7FA',
              weight: 2,
              fillOpacity: 1.0
            });
          } else if (isEnd) {
            marker = L.circleMarker([o.latitude, o.longitude], {
              radius: 6,
              fillColor: '#F43F5E',
              color: '#F5F7FA',
              weight: 2,
              fillOpacity: 1.0
            });
          } else {
            marker = L.circleMarker([o.latitude, o.longitude], {
              radius: 2.5,
              fillColor: color,
              color: color,
              weight: 0,
              fillOpacity: 0.85
            });
            marker.on('mouseover', function() { this.setRadius(5.5); this.setStyle({ weight: 2, color: '#F5F7FA' }); });
            marker.on('mouseout', function() { this.setRadius(2.5); this.setStyle({ weight: 0, color: color }); });
          }

          marker.bindPopup(`
            <div style="font-size:12px; line-height:1.4; color:#EDF3F9; background:#111B28; padding:4px;">
              <strong style="color:${isStart ? '#10B981' : isEnd ? '#F43F5E' : '#65C4D6'};">
                ${state.selectedStorm} ${isStart ? '● GENESIS' : isEnd ? '■ FINAL FIX' : `Fix #${idx+1}`}
              </strong><br>
              <strong>Time (UTC):</strong> ${timeStr}<br>
              <strong>Position:</strong> ${o.latitude.toFixed(2)}°N, ${o.longitude.toFixed(2)}°E<br>
              <strong>IMD Wind (3-min):</strong> ${o.imd_wind_speed_knots !== null && o.imd_wind_speed_knots !== undefined ? o.imd_wind_speed_knots + ' kt' : 'N/A'}<br>
              <strong>JTWC Wind (1-min):</strong> ${o.jtwc_wind_speed_knots !== null && o.jtwc_wind_speed_knots !== undefined ? o.jtwc_wind_speed_knots + ' kt' : 'N/A'}<br>
              <strong>Pressure:</strong> ${o.central_pressure_hpa !== null && o.central_pressure_hpa !== undefined ? o.central_pressure_hpa + ' hPa' : 'N/A'}<br>
              <strong>Category:</strong> ${o.imd_category || 'N/A'}
            </div>
          `);
          marker.addTo(trackGroup);
        });

        trackGroup.addTo(state.mapExplorer);
        state.trackLayer = trackGroup;
        state.mapExplorer.fitBounds(L.polyline(latlngs).getBounds(), { padding: [35, 35] });
      }"""

if old_render_track in content:
    content = content.replace(old_render_track, new_render_track)
    print("Updated renderMapTrack.")
else:
    print("Warning: old_render_track not found!")

# 4. Update Forecast track in updateForecastUI
old_fc_track = """        // Extrapolated Forecast Track (amber line)
        const fcCoords = [[fc.current_latitude, fc.current_longitude]];
        fc.forecast_points.forEach(p => {
          fcCoords.push([p.predicted_latitude, p.predicted_longitude]);

          // Uncertainty cone radius circle
          L.circle([p.predicted_latitude, p.predicted_longitude], {
            radius: p.uncertainty_radius_km * 1000,
            color: '#f59e0b',
            weight: 1,
            fillColor: '#f59e0b',
            fillOpacity: 0.12,
            dashArray: '4, 4'
          }).addTo(group);

          // Forecast Marker
          const fMarker = L.circleMarker([p.predicted_latitude, p.predicted_longitude], {
            radius: 7,
            fillColor: '#f59e0b',
            color: '#fff',
            weight: 2,
            fillOpacity: 1
          });"""

new_fc_track = """        // Extrapolated Forecast Track (amber line)
        const fcCoords = [[fc.current_latitude, fc.current_longitude]];
        fc.forecast_points.forEach(p => {
          fcCoords.push([p.predicted_latitude, p.predicted_longitude]);

          // Uncertainty cone radius circle (illustrative reference buffer)
          L.circle([p.predicted_latitude, p.predicted_longitude], {
            radius: p.uncertainty_radius_km * 1000,
            color: '#E6AB65',
            weight: 1,
            fillColor: '#E6AB65',
            fillOpacity: 0.08,
            dashArray: '4, 4'
          }).addTo(group);

          // Forecast Marker
          const fMarker = L.circleMarker([p.predicted_latitude, p.predicted_longitude], {
            radius: 6.5,
            fillColor: '#E6AB65',
            color: '#0B1624',
            weight: 2,
            fillOpacity: 1
          });"""

if old_fc_track in content:
    content = content.replace(old_fc_track, new_fc_track)
    print("Updated forecast track styling.")

with open("src/vayumarg/ui/index.html", "w", encoding="utf-8") as f:
    f.write(content)

print("Saved updated src/vayumarg/ui/index.html successfully!")
