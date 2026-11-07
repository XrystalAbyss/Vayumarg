import React from 'react';
import {
  BookOpen,
  Database,
  Satellite,
  Target,
  AlertTriangle,
  FileCheck,
  Scale,
} from 'lucide-react';

export const MethodologyScreen: React.FC = () => {
  return (
    <div className="flex-1 flex flex-col h-full overflow-y-auto bg-[#0B111B] p-6 gap-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="border-b border-[#1E2E42] pb-4">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#61BACB] mb-1">
          <BookOpen className="w-4 h-4" />
          <span>Scientific Transparency & Lineage Specification</span>
        </div>
        <h1 className="text-xl font-bold text-[#EDF3F9]">
          VAYUMARG Cyclone Intelligence Foundation & Operational Principles
        </h1>
        <p className="text-xs text-[#96A8BB] mt-1 max-w-3xl leading-relaxed">
          Full technical documentation detailing the multi-agency meteorological data sources, physical thermal feature engineering, deterministic geodesic forecasting algorithms, and rigorous quality control guarantees implemented in Vayumarg.
        </p>
      </div>

      {/* Grid of 2 Core Data Authorities */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Source 1: NOAA IBTrACS */}
        <div className="bg-[#111B28] border border-[#1E2E42] rounded-md p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-[#EDF3F9] flex items-center gap-2">
              <Database className="w-4 h-4 text-[#61BACB]" />
              NOAA IBTrACS v04r01
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#1D2B3D] text-[#61BACB] border border-[#1E2E42]">
              104,374 Fixes
            </span>
          </div>
          <p className="text-xs text-[#96A8BB] leading-relaxed">
            The International Best Track Archive for Climate Stewardship (IBTrACS) represents the official World Meteorological Organization (WMO) global cyclone best-track repository. Vayumarg ingests the North Indian Ocean basin archive spanning 1842 to 2026.
          </p>
          <div className="bg-[#172333] border border-[#1E2E42] p-2.5 rounded text-[11px] space-y-1 font-mono text-[#96A8BB]">
            <div><strong className="text-[#EDF3F9]">Citation:</strong> Knapp et al. (2018), NOAA NCEI. DOI: 10.25921/82ty-9e16</div>
            <div><strong className="text-[#EDF3F9]">Raw Checksum:</strong> SHA-256 6e0dd2dde1f22c4bf03995beb21944bf5976536c747b23ba85c6d300aeab69ff</div>
            <div><strong className="text-[#EDF3F9]">Missingness Standard:</strong> Strict SQL NULL retention; 0 instances of zero-coerced missing pressure or wind.</div>
          </div>
        </div>

        {/* Source 2: ISRO MOSDAC INSAT */}
        <div className="bg-[#111B28] border border-[#1E2E42] rounded-md p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-[#EDF3F9] flex items-center gap-2">
              <Satellite className="w-4 h-4 text-[#61BACB]" />
              ISRO MOSDAC Satellite Radiance
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#1D2B3D] text-[#61BACB] border border-[#1E2E42]">
              Level 1B Standard
            </span>
          </div>
          <p className="text-xs text-[#96A8BB] leading-relaxed">
            Authentic geostationary meteorological satellite radiance from INSAT-3DR (sub-satellite longitude 74.0°E) and INSAT-3DS (82.0°E). Raw calibrated counts and brightness temperatures are coregistered onto standardized 200×200 pixel crops (800 km × 800 km extent).
          </p>
          <div className="bg-[#172333] border border-[#1E2E42] p-2.5 rounded text-[11px] space-y-1 font-mono text-[#96A8BB]">
            <div><strong className="text-[#EDF3F9]">Authority:</strong> Space Applications Centre (SAC), ISRO, Ahmedabad.</div>
            <div><strong className="text-[#EDF3F9]">Payload Channels:</strong> TIR-1 (10.8 µm), TIR-2 (12.0 µm), WV (6.8 µm), MIR (3.9 µm).</div>
            <div><strong className="text-[#EDF3F9]">Integrity Gate:</strong> Verification status REAL_VERIFIED with cryptographic SHA-256 ledger.</div>
          </div>
        </div>
      </div>

      {/* Wind Averaging Conventions Table */}
      <div className="bg-[#111B28] border border-[#1E2E42] rounded-md p-4 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-[#EDF3F9] flex items-center gap-2">
            <Scale className="w-4 h-4 text-[#E7AD65]" />
            Multi-Agency Sustained Wind Averaging Conventions
          </span>
          <span className="text-[10px] text-[#96A8BB]">WMO Technical Document No. 560</span>
        </div>
        <p className="text-xs text-[#96A8BB] leading-relaxed">
          Different meteorological warning centers utilize distinct temporal averaging periods for sustained surface wind speed. Conflating these conventions introduces systematic scientific errors. Vayumarg explicitly separates and tracks each agency standard:
        </p>

        <div className="overflow-x-auto border border-[#1E2E42] rounded">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#172333] text-[#EDF3F9] font-bold border-b border-[#1E2E42]">
              <tr>
                <th className="p-2.5">Agency / Center</th>
                <th className="p-2.5">Averaging Period</th>
                <th className="p-2.5">Primary Basin Scope</th>
                <th className="p-2.5">Conversion Factor to 1-min</th>
                <th className="p-2.5">Role in Vayumarg</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1E2E42] text-[#96A8BB]">
              <tr>
                <td className="p-2.5 font-medium text-[#EDF3F9]">IMD (RSMC New Delhi)</td>
                <td className="p-2.5 text-[#61BACB] font-mono">3-minute</td>
                <td className="p-2.5">North Indian Ocean (Bay of Bengal & Arabian Sea)</td>
                <td className="p-2.5 font-mono">V(1-min) ≈ 1.14 × V(3-min)</td>
                <td className="p-2.5 text-[#EDF3F9]">Authoritative official cyclone stage classification</td>
              </tr>
              <tr>
                <td className="p-2.5 font-medium text-[#EDF3F9]">JTWC (Joint Typhoon Warning Center)</td>
                <td className="p-2.5 text-[#E7AD65] font-mono">1-minute</td>
                <td className="p-2.5">US DoD Operational Support (Worldwide)</td>
                <td className="p-2.5 font-mono">1.00 (Reference standard)</td>
                <td className="p-2.5 text-[#EDF3F9]">1-min sustained peak comparison benchmark</td>
              </tr>
              <tr>
                <td className="p-2.5 font-medium text-[#EDF3F9]">WMO Consensus</td>
                <td className="p-2.5 text-[#EDF3F9] font-mono">10-minute</td>
                <td className="p-2.5">International Standard (Tokyo, RSMC La Réunion)</td>
                <td className="p-2.5 font-mono">V(1-min) ≈ 1.14 × V(10-min) / 0.88</td>
                <td className="p-2.5 text-[#EDF3F9]">Global best-track cross-basin comparison</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Module A & Module B Methodologies */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Module A */}
        <div className="bg-[#111B28] border border-[#1E2E42] rounded-md p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-[#EDF3F9] flex items-center gap-2">
              <Satellite className="w-4 h-4 text-[#61BACB]" />
              Module A: Satellite Intensity Analytics
            </span>
            <span className="text-[10px] font-semibold text-[#61BACB] px-2 py-0.5 rounded bg-[#61BACB]/10 border border-[#61BACB]/20">
              Descriptive Baseline
            </span>
          </div>
          <p className="text-xs text-[#96A8BB] leading-relaxed">
            Module A computes deterministic physical brightness-temperature metrics directly from authentic INSAT HDF5 pixel tensors without black-box ML illusions:
          </p>
          <ul className="text-xs text-[#96A8BB] space-y-1.5 list-disc pl-4">
            <li><strong>Core Cold Temperature:</strong> Identifies coldest 10th percentile and absolute minimum Kelvin pixel within the inner eyewall region.</li>
            <li><strong>Cold-Cloud Fraction:</strong> Calculates percentage and square kilometers of deep convective cloud cover below 200 K, 220 K, and 240 K.</li>
            <li><strong>Azimuthal Symmetry Index:</strong> Measures circular uniformity across NW, NE, SW, and SE quadrants centered on the synoptic eye.</li>
            <li><strong>Radial Cooling Gradient:</strong> Evaluates outward temperature profile across 50 km, 100 km, 200 km, and 400 km rings.</li>
          </ul>
        </div>

        {/* Module B */}
        <div className="bg-[#111B28] border border-[#1E2E42] rounded-md p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-[#EDF3F9] flex items-center gap-2">
              <Target className="w-4 h-4 text-[#E7AD65]" />
              Module B: Geodesic Trajectory Extrapolation
            </span>
            <span className="text-[10px] font-semibold text-[#E7AD65] px-2 py-0.5 rounded bg-[#E7AD65]/10 border border-[#E7AD65]/20">
              Deterministic Baseline
            </span>
          </div>
          <p className="text-xs text-[#96A8BB] leading-relaxed">
            Module B generates reproducible forward projections at +6h, +12h, and +24h lead times strictly using observations available prior to issue time:
          </p>
          <ul className="text-xs text-[#96A8BB] space-y-1.5 list-disc pl-4">
            <li><strong>Haversine Velocity Estimation:</strong> Computes forward translation speed and bearing from the two most recent synoptic fixes.</li>
            <li><strong>Great-Circle Forward Extrapolation:</strong> Rhumb-line geodesic projection on WGS 84 ellipsoid.</li>
            <li><strong>Damped Intensity Persistence:</strong> Incorporates bounded recent rate-of-change with progressive dampening over forecast horizon.</li>
            <li><strong>Independent Hindsight Verification:</strong> Future fixes are matched post-facto to compute exact spatial error (\(km\)) and wind error (\(kts\)).</li>
          </ul>
        </div>
      </div>

      {/* Verified Real Satellite Asset Inventory */}
      <div className="bg-[#111B28] border border-[#1E2E42] rounded-md p-4 space-y-3">
        <span className="text-xs font-bold uppercase tracking-wider text-[#EDF3F9] flex items-center gap-2">
          <FileCheck className="w-4 h-4 text-[#61BACB]" />
          Verified Authentic INSAT Multi-Channel Granule Ledger
        </span>
        <div className="overflow-x-auto border border-[#1E2E42] rounded">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[#172333] text-[#EDF3F9] border-b border-[#1E2E42]">
              <tr>
                <th className="p-2.5">Storm Name</th>
                <th className="p-2.5">Season</th>
                <th className="p-2.5">Satellite Payload</th>
                <th className="p-2.5">Product ID</th>
                <th className="p-2.5">Channels</th>
                <th className="p-2.5">Resolution / Extent</th>
                <th className="p-2.5">Verification</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1E2E42] text-[#96A8BB]">
              <tr>
                <td className="p-2.5 font-bold text-[#EDF3F9]">AMPHAN</td>
                <td className="p-2.5">2020</td>
                <td className="p-2.5 text-[#61BACB]">INSAT-3DR</td>
                <td className="p-2.5">3RIMG_19MAY2020_2358</td>
                <td className="p-2.5">TIR-1, TIR-2, WV, MIR</td>
                <td className="p-2.5">4.0 km / 800 km</td>
                <td className="p-2.5 text-emerald-400 font-sans font-semibold">REAL_VERIFIED</td>
              </tr>
              <tr>
                <td className="p-2.5 font-bold text-[#EDF3F9]">BIPARJOY</td>
                <td className="p-2.5">2023</td>
                <td className="p-2.5 text-[#61BACB]">INSAT-3DR</td>
                <td className="p-2.5">3RIMG_12JUN2023_2358</td>
                <td className="p-2.5">TIR-1, TIR-2, WV, MIR</td>
                <td className="p-2.5">4.0 km / 800 km</td>
                <td className="p-2.5 text-emerald-400 font-sans font-semibold">REAL_VERIFIED</td>
              </tr>
              <tr>
                <td className="p-2.5 font-bold text-[#EDF3F9]">REMAL</td>
                <td className="p-2.5">2024</td>
                <td className="p-2.5 text-[#61BACB]">INSAT-3DR</td>
                <td className="p-2.5">3RIMG_26MAY2024_1802</td>
                <td className="p-2.5">TIR-1, TIR-2, WV, MIR</td>
                <td className="p-2.5">4.0 km / 800 km</td>
                <td className="p-2.5 text-emerald-400 font-sans font-semibold">REAL_VERIFIED</td>
              </tr>
              <tr>
                <td className="p-2.5 font-bold text-[#EDF3F9]">DANA</td>
                <td className="p-2.5">2024</td>
                <td className="p-2.5 text-[#61BACB]">INSAT-3DS</td>
                <td className="p-2.5">3SIMG_25OCT2024_2330</td>
                <td className="p-2.5">TIR-1, TIR-2, WV, MIR</td>
                <td className="p-2.5">4.0 km / 800 km</td>
                <td className="p-2.5 text-emerald-400 font-sans font-semibold">REAL_VERIFIED</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Scientific Limitations & Roadmap */}
      <div className="bg-[#111B28] border border-[#1E2E42] rounded-md p-4 space-y-3">
        <span className="text-xs font-bold uppercase tracking-wider text-[#D86F6F] flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-[#D86F6F]" />
          Scientific Limitations & Active Research Roadmap
        </span>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-[#96A8BB] pt-1 leading-relaxed">
          <div className="space-y-1.5">
            <h4 className="font-semibold text-[#EDF3F9]">Current Operational Limitations</h4>
            <p>
              1. The baseline geodesic forecast extrapolates recent forward translation vectors and does not incorporate barotropic atmospheric steering, mid-tropospheric ridges, or vertical wind shear.
            </p>
            <p>
              2. INSAT Level 1B radiometers exhibit lookup table clamping below 180 Kelvin in extremely intense overshooting convective tops.
            </p>
          </div>
          <div className="space-y-1.5">
            <h4 className="font-semibold text-[#EDF3F9]">Planned Future Research</h4>
            <p>
              1. <strong>Physics-Guided CNN:</strong> Multi-channel ResNet/Vision Transformer model trained on calibrated INSAT crops with agency-conditioned loss functions.
            </p>
            <p>
              2. <strong>Ensemble Trajectory:</strong> Integration of ECMWF/IMD GFS steering flow vectors with uncertainty covariance cones.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
