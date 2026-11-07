import type {
  CycloneForecastResult,
  PhysicalCropMetrics,
  SatelliteCropMeta,
  StormDetail,
  StormProfile,
  SystemHealth,
} from './types';

const API_BASE = '/api';

export async function fetchHealth(): Promise<SystemHealth> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchStorms(): Promise<StormProfile[]> {
  const res = await fetch(`${API_BASE}/storms`);
  if (!res.ok) {
    throw new Error(`Failed to fetch storms: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchStormDetail(stormName: string): Promise<StormDetail> {
  const res = await fetch(`${API_BASE}/storms/${encodeURIComponent(stormName)}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch details for storm '${stormName}': ${res.statusText}`);
  }
  return res.json();
}

export async function fetchSatelliteCrops(): Promise<SatelliteCropMeta[]> {
  const res = await fetch(`${API_BASE}/satellite/crops`);
  if (!res.ok) {
    throw new Error(`Failed to fetch satellite crops: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchCropMetrics(
  stormName: string,
  channel: string = 'TIR-1'
): Promise<PhysicalCropMetrics> {
  const res = await fetch(
    `${API_BASE}/satellite/crop/${encodeURIComponent(stormName)}/metrics?channel=${encodeURIComponent(channel)}`
  );
  if (!res.ok) {
    throw new Error(`Failed to fetch crop metrics: ${res.statusText}`);
  }
  return res.json();
}

export function getCropImageUrl(stormName: string, channel: string = 'TIR-1'): string {
  return `${API_BASE}/satellite/crop/${encodeURIComponent(stormName)}/image?channel=${encodeURIComponent(channel)}`;
}

export async function postGenerateForecast(
  stormName: string,
  issueTimeUtc: string,
  agency: string = 'IMD'
): Promise<CycloneForecastResult> {
  const res = await fetch(`${API_BASE}/forecast/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      storm_name: stormName,
      issue_time_utc: issueTimeUtc,
      agency,
    }),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Forecast generation failed (${res.status})`);
  }

  return res.json();
}

export async function fetchMethodology(): Promise<Record<string, unknown>> {
  const res = await fetch(`${API_BASE}/methodology`);
  if (!res.ok) {
    throw new Error(`Failed to fetch methodology: ${res.statusText}`);
  }
  return res.json();
}

// ==============================================================================
// Satellite Dataset Explorer API Calls
// ==============================================================================

export async function fetchDatasetSummary() {
  const res = await fetch(`${API_BASE}/dataset/summary`);
  if (!res.ok) {
    throw new Error(`Failed to fetch dataset summary: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchDatasetSamples() {
  const res = await fetch(`${API_BASE}/dataset/samples`);
  if (!res.ok) {
    throw new Error(`Failed to fetch dataset samples: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchDatasetSampleDetail(stormOrId: string) {
  const res = await fetch(`${API_BASE}/dataset/samples/${encodeURIComponent(stormOrId)}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch sample detail for '${stormOrId}': ${res.statusText}`);
  }
  return res.json();
}

export async function fetchDatasetPixel(
  storm: string,
  channel: string,
  x: number,
  y: number
) {
  const res = await fetch(
    `${API_BASE}/dataset/pixel?storm=${encodeURIComponent(storm)}&channel=${encodeURIComponent(
      channel
    )}&x=${x}&y=${y}`
  );
  if (!res.ok) {
    throw new Error(`Failed to probe pixel: ${res.statusText}`);
  }
  return res.json();
}

export function getDatasetPreviewUrl(
  storm: string,
  channel: string,
  colormap: string,
  composite: boolean = false,
  highlightClamped: boolean = false
): string {
  const compStr = composite ? '&composite=true' : '';
  const clampStr = highlightClamped ? '&highlight_clamped=true' : '';
  return `${API_BASE}/dataset/preview/${encodeURIComponent(storm)}/${encodeURIComponent(
    channel
  )}/${encodeURIComponent(colormap)}?format=png${compStr}${clampStr}`;
}

export function getManifestExportUrl(): string {
  return `${API_BASE}/dataset/export/manifest.json`;
}

export function getMetadataCsvExportUrl(): string {
  return `${API_BASE}/dataset/export/metadata.csv`;
}

// ============================================================================
// AI Model Lab API Services
// ============================================================================

export async function fetchMLRegistry(): Promise<any> {
  const res = await fetch(`${API_BASE}/ml/registry`);
  if (!res.ok) {
    throw new Error(`Failed to fetch ML model registry: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchMLModelDetail(modelId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/ml/models/${encodeURIComponent(modelId)}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch detail for model '${modelId}': ${res.statusText}`);
  }
  return res.json();
}

export async function runSatelliteCNNInference(
  stormName: string,
  channel: string = 'TIR-1'
): Promise<any> {
  const res = await fetch(`${API_BASE}/ml/infer/satellite_cnn`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ storm_name: stormName, channel }),
  });
  if (!res.ok) {
    throw new Error(`Satellite CNN inference failed: ${res.statusText}`);
  }
  return res.json();
}

export async function runConvLSTMInference(
  sequenceId?: string,
  leadTimeHours: number = 3.0
): Promise<any> {
  const res = await fetch(`${API_BASE}/ml/infer/convlstm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sequence_id: sequenceId, lead_time_hours: leadTimeHours }),
  });
  if (!res.ok) {
    throw new Error(`ConvLSTM inference failed: ${res.statusText}`);
  }
  return res.json();
}

export async function runTrackGRUInference(stormName: string): Promise<any> {
  const res = await fetch(`${API_BASE}/ml/infer/track_gru`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ storm_name: stormName }),
  });
  if (!res.ok) {
    throw new Error(`Track GRU inference request failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchConvLSTMSequences(split: string = 'test'): Promise<any> {
  const res = await fetch(`${API_BASE}/ml/convlstm/sequences?split=${encodeURIComponent(split)}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch ConvLSTM sequences: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchINSATEvaluations(): Promise<any> {
  const res = await fetch(`${API_BASE}/ml/insat_evaluations`);
  if (!res.ok) {
    throw new Error(`Failed to fetch INSAT evaluations ledger: ${res.statusText}`);
  }
  return res.json();
}

