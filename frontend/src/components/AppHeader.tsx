import React from 'react';
import type { StormProfile } from '../types';
import { Database, Satellite, Compass } from 'lucide-react';

interface AppHeaderProps {
  storms: StormProfile[];
  selectedStormName: string;
  onSelectStorm: (name: string) => void;
  systemConnected: boolean;
  hasSatelliteCrop: boolean;
}

export const AppHeader: React.FC<AppHeaderProps> = ({
  storms,
  selectedStormName,
  onSelectStorm,
  systemConnected,
  hasSatelliteCrop,
}) => {
  return (
    <header className="h-14 bg-[#111B28] border-b border-[#1E2E42] px-4 flex items-center justify-between select-none z-30">
      {/* Brand & Identity */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded bg-[#172333] border border-[#61BACB]/40 flex items-center justify-center text-[#61BACB]">
          <Compass className="w-5 h-5 animate-pulse" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-extrabold tracking-wider text-[#EDF3F9] text-base leading-none">
              VAYUMARG
            </span>
            <span className="px-1.5 py-0.5 text-[10px] font-semibold tracking-wide bg-[#1D2B3D] border border-[#1E2E42] rounded text-[#61BACB] uppercase">
              STUDIO
            </span>
          </div>
          <div className="text-[10px] text-[#96A8BB] leading-tight">
            Cyclone Intelligence & Scientific Trajectory Lab
          </div>
        </div>
      </div>

      {/* Center: Selected Historical Cyclone Quick Selector */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-[#96A8BB] font-medium hidden sm:inline">Active Cyclone:</span>
        <div className="relative">
          <select
            value={selectedStormName}
            onChange={(e) => onSelectStorm(e.target.value)}
            className="bg-[#172333] border border-[#1E2E42] text-[#EDF3F9] text-xs font-semibold rounded px-3 py-1.5 pr-8 focus:outline-none focus:border-[#61BACB] cursor-pointer appearance-none hover:bg-[#1D2B3D]"
          >
            {storms.map((s) => (
              <option key={s.canonical_name} value={s.canonical_name}>
                {s.canonical_name} ({s.season_year}) — {s.primary_basin}
              </option>
            ))}
          </select>
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-[#96A8BB]">
            <svg className="w-3.5 h-3.5 fill-current" viewBox="0 0 20 20">
              <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
            </svg>
          </div>
        </div>

        {hasSatelliteCrop && (
          <span className="px-2 py-0.5 text-[10px] font-semibold bg-[#61BACB]/10 border border-[#61BACB]/30 text-[#61BACB] rounded flex items-center gap-1">
            <Satellite className="w-3 h-3" />
            INSAT Multi-Channel
          </span>
        )}
      </div>

      {/* Right: Source Badges, Operational Status & Historical Disclaimer */}
      <div className="flex items-center gap-3">
        {/* Source Badge */}
        <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 bg-[#172333] border border-[#1E2E42] rounded text-[11px] text-[#96A8BB]">
          <Database className="w-3 h-3 text-[#61BACB]" />
          <span>NOAA IBTrACS v04r01 + ISRO MOSDAC</span>
        </div>

        {/* Operational Availability State */}
        <div className="flex items-center gap-1.5 px-2 py-1 bg-[#172333] border border-[#1E2E42] rounded text-[11px]">
          <span
            className={`w-2 h-2 rounded-full ${
              systemConnected ? 'bg-emerald-400' : 'bg-[#D86F6F]'
            }`}
          />
          <span className="text-[#EDF3F9] font-medium hidden sm:inline">
            {systemConnected ? 'BACKEND LINKED' : 'DISCONNECTED'}
          </span>
        </div>

        {/* Historical Archive Disclaimer Tag */}
        <div className="hidden lg:block px-2.5 py-1 bg-[#1D2B3D]/70 border border-[#1E2E42] rounded text-[10px] text-[#96A8BB]">
          Historical Operations Archive
        </div>
      </div>
    </header>
  );
};
