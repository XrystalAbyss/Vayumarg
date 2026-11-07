import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import type { ObservationPoint, ForecastPoint, HindsightVerificationPoint } from '../types';
import { Layers, ShieldCheck, KeyRound } from 'lucide-react';
import { NIO_BASEMAP_GEOJSON } from '../data/nioBasemap';

interface TrackMapProps {
  observations: ObservationPoint[];
  selectedObservation?: ObservationPoint | null;
  onSelectObservation?: (obs: ObservationPoint) => void;
  forecastPoints?: ForecastPoint[] | null;
  verificationPoints?: HindsightVerificationPoint[] | null;
  showVerification?: boolean;
  className?: string;
}

// Major geographic labels across the North Indian Ocean basin
const BASIN_LABELS = [
  { name: 'ARABIAN SEA', lat: 16.5, lon: 65.0, cls: 'text-xs tracking-[0.25em] text-[#3F556D] font-bold' },
  { name: 'BAY OF BENGAL', lat: 14.5, lon: 88.5, cls: 'text-xs tracking-[0.25em] text-[#3F556D] font-bold' },
  { name: 'INDIAN OCEAN', lat: 2.0, lon: 76.0, cls: 'text-[11px] tracking-[0.3em] text-[#2F445B] font-semibold' },
  { name: 'INDIA', lat: 22.0, lon: 78.5, cls: 'text-[11px] tracking-wider text-[#4E6782] font-semibold' },
  { name: 'SRI LANKA', lat: 7.5, lon: 80.8, cls: 'text-[9px] tracking-wider text-[#4E6782]' },
  { name: 'PAKISTAN', lat: 28.5, lon: 66.5, cls: 'text-[10px] tracking-wider text-[#4E6782]' },
  { name: 'OMAN', lat: 21.5, lon: 56.5, cls: 'text-[10px] tracking-wider text-[#4E6782]' },
  { name: 'BANGLADESH', lat: 24.0, lon: 90.2, cls: 'text-[9px] tracking-wider text-[#4E6782]' },
  { name: 'MYANMAR', lat: 19.5, lon: 96.0, cls: 'text-[10px] tracking-wider text-[#4E6782]' },
];

