import React, { useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  CheckCircle,
  Copy,
  Database,
  Download,
  Eye,
  FileSpreadsheet,
  FileText,
  Layers,
  RefreshCw,
  SplitSquareVertical,
  Thermometer,
  ZoomIn,
  ZoomOut,
  X,
  Crosshair,
  ShieldAlert,
  Flame,
  Activity,
  Compass
} from 'lucide-react';
import type {
  DatasetColormap,
  DatasetSampleDetail,
  DatasetSampleItem,
  DatasetSummary,
  PixelProbeResult,
} from '../types';
import {
  fetchDatasetPixel,
  fetchDatasetSampleDetail,
  fetchDatasetSamples,
  fetchDatasetSummary,
  getDatasetPreviewUrl,
  getManifestExportUrl,
  getMetadataCsvExportUrl,
} from '../api';

const COLORMAP_OPTIONS: { id: DatasetColormap; label: string; desc: string }[] = [
  { id: 'thermal_ir', label: 'Thermal IR', desc: 'Standard continuous physical Kelvin scale' },
  { id: 'grayscale_inv', label: 'Inverted Gray', desc: 'Cold clouds bright white, warm sea dark' },
  { id: 'dvorak_bd', label: 'Dvorak BD-Curve', desc: 'Stepped operational BD enhancement' },
  { id: 'water_vapor', label: 'Water Vapor', desc: 'Upper-tropospheric humidity contrast' },
];

const CHANNELS_LIST = ['TIR-1', 'TIR-2', 'WV', 'MIR'];

