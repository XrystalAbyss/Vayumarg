import React, { useEffect, useState } from 'react';
import type {
  CycloneForecastResult,
  ObservationPoint,
  StormDetail,
  StormProfile,
} from '../types';
import { postGenerateForecast } from '../api';
import { TrackMap } from './TrackMap';
import {
  Play,
  RotateCw,
  Eye,
  EyeOff,
  ShieldCheck,
  AlertTriangle,
} from 'lucide-react';

interface ForecastLabScreenProps {
  storms: StormProfile[];
  selectedStormName: string;
  onSelectStorm: (name: string) => void;
  stormDetail: StormDetail | null;
  observations: ObservationPoint[];
}

export const ForecastLabScreen: React.FC<ForecastLabScreenProps> = ({
  storms,
  selectedStormName,
  onSelectStorm,
  observations,
}) => {
  const [selectedIssueTime, setSelectedIssueTime] = useState<string>('');
  const [selectedAgency, setSelectedAgency] = useState<string>('IMD');
  const [forecastResult, setForecastResult] = useState<CycloneForecastResult | null>(null);
  const [showVerification, setShowVerification] = useState<boolean>(false);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Default issue time: pick a middle observation with at least 2 prior observations and several future observations for verification
  useEffect(() => {
    if (observations.length >= 6) {
      const midIdx = Math.floor(observations.length * 0.45);
      const obsTime = observations[midIdx].iso_time || observations[midIdx].observation_time_utc;
      setSelectedIssueTime(obsTime);
    } else if (observations.length >= 2) {
      const obsTime = observations[observations.length - 2].iso_time || observations[observations.length - 2].observation_time_utc;
      setSelectedIssueTime(obsTime);
    }
    setForecastResult(null);
    setErrorMessage(null);
  }, [selectedStormName, observations]);

  // Generate forecast
  const handleGenerateForecast = async () => {
    if (!selectedIssueTime || !selectedStormName) return;

    setIsGenerating(true);
    setErrorMessage(null);

    try {
      const result = await postGenerateForecast(
        selectedStormName,
        selectedIssueTime,
        selectedAgency
      );
      setForecastResult(result);
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : 'Forecast execution failed.');
    } finally {
      setIsGenerating(false);
    }
  };

  // Automatically trigger initial forecast generation when issue time is set
  useEffect(() => {
    if (selectedIssueTime && !forecastResult && !isGenerating && observations.length >= 2) {
      handleGenerateForecast();
    }
  }, [selectedIssueTime]);

  // Observations up to the issue time (cyan track)
  const historicalInputObs = selectedIssueTime
    ? observations.filter((o) => (o.iso_time || o.observation_time_utc) <= selectedIssueTime)
    : observations;

  // Normalized motion and coordinate values
  const speedKmh = forecastResult?.estimated_speed_kmh;
  const bearingDeg = forecastResult?.estimated_bearing_deg;
  const currLat = forecastResult?.current_latitude;
  const currLon = forecastResult?.current_longitude;
  const currWind = forecastResult?.current_wind_speed_knots;

  const forecastPts = forecastResult?.forecast_points || [];
  const verificationPts = forecastResult?.verification || [];

  return (
    <div className="flex-1 flex flex-col h-full overflow-y-auto bg-[#0B111B] p-4 gap-4">
      {/* Top Interactive Configuration Control Bar */}
      <div className="bg-[#111B28] border border-[#1E2E42] p-3.5 rounded-md flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex flex-wrap items-center gap-3">
          {/* Cyclone Selector */}
          <div className="flex items-center gap-1.5">
            <span className="text-[#96A8BB] uppercase font-semibold text-[10px]">Storm:</span>
            <select
              value={selectedStormName}
              onChange={(e) => onSelectStorm(e.target.value)}
              className="bg-[#172333] border border-[#1E2E42] text-[#EDF3F9] font-bold rounded px-2.5 py-1.5 focus:border-[#61BACB] focus:outline-none cursor-pointer"
            >
              {storms.map((s) => (
                <option key={s.canonical_name} value={s.canonical_name}>
                  {s.canonical_name} ({s.season_year})
                </option>
              ))}
            </select>
          </div>

          {/* Historical Issue Time Selector */}
          <div className="flex items-center gap-1.5">
            <span className="text-[#96A8BB] uppercase font-semibold text-[10px]">Issue Time (UTC):</span>
            <select
              value={selectedIssueTime}
              onChange={(e) => setSelectedIssueTime(e.target.value)}
              className="bg-[#172333] border border-[#1E2E42] text-[#61BACB] font-mono font-semibold rounded px-2.5 py-1.5 focus:border-[#61BACB] focus:outline-none cursor-pointer max-w-[210px]"
            >
              {observations.map((o, idx) => {
                const t = o.iso_time || o.observation_time_utc;
                return (
                  <option key={t} value={t}>
                    #{idx + 1} • {t.replace('T', ' ').substring(0, 16)} UTC ({o.wind_speed_knots ?? '-'} kts)
                  </option>
                );
              })}
            </select>
          </div>

          {/* Agency Selector */}
          <div className="flex items-center gap-1.5">
            <span className="text-[#96A8BB] uppercase font-semibold text-[10px]">Agency Standard:</span>
            <div className="flex rounded border border-[#1E2E42] overflow-hidden">
              {(['IMD', 'JTWC', 'WMO'] as const).map((ag) => (
                <button
                  key={ag}
                  onClick={() => setSelectedAgency(ag)}
                  className={`px-2.5 py-1 text-[11px] font-semibold transition-colors cursor-pointer ${
                    selectedAgency === ag
                      ? 'bg-[#1D2B3D] text-[#61BACB]'
                      : 'bg-[#172333] text-[#96A8BB] hover:text-[#EDF3F9]'
                  }`}
                >
                  {ag}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Action Button & Verification Toggle */}
        <div className="flex items-center gap-3">
          {/* Hindsight Verification Toggle */}
          <button
            onClick={() => setShowVerification(!showVerification)}
            className={`px-3 py-1.5 rounded border transition-colors flex items-center gap-1.5 text-xs font-medium cursor-pointer ${
              showVerification
                ? 'bg-[#1D2B3D] border-[#61BACB] text-[#EDF3F9]'
                : 'bg-[#172333] border-[#1E2E42] text-[#96A8BB] hover:text-[#EDF3F9]'
            }`}
            title="Toggle hindsight ground-truth validation (separated post-facto)"
          >
            {showVerification ? <Eye className="w-3.5 h-3.5 text-[#61BACB]" /> : <EyeOff className="w-3.5 h-3.5" />}
            <span>Hindsight Verification</span>
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                showVerification ? 'bg-[#61BACB]' : 'bg-[#96A8BB]/40'
              }`}
            />
          </button>

          {/* Generate Forecast Action */}
          <button
            onClick={handleGenerateForecast}
            disabled={isGenerating || observations.length < 2}
            className="px-4 py-1.5 bg-[#E7AD65] hover:bg-[#d69b50] text-[#0B111B] font-bold text-xs rounded transition-colors flex items-center gap-1.5 disabled:opacity-50 cursor-pointer shadow-sm"
          >
            {isGenerating ? (
              <>
                <RotateCw className="w-3.5 h-3.5 animate-spin" />
                <span>Computing...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Generate Forecast</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error notification if any */}
      {errorMessage && (
        <div className="p-3 bg-[#D86F6F]/10 border border-[#D86F6F] rounded-md text-xs text-[#D86F6F] flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Main Grid: Forecast Map + Horizon Diagnostic Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1">
        {/* Left Column: Interactive Forecast Map (7 cols) */}
        <div className="lg:col-span-7 flex flex-col bg-[#111B28] border border-[#1E2E42] rounded-md p-3 gap-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-[#EDF3F9]">
                Forward Geodesic Projection Map
              </span>
              <span className="text-[10px] text-[#E7AD65] font-mono px-2 py-0.5 rounded bg-[#E7AD65]/10 border border-[#E7AD65]/20">
                +6h / +12h / +24h Horizons
              </span>
            </div>

            {/* Current Motion Vector Badges */}
            {speedKmh != null && (
              <div className="text-[11px] text-[#96A8BB] flex items-center gap-2 font-mono">
                <span>Speed: <strong className="text-[#61BACB]">{speedKmh} km/h</strong></span>
                <span>•</span>
                <span>Bearing: <strong className="text-[#EDF3F9]">{bearingDeg}°</strong></span>
              </div>
            )}
          </div>

          {/* Interactive Map */}
          <div className="flex-1 w-full min-h-[380px] rounded border border-[#1E2E42] overflow-hidden">
            <TrackMap
              observations={historicalInputObs}
              forecastPoints={forecastPts}
              verificationPoints={verificationPts}
              showVerification={showVerification}
            />
          </div>

          {/* Map Color Legend Footer */}
          <div className="flex items-center justify-between text-[11px] text-[#96A8BB] pt-1">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#61BACB]"></span>
                <span className="text-[#EDF3F9]">Input Historical Track (Cyan)</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#E7AD65]"></span>
                <span className="text-[#E7AD65]">Forecast Projection (Amber)</span>
              </span>
              {showVerification && (
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#CCD7E2]"></span>
                  <span className="text-[#CCD7E2]">Actual Ground-Truth (Pale Gray)</span>
                </span>
              )}
            </div>
            <span className="text-[10px] text-[#96A8BB] font-mono">
              Issue: {selectedIssueTime.replace('T', ' ').substring(0, 16)} UTC
            </span>
          </div>
        </div>

        {/* Right Column: Calculated Horizons & Transparent Methodology (5 cols) */}
        <div className="lg:col-span-5 flex flex-col gap-3">
          {/* Issue State Summary Header */}
          <div className="bg-[#111B28] border border-[#1E2E42] rounded-md p-3.5 space-y-2">
            <span className="text-xs font-bold uppercase tracking-wider text-[#EDF3F9] flex items-center justify-between">
              <span>Forecast Initialization State</span>
              <span className="text-[10px] font-mono text-[#61BACB]">
                {forecastResult?.input_observation_count ?? historicalInputObs.length} Fixes Considered
              </span>
            </span>

            <div className="grid grid-cols-2 gap-2 text-xs pt-1">
              <div className="bg-[#172333] border border-[#1E2E42] p-2 rounded">
                <span className="text-[10px] text-[#96A8BB]">Eye Center at Issue Time</span>
                <div className="text-sm font-mono font-bold text-[#EDF3F9]">
                  {currLat != null && currLon != null
                    ? `${currLat.toFixed(2)}°N, ${currLon.toFixed(2)}°E`
                    : '-'}
                </div>
              </div>
              <div className="bg-[#172333] border border-[#1E2E42] p-2 rounded">
                <span className="text-[10px] text-[#96A8BB]">Wind Speed ({selectedAgency})</span>
                <div className="text-sm font-mono font-bold text-[#61BACB]">
                  {currWind ?? '-'} kts
                </div>
              </div>
              <div className="bg-[#172333] border border-[#1E2E42] p-2 rounded">
                <span className="text-[10px] text-[#96A8BB]">Translation Velocity</span>
                <div className="text-sm font-mono font-bold text-[#E7AD65]">
                  {speedKmh ?? '-'} km/h
                </div>
              </div>
              <div className="bg-[#172333] border border-[#1E2E42] p-2 rounded">
                <span className="text-[10px] text-[#96A8BB]">Initial Heading</span>
                <div className="text-sm font-mono font-bold text-[#EDF3F9]">
                  {bearingDeg ?? '-'}° (Compass)
                </div>
              </div>
            </div>
          </div>

          {/* Forecast Horizons (+6h, +12h, +24h Cards) */}
          <div className="space-y-2 flex-1">
            <span className="text-xs font-bold uppercase tracking-wider text-[#EDF3F9] px-1">
              Projected Spatial Positions & Verification
            </span>

            {forecastPts.map((pt) => {
              const vPt = verificationPts.find((v) => v.lead_time_hours === pt.lead_time_hours);
              return (
                <div
                  key={pt.lead_time_hours}
                  className="bg-[#111B28] border border-[#1E2E42] hover:border-[#E7AD65]/50 rounded-md p-3 transition-colors text-xs space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-[#E7AD65] text-sm flex items-center gap-1.5">
                      <span>+{pt.lead_time_hours} Hours</span>
                      <span className="text-[10px] text-[#96A8BB] font-normal font-mono">
                        ({pt.valid_time_utc.replace('T', ' ').substring(0, 16)} UTC)
                      </span>
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-[#1D2B3D] text-[#EDF3F9] border border-[#1E2E42]">
                      {pt.predicted_imd_category?.split(' ')[0] ?? pt.predicted_imd_category ?? 'N/A'}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-[10px] text-[#96A8BB]">Predicted Coordinates</span>
                      <div className="font-mono text-[#EDF3F9] font-medium">
                        {pt.predicted_latitude.toFixed(2)}°N, {pt.predicted_longitude.toFixed(2)}°E
                      </div>
                    </div>
                    <div>
                      <span className="text-[10px] text-[#96A8BB]">Predicted Wind</span>
                      <div className="font-mono text-[#61BACB] font-bold">
                        {pt.predicted_wind_speed_knots} kts
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-[#96A8BB] pt-1 border-t border-[#1E2E42]">
                    <span>Cone Uncertainty Radius:</span>
                    <span className="font-mono text-[#E7AD65]">±{pt.uncertainty_radius_km} km</span>
                  </div>

                  {/* Independent Hindsight Verification Row */}
                  {showVerification && vPt && (
                    <div className="mt-2 pt-2 border-t border-dashed border-[#1E2E42] bg-[#172333]/60 -mx-3 -mb-3 p-2.5 rounded-b-md space-y-1">
                      <div className="flex items-center justify-between text-[10px] font-semibold text-[#CCD7E2]">
                        <span className="uppercase tracking-wider">Hindsight Verification Match:</span>
                        {vPt.track_error_km != null ? (
                          <span className="text-[#E7AD65] font-mono">
                            Spatial Error: <strong>{vPt.track_error_km} km</strong>
                          </span>
                        ) : (
                          <span className="text-[#96A8BB]">No fix within 2h</span>
                        )}
                      </div>

                      {vPt.actual_latitude != null && (
                        <div className="grid grid-cols-2 gap-1 text-[11px]">
                          <div>
                            <span className="text-[9px] text-[#96A8BB]">Actual Fix:</span>
                            <div className="font-mono text-[#EDF3F9]">
                              {vPt.actual_latitude.toFixed(2)}°N, {vPt.actual_longitude?.toFixed(2)}°E
                            </div>
                          </div>
                          <div>
                            <span className="text-[9px] text-[#96A8BB]">Actual Wind:</span>
                            <div className="font-mono text-[#EDF3F9]">
                              {vPt.actual_wind_kt ?? '-'} kts (Δ {vPt.wind_error_kt ?? '-'} kts)
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Transparent Mathematical Formulation Card */}
          <div className="bg-[#111B28] border border-[#1E2E42] rounded-md p-3.5 space-y-2 text-xs">
            <span className="font-bold text-[#EDF3F9] uppercase tracking-wider text-[11px] flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-[#61BACB]" />
              Transparent Forecast Formulation
            </span>
            <p className="text-[11px] text-[#96A8BB] leading-relaxed">
              Forward extrapolation solves great-circle geodesic destination coordinates along bearing angle &theta; over forward distance d = v &times; &Delta;t:
            </p>
            <div className="bg-[#0B111B] border border-[#1E2E42] p-2 rounded text-[10px] font-mono text-[#61BACB] overflow-x-auto">
              sin(&phi;₂) = sin(&phi;₁)cos(&delta;) + cos(&phi;₁)sin(&delta;)cos(&theta;)
            </div>
            <p className="text-[10px] text-[#96A8BB]/80">
              *Physical constraint: Assumes short-term translation persistence. Verification data is strictly evaluated post-facto without predictive data leakage.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
