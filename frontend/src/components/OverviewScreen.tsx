import React, { useState } from 'react';
import type { ObservationPoint, StormDetail } from '../types';
import { TrackMap } from './TrackMap';
import {
  Wind,
  Gauge,
  Compass,
  Satellite,
  ArrowRight,
  Clock,
  Play,
  Pause,
  RotateCcw,
  Database,
  Info,
} from 'lucide-react';

interface OverviewScreenProps {
  stormDetail: StormDetail | null;
  observations: ObservationPoint[];
  selectedObservation: ObservationPoint | null;
  onSelectObservation: (obs: ObservationPoint) => void;
  onNavigateToSatellite: () => void;
  onNavigateToForecast: () => void;
  isLoading: boolean;
  hasSatelliteCrop: boolean;
}

export const OverviewScreen: React.FC<OverviewScreenProps> = ({
  stormDetail,
  observations,
  selectedObservation,
  onSelectObservation,
  onNavigateToSatellite,
  onNavigateToForecast,
  isLoading,
  hasSatelliteCrop,
}) => {
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const playIntervalRef = React.useRef<number | null>(null);

  if (isLoading || !stormDetail) {
    return (
      <div className="flex-1 flex items-center justify-center p-8 bg-[#0B111B] text-[#96A8BB]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-[#61BACB] border-t-transparent rounded-full animate-spin" />
          <span className="text-xs uppercase tracking-wider font-medium">
            Loading Authenticated Meteorological Data...
          </span>
        </div>
      </div>
    );
  }

  const { profile } = stormDetail;
  const currentObs = selectedObservation || (observations.length > 0 ? observations[observations.length - 1] : null);

  // Playback controls for observation timeline
  const handleTogglePlay = () => {
    if (isPlaying) {
      if (playIntervalRef.current) clearInterval(playIntervalRef.current);
      setIsPlaying(false);
    } else {
      setIsPlaying(true);
      playIntervalRef.current = window.setInterval(() => {
        if (!currentObs) {
          if (observations.length > 0) onSelectObservation(observations[0]);
          return;
        }
        const currTime = currentObs.iso_time || currentObs.observation_time_utc;
        const currIdx = observations.findIndex((o) => (o.iso_time || o.observation_time_utc) === currTime);
        const nextIdx = (currIdx + 1) % observations.length;
        onSelectObservation(observations[nextIdx]);
      }, 700);
    }
  };

  const handleResetTimeline = () => {
    if (playIntervalRef.current) clearInterval(playIntervalRef.current);
    setIsPlaying(false);
    if (observations.length > 0) {
      onSelectObservation(observations[observations.length - 1]);
    }
  };

  const currentTime = currentObs?.iso_time || currentObs?.observation_time_utc;
  const currentIdx = currentTime
    ? observations.findIndex((o) => (o.iso_time || o.observation_time_utc) === currentTime)
    : observations.length - 1;

  return (
    <div className="flex-1 flex flex-col h-full overflow-y-auto bg-[#0B111B] p-4 gap-4">
      {/* Top Operational KPI Bar */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {/* Cyclone Profile */}
        <div className="bg-[#111B28] border border-[#1E2E42] p-3 rounded-md flex flex-col justify-between">
          <span className="text-[10px] text-[#96A8BB] uppercase tracking-wider font-semibold">
            Cyclone Identity
          </span>
          <div className="mt-1">
            <div className="text-lg font-bold text-[#EDF3F9] leading-tight">
              {profile.canonical_name}
            </div>
            <div className="text-[11px] text-[#96A8BB]">
              Season {profile.season_year} • {profile.primary_basin.split(' ')[0]}
            </div>
          </div>
        </div>

        {/* Official Category */}
        <div className="bg-[#111B28] border border-[#1E2E42] p-3 rounded-md flex flex-col justify-between">
          <span className="text-[10px] text-[#96A8BB] uppercase tracking-wider font-semibold">
            Official Category (IMD)
          </span>
          <div className="mt-1">
            <div className="text-sm font-bold text-[#E7AD65] leading-tight">
              {currentObs?.imd_category || profile.official_category}
            </div>
            <div className="text-[10px] text-[#96A8BB]">
              Peak: {profile.official_category.split(' ')[0]}
            </div>
          </div>
        </div>

        {/* Sustained Wind Speed */}
        <div className="bg-[#111B28] border border-[#1E2E42] p-3 rounded-md flex flex-col justify-between">
          <span className="text-[10px] text-[#96A8BB] uppercase tracking-wider font-semibold flex items-center justify-between">
            <span>Sustained Wind</span>
            <Wind className="w-3.5 h-3.5 text-[#61BACB]" />
          </span>
          <div className="mt-1">
            <div className="text-xl font-mono font-bold text-[#61BACB] tabular-nums">
              {currentObs?.wind_speed_knots ?? currentObs?.imd_wind_speed_knots ?? '-'}
              <span className="text-xs font-normal text-[#96A8BB] ml-1">kts</span>
            </div>
            <div className="text-[10px] text-[#96A8BB]">
              3-min IMD • JTWC: {currentObs?.jtwc_wind_speed_knots ?? '-'} kts (1-min)
            </div>
          </div>
        </div>

        {/* Central Atmospheric Pressure */}
        <div className="bg-[#111B28] border border-[#1E2E42] p-3 rounded-md flex flex-col justify-between">
          <span className="text-[10px] text-[#96A8BB] uppercase tracking-wider font-semibold flex items-center justify-between">
            <span>Central Pressure</span>
            <Gauge className="w-3.5 h-3.5 text-[#EDF3F9]" />
          </span>
          <div className="mt-1">
            <div className="text-xl font-mono font-bold text-[#EDF3F9] tabular-nums">
              {currentObs?.central_pressure_hpa ?? currentObs?.imd_central_pressure_hpa ?? '-'}
              <span className="text-xs font-normal text-[#96A8BB] ml-1">hPa</span>
            </div>
            <div className="text-[10px] text-[#96A8BB]">
              Min Recorded: {profile.min_central_pressure_hpa ?? '-'} hPa
            </div>
          </div>
        </div>

        {/* Selected Fix Timestamp */}
        <div className="bg-[#111B28] border border-[#1E2E42] p-3 rounded-md flex flex-col justify-between">
          <span className="text-[10px] text-[#96A8BB] uppercase tracking-wider font-semibold flex items-center justify-between">
            <span>Observation Time</span>
            <Clock className="w-3.5 h-3.5 text-[#96A8BB]" />
          </span>
          <div className="mt-1">
            <div className="text-xs font-mono font-bold text-[#EDF3F9] leading-tight">
              {currentTime ? currentTime.replace('T', ' ').substring(0, 16) : '-'} UTC
            </div>
            <div className="text-[10px] text-[#96A8BB] font-mono mt-0.5">
              Fix #{currentIdx + 1} of {observations.length}
            </div>
          </div>
        </div>

        {/* Geographic Coordinates */}
        <div className="bg-[#111B28] border border-[#1E2E42] p-3 rounded-md flex flex-col justify-between">
          <span className="text-[10px] text-[#96A8BB] uppercase tracking-wider font-semibold flex items-center justify-between">
            <span>Eye Coordinates</span>
            <Compass className="w-3.5 h-3.5 text-[#61BACB]" />
          </span>
          <div className="mt-1">
            <div className="text-xs font-mono font-bold text-[#EDF3F9] leading-tight">
              {currentObs ? `${currentObs.latitude.toFixed(2)}°N, ${currentObs.longitude.toFixed(2)}°E` : '-'}
            </div>
            <div className="text-[10px] text-[#96A8BB]">
              Nature: {currentObs?.nature || 'Tropical Cyclone'}
            </div>
          </div>
        </div>
      </div>

      {/* Main Command Center Layout: Map Focal Point + Right Quick Panels */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-4 min-h-[460px]">
        {/* Left 3 Columns: Main Historical Track Map */}
        <div className="lg:col-span-3 flex flex-col bg-[#111B28] border border-[#1E2E42] rounded-md p-3 gap-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-[#EDF3F9]">
                Geographic Cyclone Track & Synoptic Positions
              </span>
              <span className="text-[11px] text-[#96A8BB] font-mono">
                ({observations.length} Verified Fixes)
              </span>
            </div>

            {/* Quick Map Stats */}
            <div className="text-[11px] text-[#96A8BB] hidden sm:flex items-center gap-3">
              <span>Basin: <strong className="text-[#EDF3F9]">{profile.primary_basin}</strong></span>
              <span>•</span>
              <span>SID: <strong className="text-[#EDF3F9] font-mono">{profile.storm_id}</strong></span>
            </div>
          </div>

          {/* Interactive Map Component */}
          <div className="flex-1 w-full min-h-[380px] rounded border border-[#1E2E42] overflow-hidden">
            <TrackMap
              observations={observations}
              selectedObservation={currentObs}
              onSelectObservation={onSelectObservation}
            />
          </div>

          {/* Observation Timeline Scrubber */}
          <div className="bg-[#172333] border border-[#1E2E42] rounded px-3 py-2 flex flex-col gap-1.5">
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <button
                  onClick={handleTogglePlay}
                  className="p-1 rounded bg-[#1D2B3D] border border-[#1E2E42] text-[#EDF3F9] hover:bg-[#2B3D55] transition-colors cursor-pointer"
                  title={isPlaying ? 'Pause timeline' : 'Play chronological timeline'}
                >
                  {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                </button>
                <button
                  onClick={handleResetTimeline}
                  className="p-1 rounded bg-[#1D2B3D] border border-[#1E2E42] text-[#96A8BB] hover:text-[#EDF3F9] transition-colors cursor-pointer"
                  title="Jump to latest observation"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                </button>
                <span className="text-[#EDF3F9] font-medium text-[11px]">
                  Timeline Scrubber:
                </span>
                <span className="text-[#61BACB] font-mono text-[11px]">
                  {currentTime ? currentTime.replace('T', ' ').substring(0, 16) : '-'} UTC
                </span>
              </div>
              <div className="text-[10px] text-[#96A8BB] font-mono">
                {currentIdx + 1} / {observations.length}
              </div>
            </div>

            <input
              type="range"
              min={0}
              max={Math.max(0, observations.length - 1)}
              value={currentIdx >= 0 ? currentIdx : 0}
              onChange={(e) => {
                const idx = parseInt(e.target.value, 10);
                if (observations[idx]) {
                  onSelectObservation(observations[idx]);
                }
              }}
              className="w-full accent-[#61BACB] h-1.5 bg-[#1D2B3D] rounded cursor-pointer"
            />
          </div>
        </div>

        {/* Right 1 Column: Intelligence Links & Scientific Provenance */}
        <div className="flex flex-col gap-4">
          {/* Satellite Analysis Quick Card */}
          <div className="bg-[#111B28] border border-[#1E2E42] rounded-md p-4 flex flex-col justify-between gap-3">
            <div>
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-[#EDF3F9] flex items-center gap-1.5">
                  <Satellite className="w-4 h-4 text-[#61BACB]" />
                  Satellite Intelligence
                </span>
                <span
                  className={`px-2 py-0.5 text-[10px] font-semibold rounded ${
                    hasSatelliteCrop
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                      : 'bg-[#1D2B3D] text-[#96A8BB]'
                  }`}
                >
                  {hasSatelliteCrop ? 'AVAILABLE' : 'OFFLINE ARCHIVE'}
                </span>
              </div>
              <p className="text-xs text-[#96A8BB] mt-2 leading-relaxed">
                {hasSatelliteCrop
                  ? `Authentic ${profile.satellite_sensor} multi-channel 4km HDF5 imagery is ready for thermal brightness analytics (TIR-1, TIR-2, WV, MIR).`
                  : 'Multi-channel satellite crops are indexed for primary benchmark storms (AMPHAN, BIPARJOY, REMAL, DANA).'}
              </p>
            </div>

            <button
              onClick={onNavigateToSatellite}
              className="w-full py-2 px-3 bg-[#172333] hover:bg-[#1D2B3D] border border-[#1E2E42] hover:border-[#61BACB] text-[#EDF3F9] text-xs font-semibold rounded transition-colors flex items-center justify-center gap-2 group cursor-pointer"
            >
              <span>Inspect Satellite Imagery</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform text-[#61BACB]" />
            </button>
          </div>

          {/* Forecast Lab Quick Card */}
          <div className="bg-[#111B28] border border-[#1E2E42] rounded-md p-4 flex flex-col justify-between gap-3">
            <div>
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-[#EDF3F9] flex items-center gap-1.5">
                  <Wind className="w-4 h-4 text-[#E7AD65]" />
                  Forecast Lab
                </span>
                <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-[#E7AD65]/10 text-[#E7AD65] border border-[#E7AD65]/30">
                  +6h / +12h / +24h
                </span>
              </div>
              <p className="text-xs text-[#96A8BB] mt-2 leading-relaxed">
                Run transparent Geodesic Constant-Velocity forward projection with independent hindsight verification against future observations.
              </p>
            </div>

            <button
              onClick={onNavigateToForecast}
              className="w-full py-2 px-3 bg-[#172333] hover:bg-[#1D2B3D] border border-[#1E2E42] hover:border-[#E7AD65] text-[#EDF3F9] text-xs font-semibold rounded transition-colors flex items-center justify-center gap-2 group cursor-pointer"
            >
              <span>Launch Trajectory Simulation</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform text-[#E7AD65]" />
            </button>
          </div>

          {/* Scientific Provenance Summary Card */}
          <div className="bg-[#111B28] border border-[#1E2E42] rounded-md p-4 flex flex-col gap-2.5 flex-1">
            <span className="text-xs font-bold uppercase tracking-wider text-[#EDF3F9] flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-[#61BACB]" />
              Data Provenance
            </span>

            <div className="space-y-2 text-[11px] text-[#96A8BB]">
              <div className="flex justify-between py-1 border-b border-[#1E2E42]">
                <span>Best-Track Source:</span>
                <span className="text-[#EDF3F9] font-medium">NOAA IBTrACS v04r01</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#1E2E42]">
                <span>WMO Agency:</span>
                <span className="text-[#EDF3F9] font-medium">IMD / RSMC New Delhi</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#1E2E42]">
                <span>Wind Averaging:</span>
                <span className="text-[#EDF3F9] font-medium">3-minute sustained</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#1E2E42]">
                <span>Satellite Archive:</span>
                <span className="text-[#EDF3F9] font-medium">ISRO MOSDAC Level 1B</span>
              </div>
              <div className="flex justify-between py-1">
                <span>Total Observations:</span>
                <span className="text-[#EDF3F9] font-mono">{profile.total_observations} fixes</span>
              </div>
            </div>

            <div className="mt-auto pt-2 border-t border-[#1E2E42] flex items-start gap-1.5 text-[10px] text-[#96A8BB]/80">
              <Info className="w-3 h-3 text-[#61BACB] shrink-0 mt-0.5" />
              <span>
                All historical fixes adhere to authoritative WMO international best-track guidelines without synthetic interpolation.
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