export const TrackMap: React.FC<TrackMapProps> = ({
  observations,
  selectedObservation,
  onSelectObservation,
  forecastPoints,
  verificationPoints,
  showVerification = false,
  className = '',
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const basemapGroupRef = useRef<L.LayerGroup | null>(null);
  const trackGroupRef = useRef<L.LayerGroup | null>(null);
  const onlineTileLayerRef = useRef<L.TileLayer | null>(null);

  // Default mode is strictly keyless offline vector basemap
  const [useOnlineCarto, setUseOnlineCarto] = useState<boolean>(false);
  const [cartoApiKey, setCartoApiKey] = useState<string>(() => localStorage.getItem('carto_api_key') || '');
  const [showKeyModal, setShowKeyModal] = useState<boolean>(false);
  const [keyInput, setKeyInput] = useState<string>('');

  // 1. Initialize Leaflet map and local keyless offline basemap
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    // Center on Bay of Bengal / Arabian Sea (16°N, 76°E)
    const map = L.map(mapContainerRef.current, {
      center: [16.0, 76.0],
      zoom: 5,
      minZoom: 3,
      maxZoom: 11,
      zoomControl: false,
      attributionControl: false,
    });

    // Zoom control in top right
    L.control.zoom({ position: 'topright' }).addTo(map);

    // Metric scale control in bottom right
    L.control.scale({ imperial: false, metric: true, position: 'bottomright' }).addTo(map);

    // Base layer group (Ocean, Land polygons, Graticule, Basin labels)
    const basemapGroup = L.layerGroup().addTo(map);
    basemapGroupRef.current = basemapGroup;

    // Render local authentic Natural Earth GeoJSON land polygons
    L.geoJSON(NIO_BASEMAP_GEOJSON as any, {
      style: {
        fillColor: '#1B2B3A', // Land polygon fill
        fillOpacity: 1.0,
        color: '#526A7D',     // Coastline and national boundary stroke
        weight: 1.2,
        opacity: 0.9,
      },
      interactive: false,
    }).addTo(basemapGroup);

    // 5-degree Lat/Lon Graticule lines (Meteorological coordinate grid)
    for (let lat = 5; lat <= 35; lat += 5) {
      L.polyline([[lat, 40], [lat, 105]], {
        color: '#27394B',
        weight: 0.75,
        dashArray: '3, 4',
        opacity: 0.8,
        interactive: false,
      }).addTo(basemapGroup);

      // Edge latitude tick label
      L.marker([lat, 41], {
        icon: L.divIcon({
          className: 'pointer-events-none select-none',
          html: `<div class="text-[9px] font-mono text-[#3F556D] -mt-2">${lat}°N</div>`,
        }),
      }).addTo(basemapGroup);
    }

    for (let lon = 45; lon <= 105; lon += 10) {
      L.polyline([[0, lon], [38, lon]], {
        color: '#27394B',
        weight: 0.75,
        dashArray: '3, 4',
        opacity: 0.8,
        interactive: false,
      }).addTo(basemapGroup);

      // Edge longitude tick label
      L.marker([1, lon], {
        icon: L.divIcon({
          className: 'pointer-events-none select-none',
          html: `<div class="text-[9px] font-mono text-[#3F556D] -ml-3">${lon}°E</div>`,
        }),
      }).addTo(basemapGroup);
    }

    // Add static geographic labels
    BASIN_LABELS.forEach((lbl) => {
      L.marker([lbl.lat, lbl.lon], {
        icon: L.divIcon({
          className: 'pointer-events-none select-none',
          html: `<div class="${lbl.cls} whitespace-nowrap">${lbl.name}</div>`,
        }),
      }).addTo(basemapGroup);
    });

    // Dynamic track group (Historical fixes, Forecast, Verification)
    const trackGroup = L.layerGroup().addTo(map);
    trackGroupRef.current = trackGroup;

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // 2. Handle Optional Online CARTO Tile Layer (Strictly opt-in with valid API key)
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (onlineTileLayerRef.current) {
      map.removeLayer(onlineTileLayerRef.current);
      onlineTileLayerRef.current = null;
    }

    if (useOnlineCarto && cartoApiKey.trim()) {
      const tileUrl = `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png?api_key=${encodeURIComponent(
        cartoApiKey.trim()
      )}`;
      const layer = L.tileLayer(tileUrl, {
        subdomains: 'abcd',
        maxZoom: 18,
        attribution: '&copy; CARTO, &copy; OpenStreetMap',
      });

      layer.on('tileerror', () => {
        // Automatically revert to local keyless basemap on tile authorization failure
        setUseOnlineCarto(false);
      });

      layer.addTo(map);
      layer.bringToBack();
      onlineTileLayerRef.current = layer;
    }
  }, [useOnlineCarto, cartoApiKey]);

  // 3. Render Historical Track, Forecast Projections, and Observation Markers
  useEffect(() => {
    const map = mapInstanceRef.current;
    const group = trackGroupRef.current;
    if (!map || !group) return;

    group.clearLayers();

    if (!observations || observations.length === 0) return;

    const latLngs: L.LatLngTuple[] = observations.map((o) => [o.latitude, o.longitude]);

    // 3a. Draw Continuous Historical Track Line (#65C4D6 Cyan)
    L.polyline(latLngs, {
      color: '#65C4D6',
      weight: 2.5,
      opacity: 0.9,
      smoothFactor: 1.0,
    }).addTo(group);

    // Identify start, end, and selected indices
    const startIndex = 0;
    const endIndex = observations.length - 1;
    const selectedTime = selectedObservation?.iso_time || selectedObservation?.observation_time_utc;
    const selectedIndex = selectedTime
      ? observations.findIndex((o) => (o.iso_time || o.observation_time_utc) === selectedTime)
      : -1;

    // 3b. Draw Observation Markers with Intelligent De-cluttering:
    // Display continuous line + crisp micro-markers for intermediate points (hover to inspect)
    // Display prominent markers for Start (Genesis), End (Latest), and Selected point
    observations.forEach((obs, idx) => {
      const obsTime = (obs.iso_time || obs.observation_time_utc || '').replace('T', ' ').substring(0, 16);
      const isStart = idx === startIndex;
      const isEnd = idx === endIndex;
      const isSelected = idx === selectedIndex;
      const windKt = obs.wind_speed_knots || 0;

      // Color based on meteorological category
      let catColor = '#65C4D6'; // D / DD
      if (windKt >= 34) catColor = '#38BDF8'; // CS / SCS
      if (windKt >= 64) catColor = '#E6AB65'; // VSCS
      if (windKt >= 90) catColor = '#D86F6F'; // ESCS / SuCS

      // Render Distinct Start Position Marker (Green Ring)
      if (isStart) {
        const startMarker = L.circleMarker([obs.latitude, obs.longitude], {
          radius: isSelected ? 8 : 6,
          fillColor: '#10B981',
          color: isSelected ? '#F5F7FA' : '#0B1624',
          weight: isSelected ? 3 : 2,
          fillOpacity: 1.0,
        });

        startMarker.bindTooltip(
          `<div class="p-1.5 text-xs bg-[#111B28] text-[#EDF3F9] rounded border border-[#10B981]/60 font-sans">
            <div class="font-bold text-[#10B981] flex items-center gap-1">● GENESIS / START (Fix #1)</div>
            <div class="text-[#96A8BB] font-mono">${obsTime} UTC</div>
            <div class="text-[#EDF3F9] font-medium">${obs.imd_category || 'Initial Fix'} • ${obs.latitude.toFixed(2)}°N, ${obs.longitude.toFixed(2)}°E</div>
            <div class="text-[#96A8BB] font-mono mt-0.5">Wind: ${obs.wind_speed_knots ?? '-'} kt | Pres: ${obs.central_pressure_hpa ?? '-'} hPa</div>
          </div>`,
          { direction: 'top', offset: [0, -6], className: 'map-tooltip' }
        );

        if (onSelectObservation) startMarker.on('click', () => onSelectObservation(obs));
        startMarker.addTo(group);
        return;
      }

      // Render Distinct End Position Marker (Crimson Ring)
      if (isEnd && !isStart) {
        const endMarker = L.circleMarker([obs.latitude, obs.longitude], {
          radius: isSelected ? 8 : 6,
          fillColor: '#F43F5E',
          color: isSelected ? '#F5F7FA' : '#0B1624',
          weight: isSelected ? 3 : 2,
          fillOpacity: 1.0,
        });

        endMarker.bindTooltip(
          `<div class="p-1.5 text-xs bg-[#111B28] text-[#EDF3F9] rounded border border-[#F43F5E]/60 font-sans">
            <div class="font-bold text-[#F43F5E] flex items-center gap-1">■ LATEST / FINAL FIX (#${idx + 1})</div>
            <div class="text-[#96A8BB] font-mono">${obsTime} UTC</div>
            <div class="text-[#EDF3F9] font-medium">${obs.imd_category || 'Final Fix'} • ${obs.latitude.toFixed(2)}°N, ${obs.longitude.toFixed(2)}°E</div>
            <div class="text-[#96A8BB] font-mono mt-0.5">Wind: ${obs.wind_speed_knots ?? '-'} kt | Pres: ${obs.central_pressure_hpa ?? '-'} hPa</div>
          </div>`,
          { direction: 'top', offset: [0, -6], className: 'map-tooltip' }
        );

        if (onSelectObservation) endMarker.on('click', () => onSelectObservation(obs));
        endMarker.addTo(group);
        return;
      }

      // Render Selected Observation Marker (High-Contrast Pulsing Indicator)
      if (isSelected) {
        const selMarker = L.circleMarker([obs.latitude, obs.longitude], {
          radius: 8,
          fillColor: '#F5F7FA',
          color: '#65C4D6',
          weight: 3.5,
          fillOpacity: 1.0,
        });

        selMarker.bindTooltip(
          `<div class="p-1.5 text-xs bg-[#111B28] text-[#EDF3F9] rounded border border-[#65C4D6] font-sans">
            <div class="font-bold text-[#65C4D6]">SELECTED OBSERVATION (Fix #${idx + 1})</div>
            <div class="text-[#96A8BB] font-mono">${obsTime} UTC</div>
            <div class="text-[#EDF3F9] font-medium">${obs.imd_category || 'Cyclonic Observation'} • ${obs.latitude.toFixed(2)}°N, ${obs.longitude.toFixed(2)}°E</div>
            <div class="text-[#96A8BB] font-mono mt-0.5">Wind: ${obs.wind_speed_knots ?? '-'} kt | Pres: ${obs.central_pressure_hpa ?? '-'} hPa</div>
          </div>`,
          { direction: 'top', offset: [0, -8], className: 'map-tooltip' }
        );

        if (onSelectObservation) selMarker.on('click', () => onSelectObservation(obs));
        selMarker.addTo(group);
        return;
      }

      // Intermediate Observations: Clean, un-cluttered interactive micro-dots (radius 2.5)
      // Expands dynamically on hover to radius 5.5 without cluttering the 113-point path
      const microMarker = L.circleMarker([obs.latitude, obs.longitude], {
        radius: 2.5,
        fillColor: catColor,
        color: catColor,
        weight: 0,
        fillOpacity: 0.8,
      });

      microMarker.bindTooltip(
        `<div class="p-1.5 text-xs bg-[#111B28] text-[#EDF3F9] rounded border border-[#1E2E42] font-sans shadow-lg">
          <div class="font-bold text-[#65C4D6]">Fix #${idx + 1} • ${obsTime} UTC</div>
          <div class="text-[#EDF3F9] font-medium">${obs.imd_category || 'Observation'} • ${obs.latitude.toFixed(2)}°N, ${obs.longitude.toFixed(2)}°E</div>
          <div class="text-[#96A8BB] font-mono mt-0.5">Wind: ${obs.wind_speed_knots ?? '-'} kt | Pres: ${obs.central_pressure_hpa ?? '-'} hPa</div>
        </div>`,
        { direction: 'top', offset: [0, -4], className: 'map-tooltip' }
      );

      microMarker.on('mouseover', () => {
        microMarker.setRadius(5.5);
        microMarker.setStyle({ weight: 2, color: '#F5F7FA' });
      });

      microMarker.on('mouseout', () => {
        microMarker.setRadius(2.5);
        microMarker.setStyle({ weight: 0, color: catColor });
      });

      if (onSelectObservation) {
        microMarker.on('click', () => onSelectObservation(obs));
      }

      microMarker.addTo(group);
    });

    // 3c. Draw Forward Forecast Track (+6h, +12h, +24h) in Amber (#E6AB65)
    if (forecastPoints && forecastPoints.length > 0) {
      const lastObs = observations[observations.length - 1];
      const forecastLatLngs: L.LatLngTuple[] = [
        [lastObs.latitude, lastObs.longitude],
        ...forecastPoints.map((f) => [f.predicted_latitude, f.predicted_longitude] as L.LatLngTuple),
      ];

      // Amber dashed forecast track
      L.polyline(forecastLatLngs, {
        color: '#E6AB65',
        weight: 3,
        dashArray: '5, 7',
        opacity: 0.95,
      }).addTo(group);

      // Forecast points and uncertainty reference envelopes
      forecastPoints.forEach((f) => {
        // Non-calibrated illustrative reference buffer
        L.circle([f.predicted_latitude, f.predicted_longitude], {
          radius: f.uncertainty_radius_km * 1000,
          color: '#E6AB65',
          weight: 1,
          opacity: 0.45,
          fillColor: '#E6AB65',
          fillOpacity: 0.08,
          dashArray: '3, 4',
        }).addTo(group);

        const fMarker = L.circleMarker([f.predicted_latitude, f.predicted_longitude], {
          radius: 6.5,
          fillColor: '#E6AB65',
          color: '#0B1624',
          weight: 2,
          fillOpacity: 1.0,
        });

        const validTime = (f.valid_time_utc || '').replace('T', ' ').substring(0, 16);
        fMarker.bindTooltip(
          `<div class="p-1.5 text-xs bg-[#111B28] text-[#EDF3F9] rounded border border-[#E6AB65] font-sans">
            <div class="font-bold text-[#E6AB65]">+${f.lead_time_hours}h Forecast Horizon</div>
            <div class="text-[#96A8BB] font-mono">${validTime} UTC</div>
            <div class="text-[#EDF3F9] font-medium">${f.predicted_imd_category} • ${f.predicted_latitude.toFixed(2)}°N, ${f.predicted_longitude.toFixed(2)}°E</div>
            <div class="text-[#EDF3F9] font-mono mt-0.5">Est. Wind: ${f.predicted_wind_speed_knots} kt | Envelope: ±${f.uncertainty_radius_km} km</div>
          </div>`,
          { direction: 'top', offset: [0, -8], className: 'map-tooltip' }
        );

        fMarker.addTo(group);
      });
    }

    // 3d. Draw Retrospective Hindsight Verification Points (Pale Gray #CCD7E2)
    if (showVerification && verificationPoints && verificationPoints.length > 0) {
      verificationPoints.forEach((v) => {
        if (v.actual_latitude != null && v.actual_longitude != null) {
          // Connecting error vector between prediction and actual ground-truth
          if (v.predicted_latitude != null && v.predicted_longitude != null) {
            L.polyline(
              [
                [v.predicted_latitude, v.predicted_longitude],
                [v.actual_latitude, v.actual_longitude],
              ],
              {
                color: '#96A8BB',
                weight: 1.5,
                dashArray: '2, 3',
                opacity: 0.75,
              }
            ).addTo(group);
          }

          const vMarker = L.circleMarker([v.actual_latitude, v.actual_longitude], {
            radius: 5.5,
            fillColor: '#CCD7E2',
            color: '#111B28',
            weight: 2,
            fillOpacity: 0.95,
          });

          const vTime = (v.valid_time_utc || '').replace('T', ' ').substring(0, 16);
          vMarker.bindTooltip(
            `<div class="p-1.5 text-xs bg-[#111B28] text-[#EDF3F9] rounded border border-[#CCD7E2] font-sans">
              <div class="font-bold text-[#CCD7E2]">+${v.lead_time_hours}h Ground-Truth Fix</div>
              <div class="text-[#96A8BB] font-mono">${vTime} UTC</div>
              <div class="text-[#EDF3F9] font-medium">${v.actual_category || 'Verified Fix'} • ${v.actual_latitude.toFixed(2)}°N, ${v.actual_longitude.toFixed(2)}°E</div>
              <div class="text-[#EDF3F9] font-mono mt-0.5">Actual Wind: ${v.actual_wind_kt ?? '-'} kt</div>
              <div class="text-[#E6AB65] font-mono font-bold mt-0.5">Track Error: ${v.track_error_km?.toFixed(1) ?? '-'} km</div>
            </div>`,
            { direction: 'top', offset: [0, -6], className: 'map-tooltip' }
          );

          vMarker.addTo(group);
        }
      });
    }

    // 3e. Smoothly Fit Map Bounds to Track Extent
    if (latLngs.length > 0) {
      const allPoints: L.LatLngTuple[] = [...latLngs];
      if (forecastPoints) {
        forecastPoints.forEach((f) => allPoints.push([f.predicted_latitude, f.predicted_longitude]));
      }
      map.fitBounds(L.latLngBounds(allPoints), { padding: [40, 40], maxZoom: 7 });
    }
  }, [observations, selectedObservation, forecastPoints, verificationPoints, showVerification, onSelectObservation]);

  const handleSaveApiKey = () => {
    localStorage.setItem('carto_api_key', keyInput.trim());
    setCartoApiKey(keyInput.trim());
    setShowKeyModal(false);
    if (keyInput.trim()) {
      setUseOnlineCarto(true);
    } else {
      setUseOnlineCarto(false);
    }
  };

  return (
    <div className={`relative w-full h-full rounded-md border border-[#1E2E42] bg-[#0B1624] overflow-hidden ${className}`}>
      {/* Map canvas container */}
      <div ref={mapContainerRef} className="w-full h-full bg-[#0B1624]" />

      {/* Top Header Mode Indicator & Optional CARTO Configuration */}
      <div className="absolute top-3 right-12 z-20 flex items-center gap-2">
        {/* Offline Vector Basemap Badge */}
        <div className="bg-[#111B28]/95 border border-[#1E2E42] px-2.5 py-1 rounded text-xs text-[#96A8BB] flex items-center gap-1.5 shadow-md backdrop-blur-sm">
          <ShieldCheck className="w-3.5 h-3.5 text-[#10B981]" />
          <span>{useOnlineCarto ? 'CARTO Online (Auth)' : 'Keyless Offline Basemap (WGS84)'}</span>
        </div>

        {/* Optional Online CARTO Key Config Button */}
        <button
          onClick={() => {
            setKeyInput(cartoApiKey);
            setShowKeyModal(true);
          }}
          title="Configure optional CARTO API key"
          className="p-1.5 bg-[#172333]/90 hover:bg-[#1D2B3D] border border-[#1E2E42] text-[#96A8BB] hover:text-[#EDF3F9] rounded transition-colors cursor-pointer shadow-md"
        >
          <KeyRound className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Optional CARTO Key Modal */}
      {showKeyModal && (
        <div className="absolute inset-0 z-50 bg-[#0B111B]/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#111B28] border border-[#1E2E42] rounded-lg p-4 max-w-sm w-full shadow-2xl space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-[#EDF3F9] uppercase tracking-wider flex items-center gap-1.5">
                <Layers className="w-4 h-4 text-[#65C4D6]" />
                Basemap Provider Settings
              </span>
              <button
                onClick={() => setShowKeyModal(false)}
                className="text-xs text-[#96A8BB] hover:text-[#EDF3F9]"
              >
                ✕
              </button>
            </div>
            <p className="text-[11px] text-[#96A8BB] leading-relaxed">
              Vayumarg operates by default with a 100% keyless, offline Natural Earth vector basemap. If you have an official CARTO API key, enter it below to enable optional satellite/dark raster tiles.
            </p>
            <div className="space-y-1">
              <label className="text-[10px] text-[#96A8BB] uppercase tracking-wider font-semibold">
                CARTO API Key (Optional)
              </label>
              <input
                type="password"
                value={keyInput}
                onChange={(e) => setKeyInput(e.target.value)}
                placeholder="Leave blank for offline vector basemap"
                className="w-full bg-[#0B1624] border border-[#1E2E42] rounded px-2.5 py-1.5 text-xs text-[#EDF3F9] font-mono focus:outline-none focus:border-[#65C4D6]"
              />
            </div>
            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => {
                  setKeyInput('');
                  localStorage.removeItem('carto_api_key');
                  setCartoApiKey('');
                  setUseOnlineCarto(false);
                  setShowKeyModal(false);
                }}
                className="px-2.5 py-1 text-xs text-[#D86F6F] hover:bg-[#1D2B3D] rounded border border-transparent hover:border-[#D86F6F]/40 cursor-pointer"
              >
                Reset to Offline
              </button>
              <button
                onClick={handleSaveApiKey}
                className="px-3 py-1 text-xs bg-[#1D2B3D] hover:bg-[#2B3D55] text-[#65C4D6] border border-[#65C4D6]/50 rounded cursor-pointer font-medium"
              >
                Save & Apply
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Map Legend Overlay */}
      <div className="absolute bottom-3 left-3 z-20 bg-[#111B28]/95 border border-[#1E2E42] p-2.5 rounded-md text-xs backdrop-blur-sm shadow-lg max-w-[260px]">
        <div className="font-semibold text-[#EDF3F9] text-[11px] mb-1.5 uppercase tracking-wider flex items-center justify-between">
          <span>Map Reference</span>
          <span className="text-[10px] text-[#96A8BB] font-mono">WGS 84 • OFFLINE</span>
        </div>
        <div className="space-y-1.5 text-[11px]">
          <div className="flex items-center gap-2">
            <span className="w-3 h-0.5 bg-[#65C4D6] rounded"></span>
            <span className="w-2 h-2 rounded-full bg-[#10B981] border border-[#F5F7FA]"></span>
            <span className="text-[#EDF3F9]">Observed Track (Start / Path)</span>
          </div>
          {forecastPoints && forecastPoints.length > 0 && (
            <div className="flex items-center gap-2">
              <span className="w-3 h-0.5 bg-[#E6AB65] border-t border-dashed border-[#E6AB65]"></span>
              <span className="w-2 h-2 rounded-full bg-[#E6AB65]"></span>
              <span className="text-[#E6AB65]">Forecast Extrapolation (+6/12/24h)</span>
            </div>
          )}
          {showVerification && verificationPoints && verificationPoints.length > 0 && (
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#CCD7E2]"></span>
              <span className="text-[#CCD7E2]">Ground-Truth Verification</span>
            </div>
          )}
          <div className="pt-1 border-t border-[#1E2E42] flex items-center justify-between text-[10px] text-[#96A8BB]">
            <span>Category:</span>
            <span className="text-[#65C4D6]">D/CS</span>
            <span className="text-[#E6AB65]">VSCS</span>
            <span className="text-[#D86F6F]">ESCS/SuCS</span>
          </div>
        </div>
      </div>
    </div>
  );
};
