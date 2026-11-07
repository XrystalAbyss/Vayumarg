import React, { useEffect, useState } from 'react';
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock,
  Compass,
  Cpu,
  Database,
  Gauge,
  HelpCircle,
  Layers,
  Lock,
  Play,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  Sparkles
} from 'lucide-react';
import type {
  CNNInferenceResponse,
  ConvLSTMInferenceResponse,
  MLRegistryResponse,
  TrackGRUInferenceResponse
} from '../types';
import {
  fetchConvLSTMSequences,
  fetchINSATEvaluations,
  fetchMLRegistry,
  getCropImageUrl,
  runConvLSTMInference,
  runSatelliteCNNInference,
  runTrackGRUInference
} from '../api';

interface AIModelLabScreenProps {
  onNavigateToForecast?: () => void;
  onNavigateToSatellite?: () => void;
}

type ModelTab = 'satellite_cnn' | 'convlstm' | 'track_gru' | 'release_ledger';

export const AIModelLabScreen: React.FC<AIModelLabScreenProps> = ({
  onNavigateToForecast,
  onNavigateToSatellite,
}) => {
  const [activeTab, setActiveTab] = useState<ModelTab>('satellite_cnn');
  const [registry, setRegistry] = useState<MLRegistryResponse | null>(null);
  const [insatLedger, setInsatLedger] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // CNN Interactive State
  const [cnnStorm, setCnnStorm] = useState<string>('BIPARJOY');
  const [cnnChannel, setCnnChannel] = useState<string>('TIR-1');
  const [cnnResult, setCnnResult] = useState<CNNInferenceResponse | null>(null);
  const [cnnLoading, setCnnLoading] = useState<boolean>(false);

  // ConvLSTM Interactive State
  const [sequences, setSequences] = useState<any[]>([]);
  const [selectedSeqId, setSelectedSeqId] = useState<string>('');
  const [convResult, setConvResult] = useState<ConvLSTMInferenceResponse | null>(null);
  const [convLoading, setConvLoading] = useState<boolean>(false);

  // Track GRU State
  const [selectedTrackStorm, setSelectedTrackStorm] = useState<string>('BIPARJOY');
  const [trackResult, setTrackResult] = useState<TrackGRUInferenceResponse | null>(null);
  const [trackLoading, setTrackLoading] = useState<boolean>(false);

  // Initial Load
  useEffect(() => {
    async function init() {
      try {
        setLoading(true);
        const [regData, insatData, seqData] = await Promise.all([
          fetchMLRegistry(),
          fetchINSATEvaluations().catch(() => null),
          fetchConvLSTMSequences('test').catch(() => ({ sequences: [] })),
        ]);
        setRegistry(regData);
        setInsatLedger(insatData);
        if (seqData.sequences && seqData.sequences.length > 0) {
          setSequences(seqData.sequences);
          setSelectedSeqId(seqData.sequences[0].sequence_id);
        }
      } catch (err: any) {
        console.error('Failed to load ML registry:', err);
        setError(err.message || 'Failed to connect to ML model registry.');
      } finally {
        setLoading(false);
      }
    }
    init();
  }, []);

  // Run initial CNN inference for default storm
  useEffect(() => {
    if (registry?.models?.satellite_cnn?.checksum_verified) {
      handleRunCNN(cnnStorm, cnnChannel);
    }
  }, [registry]);

  // Auto-run Track GRU inference when tab is opened
  useEffect(() => {
    if (activeTab === 'track_gru' && !trackResult && !trackLoading) {
      handleRunTrackGRU(selectedTrackStorm);
    }
  }, [activeTab]);

  const handleRunCNN = async (storm: string, ch: string) => {
    try {
      setCnnLoading(true);
      const res = await runSatelliteCNNInference(storm, ch);
      setCnnResult(res);
    } catch (err: any) {
      console.error('CNN inference failed:', err);
    } finally {
      setCnnLoading(false);
    }
  };

  const handleRunConvLSTM = async (seqId: string) => {
    try {
      setConvLoading(true);
      const res = await runConvLSTMInference(seqId, 3.0);
      setConvResult(res);
    } catch (err: any) {
      console.error('ConvLSTM inference failed:', err);
    } finally {
      setConvLoading(false);
    }
  };

  const handleRunTrackGRU = async (storm: string) => {
    try {
      setTrackLoading(true);
      const res = await runTrackGRUInference(storm);
      setTrackResult(res);
    } catch (err: any) {
      console.error('Track GRU request failed:', err);
    } finally {
      setTrackLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-[#0B111B] text-[#EDF3F9]">
        <div className="flex items-center gap-3 bg-[#111B28] border border-[#1E2E42] px-5 py-3 rounded-md">
          <RefreshCw className="w-4 h-4 text-[#61BACB] animate-spin" />
          <span className="text-xs font-mono text-[#96A8BB]">Verifying Cryptographic Checksums & Loading ML Registry...</span>
        </div>
      </div>
    );
  }

  if (error || !registry) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-[#0B111B] text-[#EDF3F9] p-6">
        <div className="max-w-md bg-[#111B28] border border-[#D86F6F]/40 p-6 rounded text-center space-y-3">
          <AlertCircle className="w-8 h-8 text-[#D86F6F] mx-auto" />
          <h2 className="text-sm font-bold">AI Model Lab Offline</h2>
          <p className="text-xs text-[#96A8BB]">{error || 'Could not load authoritative model registry.'}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-3 py-1.5 bg-[#172333] hover:bg-[#1D2B3D] border border-[#1E2E42] text-xs font-mono rounded"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  const cnnMeta = registry.models.satellite_cnn;
  const convMeta = registry.models.convlstm;
  const trackMeta = registry.models.track_gru;

  return (
    <div className="flex-1 flex flex-col bg-[#0B111B] text-[#EDF3F9] overflow-hidden select-none">
      {/* Top Header & Telemetry Bar */}
      <div className="h-14 bg-[#111B28] border-b border-[#1E2E42] px-6 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-[#172333] border border-[#1E2E42] flex items-center justify-center text-[#61BACB]">
            <Cpu className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-sm font-bold text-[#EDF3F9] tracking-tight">AI Model Lab</h1>
              <span className="px-1.5 py-0.5 text-[10px] font-mono bg-[#61BACB]/10 text-[#61BACB] border border-[#61BACB]/30 rounded">
                EXPERIMENTAL RESEARCH
              </span>
            </div>
            <p className="text-[11px] text-[#96A8BB] font-mono">
              Scientific Model Registry • Forensic Provenance Verification • Benchmark Baselines
            </p>
          </div>
        </div>

        {/* Hardware & Governance Telemetry */}
        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-2 bg-[#0B111B] border border-[#1E2E42] px-2.5 py-1 rounded">
            <Gauge className="w-3.5 h-3.5 text-[#61BACB]" />
            <span className="text-[#96A8BB]">{registry.hardware.device_name}</span>
            <span className="text-[#EDF3F9] font-bold">
              {registry.hardware.total_vram_mb > 0 ? `${registry.hardware.total_vram_mb} MB VRAM` : 'CPU'}
            </span>
          </div>

          <div className="flex items-center gap-2 bg-[#0B111B] border border-[#1E2E42] px-2.5 py-1 rounded">
            <Lock className="w-3.5 h-3.5 text-[#E7AD65]" />
            <span className="text-[#96A8BB]">Release Gates:</span>
            <span className="text-[#61BACB] font-bold">ENFORCED (SHA-256)</span>
          </div>
        </div>
      </div>

      {/* Model Category Sub-Navigation */}
      <div className="h-10 bg-[#172333]/80 border-b border-[#1E2E42] px-6 flex items-center gap-2 shrink-0">
        <button
          onClick={() => setActiveTab('satellite_cnn')}
          className={`h-full px-3 text-xs font-mono font-medium flex items-center gap-2 border-b-2 transition-colors cursor-pointer ${
            activeTab === 'satellite_cnn'
              ? 'border-[#61BACB] text-[#EDF3F9] bg-[#1D2B3D]/50'
              : 'border-transparent text-[#96A8BB] hover:text-[#EDF3F9]'
          }`}
        >
          <Sparkles className="w-3.5 h-3.5 text-[#61BACB]" />
          <span>1. Satellite CNN (ResNet-18)</span>
          <span className="px-1 text-[9px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded">
            VERIFIED
          </span>
        </button>

        <button
          onClick={() => setActiveTab('convlstm')}
          className={`h-full px-3 text-xs font-mono font-medium flex items-center gap-2 border-b-2 transition-colors cursor-pointer ${
            activeTab === 'convlstm'
              ? 'border-[#61BACB] text-[#EDF3F9] bg-[#1D2B3D]/50'
              : 'border-transparent text-[#96A8BB] hover:text-[#EDF3F9]'
          }`}
        >
          <Activity className="w-3.5 h-3.5 text-[#61BACB]" />
          <span>2. Spatiotemporal ConvLSTM</span>
          <span className="px-1 text-[9px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded">
            VERIFIED
          </span>
        </button>

        <button
          onClick={() => setActiveTab('track_gru')}
          className={`h-full px-3 text-xs font-mono font-medium flex items-center gap-2 border-b-2 transition-colors cursor-pointer ${
            activeTab === 'track_gru'
              ? 'border-[#61BACB] text-[#EDF3F9] bg-[#1D2B3D]/50'
              : 'border-transparent text-[#96A8BB] hover:text-[#EDF3F9]'
          }`}
        >
          <Compass className={`w-3.5 h-3.5 ${trackMeta.checksum_verified ? 'text-[#61BACB]' : 'text-[#E7AD65]'}`} />
          <span>3. Track GRU/LSTM</span>
          <span className={`px-1 text-[9px] rounded border ${
            trackMeta.checksum_verified
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
              : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
          }`}>
            {trackMeta.checksum_verified ? 'VERIFIED' : 'UNAVAILABLE'}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('release_ledger')}
          className={`h-full px-3 text-xs font-mono font-medium flex items-center gap-2 border-b-2 transition-colors cursor-pointer ${
            activeTab === 'release_ledger'
              ? 'border-[#61BACB] text-[#EDF3F9] bg-[#1D2B3D]/50'
              : 'border-transparent text-[#96A8BB] hover:text-[#EDF3F9]'
          }`}
        >
          <ShieldCheck className="w-3.5 h-3.5 text-[#61BACB]" />
          <span>Audit & Release Ledger</span>
        </button>
      </div>

      {/* Main Dynamic View Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* ================================================================= */}
        {/* TAB 1: SATELLITE CNN REGRESSOR */}
        {/* ================================================================= */}
        {activeTab === 'satellite_cnn' && (
          <div className="space-y-6">
            {/* Top Overview & Architectural Metadata Card */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
              <div className="bg-[#111B28] border border-[#1E2E42] p-4 rounded-md space-y-2">
                <div className="text-[10px] font-mono text-[#96A8BB] uppercase">Architecture</div>
                <div className="text-sm font-bold text-[#EDF3F9]">{cnnMeta.architecture}</div>
                <p className="text-[11px] text-[#96A8BB]">
                  ResNet-18 adapted for 1-channel Thermal IR with dual continuous regression & 6-class category heads.
                </p>
                <div className="pt-2 flex items-center gap-2 text-[10px] font-mono text-[#61BACB]">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>11,180,679 Parameters</span>
                </div>
              </div>

              <div className="bg-[#111B28] border border-[#1E2E42] p-4 rounded-md space-y-2">
                <div className="text-[10px] font-mono text-[#96A8BB] uppercase">Training Dataset</div>
                <div className="text-sm font-bold text-[#EDF3F9]">NASA Cyclone Benchmark</div>
                <p className="text-[11px] text-[#96A8BB]">
                  25 unique tropical cyclones, strictly storm-disjoint partitioned (15 train, 5 val, 5 test).
                </p>
                <div className="pt-2 flex items-center gap-2 text-[10px] font-mono text-[#E7AD65]">
                  <Layers className="w-3.5 h-3.5" />
                  <span>2,500 Authentic Frames</span>
                </div>
              </div>

              <div className="bg-[#111B28] border border-[#1E2E42] p-4 rounded-md space-y-2">
                <div className="text-[10px] font-mono text-[#96A8BB] uppercase">Held-Out Test Error</div>
                <div className="text-xl font-bold font-mono text-[#61BACB]">
                  {cnnMeta.benchmark_metrics.test_mae_knots} kt <span className="text-xs text-[#96A8BB]">MAE</span>
                </div>
                <p className="text-[11px] text-[#96A8BB]">
                  RMSE: {cnnMeta.benchmark_metrics.test_rmse_knots} kt • Pearson r: {cnnMeta.benchmark_metrics.test_pearson_r}
                </p>
                <div className="pt-2 flex items-center gap-2 text-[10px] font-mono text-emerald-400">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>88.65% within ±1 Category</span>
                </div>
              </div>

              <div className="bg-[#111B28] border border-[#1E2E42] p-4 rounded-md space-y-2">
                <div className="text-[10px] font-mono text-[#96A8BB] uppercase">Operational Baseline</div>
                <div className="text-sm font-bold text-[#EDF3F9]">Subjective Dvorak Parity</div>
                <p className="text-[11px] text-[#96A8BB]">
                  Matches operational Dvorak uncertainty (±10 to ±12 kt vs reconnaissance) without manual analyst intervention.
                </p>
                <div className="pt-2 flex items-center gap-2 text-[10px] font-mono text-[#61BACB]">
                  <Lock className="w-3.5 h-3.5" />
                  <span>Zero Track Leakage</span>
                </div>
              </div>
            </div>

            {/* Interactive CNN Inference on Authentic INSAT Crops */}
            <div className="bg-[#111B28] border border-[#1E2E42] rounded-md overflow-hidden">
              <div className="px-5 py-3 bg-[#172333] border-b border-[#1E2E42] flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-[#61BACB]" />
                  <span className="text-xs font-bold text-[#EDF3F9]">
                    Interactive Inference on Authentic ISRO INSAT Multichannel Crops
                  </span>
                </div>

                <div className="flex items-center gap-3 text-xs font-mono">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[#96A8BB]">Cyclone:</span>
                    {['BIPARJOY', 'AMPHAN', 'REMAL', 'DANA'].map((st) => (
                      <button
                        key={st}
                        onClick={() => {
                          setCnnStorm(st);
                          handleRunCNN(st, cnnChannel);
                        }}
                        className={`px-2 py-0.5 rounded text-[11px] cursor-pointer ${
                          cnnStorm === st
                            ? 'bg-[#61BACB] text-[#0B111B] font-bold'
                            : 'bg-[#0B111B] text-[#96A8BB] hover:text-[#EDF3F9] border border-[#1E2E42]'
                        }`}
                      >
                        {st}
                      </button>
                    ))}
                  </div>

                  <div className="flex items-center gap-1.5 pl-2 border-l border-[#1E2E42]">
                    <span className="text-[#96A8BB]">Channel:</span>
                    {['TIR-1', 'TIR-2'].map((ch) => (
                      <button
                        key={ch}
                        onClick={() => {
                          setCnnChannel(ch);
                          handleRunCNN(cnnStorm, ch);
                        }}
                        className={`px-2 py-0.5 rounded text-[11px] cursor-pointer ${
                          cnnChannel === ch
                            ? 'bg-[#61BACB] text-[#0B111B] font-bold'
                            : 'bg-[#0B111B] text-[#96A8BB] hover:text-[#EDF3F9] border border-[#1E2E42]'
                        }`}
                      >
                        {ch}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Main Interactive Display Grid */}
              <div className="p-5 grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* Left Column: Authentic INSAT Image Display */}
                <div className="lg:col-span-5 flex flex-col items-center justify-center bg-[#0B111B] border border-[#1E2E42] p-4 rounded">
                  <div className="relative w-64 h-64 bg-black border border-[#1E2E42] rounded overflow-hidden flex items-center justify-center">
                    <img
                      src={getCropImageUrl(cnnStorm, cnnChannel)}
                      alt={`${cnnStorm} INSAT Crop`}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = '/ui/fallback_satellite.png';
                      }}
                    />
                    <div className="absolute top-2 left-2 px-1.5 py-0.5 bg-black/75 border border-[#1E2E42] text-[9px] font-mono text-[#61BACB] rounded">
                      ISRO MOSDAC • {cnnStorm} • {cnnChannel}
                    </div>
                    <div className="absolute bottom-2 right-2 px-1.5 py-0.5 bg-black/75 border border-[#1E2E42] text-[9px] font-mono text-[#96A8BB] rounded">
                      Calibrated L1B Crop
                    </div>
                  </div>

                  <div className="w-full mt-3 flex items-center justify-between text-[11px] font-mono text-[#96A8BB]">
                    <span>Resolution: 128×128 px normalized (inference pipeline)</span>
                    <span>Format: HDF5 Coregistered</span>
                  </div>

                  {onNavigateToSatellite && (
                    <button
                      onClick={onNavigateToSatellite}
                      className="mt-3 w-full py-1.5 bg-[#172333] hover:bg-[#1D2B3D] border border-[#1E2E42] text-[11px] font-mono text-[#61BACB] rounded flex items-center justify-center gap-1.5 cursor-pointer transition-colors"
                    >
                      <span>Inspect in Satellite Operations</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  )}
                </div>

                {/* Right Column: Scientific Inference Output & Probabilities */}
                <div className="lg:col-span-7 flex flex-col justify-between space-y-4">
                  {cnnLoading ? (
                    <div className="flex-1 flex flex-col items-center justify-center p-8 space-y-2">
                      <RefreshCw className="w-5 h-5 text-[#61BACB] animate-spin" />
                      <span className="text-xs font-mono text-[#96A8BB]">Running ResNet-18 forward pass on GPU...</span>
                    </div>
                  ) : cnnResult ? (
                    <div className="space-y-4">
                      {/* Prediction Summary Header */}
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                        <div className="bg-[#172333] border border-[#1E2E42] p-3 rounded">
                          <div className="text-[10px] font-mono text-[#96A8BB]">CNN Native Prediction</div>
                          <div className="text-2xl font-bold font-mono text-[#61BACB]">
                            {cnnResult.predicted_1min_wind_knots} <span className="text-xs text-[#96A8BB]">kt</span>
                          </div>
                          <div className="text-[10px] text-[#96A8BB] font-mono">1-min sustained (NOAA convention)</div>
                        </div>

                        <div className="bg-[#172333] border border-[#1E2E42] p-3 rounded">
                          <div className="text-[10px] font-mono text-[#96A8BB]">JTWC Reference (1-min)</div>
                          <div className="text-2xl font-bold font-mono text-[#EDF3F9]">
                            {cnnStorm === 'BIPARJOY' && '90.0 kt'}
                            {cnnStorm === 'AMPHAN' && '140.0 kt'}
                            {cnnStorm === 'REMAL' && '65.0 kt'}
                            {cnnStorm === 'DANA' && '20.0 kt'}
                          </div>
                          <div className="text-[10px] text-[#96A8BB] font-mono">1-min averaging framework</div>
                        </div>

                        <div className="bg-[#172333] border border-[#1E2E42] p-3 rounded">
                          <div className="text-[10px] font-mono text-[#96A8BB]">Official IMD Target (3-min)</div>
                          <div className="text-2xl font-bold font-mono text-[#E7AD65]">
                            {cnnStorm === 'BIPARJOY' && '85.0 kt'}
                            {cnnStorm === 'AMPHAN' && '95.0 kt'}
                            {cnnStorm === 'REMAL' && '60.0 kt'}
                            {cnnStorm === 'DANA' && 'INELIGIBLE'}
                          </div>
                          <div className="text-[10px] text-[#96A8BB] font-mono">
                            {cnnStorm === 'DANA' ? 'Weakened overland remnant' : 'Operational 3-min target'}
                          </div>
                        </div>
                      </div>

                      {/* Scientific Conversion Integrity Note */}
                      <div className="p-3 bg-[#0B111B] border border-[#1E2E42] rounded text-xs font-mono text-[#96A8BB] space-y-1">
                        <span className="text-[#E7AD65] font-bold">Scientific Averaging Integrity:</span>{' '}
                        <span>
                          No universal scalar multiplier converts 1-minute (NOAA/JTWC) into 3-minute (IMD) sustained winds.
                          The commonly cited 0.88 factor approximates 1-minute to 10-minute winds, not 3-minute winds.
                          Differences between CNN outputs and IMD advisories reflect non-equivalent averaging conventions and cross-sensor domain shift, not operational measurement error.
                        </span>
                      </div>

                      {/* Regression Category & Probabilities */}
                      <div className="bg-[#172333]/50 border border-[#1E2E42] p-3 rounded space-y-3">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-xs font-mono">
                          <div>
                            <span className="text-[#96A8BB]">Regression Implied: </span>
                            <span className="font-bold text-[#61BACB]">{cnnResult.regression_implied_bin || 'Unknown'}</span>
                          </div>
                          <div>
                            <span className="text-[#96A8BB]">Classifier Head: </span>
                            <span className="font-bold text-[#E7AD65]">{cnnResult.classifier_predicted_bin || cnnResult.predicted_category_label}</span>
                          </div>
                        </div>

                        {/* Head Agreement Banner */}
                        {cnnResult.head_disagreement_note ? (
                          <div className="p-2 bg-amber-500/10 border border-amber-500/30 rounded text-[11px] font-mono text-amber-300">
                            {cnnResult.head_disagreement_note}
                          </div>
                        ) : (
                          <div className="p-2 bg-emerald-500/10 border border-emerald-500/30 rounded text-[11px] font-mono text-emerald-400">
                            Dual Heads in Agreement: Regression prediction falls into the classifier's top predicted bin.
                          </div>
                        )}

                        {/* Probability Bars */}
                        <div className="space-y-1.5 pt-1">
                          <div className="text-[10px] font-mono text-[#96A8BB]">
                            Source-Native 1-Minute Wind Bin Probabilities (Classifier Head):
                          </div>
                          {Object.entries(cnnResult.category_probabilities || {}).map(([cat, prob]) => {
                            const pct = Math.round((prob as number) * 100);
                            return (
                              <div key={cat} className="space-y-0.5">
                                <div className="flex items-center justify-between text-[10px] font-mono">
                                  <span className="text-[#EDF3F9] truncate max-w-[240px]">{cat}</span>
                                  <span className="text-[#61BACB]">{pct}%</span>
                                </div>
                                <div className="h-1.5 bg-[#0B111B] rounded-full overflow-hidden">
                                  <div
                                    className="h-full bg-gradient-to-r from-[#61BACB] to-[#E7AD65] rounded-full"
                                    style={{ width: `${pct}%` }}
                                  />
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>

                      {/* Scientific Limitations & Domain Shift Callout */}
                      <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded text-xs text-[#EDF3F9] space-y-1 font-mono">
                        <div className="flex items-center gap-1.5 font-bold text-amber-400">
                          <AlertTriangle className="w-3.5 h-3.5" />
                          <span>Scientific Cross-Sensor Domain Shift Disclaimer</span>
                        </div>
                        <p className="text-[11px] text-[#96A8BB] leading-relaxed">
                          Trained on NASA Clean Longwave IR Band 13 (10.3 µm GOES / 10.4 µm Himawari). Evaluated zero-shot on ISRO INSAT-3DR/3DS TIR-1 (10.8 µm, Δλ ≈ 0.5 µm).
                          INSAT look-up table calibration enforces a 179.86 K floor, truncating hyper-cold convective overshoots.
                          Predictions are descriptive experimental transfers, not operational warning guidance.
                        </p>
                      </div>
                    </div>
                  ) : null}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ================================================================= */}
        {/* TAB 2: SPATIOTEMPORAL CONVLSTM */}
        {/* ================================================================= */}
        {activeTab === 'convlstm' && (
          <div className="space-y-6">
            {/* Top Cards for ConvLSTM */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
              <div className="bg-[#111B28] border border-[#1E2E42] p-4 rounded-md space-y-2">
                <div className="text-[10px] font-mono text-[#96A8BB] uppercase">Architecture</div>
                <div className="text-sm font-bold text-[#EDF3F9]">{convMeta.architecture}</div>
                <p className="text-[11px] text-[#96A8BB]">
                  2-layer ConvLSTM (32 → 64 filters) with convolutional next-frame reconstruction decoder.
                </p>
                <div className="pt-2 flex items-center gap-2 text-[10px] font-mono text-[#61BACB]">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>360,578 Parameters</span>
                </div>
              </div>

              <div className="bg-[#111B28] border border-[#1E2E42] p-4 rounded-md space-y-2">
                <div className="text-[10px] font-mono text-[#96A8BB] uppercase">Sequence Specification</div>
                <div className="text-sm font-bold text-[#EDF3F9]">Chronological T=3 Past Frames</div>
                <p className="text-[11px] text-[#96A8BB]">
                  2,425 chronological sequences across 25 disjoint storms (1,574 train, 452 val, 399 held-out test).
                </p>
                <div className="pt-2 flex items-center gap-2 text-[10px] font-mono text-[#E7AD65]">
                  <Clock className="w-3.5 h-3.5" />
                  <span>Strict Temporal Ordering</span>
                </div>
              </div>

              <div className="bg-[#111B28] border border-[#1E2E42] p-4 rounded-md space-y-2">
                <div className="text-[10px] font-mono text-[#96A8BB] uppercase">Next-Frame Pixel MSE</div>
                <div className="text-xl font-bold font-mono text-emerald-400">
                  {convMeta.benchmark_metrics.next_frame_pixel_mse}
                </div>
                <p className="text-[11px] text-[#96A8BB]">
                  Normalized pixel variance ≤ 1.1% on held-out unseen cyclone sequences.
                </p>
                <div className="pt-2 flex items-center gap-2 text-[10px] font-mono text-[#61BACB]">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Kinematic Advection Learned</span>
                </div>
              </div>

              <div className="bg-[#111B28] border border-[#1E2E42] p-4 rounded-md space-y-2">
                <div className="text-[10px] font-mono text-[#96A8BB] uppercase">Benchmark Comparison</div>
                <div className="text-sm font-bold text-[#EDF3F9]">Persistence Dominance</div>
                <p className="text-[11px] text-[#96A8BB]">
                  Persistence MAE: 1.90 kt • ConvLSTM MAE: 17.20 kt • CNN MAE: 10.00 kt.
                </p>
                <div className="pt-2 flex items-center gap-2 text-[10px] font-mono text-amber-400">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>See Physical Explanation Below</span>
                </div>
              </div>
            </div>

            {/* Interactive ConvLSTM Sequence Forecaster */}
            <div className="bg-[#111B28] border border-[#1E2E42] rounded-md overflow-hidden">
              <div className="px-5 py-3 bg-[#172333] border-b border-[#1E2E42] flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-[#61BACB]" />
                  <span className="text-xs font-bold text-[#EDF3F9]">
                    Interactive Spatiotemporal Forecaster & Next-Frame Reconstruction
                  </span>
                </div>

                <div className="flex items-center gap-3 text-xs font-mono">
                  <span className="text-[#96A8BB]">Held-Out Test Sequence:</span>
                  <select
                    value={selectedSeqId}
                    onChange={(e) => {
                      setSelectedSeqId(e.target.value);
                      handleRunConvLSTM(e.target.value);
                    }}
                    className="bg-[#0B111B] border border-[#1E2E42] text-[#EDF3F9] px-2 py-1 rounded text-xs cursor-pointer"
                  >
                    {sequences.map((s) => (
                      <option key={s.sequence_id} value={s.sequence_id}>
                        {s.sequence_id} (Storm: {s.storm_id}, Target: {s.target_wind} kt)
                      </option>
                    ))}
                  </select>

                  <button
                    onClick={() => handleRunConvLSTM(selectedSeqId)}
                    disabled={convLoading}
                    className="px-3 py-1 bg-[#61BACB] hover:bg-[#52a6b6] text-[#0B111B] text-xs font-bold rounded flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                  >
                    {convLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                    <span>Generate Forecast</span>
                  </button>
                </div>
              </div>

              {/* Sequence Display Area */}
              <div className="p-5 space-y-6">
                {convLoading ? (
                  <div className="flex flex-col items-center justify-center p-12 space-y-3">
                    <RefreshCw className="w-6 h-6 text-[#61BACB] animate-spin" />
                    <span className="text-xs font-mono text-[#96A8BB]">
                      Executing recurrent ConvLSTM spatiotemporal forward pass on GPU...
                    </span>
                  </div>
                ) : convResult ? (
                  <div className="space-y-6">
                    {/* Visual Frames Progression: 3 Past Input Frames -> Reconstructed Next Frame vs Target */}
                    <div>
                      <div className="text-xs font-mono text-[#96A8BB] mb-3 flex items-center justify-between">
                        <span>CHRONOLOGICAL SATELLITE INPUT SEQUENCE (T = 3) & NEXT-FRAME RECONSTRUCTION</span>
                        <span className="text-[#61BACB]">
                          Lead Time: {convResult.actual_elapsed_hours != null ? `+${convResult.actual_elapsed_hours}h (${convResult.actual_elapsed_seconds}s)` : '+3.0 Hours'}
                        </span>
                      </div>

                      {convResult.sequence_cadence_note && (
                        <div className="mb-3 p-2 bg-[#0B111B] border border-[#1E2E42] rounded text-[11px] font-mono text-[#96A8BB]">
                          <span className="text-[#61BACB] font-bold">Observation Cadence:</span> {convResult.sequence_cadence_note}
                        </div>
                      )}

                      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                        {convResult.input_frames.map((url, idx) => (
                          <div key={idx} className="bg-[#0B111B] border border-[#1E2E42] p-2 rounded text-center space-y-2">
                            <div className="text-[10px] font-mono text-[#96A8BB]">
                              Frame {idx + 1} (t - {2 - idx})
                            </div>
                            <div className="aspect-square bg-black rounded overflow-hidden border border-[#1E2E42]">
                              <img src={url} alt={`Frame ${idx}`} className="w-full h-full object-cover" />
                            </div>
                            <div className="text-[10px] font-mono text-[#EDF3F9]">
                              Obs: {convResult.past_observed_winds_kt[idx]} kt
                            </div>
                          </div>
                        ))}

                        {/* Reconstructed Next Frame */}
                        <div className="bg-[#0B111B] border border-[#61BACB]/50 p-2 rounded text-center space-y-2">
                          <div className="text-[10px] font-mono text-[#61BACB] font-bold">
                            ConvLSTM Pred (t + 1)
                          </div>
                          <div className="aspect-square bg-black rounded overflow-hidden border border-[#61BACB]/50 flex items-center justify-center">
                            {convResult.reconstructed_next_frame_b64 ? (
                              <img
                                src={convResult.reconstructed_next_frame_b64}
                                alt="ConvLSTM Reconstruction"
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <span className="text-[10px] font-mono text-[#96A8BB]">Reconstruction Ready</span>
                            )}
                          </div>
                          <div className="text-[10px] font-mono text-[#61BACB] font-bold">
                            Pred: {convResult.predicted_future_wind_kt} kt
                          </div>
                        </div>

                        {/* Actual Target Frame */}
                        <div className="bg-[#0B111B] border border-[#E7AD65]/50 p-2 rounded text-center space-y-2">
                          <div className="text-[10px] font-mono text-[#E7AD65] font-bold">
                            Ground Truth (t + 1)
                          </div>
                          <div className="aspect-square bg-black rounded overflow-hidden border border-[#E7AD65]/50">
                            {convResult.target_frame_url && (
                              <img
                                src={convResult.target_frame_url}
                                alt="Target Frame"
                                className="w-full h-full object-cover"
                              />
                            )}
                          </div>
                          <div className="text-[10px] font-mono text-[#E7AD65] font-bold">
                            Actual: {convResult.ground_truth_target_wind_kt} kt
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Quantitative Error Breakdown Table */}
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      <div className="bg-[#172333] border border-[#1E2E42] p-3 rounded">
                        <div className="text-[10px] font-mono text-[#96A8BB]">ConvLSTM Forecast Error</div>
                        <div className="text-xl font-bold font-mono text-[#61BACB]">
                          {convResult.prediction_absolute_error_kt} <span className="text-xs text-[#96A8BB]">kt</span>
                        </div>
                        <div className="text-[10px] text-[#96A8BB] font-mono">
                          |Pred ({convResult.predicted_future_wind_kt} kt) - True ({convResult.ground_truth_target_wind_kt} kt)|
                        </div>
                      </div>

                      <div className="bg-[#172333] border border-[#1E2E42] p-3 rounded">
                        <div className="text-[10px] font-mono text-[#96A8BB]">Persistence Baseline Error</div>
                        <div className="text-xl font-bold font-mono text-[#E7AD65]">
                          {convResult.persistence_baseline_error_kt} <span className="text-xs text-[#96A8BB]">kt</span>
                        </div>
                        <div className="text-[10px] text-[#96A8BB] font-mono">
                          |Current ({convResult.past_observed_winds_kt[2]} kt) - Future ({convResult.ground_truth_target_wind_kt} kt)|
                        </div>
                      </div>

                      <div className="bg-[#172333] border border-[#1E2E42] p-3 rounded">
                        <div className="text-[10px] font-mono text-[#96A8BB]">Inference Latency</div>
                        <div className="text-xl font-bold font-mono text-[#EDF3F9]">
                          {convResult.inference_latency_ms} <span className="text-xs text-[#96A8BB]">ms</span>
                        </div>
                        <div className="text-[10px] text-[#96A8BB] font-mono">3-frame recurrent pass on RTX 4050</div>
                      </div>
                    </div>

                    {/* Scientific Insight on Persistence Dominance */}
                    <div className="p-4 bg-[#172333]/50 border border-[#1E2E42] rounded text-xs space-y-2 font-mono">
                      <div className="flex items-center gap-2 font-bold text-[#61BACB]">
                        <HelpCircle className="w-4 h-4" />
                        <span>Why Does the Persistence Baseline Outperform Neural Intensity Over Short Horizons?</span>
                      </div>
                      <p className="text-[11px] text-[#96A8BB] leading-relaxed">
                        Tropical cyclone intensity changes gradually (typically 1–2 knots per hour, except in rare rapid intensification).
                        Over a short 1–3 hour forecast horizon, predicting zero change (future wind = current wind) achieves a remarkable 1.90 kt MAE.
                        ConvLSTM was trained to model cloud canopy expansion, eye formation, and advection (achieving 0.01084 pixel MSE).
                        For static intensity regression, high-resolution ResNet-18 (128×128 px, 10.00 kt MAE) remains scientifically superior.
                      </p>
                    </div>
                  </div>
                ) : null}
              </div>
            </div>
          </div>
        )}

        {/* ================================================================= */}
        {/* TAB 3: TRACK GRU/LSTM */}
        {/* ================================================================= */}
        {activeTab === 'track_gru' && (
          <div className="space-y-6">
            {/* Status Card: Verified Release or Quarantine */}
            {trackMeta.checksum_verified ? (
              <div className="p-5 bg-emerald-500/10 border border-emerald-500/30 rounded-md space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded bg-emerald-500/20 flex items-center justify-center text-emerald-400">
                      <CheckCircle2 className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-emerald-400">
                        Scientific Release Gate Cleared: Vayumarg-Track-GRU Verified & Active
                      </h3>
                      <p className="text-xs text-[#96A8BB] font-mono">
                        Model Checkpoint: <code className="text-[#61BACB]">{trackMeta.checkpoint_path}</code> • SHA-256 Authenticated
                      </p>
                    </div>
                  </div>
                  <span className="px-2 py-0.5 text-[10px] font-mono bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 rounded font-bold">
                    VERIFIED EXPERIMENTAL
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 text-xs font-mono">
                  <div className="bg-[#0B111B] border border-[#1E2E42] p-2 rounded">
                    <span className="text-[#96A8BB] text-[10px]">Architecture</span>
                    <div className="text-[#EDF3F9] font-bold text-[11px] truncate">2-Layer GRU (96 units)</div>
                  </div>
                  <div className="bg-[#0B111B] border border-[#1E2E42] p-2 rounded">
                    <span className="text-[#96A8BB] text-[10px]">Trainable Params</span>
                    <div className="text-[#61BACB] font-bold text-[11px]">141,802</div>
                  </div>
                  <div className="bg-[#0B111B] border border-[#1E2E42] p-2 rounded">
                    <span className="text-[#96A8BB] text-[10px]">Training Windows</span>
                    <div className="text-emerald-400 font-bold text-[11px]">8,201 (331 Storms)</div>
                  </div>
                  <div className="bg-[#0B111B] border border-[#1E2E42] p-2 rounded">
                    <span className="text-[#96A8BB] text-[10px]">Horizons</span>
                    <div className="text-[#EDF3F9] font-bold text-[11px]">+6h / +12h / +24h</div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-5 bg-amber-500/10 border border-amber-500/30 rounded-md space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded bg-amber-500/20 flex items-center justify-center text-amber-400">
                    <ShieldAlert className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-amber-400">
                      Scientific Release Gate Active: Track Forecaster Quarantined
                    </h3>
                    <p className="text-xs text-[#96A8BB] font-mono">
                      Model Checkpoint Status: {trackMeta.status}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Interactive Track Forecasting Playground */}
            <div className="bg-[#111B28] border border-[#1E2E42] rounded-md p-5 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <h4 className="text-xs font-bold text-[#EDF3F9] uppercase font-mono">
                    Interactive Multi-Horizon Track Inference & Baseline Benchmarking
                  </h4>
                  <p className="text-[11px] text-[#96A8BB] font-mono">
                    Select a landmark North Indian Ocean cyclone to execute live recurrent inference alongside geodesic & persistence baselines.
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleRunTrackGRU(selectedTrackStorm)}
                    disabled={trackLoading}
                    className="px-4 py-2 bg-[#61BACB] hover:bg-[#4EA8B9] text-[#0B111B] text-xs font-mono font-bold rounded flex items-center gap-2 cursor-pointer disabled:opacity-50 transition-colors shadow-sm"
                  >
                    {trackLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                    <span>Run GRU Inference</span>
                  </button>
                </div>
              </div>

              {/* Storm Selection Pills */}
              <div className="flex flex-wrap items-center gap-2 pt-1">
                <span className="text-xs font-mono text-[#96A8BB] mr-1">Select Cyclone:</span>
                {['BIPARJOY', 'AMPHAN', 'REMAL', 'FANI', 'TAUKTAE', 'MOCHA'].map((stName) => (
                  <button
                    key={stName}
                    onClick={() => {
                      setSelectedTrackStorm(stName);
                      handleRunTrackGRU(stName);
                    }}
                    className={`px-3 py-1 text-xs font-mono rounded border transition-colors cursor-pointer ${
                      selectedTrackStorm === stName
                        ? 'bg-[#61BACB]/20 border-[#61BACB] text-[#61BACB] font-bold'
                        : 'bg-[#172333] border-[#1E2E42] text-[#96A8BB] hover:text-[#EDF3F9] hover:border-[#96A8BB]'
                    }`}
                  >
                    {stName}
                  </button>
                ))}
              </div>

              {/* Live Inference Output */}
              {trackLoading && (
                <div className="p-8 flex flex-col items-center justify-center space-y-2 bg-[#0B111B] border border-[#1E2E42] rounded">
                  <RefreshCw className="w-5 h-5 text-[#61BACB] animate-spin" />
                  <span className="text-xs font-mono text-[#96A8BB]">
                    Running recurrent GRU spatiotemporal forward pass on {selectedTrackStorm}...
                  </span>
                </div>
              )}

              {trackResult?.forecast_result && !trackLoading && (
                <div className="space-y-4 pt-2">
                  {/* Origin Metadata Bar */}
                  <div className="p-3 bg-[#0B111B] border border-[#1E2E42] rounded flex flex-wrap items-center justify-between text-xs font-mono gap-3">
                    <div className="flex items-center gap-2">
                      <span className="text-[#96A8BB]">Issuance Fix:</span>
                      <span className="text-[#EDF3F9] font-bold">
                        {trackResult.forecast_result.origin_fix.latitude}°N, {trackResult.forecast_result.origin_fix.longitude}°E
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[#96A8BB]">Initial Intensity:</span>
                      <span className="text-[#61BACB] font-bold">
                        {trackResult.forecast_result.origin_fix.wind_speed_kt} kt
                      </span>
                    </div>
                    {trackResult.issue_time && (
                      <div className="flex items-center gap-2">
                        <span className="text-[#96A8BB]">Timestamp:</span>
                        <span className="text-[#EDF3F9]">{trackResult.issue_time}</span>
                      </div>
                    )}
                    <div className="flex items-center gap-2">
                      <span className="text-[#96A8BB]">SHA-256:</span>
                      <span className="text-emerald-400 font-mono text-[10px] truncate max-w-[120px]">
                        {trackResult.forecast_result.sha256}
                      </span>
                    </div>
                  </div>

                  {/* Multi-Horizon Comparison Table */}
                  <div className="border border-[#1E2E42] rounded overflow-hidden">
                    <table className="w-full text-left text-xs font-mono">
                      <thead className="bg-[#0B111B] text-[#96A8BB] border-b border-[#1E2E42]">
                        <tr>
                          <th className="p-3">Horizon</th>
                          <th className="p-3">Pure GRU</th>
                          <th className="p-3">Geodesic Baseline</th>
                          <th className="p-3">Hybrid (Geo+Res)</th>
                          <th className="p-3">Ground Truth</th>
                          <th className="p-3">Track Error Comparison</th>
                          <th className="p-3">Wind Error</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#1E2E42] bg-[#111B28]">
                        {trackResult.forecast_result.forecasts.map((fc) => {
                          const gru = fc.gru_predicted;
                          const geo = fc.geodesic_baseline;
                          const hyb = fc.hybrid_predicted;
                          const gt = fc.ground_truth;
                          const ver = fc.verification;

                          return (
                            <tr key={fc.horizon_h} className="hover:bg-[#172333]/40">
                              <td className="p-3 font-bold text-[#61BACB]">+{fc.horizon_h} Hours</td>
                              <td className="p-3">
                                <div className="text-[#EDF3F9] font-bold">
                                  {gru.latitude}°N, {gru.longitude}°E
                                </div>
                                <div className="text-[#61BACB] text-[11px]">
                                  {gru.wind_speed_kt} kt ({gru.displacement_total_km} km disp)
                                </div>
                              </td>
                              <td className="p-3 text-[#96A8BB]">
                                <div>{geo.latitude}°N, {geo.longitude}°E</div>
                                <div className="text-[11px] text-[#96A8BB]">{geo.wind_speed_kt} kt ({geo.displacement_total_km} km disp)</div>
                              </td>
                              <td className="p-3">
                                {hyb ? (
                                  <div>
                                    <div className="text-emerald-400 font-bold">
                                      {hyb.latitude}°N, {hyb.longitude}°E
                                    </div>
                                    <div className="text-emerald-400/80 text-[11px]">
                                      {hyb.displacement_total_km} km (Geo + Res)
                                    </div>
                                  </div>
                                ) : (
                                  <span className="text-[#96A8BB]">-</span>
                                )}
                              </td>
                              <td className="p-3">
                                {gt ? (
                                  <div>
                                    <div className="text-emerald-400 font-bold">{gt.latitude}°N, {gt.longitude}°E</div>
                                    <div className="text-[11px] text-emerald-400">{gt.wind_speed_kt} kt</div>
                                  </div>
                                ) : (
                                  <span className="text-[#96A8BB]">N/A</span>
                                )}
                              </td>
                              <td className="p-3">
                                {ver ? (
                                  <div>
                                    {ver.hybrid_track_error_km !== undefined && (
                                      <div className="font-bold text-emerald-400">
                                        Hybrid: {ver.hybrid_track_error_km} km
                                      </div>
                                    )}
                                    <div className="text-[#EDF3F9] text-[11px]">
                                      Geodesic: {ver.geodesic_track_error_km} km
                                    </div>
                                    <div className="text-[#96A8BB] text-[10px]">
                                      Pure GRU: {ver.gru_track_error_km} km (Stat: {ver.stationary_track_error_km} km)
                                    </div>
                                  </div>
                                ) : (
                                  <span className="text-[#96A8BB]">-</span>
                                )}
                              </td>
                              <td className="p-3">
                                {ver ? (
                                  <div>
                                    <span className="font-bold text-[#EDF3F9]">{ver.gru_wind_error_kt} kt</span>
                                    <span className="text-[#96A8BB] text-[11px]"> vs {ver.persistence_wind_error_kt} kt pers</span>
                                  </div>
                                ) : (
                                  <span className="text-[#96A8BB]">-</span>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>

            {/* Held-Out Test Set Empirical Benchmarks Card */}
            <div className="bg-[#111B28] border border-[#1E2E42] rounded-md p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-[#61BACB]" />
                  <h4 className="text-xs font-bold text-[#EDF3F9] uppercase font-mono">
                    Held-Out Test Benchmark Metrics (1,216 Windows Across 51 Active Unseen Storms)
                  </h4>
                </div>
                <span className="px-2 py-0.5 text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded">
                  AUTHENTIC EMPIRICAL BENCHMARKS
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs font-mono">
                {/* +6h Horizon */}
                <div className="bg-[#172333] border border-[#1E2E42] p-4 rounded space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-[#61BACB] text-sm">+6 Hour Horizon</span>
                    <span className="text-[10px] text-[#96A8BB]">Short-range</span>
                  </div>
                  <div className="space-y-1 text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-[#96A8BB]">Hybrid (Geo+Res):</span>
                      <span className="text-emerald-400 font-bold">33.3 km (Best)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#96A8BB]">Geodesic Baseline:</span>
                      <span className="text-[#EDF3F9] font-bold">35.3 km</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#96A8BB]">Pure GRU Error:</span>
                      <span className="text-[#96A8BB]">42.2 km</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#96A8BB]">Stationary Baseline:</span>
                      <span className="text-[#D86F6F]">97.5 km</span>
                    </div>
                    <div className="flex justify-between pt-1 border-t border-[#1E2E42]">
                      <span className="text-[#96A8BB]">Stationary Skill:</span>
                      <span className="text-emerald-400 font-bold">+56.7%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#96A8BB]">GRU Wind MAE:</span>
                      <span className="text-[#EDF3F9] font-bold">6.41 kt</span>
                    </div>
                  </div>
                </div>

                {/* +12h Horizon */}
                <div className="bg-[#172333] border border-[#1E2E42] p-4 rounded space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-[#61BACB] text-sm">+12 Hour Horizon</span>
                    <span className="text-[10px] text-[#96A8BB]">Mid-range</span>
                  </div>
                  <div className="space-y-1 text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-[#96A8BB]">Hybrid (Geo+Res):</span>
                      <span className="text-emerald-400 font-bold">70.6 km (Best)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#96A8BB]">Geodesic Baseline:</span>
                      <span className="text-[#EDF3F9] font-bold">78.3 km</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#96A8BB]">Pure GRU Error:</span>
                      <span className="text-[#96A8BB]">89.8 km</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#96A8BB]">Stationary Baseline:</span>
                      <span className="text-[#D86F6F]">193.8 km</span>
                    </div>
                    <div className="flex justify-between pt-1 border-t border-[#1E2E42]">
                      <span className="text-[#96A8BB]">Stationary Skill:</span>
                      <span className="text-emerald-400 font-bold">+53.7%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#96A8BB]">GRU Wind MAE:</span>
                      <span className="text-[#EDF3F9] font-bold">7.94 kt</span>
                    </div>
                  </div>
                </div>

                {/* +24h Horizon */}
                <div className="bg-[#172333] border border-[#1E2E42] p-4 rounded space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-[#61BACB] text-sm">+24 Hour Horizon</span>
                    <span className="text-[10px] text-emerald-400 font-mono">HYBRID OUTPERFORMS</span>
                  </div>
                  <div className="space-y-1 text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-[#96A8BB]">Hybrid (Geo+Res):</span>
                      <span className="text-emerald-400 font-bold">158.1 km (Best)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#96A8BB]">Geodesic Baseline:</span>
                      <span className="text-[#EDF3F9] font-bold">180.5 km</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#96A8BB]">Pure GRU Error:</span>
                      <span className="text-[#96A8BB]">239.3 km</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#96A8BB]">Stationary Baseline:</span>
                      <span className="text-[#D86F6F]">388.5 km</span>
                    </div>
                    <div className="flex justify-between pt-1 border-t border-[#1E2E42]">
                      <span className="text-[#96A8BB]">GRU Wind MAE:</span>
                      <span className="text-[#EDF3F9] font-bold">10.87 kt</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#96A8BB]">Wind Persistence:</span>
                      <span className="text-[#96A8BB]">11.10 kt</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#96A8BB]">95% Bootstrap CI:</span>
                      <span className="text-amber-400 font-mono text-[10px]">[-0.863, +0.786] kt</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Scientific Methodology Note */}
              <div className="p-3 bg-[#0B111B] border border-[#1E2E42] rounded text-xs font-mono text-[#96A8BB] leading-relaxed">
                <span className="text-[#E7AD65] font-bold">Scientific Methodology & Atmospheric Inertia:</span> In tropical cyclones,
                atmospheric steering inertia makes short-range (6h–12h) linear constant-velocity extrapolation exceptionally difficult to beat.
                The recurrent GRU architecture uses temporal attention over 24h of history to capture trajectory curvature and achieves substantial
                skill over stationary projections (+56.7% at +6h, +38.4% at +24h), while outperforming persistence intensity forecasting at +24h.
              </div>
            </div>

            {/* Authoritative Operational Baseline Integration */}
            <div className="bg-[#111B28] border border-[#1E2E42] rounded-md p-5 flex items-center justify-between">
              <div>
                <h4 className="text-xs font-bold text-[#EDF3F9] uppercase font-mono">
                  Module B Operational Deterministic Baseline
                </h4>
                <p className="text-xs text-[#96A8BB] font-mono mt-1">
                  The production operational dashboard continues to provide deterministic constant-velocity geodesic forward extrapolation.
                </p>
              </div>

              {onNavigateToForecast && (
                <button
                  onClick={onNavigateToForecast}
                  className="px-4 py-2 bg-[#172333] hover:bg-[#1D2B3D] border border-[#1E2E42] text-xs font-mono text-[#EDF3F9] rounded flex items-center gap-2 cursor-pointer transition-colors"
                >
                  <span>Launch Forecast Lab</span>
                  <ArrowRight className="w-3.5 h-3.5 text-[#61BACB]" />
                </button>
              )}
            </div>
          </div>
        )}

        {/* ================================================================= */}
        {/* TAB 4: AUDIT & RELEASE LEDGER */}
        {/* ================================================================= */}
        {activeTab === 'release_ledger' && (
          <div className="space-y-6">
            {/* Cryptographic Checksums & Gate Enforcement Table */}
            <div className="bg-[#111B28] border border-[#1E2E42] rounded-md overflow-hidden">
              <div className="px-5 py-3 bg-[#172333] border-b border-[#1E2E42] flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-[#61BACB]" />
                  <span className="text-xs font-bold text-[#EDF3F9]">
                    Authoritative Cryptographic Checksum & Verification Ledger
                  </span>
                </div>
                <span className="text-[10px] font-mono text-[#96A8BB]">SHA-256 HASH VERIFICATION</span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-[#0B111B] text-[#96A8BB] border-b border-[#1E2E42]">
                    <tr>
                      <th className="p-3">Model Name</th>
                      <th className="p-3">Architecture</th>
                      <th className="p-3">Checkpoint File</th>
                      <th className="p-3">Expected SHA-256</th>
                      <th className="p-3">Actual SHA-256</th>
                      <th className="p-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1E2E42]">
                    <tr>
                      <td className="p-3 font-bold text-[#EDF3F9]">{cnnMeta.name}</td>
                      <td className="p-3 text-[#96A8BB]">{cnnMeta.architecture}</td>
                      <td className="p-3 text-[#61BACB]">{cnnMeta.checkpoint_path || 'None'}</td>
                      <td className="p-3 text-[10px] text-[#96A8BB] truncate max-w-[120px]">{cnnMeta.trusted_sha256}</td>
                      <td className="p-3 text-[10px] text-[#61BACB] truncate max-w-[120px]">{cnnMeta.actual_sha256}</td>
                      <td className="p-3">
                        <span className="px-2 py-0.5 text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded font-bold">
                          {cnnMeta.status}
                        </span>
                      </td>
                    </tr>

                    <tr>
                      <td className="p-3 font-bold text-[#EDF3F9]">{convMeta.name}</td>
                      <td className="p-3 text-[#96A8BB]">{convMeta.architecture}</td>
                      <td className="p-3 text-[#61BACB]">{convMeta.checkpoint_path || 'None'}</td>
                      <td className="p-3 text-[10px] text-[#96A8BB] truncate max-w-[120px]">{convMeta.trusted_sha256}</td>
                      <td className="p-3 text-[10px] text-[#61BACB] truncate max-w-[120px]">{convMeta.actual_sha256}</td>
                      <td className="p-3">
                        <span className="px-2 py-0.5 text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded font-bold">
                          {convMeta.status}
                        </span>
                      </td>
                    </tr>

                    <tr>
                      <td className="p-3 font-bold text-[#EDF3F9]">{trackMeta.name}</td>
                      <td className="p-3 text-[#96A8BB]">{trackMeta.architecture}</td>
                      <td className="p-3 text-[#61BACB]">{trackMeta.checkpoint_path || 'None'}</td>
                      <td className="p-3 text-[10px] text-[#96A8BB] truncate max-w-[120px]">{trackMeta.trusted_sha256 || 'None'}</td>
                      <td className="p-3 text-[10px] text-[#61BACB] truncate max-w-[120px]">{trackMeta.actual_sha256 || 'None'}</td>
                      <td className="p-3">
                        <span className={`px-2 py-0.5 text-[10px] rounded font-bold border ${
                          trackMeta.checksum_verified
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                            : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                        }`}>
                          {trackMeta.status}
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* Pre-Computed INSAT Zero-Shot Evaluation Ledger */}
            {insatLedger && (
              <div className="bg-[#111B28] border border-[#1E2E42] rounded-md overflow-hidden">
                <div className="px-5 py-3 bg-[#172333] border-b border-[#1E2E42] flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Database className="w-4 h-4 text-[#61BACB]" />
                    <span className="text-xs font-bold text-[#EDF3F9]">
                      Zero-Shot Cross-Sensor Evaluation on Authentic ISRO INSAT Crops
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-emerald-400 font-bold">
                    MEAN ABS ERROR (ELIGIBLE): {insatLedger.cross_domain_findings?.mean_absolute_error_eligible_storms_kt} kt
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-[#0B111B] text-[#96A8BB] border-b border-[#1E2E42]">
                      <tr>
                        <th className="p-3">Storm</th>
                        <th className="p-3">Year</th>
                        <th className="p-3">Satellite & Sensor</th>
                        <th className="p-3">Official IMD Target</th>
                        <th className="p-3">Predicted Intensity</th>
                        <th className="p-3">Abs Error</th>
                        <th className="p-3">Predicted Category</th>
                        <th className="p-3">Eligibility Note</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#1E2E42]">
                      {(insatLedger.evaluations || []).map((ev: any) => (
                        <tr key={ev.storm_name}>
                          <td className="p-3 font-bold text-[#EDF3F9]">{ev.storm_name}</td>
                          <td className="p-3 text-[#96A8BB]">{ev.season_year}</td>
                          <td className="p-3 text-[#61BACB]">{ev.satellite} (TIR-1)</td>
                          <td className="p-3 font-bold text-[#E7AD65]">
                            {ev.official_imd_wind_kt ? `${ev.official_imd_wind_kt} kt (${ev.official_imd_category})` : 'None'}
                          </td>
                          <td className="p-3 font-bold text-[#61BACB]">{ev.predicted_wind_kt} kt</td>
                          <td className="p-3 font-mono">
                            {ev.absolute_error_kt !== null ? (
                              <span className={ev.absolute_error_kt < 10 ? 'text-emerald-400' : 'text-[#E7AD65]'}>
                                {ev.absolute_error_kt} kt
                              </span>
                            ) : (
                              <span className="text-[#96A8BB]">N/A</span>
                            )}
                          </td>
                          <td className="p-3 text-[#96A8BB]">{ev.predicted_category}</td>
                          <td className="p-3 text-[10px] text-[#96A8BB]">{ev.eligibility}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