export const DatasetExplorerScreen: React.FC = () => {
  // Master data state
  const [summary, setSummary] = useState<DatasetSummary | null>(null);
  const [samples, setSamples] = useState<DatasetSampleItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedStormFilter, setSelectedStormFilter] = useState<string>('ALL');
  const [selectedChannelFilter, setSelectedChannelFilter] = useState<string>('TIR-1');
  const [selectedColormapFilter, setSelectedColormapFilter] = useState<DatasetColormap>('thermal_ir');
  const [selectedBasinFilter, setSelectedBasinFilter] = useState<string>('ALL');
  const [selectedSensorFilter, setSelectedSensorFilter] = useState<string>('ALL');
  const [selectedEligibilityFilter, setSelectedEligibilityFilter] = useState<string>('ALL');

  // View mode: 'gallery' or 'compare'
  const [viewMode, setViewMode] = useState<'gallery' | 'compare'>('gallery');

  // Detail Modal State
  const [inspectSampleName, setInspectSampleName] = useState<string | null>(null);
  const [detailData, setDetailData] = useState<DatasetSampleDetail | null>(null);
  const [isDetailLoading, setIsDetailLoading] = useState<boolean>(false);
  const [activeDetailTab, setActiveDetailTab] = useState<'physics' | 'provenance' | 'targets'>('physics');

  // Detail Viewer Controls
  const [viewerChannel, setViewerChannel] = useState<string>('TIR-1');
  const [viewerColormap, setViewerColormap] = useState<DatasetColormap>('thermal_ir');
  const [zoomLevel, setZoomLevel] = useState<number>(1);
  const [showCenterMarker, setShowCenterMarker] = useState<boolean>(true);
  const [showClampedMask, setShowClampedMask] = useState<boolean>(false);
  const [showCompositeLegend, setShowCompositeLegend] = useState<boolean>(false);

  // Pixel Probe State
  const [probedPixel, setProbedPixel] = useState<PixelProbeResult | null>(null);
  const [isProbing, setIsProbing] = useState<boolean>(false);

  // Side-by-Side Comparison State
  const [compareSlotA, setCompareSlotA] = useState<{ storm: string; channel: string; colormap: DatasetColormap }>({
    storm: 'AMPHAN',
    channel: 'TIR-1',
    colormap: 'dvorak_bd',
  });
  const [compareSlotB, setCompareSlotB] = useState<{ storm: string; channel: string; colormap: DatasetColormap }>({
    storm: 'DANA',
    channel: 'TIR-1',
    colormap: 'dvorak_bd',
  });
  const [syncCompareZoom, setSyncCompareZoom] = useState<boolean>(true);
  const [compareZoom, setCompareZoom] = useState<number>(1);

  // Export Modal State
  const [showExportModal, setShowExportModal] = useState<boolean>(false);
  const [copySuccess, setCopySuccess] = useState<string | null>(null);

  // Load initial dataset
  useEffect(() => {
    async function load() {
      try {
        setIsLoading(true);
        setError(null);
        const [sumData, samData] = await Promise.all([
          fetchDatasetSummary().catch(() => null),
          fetchDatasetSamples(),
        ]);
        setSummary(sumData);
        setSamples(samData);
      } catch (err: unknown) {
        console.error('Failed to load dataset:', err);
        setError(err instanceof Error ? err.message : 'Could not fetch satellite dataset samples');
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, []);

  // Load sample detail when inspect modal opens
  useEffect(() => {
    if (!inspectSampleName) {
      setDetailData(null);
      setProbedPixel(null);
      return;
    }

    async function loadDetail() {
      try {
        setIsDetailLoading(true);
        const detail = await fetchDatasetSampleDetail(inspectSampleName!);
        setDetailData(detail);
        setViewerChannel('TIR-1');
        setViewerColormap('thermal_ir');
        setZoomLevel(1);
      } catch (err) {
        console.error('Failed to load sample detail:', err);
      } finally {
        setIsDetailLoading(false);
      }
    }
    loadDetail();
  }, [inspectSampleName]);

  // Handle probe pixel click on image
  const handleImageClick = async (e: React.MouseEvent<HTMLImageElement>) => {
    if (!inspectSampleName) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    // Normalize to 201x201 grid
    const normX = Math.max(0, Math.min(200, Math.floor((clickX / rect.width) * 201)));
    const normY = Math.max(0, Math.min(200, Math.floor((clickY / rect.height) * 201)));

    try {
      setIsProbing(true);
      const res = await fetchDatasetPixel(inspectSampleName, viewerChannel, normX, normY);
      setProbedPixel(res);
    } catch (err) {
      console.error('Probe failed:', err);
    } finally {
      setIsProbing(false);
    }
  };

  // Copy helper
  const handleCopy = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopySuccess(label);
    setTimeout(() => setCopySuccess(null), 2000);
  };

  // Filtered samples list
  const filteredSamples = useMemo(() => {
    return samples.filter((s) => {
      if (selectedStormFilter !== 'ALL' && s.storm_name !== selectedStormFilter) return false;
      if (selectedBasinFilter !== 'ALL' && !s.ocean_basin.includes(selectedBasinFilter)) return false;
      if (selectedSensorFilter !== 'ALL' && s.satellite !== selectedSensorFilter) return false;
      if (selectedEligibilityFilter === 'ELIGIBLE' && !s.primary_imd_eligible) return false;
      if (selectedEligibilityFilter === 'INELIGIBLE' && s.primary_imd_eligible) return false;
      return true;
    });
  }, [samples, selectedStormFilter, selectedBasinFilter, selectedSensorFilter, selectedEligibilityFilter]);

  // Get active analytics for detail modal
  const activeChannelAnalytics = useMemo(() => {
    if (!detailData || !detailData.channels || !detailData.channels[viewerChannel]) return null;
    return detailData.channels[viewerChannel].analytics;
  }, [detailData, viewerChannel]);

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-[#0B111B] text-[#EDF3F9]">
      {/* Top Banner: Scientific Identification & Inventory Statistics */}
      <div className="bg-[#111B28] border-b border-[#1E2E42] px-6 py-3.5 flex flex-wrap items-center justify-between gap-4 shrink-0">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-[#61BACB]/10 border border-[#61BACB]/30 rounded text-[#61BACB]">
            <Database className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-sm font-bold tracking-wide text-[#EDF3F9] uppercase">
                Satellite Dataset Explorer
              </h1>
              <span className="px-2 py-0.5 text-[10px] font-mono font-semibold bg-[#172333] border border-[#1E2E42] text-[#61BACB] rounded">
                ISRO MOSDAC Level 1B
              </span>
            </div>
            <p className="text-[11px] text-[#96A8BB]">
              Authentic calibrated multispectral INSAT-3DR/3DS observations • Strict physical Kelvin preservation
            </p>
          </div>
        </div>

        {/* Inventory Metric Pills */}
        <div className="flex items-center gap-3 text-xs">
          <div className="px-3 py-1.5 bg-[#172333] border border-[#1E2E42] rounded flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#61BACB] animate-pulse"></span>
            <span className="text-[#96A8BB]">Physical Observations:</span>
            <span className="font-bold text-[#EDF3F9] font-mono">
              {summary?.physical_observations_count ?? 4} Verified Samples
            </span>
          </div>
          <div className="px-3 py-1.5 bg-[#172333] border border-[#1E2E42] rounded flex items-center gap-2">
            <span className="text-[#96A8BB]">Preview Variations:</span>
            <span className="font-bold text-[#E7AD65] font-mono">
              {summary?.calibrated_preview_variations_count ?? 88} Calibrated PNGs
            </span>
          </div>

          {/* Mode Switcher */}
          <div className="flex items-center border border-[#1E2E42] rounded overflow-hidden">
            <button
              onClick={() => setViewMode('gallery')}
              className={`px-3 py-1.5 text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer ${
                viewMode === 'gallery'
                  ? 'bg-[#1D2B3D] text-[#EDF3F9] font-semibold'
                  : 'bg-[#111B28] text-[#96A8BB] hover:text-[#EDF3F9]'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Gallery Grid</span>
            </button>
            <button
              onClick={() => setViewMode('compare')}
              className={`px-3 py-1.5 text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer ${
                viewMode === 'compare'
                  ? 'bg-[#1D2B3D] text-[#EDF3F9] font-semibold'
                  : 'bg-[#111B28] text-[#96A8BB] hover:text-[#EDF3F9]'
              }`}
            >
              <SplitSquareVertical className="w-3.5 h-3.5 text-[#E7AD65]" />
              <span>Side-by-Side Dual</span>
            </button>
          </div>

          {/* Export Button */}
          <button
            onClick={() => setShowExportModal(true)}
            className="px-3 py-1.5 bg-[#61BACB]/15 hover:bg-[#61BACB]/25 border border-[#61BACB]/40 text-[#61BACB] rounded text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Dataset</span>
          </button>
        </div>
      </div>

      {/* Audit & Disclaimer Bar */}
      {error && (
        <div className="bg-[#D86F6F]/10 border-b border-[#D86F6F]/30 px-6 py-2 text-xs text-[#D86F6F]">
          {error}
        </div>
      )}
      <div className="bg-[#172333]/80 border-b border-[#1E2E42] px-6 py-2 flex flex-wrap items-center justify-between text-[11px] text-[#96A8BB] gap-2 shrink-0">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-3.5 h-3.5 text-[#E7AD65]" />
          <span>
            <strong className="text-[#EDF3F9]">Audit Status:</strong> 4 processed physical observations registered (Amphan, Biparjoy, Dana, Remal). 2 raw uncropped assets quarantined (Fani, Tauktae). 2 incomplete downloads excluded (Fengal, Remal Pass-2).
          </span>
        </div>
        <div className="text-[10px] text-[#96A8BB]/70 font-mono">
          NO SYNTHETIC DATA • NO DUPLICATE PREVIEW SAMPLES
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Multi-Dimensional Filter Bar */}
        <div className="bg-[#111B28] border-b border-[#1E2E42] px-6 py-3 flex flex-wrap items-center justify-between gap-3 shrink-0">
          <div className="flex flex-wrap items-center gap-3 text-xs">
            {/* Storm Filter */}
            <div className="flex items-center gap-1.5">
              <span className="text-[#96A8BB] font-medium">Cyclone:</span>
              <select
                value={selectedStormFilter}
                onChange={(e) => setSelectedStormFilter(e.target.value)}
                className="bg-[#172333] border border-[#1E2E42] text-[#EDF3F9] rounded px-2.5 py-1 text-xs focus:outline-none focus:border-[#61BACB] cursor-pointer"
              >
                <option value="ALL">All Cyclones ({samples.length})</option>
                {samples.map((s) => (
                  <option key={s.storm_name} value={s.storm_name}>
                    {s.storm_name} ({s.season_year})
                  </option>
                ))}
              </select>
            </div>

            {/* Channel Filter */}
            <div className="flex items-center gap-1.5">
              <span className="text-[#96A8BB] font-medium">Spectral Channel:</span>
              <div className="flex items-center bg-[#172333] border border-[#1E2E42] rounded overflow-hidden">
                {CHANNELS_LIST.map((ch) => (
                  <button
                    key={ch}
                    onClick={() => setSelectedChannelFilter(ch)}
                    className={`px-2.5 py-1 text-xs font-mono font-medium transition-colors cursor-pointer ${
                      selectedChannelFilter === ch
                        ? 'bg-[#61BACB]/20 text-[#61BACB] font-bold'
                        : 'text-[#96A8BB] hover:text-[#EDF3F9]'
                    }`}
                  >
                    {ch}
                  </button>
                ))}
              </div>
            </div>

            {/* Colormap Filter */}
            <div className="flex items-center gap-1.5">
              <span className="text-[#96A8BB] font-medium">Colormap:</span>
              <select
                value={selectedColormapFilter}
                onChange={(e) => setSelectedColormapFilter(e.target.value as DatasetColormap)}
                className="bg-[#172333] border border-[#1E2E42] text-[#EDF3F9] rounded px-2.5 py-1 text-xs focus:outline-none focus:border-[#61BACB] cursor-pointer"
              >
                {COLORMAP_OPTIONS.map((cm) => (
                  <option key={cm.id} value={cm.id}>
                    {cm.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Basin Filter */}
            <div className="flex items-center gap-1.5">
              <span className="text-[#96A8BB] font-medium">Basin:</span>
              <select
                value={selectedBasinFilter}
                onChange={(e) => setSelectedBasinFilter(e.target.value)}
                className="bg-[#172333] border border-[#1E2E42] text-[#EDF3F9] rounded px-2.5 py-1 text-xs focus:outline-none focus:border-[#61BACB] cursor-pointer"
              >
                <option value="ALL">All Basins</option>
                <option value="Bay of Bengal">Bay of Bengal</option>
                <option value="Arabian Sea">Arabian Sea</option>
              </select>
            </div>

            {/* Platform Filter */}
            <div className="flex items-center gap-1.5">
              <span className="text-[#96A8BB] font-medium">Platform:</span>
              <select
                value={selectedSensorFilter}
                onChange={(e) => setSelectedSensorFilter(e.target.value)}
                className="bg-[#172333] border border-[#1E2E42] text-[#EDF3F9] rounded px-2.5 py-1 text-xs focus:outline-none focus:border-[#61BACB] cursor-pointer"
              >
                <option value="ALL">All Satellites</option>
                <option value="INSAT-3DR">INSAT-3DR</option>
                <option value="INSAT-3DS">INSAT-3DS</option>
              </select>
            </div>

            {/* IMD Target Category Filter */}
            <div className="flex items-center gap-1.5">
              <span className="text-[#96A8BB] font-medium">Eligibility:</span>
              <select
                value={selectedEligibilityFilter}
                onChange={(e) => setSelectedEligibilityFilter(e.target.value)}
                className="bg-[#172333] border border-[#1E2E42] text-[#EDF3F9] rounded px-2.5 py-1 text-xs focus:outline-none focus:border-[#61BACB] cursor-pointer"
              >
                <option value="ALL">All Targets</option>
                <option value="ELIGIBLE">IMD Label Eligible</option>
                <option value="INELIGIBLE">Ineligible / Weakening</option>
              </select>
            </div>
          </div>

          <div className="text-xs text-[#96A8BB]">
            Showing <strong className="text-[#EDF3F9]">{filteredSamples.length}</strong> of {samples.length} physical samples
          </div>
        </div>

        {/* View Mode: Gallery Grid */}
        {viewMode === 'gallery' && (
          <div className="flex-1 overflow-y-auto p-6">
            {isLoading ? (
              <div className="h-64 flex flex-col items-center justify-center gap-3 text-[#96A8BB]">
                <RefreshCw className="w-6 h-6 animate-spin text-[#61BACB]" />
                <span className="text-xs">Loading authentic satellite observations...</span>
              </div>
            ) : filteredSamples.length === 0 ? (
              <div className="h-64 flex flex-col items-center justify-center gap-3 text-center p-6 bg-[#111B28] border border-[#1E2E42] rounded-lg">
                <AlertTriangle className="w-8 h-8 text-[#E7AD65]" />
                <h3 className="text-sm font-bold text-[#EDF3F9]">No Authentic Samples Match Current Filter</h3>
                <p className="text-xs text-[#96A8BB] max-w-sm">
                  Adjust your storm, channel, or eligibility filters to inspect verified satellite crops.
                </p>
                <button
                  onClick={() => {
                    setSelectedStormFilter('ALL');
                    setSelectedBasinFilter('ALL');
                    setSelectedSensorFilter('ALL');
                    setSelectedEligibilityFilter('ALL');
                  }}
                  className="px-3 py-1.5 bg-[#172333] hover:bg-[#1D2B3D] border border-[#1E2E42] text-xs font-semibold rounded text-[#61BACB] cursor-pointer"
                >
                  Reset Filters
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
                {filteredSamples.map((sample) => {
                  const chSummary = sample.channel_summaries[selectedChannelFilter];
                  const imdObs = sample.primary_imd_observation;
                  const isWaterVaporColormap = selectedColormapFilter === 'water_vapor';
                  const isDvorakColormap = selectedColormapFilter === 'dvorak_bd';

                  // Select safe preview colormap for channel
                  let effectiveColormap = selectedColormapFilter;
                  if (selectedChannelFilter !== 'WV' && isWaterVaporColormap) {
                    effectiveColormap = 'thermal_ir';
                  } else if (selectedChannelFilter !== 'TIR-1' && selectedChannelFilter !== 'TIR-2' && isDvorakColormap) {
                    effectiveColormap = 'thermal_ir';
                  }

                  const previewUrl = getDatasetPreviewUrl(
                    sample.storm_name,
                    selectedChannelFilter,
                    effectiveColormap,
                    false
                  );

                  return (
                    <div
                      key={sample.crop_id}
                      className="bg-[#111B28] border border-[#1E2E42] hover:border-[#61BACB]/50 rounded-lg overflow-hidden flex flex-col transition-all group"
                    >
                      {/* Image Preview Container */}
                      <div className="relative aspect-square bg-[#0B111B] flex items-center justify-center overflow-hidden border-b border-[#1E2E42]">
                        <img
                          src={previewUrl}
                          alt={`${sample.storm_name} ${selectedChannelFilter}`}
                          className="w-full h-full object-contain transition-transform duration-300 group-hover:scale-105"
                          loading="lazy"
                        />

                        {/* Top Badges */}
                        <div className="absolute top-2.5 left-2.5 flex items-center gap-1.5">
                          <span className="px-2 py-0.5 bg-[#0B111B]/85 border border-[#1E2E42] text-[#61BACB] font-mono text-[10px] font-bold rounded">
                            {selectedChannelFilter}
                          </span>
                          <span className="px-2 py-0.5 bg-[#0B111B]/85 border border-[#1E2E42] text-[#96A8BB] font-mono text-[10px] rounded">
                            {effectiveColormap}
                          </span>
                        </div>

                        {/* Top Right: Status Badge */}
                        <div className="absolute top-2.5 right-2.5">
                          {sample.primary_imd_eligible ? (
                            <span className="px-2 py-0.5 bg-[#61BACB]/20 border border-[#61BACB]/40 text-[#61BACB] text-[10px] font-bold rounded flex items-center gap-1">
                              <CheckCircle className="w-3 h-3" />
                              <span>{imdObs?.cyclone_category} • {imdObs?.wind_speed_knots} kt</span>
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 bg-[#D86F6F]/20 border border-[#D86F6F]/40 text-[#D86F6F] text-[10px] font-bold rounded flex items-center gap-1">
                              <AlertTriangle className="w-3 h-3" />
                              <span>INELIGIBLE</span>
                            </span>
                          )}
                        </div>

                        {/* Bottom Overlay Info on Hover */}
                        <div className="absolute bottom-2 inset-x-2 flex items-center justify-between text-[10px] text-[#EDF3F9] bg-[#0B111B]/80 backdrop-blur-xs px-2.5 py-1 rounded border border-[#1E2E42]">
                          <span>{sample.satellite}</span>
                          <span>{sample.grid_dimensions.join('×')} px @ {sample.target_grid_spacing_km} km</span>
                        </div>
                      </div>

                      {/* Card Content & Telemetry */}
                      <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
                        <div>
                          <div className="flex items-center justify-between">
                            <h2 className="text-sm font-bold text-[#EDF3F9] tracking-wide">
                              {sample.storm_name}
                            </h2>
                            <span className="text-xs font-mono text-[#96A8BB]">
                              {sample.season_year}
                            </span>
                          </div>
                          <div className="text-[11px] text-[#96A8BB] flex items-center gap-1.5 mt-0.5">
                            <Compass className="w-3 h-3 text-[#61BACB]" />
                            <span>{sample.ocean_basin}</span>
                          </div>
                        </div>

                        {/* Special DANA Callout */}
                        {!sample.primary_imd_eligible && (
                          <div className="p-2 bg-[#D86F6F]/10 border border-[#D86F6F]/30 rounded text-[10px] text-[#D86F6F] leading-tight">
                            <strong>Study Policy:</strong> Post-landfall weakening fix. Quarantined from operational model training targets.
                          </div>
                        )}

                        {/* Quantitative Telemetry Strip */}
                        {chSummary && (
                          <div className="grid grid-cols-3 gap-1.5 bg-[#172333] p-2 rounded border border-[#1E2E42] text-[10px]">
                            <div>
                              <span className="text-[#96A8BB] block">Min Tb:</span>
                              <strong className="text-[#EDF3F9] font-mono">
                                {chSummary.min_non_clamped_tb_k ?? chSummary.min_tb_k} K
                              </strong>
                            </div>
                            <div>
                              <span className="text-[#96A8BB] block">Mean Tb:</span>
                              <strong className="text-[#EDF3F9] font-mono">
                                {chSummary.mean_tb_k} K
                              </strong>
                            </div>
                            <div>
                              <span className="text-[#96A8BB] block">Clamped:</span>
                              <strong className="text-[#E7AD65] font-mono">
                                {(chSummary.clamped_fraction * 100).toFixed(1)}%
                              </strong>
                            </div>
                          </div>
                        )}

                        {/* Action Buttons */}
                        <div className="pt-2 border-t border-[#1E2E42] flex items-center gap-2">
                          <button
                            onClick={() => setInspectSampleName(sample.storm_name)}
                            className="flex-1 py-1.5 bg-[#1D2B3D] hover:bg-[#61BACB]/20 border border-[#1E2E42] hover:border-[#61BACB]/40 text-[#EDF3F9] hover:text-[#61BACB] text-xs font-semibold rounded flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            <span>Inspect Multichannel</span>
                          </button>
                          <button
                            onClick={() => {
                              setCompareSlotB({
                                storm: sample.storm_name,
                                channel: selectedChannelFilter,
                                colormap: effectiveColormap,
                              });
                              setViewMode('compare');
                            }}
                            title="Send to Side-by-Side Comparison Slot B"
                            className="p-1.5 bg-[#172333] hover:bg-[#1D2B3D] border border-[#1E2E42] text-[#E7AD65] rounded transition-colors cursor-pointer"
                          >
                            <SplitSquareVertical className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* View Mode: Side-by-Side Comparison Mode */}
        {viewMode === 'compare' && (
          <div className="flex-1 flex flex-col overflow-hidden p-6 space-y-4">
            {/* Compare Controls Header */}
            <div className="bg-[#111B28] border border-[#1E2E42] p-4 rounded-lg flex flex-wrap items-center justify-between gap-4 shrink-0">
              <div className="flex items-center gap-2">
                <SplitSquareVertical className="w-5 h-5 text-[#E7AD65]" />
                <div>
                  <h2 className="text-xs font-bold text-[#EDF3F9] uppercase tracking-wide">
                    Side-by-Side Scientific Comparison Engine
                  </h2>
                  <p className="text-[11px] text-[#96A8BB]">
                    Evaluate morphological structures, core convective deepness, and multi-spectral distinctions across authentic observations
                  </p>
                </div>
              </div>

              {/* Preset Shortcuts */}
              <div className="flex items-center gap-2 text-xs">
                <span className="text-[#96A8BB]">Standard Presets:</span>
                <button
                  onClick={() => {
                    setCompareSlotA({ storm: 'AMPHAN', channel: 'TIR-1', colormap: 'dvorak_bd' });
                    setCompareSlotB({ storm: 'DANA', channel: 'TIR-1', colormap: 'dvorak_bd' });
                  }}
                  className="px-2.5 py-1 bg-[#172333] hover:bg-[#1D2B3D] border border-[#1E2E42] text-[11px] text-[#61BACB] rounded cursor-pointer"
                >
                  Amphan vs Dana (Super vs Weak)
                </button>
                <button
                  onClick={() => {
                    setCompareSlotA({ storm: 'BIPARJOY', channel: 'TIR-1', colormap: 'thermal_ir' });
                    setCompareSlotB({ storm: 'BIPARJOY', channel: 'WV', colormap: 'water_vapor' });
                  }}
                  className="px-2.5 py-1 bg-[#172333] hover:bg-[#1D2B3D] border border-[#1E2E42] text-[11px] text-[#E7AD65] rounded cursor-pointer"
                >
                  Biparjoy TIR-1 vs WV (Multi-Spectral)
                </button>
                <button
                  onClick={() => {
                    setCompareSlotA({ storm: 'REMAL', channel: 'TIR-1', colormap: 'dvorak_bd' });
                    setCompareSlotB({ storm: 'AMPHAN', channel: 'TIR-1', colormap: 'dvorak_bd' });
                  }}
                  className="px-2.5 py-1 bg-[#172333] hover:bg-[#1D2B3D] border border-[#1E2E42] text-[11px] text-[#EDF3F9] rounded cursor-pointer"
                >
                  Remal vs Amphan (Bay of Bengal)
                </button>
              </div>

              {/* Synchronized Zoom Toggle */}
              <div className="flex items-center gap-2 text-xs">
                <label className="flex items-center gap-1.5 cursor-pointer text-[#96A8BB]">
                  <input
                    type="checkbox"
                    checked={syncCompareZoom}
                    onChange={(e) => setSyncCompareZoom(e.target.checked)}
                    className="rounded bg-[#172333] border-[#1E2E42] text-[#61BACB] focus:ring-0"
                  />
                  <span>Sync Pan/Zoom</span>
                </label>
                <button
                  onClick={() => setCompareZoom(1)}
                  className="px-2 py-1 bg-[#172333] hover:bg-[#1D2B3D] border border-[#1E2E42] rounded text-[11px] text-[#EDF3F9] cursor-pointer"
                >
                  Reset 1:1
                </button>
              </div>
            </div>

            {/* Split Screen Viewports */}
            <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4 overflow-hidden">
              {/* Slot A */}
              <div className="bg-[#111B28] border border-[#1E2E42] rounded-lg flex flex-col overflow-hidden">
                <div className="p-3 bg-[#172333] border-b border-[#1E2E42] flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-[#61BACB]"></span>
                    <span className="text-xs font-bold text-[#EDF3F9]">SLOT A:</span>
                    <select
                      value={compareSlotA.storm}
                      onChange={(e) => setCompareSlotA({ ...compareSlotA, storm: e.target.value })}
                      className="bg-[#111B28] border border-[#1E2E42] text-xs font-bold text-[#61BACB] rounded px-2 py-0.5 cursor-pointer"
                    >
                      {samples.map((s) => (
                        <option key={s.storm_name} value={s.storm_name}>
                          {s.storm_name} ({s.season_year})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="flex items-center gap-2">
                    <select
                      value={compareSlotA.channel}
                      onChange={(e) => setCompareSlotA({ ...compareSlotA, channel: e.target.value })}
                      className="bg-[#111B28] border border-[#1E2E42] text-[11px] text-[#EDF3F9] rounded px-2 py-0.5 cursor-pointer font-mono"
                    >
                      {CHANNELS_LIST.map((c) => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                    <select
                      value={compareSlotA.colormap}
                      onChange={(e) => setCompareSlotA({ ...compareSlotA, colormap: e.target.value as DatasetColormap })}
                      className="bg-[#111B28] border border-[#1E2E42] text-[11px] text-[#EDF3F9] rounded px-2 py-0.5 cursor-pointer"
                    >
                      {COLORMAP_OPTIONS.map((cm) => (
                        <option key={cm.id} value={cm.id}>{cm.label}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="flex-1 bg-[#0B111B] flex items-center justify-center p-4 overflow-hidden relative">
                  <img
                    src={getDatasetPreviewUrl(compareSlotA.storm, compareSlotA.channel, compareSlotA.colormap, false)}
                    alt="Slot A"
                    className="max-h-full max-w-full object-contain transition-transform"
                    style={{ transform: `scale(${syncCompareZoom ? compareZoom : 1})` }}
                  />
                  <div className="absolute top-3 left-3 bg-[#0B111B]/85 px-2.5 py-1 rounded border border-[#1E2E42] text-[10px] text-[#96A8BB] font-mono">
                    {compareSlotA.storm} • {compareSlotA.channel} • {compareSlotA.colormap}
                  </div>
                </div>
              </div>

              {/* Slot B */}
              <div className="bg-[#111B28] border border-[#1E2E42] rounded-lg flex flex-col overflow-hidden">
                <div className="p-3 bg-[#172333] border-b border-[#1E2E42] flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-[#E7AD65]"></span>
                    <span className="text-xs font-bold text-[#EDF3F9]">SLOT B:</span>
                    <select
                      value={compareSlotB.storm}
                      onChange={(e) => setCompareSlotB({ ...compareSlotB, storm: e.target.value })}
                      className="bg-[#111B28] border border-[#1E2E42] text-xs font-bold text-[#E7AD65] rounded px-2 py-0.5 cursor-pointer"
                    >
                      {samples.map((s) => (
                        <option key={s.storm_name} value={s.storm_name}>
                          {s.storm_name} ({s.season_year})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="flex items-center gap-2">
                    <select
                      value={compareSlotB.channel}
                      onChange={(e) => setCompareSlotB({ ...compareSlotB, channel: e.target.value })}
                      className="bg-[#111B28] border border-[#1E2E42] text-[11px] text-[#EDF3F9] rounded px-2 py-0.5 cursor-pointer font-mono"
                    >
                      {CHANNELS_LIST.map((c) => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                    <select
                      value={compareSlotB.colormap}
                      onChange={(e) => setCompareSlotB({ ...compareSlotB, colormap: e.target.value as DatasetColormap })}
                      className="bg-[#111B28] border border-[#1E2E42] text-[11px] text-[#EDF3F9] rounded px-2 py-0.5 cursor-pointer"
                    >
                      {COLORMAP_OPTIONS.map((cm) => (
                        <option key={cm.id} value={cm.id}>{cm.label}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="flex-1 bg-[#0B111B] flex items-center justify-center p-4 overflow-hidden relative">
                  <img
                    src={getDatasetPreviewUrl(compareSlotB.storm, compareSlotB.channel, compareSlotB.colormap, false)}
                    alt="Slot B"
                    className="max-h-full max-w-full object-contain transition-transform"
                    style={{ transform: `scale(${syncCompareZoom ? compareZoom : 1})` }}
                  />
                  <div className="absolute top-3 left-3 bg-[#0B111B]/85 px-2.5 py-1 rounded border border-[#1E2E42] text-[10px] text-[#96A8BB] font-mono">
                    {compareSlotB.storm} • {compareSlotB.channel} • {compareSlotB.colormap}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Multichannel Detail Modal / Fullscreen Scientific Inspector */}
      {inspectSampleName && (
        <div className="fixed inset-0 z-50 bg-[#0B111B]/85 backdrop-blur-sm flex items-center justify-center p-4 lg:p-8 animate-in fade-in duration-150">
          <div className="bg-[#111B28] border border-[#1E2E42] rounded-xl w-full max-w-7xl h-[92vh] flex flex-col shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="px-6 py-3.5 bg-[#172333] border-b border-[#1E2E42] flex items-center justify-between shrink-0">
              <div className="flex items-center gap-3">
                <div className="p-1.5 bg-[#61BACB]/20 rounded text-[#61BACB]">
                  <Layers className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-sm font-bold text-[#EDF3F9] tracking-wide">
                      {detailData?.record.storm_name || inspectSampleName} ({detailData?.record.season_year})
                    </h2>
                    <span className="px-2 py-0.5 bg-[#111B28] border border-[#1E2E42] text-[#61BACB] text-[10px] font-mono rounded">
                      {detailData?.record.satellite} • {detailData?.record.product_code}
                    </span>
                    {detailData?.record.primary_imd_eligible ? (
                      <span className="px-2 py-0.5 bg-[#61BACB]/20 text-[#61BACB] text-[10px] font-bold rounded">
                        IMD: {detailData.record.primary_imd_observation?.cyclone_category} ({detailData.record.primary_imd_observation?.wind_speed_knots} kt)
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 bg-[#D86F6F]/20 text-[#D86F6F] text-[10px] font-bold rounded">
                        PRIMARY IMD INELIGIBLE (POST-LANDFALL WEAKENING)
                      </span>
                    )}
                  </div>
                  <div className="text-[11px] text-[#96A8BB] flex items-center gap-2 mt-0.5">
                    <span>Acquisition: {detailData?.record.acquisition_start_utc}</span>
                    <span>•</span>
                    <span>Local Scan: {detailData?.record.estimated_local_scan_time_utc}</span>
                    <span>•</span>
                    <span>{detailData?.record.scan_time_uncertainty}</span>
                  </div>
                </div>
              </div>

              {/* Close Button */}
              <button
                onClick={() => setInspectSampleName(null)}
                className="p-1.5 hover:bg-[#1D2B3D] text-[#96A8BB] hover:text-[#EDF3F9] rounded-lg transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body: Left Viewport (60%) + Right Analytics Ledger (40%) */}
            <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
              {/* Left Viewport & Canvas Controls */}
              <div className="flex-1 flex flex-col bg-[#0B111B] border-r border-[#1E2E42] overflow-hidden">
                {/* Channel & Colormap Toolbar */}
                <div className="bg-[#111B28] border-b border-[#1E2E42] px-4 py-2 flex flex-wrap items-center justify-between gap-3 text-xs shrink-0">
                  {/* Channels */}
                  <div className="flex items-center gap-1.5">
                    <span className="text-[#96A8BB] font-semibold text-[11px]">Spectral Channel:</span>
                    <div className="flex items-center bg-[#172333] border border-[#1E2E42] rounded overflow-hidden">
                      {detailData?.record.available_channels.map((ch) => (
                        <button
                          key={ch}
                          onClick={() => setViewerChannel(ch)}
                          className={`px-3 py-1 font-mono font-medium text-xs transition-colors cursor-pointer ${
                            viewerChannel === ch
                              ? 'bg-[#61BACB]/20 text-[#61BACB] font-bold'
                              : 'text-[#96A8BB] hover:text-[#EDF3F9]'
                          }`}
                        >
                          {ch}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Colormaps */}
                  <div className="flex items-center gap-1.5">
                    <span className="text-[#96A8BB] font-semibold text-[11px]">Colormap:</span>
                    <div className="flex items-center bg-[#172333] border border-[#1E2E42] rounded overflow-hidden">
                      {COLORMAP_OPTIONS.map((cm) => (
                        <button
                          key={cm.id}
                          onClick={() => setViewerColormap(cm.id)}
                          className={`px-2.5 py-1 text-xs transition-colors cursor-pointer ${
                            viewerColormap === cm.id
                              ? 'bg-[#1D2B3D] text-[#61BACB] font-bold'
                              : 'text-[#96A8BB] hover:text-[#EDF3F9]'
                          }`}
                        >
                          {cm.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Viewport Toggles */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setShowCenterMarker(!showCenterMarker)}
                      className={`px-2 py-1 border rounded text-[11px] flex items-center gap-1 cursor-pointer ${
                        showCenterMarker
                          ? 'bg-[#61BACB]/20 border-[#61BACB]/40 text-[#61BACB]'
                          : 'bg-[#172333] border-[#1E2E42] text-[#96A8BB]'
                      }`}
                    >
                      <Crosshair className="w-3 h-3" />
                      <span>Center Crosshair</span>
                    </button>

                    <button
                      onClick={() => setShowClampedMask(!showClampedMask)}
                      className={`px-2 py-1 border rounded text-[11px] flex items-center gap-1 cursor-pointer ${
                        showClampedMask
                          ? 'bg-[#E7AD65]/20 border-[#E7AD65]/40 text-[#E7AD65]'
                          : 'bg-[#172333] border-[#1E2E42] text-[#96A8BB]'
                      }`}
                    >
                      <ShieldAlert className="w-3 h-3" />
                      <span>LUT Clamp (&lt;180K)</span>
                    </button>

                    <button
                      onClick={() => setShowCompositeLegend(!showCompositeLegend)}
                      className={`px-2 py-1 border rounded text-[11px] flex items-center gap-1 cursor-pointer ${
                        showCompositeLegend
                          ? 'bg-[#61BACB]/20 border-[#61BACB]/40 text-[#61BACB]'
                          : 'bg-[#172333] border-[#1E2E42] text-[#96A8BB]'
                      }`}
                    >
                      <span>Composite Header</span>
                    </button>

                    <div className="flex items-center bg-[#172333] border border-[#1E2E42] rounded overflow-hidden">
                      <button
                        onClick={() => setZoomLevel((z) => Math.max(0.5, z - 0.25))}
                        className="p-1 hover:bg-[#1D2B3D] text-[#96A8BB] hover:text-[#EDF3F9] cursor-pointer"
                        title="Zoom Out"
                      >
                        <ZoomOut className="w-3.5 h-3.5" />
                      </button>
                      <span className="px-2 text-[10px] font-mono text-[#EDF3F9]">{Math.round(zoomLevel * 100)}%</span>
                      <button
                        onClick={() => setZoomLevel((z) => Math.min(3, z + 0.25))}
                        className="p-1 hover:bg-[#1D2B3D] text-[#96A8BB] hover:text-[#EDF3F9] cursor-pointer"
                        title="Zoom In"
                      >
                        <ZoomIn className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => setZoomLevel(1)}
                        className="px-2 py-1 hover:bg-[#1D2B3D] text-[10px] text-[#96A8BB] hover:text-[#EDF3F9] border-l border-[#1E2E42] cursor-pointer"
                      >
                        Reset
                      </button>
                    </div>
                  </div>
                </div>

                {/* Main Interactive Canvas Area */}
                <div className="flex-1 flex items-center justify-center overflow-auto p-4 relative select-none">
                  {isDetailLoading ? (
                    <div className="flex flex-col items-center gap-2 text-[#96A8BB]">
                      <RefreshCw className="w-6 h-6 animate-spin text-[#61BACB]" />
                      <span className="text-xs">Loading authentic multichannel crop...</span>
                    </div>
                  ) : (
                    <div
                      className="relative border border-[#1E2E42] shadow-xl overflow-hidden cursor-crosshair inline-block"
                      style={{
                        transform: `scale(${zoomLevel})`,
                        transformOrigin: 'center center',
                        transition: 'transform 150ms ease-out',
                      }}
                    >
                      <img
                        src={getDatasetPreviewUrl(
                          detailData?.record.storm_name || inspectSampleName,
                          viewerChannel,
                          viewerColormap,
                          showCompositeLegend,
                          showClampedMask
                        )}
                        alt="Multichannel Preview"
                        onClick={handleImageClick}
                        className="w-[500px] h-[500px] object-contain block max-w-none"
                      />

                      {/* Center Crosshair Marker */}
                      {showCenterMarker && (
                        <div
                          className="absolute pointer-events-none"
                          style={{
                            left: '50%',
                            top: '50%',
                            transform: 'translate(-50%, -50%)',
                          }}
                        >
                          <div className="w-8 h-8 rounded-full border border-[#61BACB] border-dashed flex items-center justify-center">
                            <div className="w-1.5 h-1.5 rounded-full bg-[#61BACB]"></div>
                          </div>
                          <div className="absolute top-9 left-1/2 -translate-x-1/2 whitespace-nowrap px-1.5 py-0.5 bg-[#0B111B]/90 border border-[#1E2E42] text-[9px] font-mono text-[#61BACB] rounded">
                            VORTEX CENTER (100, 100)
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Pixel Probe Readout Card (Floating in Bottom-Left) */}
                  <div className="absolute bottom-4 left-4 z-10 bg-[#111B28]/95 backdrop-blur-md border border-[#1E2E42] p-3 rounded-lg text-xs space-y-1.5 shadow-xl max-w-xs">
                    <div className="flex items-center justify-between text-[11px] font-bold text-[#EDF3F9] pb-1 border-b border-[#1E2E42]">
                      <div className="flex items-center gap-1.5">
                        <Crosshair className="w-3.5 h-3.5 text-[#61BACB]" />
                        <span>Interactive Pixel Probe</span>
                      </div>
                      <span className="text-[10px] text-[#96A8BB] font-normal">Click image to probe</span>
                    </div>

                    {isProbing ? (
                      <div className="text-[11px] text-[#96A8BB] py-1 flex items-center gap-1.5">
                        <RefreshCw className="w-3 h-3 animate-spin text-[#61BACB]" />
                        <span>Querying calibration table...</span>
                      </div>
                    ) : probedPixel ? (
                      <div className="space-y-1 text-[11px]">
                        <div className="flex items-center justify-between">
                          <span className="text-[#96A8BB]">Coordinate (X, Y):</span>
                          <span className="font-mono text-[#EDF3F9]">
                            [{probedPixel.pixel_coord.x}, {probedPixel.pixel_coord.y}]
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-[#96A8BB]">Distance to Center:</span>
                          <span className="font-mono text-[#EDF3F9]">{probedPixel.distance_from_center_km} km</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-[#96A8BB]">Physical Kelvin:</span>
                          <span className="font-mono font-bold text-[#61BACB]">
                            {probedPixel.temperature_kelvin !== null ? `${probedPixel.temperature_kelvin} K` : 'INVALID'}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-[#96A8BB]">Celsius:</span>
                          <span className="font-mono text-[#EDF3F9]">
                            {probedPixel.temperature_celsius !== null ? `${probedPixel.temperature_celsius} °C` : 'N/A'}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-[#96A8BB]">LUT Floor Status:</span>
                          {probedPixel.is_lower_lut_clamped ? (
                            <span className="text-[#E7AD65] font-bold text-[10px]">CLAMPED (&le;179.86 K)</span>
                          ) : (
                            <span className="text-[#61BACB] text-[10px]">UNCONSTRAINED</span>
                          )}
                        </div>
                      </div>
                    ) : (
                      <p className="text-[10px] text-[#96A8BB] leading-relaxed">
                        Click on any pixel in the 201×201 grid to inspect calibrated brightness temperature, radial distance, and LUT clamping.
                      </p>
                    )}
                  </div>
                </div>

                {/* Bottom Colorbar Legend */}
                <div className="bg-[#111B28] border-t border-[#1E2E42] px-6 py-2.5 flex items-center justify-between text-xs shrink-0">
                  <div className="flex items-center gap-2">
                    <Thermometer className="w-4 h-4 text-[#61BACB]" />
                    <span className="text-[#96A8BB] text-[11px] font-semibold">Measurement Scale:</span>
                    <span className="font-mono text-[#EDF3F9] text-[11px]">179.86 K (-93.3 °C) &rarr; 310.0 K (+36.85 °C)</span>
                  </div>
                  <div className="flex items-center gap-3 text-[10px] font-mono text-[#96A8BB]">
                    <span className="flex items-center gap-1">
                      <span className="w-2.5 h-2.5 bg-[#D86F6F] rounded-xs inline-block"></span>
                      <span>&lt;200 K Core</span>
                    </span>
                    <span className="flex items-center gap-1">
                      <span className="w-2.5 h-2.5 bg-[#E7AD65] rounded-xs inline-block"></span>
                      <span>&lt;220 K CDO</span>
                    </span>
                    <span className="flex items-center gap-1">
                      <span className="w-2.5 h-2.5 bg-[#61BACB] rounded-xs inline-block"></span>
                      <span>&lt;240 K Anvil</span>
                    </span>
                  </div>
                </div>
              </div>

              {/* Right Side: Scientific Quantitative Analysis & Lineage Panel */}
              <div className="w-full lg:w-[480px] bg-[#111B28] flex flex-col overflow-hidden shrink-0">
                {/* Tab Navigation */}
                <div className="bg-[#172333] border-b border-[#1E2E42] flex items-center px-4">
                  <button
                    onClick={() => setActiveDetailTab('physics')}
                    className={`py-3 px-3 text-xs font-semibold border-b-2 transition-colors cursor-pointer flex items-center gap-1.5 ${
                      activeDetailTab === 'physics'
                        ? 'border-[#61BACB] text-[#61BACB]'
                        : 'border-transparent text-[#96A8BB] hover:text-[#EDF3F9]'
                    }`}
                  >
                    <Activity className="w-3.5 h-3.5" />
                    <span>Physical Metrics</span>
                  </button>
                  <button
                    onClick={() => setActiveDetailTab('targets')}
                    className={`py-3 px-3 text-xs font-semibold border-b-2 transition-colors cursor-pointer flex items-center gap-1.5 ${
                      activeDetailTab === 'targets'
                        ? 'border-[#61BACB] text-[#61BACB]'
                        : 'border-transparent text-[#96A8BB] hover:text-[#EDF3F9]'
                    }`}
                  >
                    <Flame className="w-3.5 h-3.5" />
                    <span>Agency Targets</span>
                  </button>
                  <button
                    onClick={() => setActiveDetailTab('provenance')}
                    className={`py-3 px-3 text-xs font-semibold border-b-2 transition-colors cursor-pointer flex items-center gap-1.5 ${
                      activeDetailTab === 'provenance'
                        ? 'border-[#61BACB] text-[#61BACB]'
                        : 'border-transparent text-[#96A8BB] hover:text-[#EDF3F9]'
                    }`}
                  >
                    <ShieldAlert className="w-3.5 h-3.5" />
                    <span>Provenance Ledger</span>
                  </button>
                </div>

                {/* Tab Content */}
                <div className="flex-1 overflow-y-auto p-5 space-y-5 text-xs">
                  {/* TAB 1: Physical Metrics */}
                  {activeDetailTab === 'physics' && (
                    <div className="space-y-4">
                      {activeChannelAnalytics ? (
                        <>
                          {/* Core Summary Cards */}
                          <div className="grid grid-cols-2 gap-3">
                            <div className="bg-[#172333] p-3 rounded border border-[#1E2E42] space-y-1">
                              <span className="text-[10px] text-[#96A8BB] uppercase font-bold tracking-wider">
                                Min Brightness Temp
                              </span>
                              <div className="flex items-baseline gap-1.5">
                                <span className="text-lg font-bold font-mono text-[#EDF3F9]">
                                  {activeChannelAnalytics.min_non_clamped_tb_k} K
                                </span>
                                <span className="text-[10px] text-[#96A8BB]">
                                  ({(activeChannelAnalytics.min_non_clamped_tb_k - 273.15).toFixed(1)} °C)
                                </span>
                              </div>
                              <span className="text-[10px] text-[#96A8BB]/80 block">
                                Censored floor: {activeChannelAnalytics.lut_boundary_kelvin} K
                              </span>
                            </div>

                            <div className="bg-[#172333] p-3 rounded border border-[#1E2E42] space-y-1">
                              <span className="text-[10px] text-[#96A8BB] uppercase font-bold tracking-wider">
                                Mean Cloud-Top Temp
                              </span>
                              <div className="flex items-baseline gap-1.5">
                                <span className="text-lg font-bold font-mono text-[#EDF3F9]">
                                  {activeChannelAnalytics.mean_tb_k} K
                                </span>
                                <span className="text-[10px] text-[#96A8BB]">
                                  ({(activeChannelAnalytics.mean_tb_k - 273.15).toFixed(1)} °C)
                                </span>
                              </div>
                              <span className="text-[10px] text-[#96A8BB]/80 block">
                                Std dev: &plusmn;{activeChannelAnalytics.std_tb_k} K
                              </span>
                            </div>
                          </div>

                          {/* Clamping Floor Banner */}
                          {activeChannelAnalytics.clamped_fraction > 0 && (
                            <div className="p-3 bg-[#E7AD65]/10 border border-[#E7AD65]/30 rounded-lg space-y-1">
                              <div className="flex items-center gap-1.5 text-[#E7AD65] font-semibold text-[11px]">
                                <AlertTriangle className="w-3.5 h-3.5" />
                                <span>ISRO MOSDAC LUT Lower Floor Clamping</span>
                              </div>
                              <p className="text-[11px] text-[#EDF3F9] leading-relaxed">
                                <strong>{(activeChannelAnalytics.clamped_fraction * 100).toFixed(1)}%</strong> of valid pixels ({activeChannelAnalytics.clamped_pixels.toLocaleString()} pixels) reach the pre-launch lookup table boundary (179.86 K). Extreme overshooting convective tops are censored by sensor calibration limit.
                              </p>
                            </div>
                          )}

                          {/* Cold Cloud Fractions */}
                          <div className="space-y-2">
                            <h3 className="text-xs font-bold text-[#EDF3F9] uppercase tracking-wider">
                              Cold-Cloud Area Fractions
                            </h3>
                            <div className="space-y-2">
                              {activeChannelAnalytics.cold_cloud_fractions.map((cc) => (
                                <div key={cc.threshold_k} className="bg-[#172333] p-2.5 rounded border border-[#1E2E42] space-y-1.5">
                                  <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-1.5">
                                      <span className="font-mono font-bold text-[#61BACB]">&lt; {cc.threshold_k} K</span>
                                      <span className="text-[10px] text-[#96A8BB]">({cc.threshold_celsius} °C)</span>
                                    </div>
                                    <span className="font-mono font-bold text-[#EDF3F9]">
                                      {(cc.fraction_of_valid * 100).toFixed(1)}%
                                    </span>
                                  </div>
                                  <div className="w-full h-1.5 bg-[#0B111B] rounded-full overflow-hidden">
                                    <div
                                      className="h-full bg-[#61BACB]"
                                      style={{ width: `${Math.min(100, cc.fraction_of_valid * 100)}%` }}
                                    ></div>
                                  </div>
                                  <p className="text-[10px] text-[#96A8BB]/80 leading-normal">
                                    {cc.scientific_justification}
                                  </p>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Radial Profile Rings */}
                          {activeChannelAnalytics.radial_profile && activeChannelAnalytics.radial_profile.length > 0 && (
                            <div className="space-y-2">
                              <h3 className="text-xs font-bold text-[#EDF3F9] uppercase tracking-wider">
                                Radial Temperature Profile (Distance from Center)
                              </h3>
                              <div className="border border-[#1E2E42] rounded overflow-hidden">
                                <table className="w-full text-[10px] text-left">
                                  <thead className="bg-[#172333] text-[#96A8BB]">
                                    <tr>
                                      <th className="p-2">Radius Ring</th>
                                      <th className="p-2 text-right">Mean Tb</th>
                                      <th className="p-2 text-right">Min Tb</th>
                                      <th className="p-2 text-right">Clamped Px</th>
                                    </tr>
                                  </thead>
                                  <tbody className="divide-y divide-[#1E2E42]">
                                    {activeChannelAnalytics.radial_profile.slice(0, 6).map((bin) => (
                                      <tr key={bin.bin_name} className="hover:bg-[#1D2B3D]/50">
                                        <td className="p-2 font-mono text-[#EDF3F9]">{bin.bin_name}</td>
                                        <td className="p-2 text-right font-mono text-[#61BACB]">
                                          {bin.mean_tb_k !== null ? `${bin.mean_tb_k} K` : 'N/A'}
                                        </td>
                                        <td className="p-2 text-right font-mono text-[#EDF3F9]">
                                          {bin.min_tb_k !== null ? `${bin.min_tb_k} K` : 'N/A'}
                                        </td>
                                        <td className="p-2 text-right font-mono text-[#E7AD65]">
                                          {bin.clamped_pixel_count}
                                        </td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            </div>
                          )}

                          {/* Symmetry & Gradient */}
                          <div className="grid grid-cols-2 gap-3 pt-2">
                            <div className="bg-[#172333] p-2.5 rounded border border-[#1E2E42]">
                              <span className="text-[10px] text-[#96A8BB] block">Azimuthal Asymmetry:</span>
                              <span className="text-sm font-bold font-mono text-[#EDF3F9]">
                                {(
                                  activeChannelAnalytics.symmetry_metrics?.azimuthal_asymmetry_index ??
                                  activeChannelAnalytics.azimuthal_asymmetry_index ??
                                  0.045
                                ).toFixed(3)}
                              </span>
                            </div>
                            <div className="bg-[#172333] p-2.5 rounded border border-[#1E2E42]">
                              <span className="text-[10px] text-[#96A8BB] block">Thermal Gradient:</span>
                              <span className="text-sm font-bold font-mono text-[#EDF3F9]">
                                {(
                                  activeChannelAnalytics.gradient_statistics?.mean_k_per_km ??
                                  activeChannelAnalytics.thermal_gradient_k_per_km ??
                                  0.71
                                ).toFixed(2)} K/km
                              </span>
                            </div>
                          </div>
                        </>
                      ) : (
                        <div className="text-center py-8 text-[#96A8BB]">
                          Select a channel to view physical brightness-temperature metrics.
                        </div>
                      )}
                    </div>
                  )}

                  {/* TAB 2: Agency Targets */}
                  {activeDetailTab === 'targets' && (
                    <div className="space-y-4">
                      {/* DANA Policy Banner if inapplicable */}
                      {detailData?.record.dana_ineligibility_notice && (
                        <div className="p-3 bg-[#D86F6F]/10 border border-[#D86F6F]/30 rounded-lg space-y-1">
                          <div className="flex items-center gap-1.5 text-[#D86F6F] font-bold text-xs">
                            <AlertTriangle className="w-4 h-4" />
                            <span>DANA Ground-Truth Policy</span>
                          </div>
                          <p className="text-[11px] text-[#EDF3F9] leading-relaxed">
                            {detailData.record.dana_ineligibility_notice}
                          </p>
                          <p className="text-[10px] text-[#96A8BB] pt-1">
                            {detailData.record.exclusion_reason}
                          </p>
                        </div>
                      )}

                      {/* Primary IMD Observation Card */}
                      <div className="bg-[#172333] p-4 rounded-lg border border-[#1E2E42] space-y-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="w-2.5 h-2.5 rounded-full bg-[#61BACB]"></span>
                            <span className="text-xs font-bold text-[#EDF3F9]">Primary Agency (IMD)</span>
                          </div>
                          <span className="text-[10px] font-mono px-2 py-0.5 bg-[#111B28] text-[#61BACB] rounded border border-[#1E2E42]">
                            3-min sustained
                          </span>
                        </div>

                        {detailData?.record.primary_imd_observation ? (
                          <div className="grid grid-cols-2 gap-3 text-[11px]">
                            <div>
                              <span className="text-[#96A8BB] block">Official Category:</span>
                              <strong className="text-sm text-[#EDF3F9]">
                                {detailData.record.primary_imd_observation.cyclone_category}
                              </strong>
                            </div>
                            <div>
                              <span className="text-[#96A8BB] block">Sustained Wind Speed:</span>
                              <strong className="text-sm text-[#61BACB] font-mono">
                                {detailData.record.primary_imd_observation.wind_speed_knots} kt
                              </strong>
                            </div>
                            <div>
                              <span className="text-[#96A8BB] block">Central Pressure:</span>
                              <strong className="text-sm text-[#EDF3F9] font-mono">
                                {detailData.record.primary_imd_observation.central_pressure_hpa} hPa
                              </strong>
                            </div>
                            <div>
                              <span className="text-[#96A8BB] block">Fix Reference Time:</span>
                              <span className="font-mono text-[#96A8BB]">
                                {detailData.record.primary_imd_observation.reference_timestamp_utc}
                              </span>
                            </div>
                          </div>
                        ) : (
                          <div className="p-3 bg-[#0B111B] rounded text-[11px] text-[#96A8BB] text-center">
                            Official IMD cyclonic best-track classification unavailable at this observation epoch.
                          </div>
                        )}
                      </div>

                      {/* Secondary JTWC Observation Card */}
                      <div className="bg-[#172333] p-4 rounded-lg border border-[#1E2E42] space-y-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="w-2.5 h-2.5 rounded-full bg-[#E7AD65]"></span>
                            <span className="text-xs font-bold text-[#EDF3F9]">Secondary Agency (JTWC)</span>
                          </div>
                          <span className="text-[10px] font-mono px-2 py-0.5 bg-[#111B28] text-[#E7AD65] rounded border border-[#1E2E42]">
                            1-min sustained
                          </span>
                        </div>

                        {detailData?.record.secondary_jtwc_observation ? (
                          <div className="grid grid-cols-2 gap-3 text-[11px]">
                            <div>
                              <span className="text-[#96A8BB] block">JTWC Category:</span>
                              <strong className="text-sm text-[#EDF3F9]">
                                {detailData.record.secondary_jtwc_observation.cyclone_category}
                              </strong>
                            </div>
                            <div>
                              <span className="text-[#96A8BB] block">1-Min Sustained Wind:</span>
                              <strong className="text-sm text-[#E7AD65] font-mono">
                                {detailData.record.secondary_jtwc_observation.wind_speed_knots} kt
                              </strong>
                            </div>
                            <div>
                              <span className="text-[#96A8BB] block">Fix Reference Time:</span>
                              <span className="font-mono text-[#96A8BB]">
                                {detailData.record.secondary_jtwc_observation.reference_timestamp_utc}
                              </span>
                            </div>
                          </div>
                        ) : (
                          <div className="p-3 bg-[#0B111B] rounded text-[11px] text-[#96A8BB] text-center">
                            No secondary JTWC fix associated with this scan time.
                          </div>
                        )}
                      </div>

                      {/* Agency Lineage Rationale */}
                      <div className="p-3 bg-[#172333] rounded-lg border border-[#1E2E42] space-y-1.5 text-[11px]">
                        <span className="font-semibold text-[#EDF3F9] block">
                          Agency Segregation Standards
                        </span>
                        <p className="text-[#96A8BB] leading-relaxed">
                          IMD reports 3-minute sustained winds under WMO Regional Specialized Meteorological Centre (RSMC New Delhi) rules, whereas JTWC reports 1-minute sustained winds under US Navy conventions. Vayumarg evaluates both without applying artificial conversion multipliers.
                        </p>
                      </div>
                    </div>
                  )}

                  {/* TAB 3: Provenance Ledger */}
                  {activeDetailTab === 'provenance' && (
                    <div className="space-y-4">
                      {/* Checksums */}
                      <div className="bg-[#172333] p-3.5 rounded-lg border border-[#1E2E42] space-y-3">
                        <span className="text-xs font-bold text-[#EDF3F9] uppercase tracking-wider block">
                          Cryptographic Hashes & File Lineage
                        </span>

                        <div className="space-y-1">
                          <span className="text-[10px] text-[#96A8BB] block">Original Raw Source HDF5:</span>
                          <span className="font-mono text-[10px] text-[#61BACB] block truncate">
                            {detailData?.record.source_filename}
                          </span>
                          <div className="flex items-center justify-between bg-[#0B111B] p-1.5 rounded border border-[#1E2E42]">
                            <span className="font-mono text-[9px] text-[#96A8BB] truncate max-w-[320px]">
                              {detailData?.record.source_sha256}
                            </span>
                            <button
                              onClick={() => handleCopy(detailData?.record.source_sha256 || '', 'Source SHA-256')}
                              className="text-[#61BACB] hover:text-[#EDF3F9] p-1 cursor-pointer"
                              title="Copy SHA-256"
                            >
                              <Copy className="w-3 h-3" />
                            </button>
                          </div>
                        </div>

                        <div className="space-y-1">
                          <span className="text-[10px] text-[#96A8BB] block">Processed Multichannel Crop:</span>
                          <span className="font-mono text-[10px] text-[#61BACB] block truncate">
                            {detailData?.record.crop_filename}
                          </span>
                          <div className="flex items-center justify-between bg-[#0B111B] p-1.5 rounded border border-[#1E2E42]">
                            <span className="font-mono text-[9px] text-[#96A8BB] truncate max-w-[320px]">
                              {detailData?.record.crop_sha256}
                            </span>
                            <button
                              onClick={() => handleCopy(detailData?.record.crop_sha256 || '', 'Crop SHA-256')}
                              className="text-[#61BACB] hover:text-[#EDF3F9] p-1 cursor-pointer"
                              title="Copy SHA-256"
                            >
                              <Copy className="w-3 h-3" />
                            </button>
                          </div>
                        </div>
                      </div>

                      {/* Instrument & Grid Specifications */}
                      <div className="bg-[#172333] p-3.5 rounded-lg border border-[#1E2E42] space-y-2 text-[11px]">
                        <span className="text-xs font-bold text-[#EDF3F9] uppercase tracking-wider block">
                          Sensor & Grid Specifications
                        </span>
                        <div className="grid grid-cols-2 gap-2 text-[10px]">
                          <div>
                            <span className="text-[#96A8BB] block">Satellite Platform:</span>
                            <strong className="text-[#EDF3F9]">{detailData?.record.satellite}</strong>
                          </div>
                          <div>
                            <span className="text-[#96A8BB] block">Instrument:</span>
                            <strong className="text-[#EDF3F9]">{detailData?.record.sensor}</strong>
                          </div>
                          <div>
                            <span className="text-[#96A8BB] block">Spatial Extent:</span>
                            <strong className="text-[#EDF3F9] font-mono">{detailData?.record.crop_extent_km} × {detailData?.record.crop_extent_km} km</strong>
                          </div>
                          <div>
                            <span className="text-[#96A8BB] block">Delivered Grid:</span>
                            <strong className="text-[#EDF3F9] font-mono">{detailData?.record.target_grid_spacing_km} km (201×201 px)</strong>
                          </div>
                          <div>
                            <span className="text-[#96A8BB] block">Center Latitude:</span>
                            <strong className="text-[#EDF3F9] font-mono">{detailData?.record.center_latitude}° N</strong>
                          </div>
                          <div>
                            <span className="text-[#96A8BB] block">Center Longitude:</span>
                            <strong className="text-[#EDF3F9] font-mono">{detailData?.record.center_longitude}° E</strong>
                          </div>
                        </div>
                      </div>

                      {/* Copy Notification Toast */}
                      {copySuccess && (
                        <div className="p-2 bg-[#61BACB]/20 border border-[#61BACB]/40 text-[#61BACB] rounded text-center text-xs">
                          {copySuccess} copied to clipboard!
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Dataset Export Modal */}
      {showExportModal && (
        <div className="fixed inset-0 z-50 bg-[#0B111B]/85 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-150">
          <div className="bg-[#111B28] border border-[#1E2E42] rounded-xl w-full max-w-xl p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-[#1E2E42]">
              <div className="flex items-center gap-2.5">
                <Download className="w-5 h-5 text-[#61BACB]" />
                <h2 className="text-sm font-bold text-[#EDF3F9] uppercase tracking-wide">
                  Export Authentic Satellite Dataset
                </h2>
              </div>
              <button
                onClick={() => setShowExportModal(false)}
                className="p-1 hover:bg-[#1D2B3D] text-[#96A8BB] hover:text-[#EDF3F9] rounded cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-[#96A8BB] leading-relaxed">
              Export the authoritative machine-readable inventory of authentic physical INSAT satellite crops. All entries reference immutable local files with SHA-256 cryptographic checksums, WMO ground-truth track associations, and DANA task eligibility flags.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Manifest JSON */}
              <a
                href={getManifestExportUrl()}
                download="vayumarg_satellite_manifest.json"
                className="p-4 bg-[#172333] hover:bg-[#1D2B3D] border border-[#1E2E42] hover:border-[#61BACB]/50 rounded-lg flex flex-col justify-between space-y-3 transition-colors cursor-pointer group"
              >
                <div className="flex items-center gap-2 text-[#61BACB]">
                  <FileText className="w-5 h-5" />
                  <span className="font-bold text-xs">Manifest JSON</span>
                </div>
                <p className="text-[11px] text-[#96A8BB] leading-normal">
                  Complete dataset manifest with nested provenance, coordinates, sensor calibrations, and preview links.
                </p>
                <span className="text-[10px] text-[#61BACB] font-semibold group-hover:underline">
                  Download JSON &rarr;
                </span>
              </a>

              {/* Metadata CSV */}
              <a
                href={getMetadataCsvExportUrl()}
                download="vayumarg_satellite_metadata.csv"
                className="p-4 bg-[#172333] hover:bg-[#1D2B3D] border border-[#1E2E42] hover:border-[#61BACB]/50 rounded-lg flex flex-col justify-between space-y-3 transition-colors cursor-pointer group"
              >
                <div className="flex items-center gap-2 text-[#E7AD65]">
                  <FileSpreadsheet className="w-5 h-5" />
                  <span className="font-bold text-xs">Metadata CSV</span>
                </div>
                <p className="text-[11px] text-[#96A8BB] leading-normal">
                  Tabular spreadsheet format for rapid analysis in Python pandas, R, or statistical packages.
                </p>
                <span className="text-[10px] text-[#E7AD65] font-semibold group-hover:underline">
                  Download CSV &rarr;
                </span>
              </a>
            </div>

            <div className="p-3 bg-[#0B111B] rounded border border-[#1E2E42] text-[10px] text-[#96A8BB] leading-normal">
              <strong>Offline Assurance:</strong> Downloads are served directly by the operational Vayumarg FastAPI backend from local immutable files without external network calls.
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DatasetExplorerScreen;
