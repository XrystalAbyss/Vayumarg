export interface StormProfile {
  storm_id: string;
  canonical_name: string;
  season_year: number;
  primary_basin: string;
  official_category: string;
  peak_imd_wind_knots: number | null;
  peak_jtwc_wind_knots: number | null;
  min_central_pressure_hpa: number | null;
  total_observations: number;
  start_time_utc: string | null;
  end_time_utc: string | null;
  has_satellite_crop: boolean;
  crop_filename: string | null;
  satellite_sensor: string;
  provenance: string;
}

export interface ObservationPoint {
  observation_time_utc: string;
  iso_time?: string;
  latitude: number;
  longitude: number;
  imd_wind_speed_knots?: number | null;
  imd_central_pressure_hpa?: number | null;
  jtwc_wind_speed_knots?: number | null;
  jtwc_central_pressure_hpa?: number | null;
  wmo_wind_speed_knots?: number | null;
  wmo_central_pressure_hpa?: number | null;
  wind_speed_knots?: number | null;
  central_pressure_hpa?: number | null;
  imd_category: string;
  nature?: string;
}

export interface StormDetail {
  profile: StormProfile;
  observations: ObservationPoint[];
}

export interface SatelliteCropMeta {
  storm_name: string;
  year: number;
  sensor: string;
  crop_filename: string;
  file_size_bytes: number;
  supported_channels: string[];
  grid_resolution_km: number;
  physical_extent_km: number;
  grid_shape: [number, number];
  provenance: string;
  science_disclaimer: string;
}

export interface TemperatureQuantiles {
  min_kelvin: number;
  p10_kelvin: number;
  p25_kelvin: number;
  median_kelvin: number;
  p75_kelvin: number;
  p90_kelvin: number;
  max_kelvin: number;
  mean_kelvin: number;
  std_kelvin: number;
}

export interface ColdCloudAnalytics {
  pixels_under_200k: number;
  area_under_200k_km2: number;
  fraction_under_200k: number;
  pixels_under_220k: number;
  area_under_220k_km2: number;
  fraction_under_220k: number;
  pixels_under_240k: number;
  area_under_240k_km2: number;
  fraction_under_240k: number;
}

export interface RadialRingMetric {
  mean_kelvin: number | null;
  min_kelvin?: number;
  p25_kelvin?: number;
  pixel_count: number;
}

export interface PhysicalCropMetrics {
  channel: string;
  grid_shape: [number, number];
  spatial_resolution_km: number;
  physical_extent_km: [number, number];
  valid_pixels: number;
  total_pixels: number;
  valid_pixel_ratio: number;
  temperature_quantiles_kelvin: TemperatureQuantiles;
  cold_cloud_analytics: ColdCloudAnalytics;
  radial_temperature_profile: Record<string, RadialRingMetric>;
  azimuthal_symmetry_index: number;
  clamped_low_temperature_pixels: number;
  clamped_warning: boolean;
  crop_metadata: Record<string, unknown>;
  storm_name: string;
  satellite_sensor: string;
  crop_filename: string;
  science_disclaimer?: string;
}

export interface ForecastPoint {
  lead_time_hours: number;
  valid_time_utc: string;
  predicted_latitude: number;
  predicted_longitude: number;
  predicted_wind_speed_knots: number;
  predicted_imd_category: string;
  uncertainty_radius_km: number;
}

export interface HindsightVerificationPoint {
  lead_time_hours: number;
  valid_time_utc: string;
  predicted_latitude: number;
  predicted_longitude: number;
  actual_latitude?: number | null;
  actual_longitude?: number | null;
  track_error_km?: number | null;
  predicted_wind_kt: number;
  actual_wind_kt?: number | null;
  wind_error_kt?: number | null;
  actual_category?: string | null;
}

export interface CycloneForecastResult {
  storm_id: string;
  storm_name: string;
  issue_time_utc: string;
  input_observation_count: number;
  current_latitude: number;
  current_longitude: number;
  current_wind_speed_knots: number | null;
  current_imd_category: string | null;
  estimated_speed_kmh: number;
  estimated_bearing_deg: number;
  forecast_points: ForecastPoint[];
  verification: HindsightVerificationPoint[];
  methodology: string;
  limitations: string;
}

export interface SystemHealth {
  status: string;
  service: string;
  system_time_utc: string;
  database_backend: string;
  satellite_provider: string;
  verified_storms_loaded: number;
  available_satellite_crops: number;
  license: string;
}

export type DatasetColormap = 'thermal_ir' | 'grayscale_inv' | 'dvorak_bd' | 'water_vapor';

export interface GroundTruthObs {
  agency: string;
  averaging_period: string;
  wind_speed_knots: number | null;
  central_pressure_hpa: number | null;
  cyclone_category: string | null;
  reference_timestamp_utc: string;
  latitude: number;
  longitude: number;
  is_retrospective_best_track: boolean;
  is_primary_target: boolean;
}

export interface ColdCloudFraction {
  threshold_k: number;
  threshold_celsius: number;
  pixel_count: number;
  fraction_of_valid: number;
  fraction_of_total: number;
  scientific_justification: string;
}

export interface ChannelSummary {
  min_tb_k: number | null;
  min_non_clamped_tb_k: number | null;
  max_tb_k: number | null;
  mean_tb_k: number | null;
  clamped_fraction: number;
  valid_fraction: number;
  cold_cloud_fractions: ColdCloudFraction[];
}

export interface DatasetSampleItem {
  crop_id: string;
  storm_name: string;
  canonical_storm_sid: string;
  season_year: number;
  ocean_basin: string;
  satellite: string;
  sensor: string;
  product_code: string;
  source_filename: string;
  source_sha256: string;
  crop_filename: string;
  crop_sha256: string;
  verification_status: string;
  acquisition_start_utc: string;
  estimated_local_scan_time_utc: string;
  scan_time_uncertainty: string;
  crop_extent_km: number;
  target_grid_spacing_km: number;
  grid_dimensions: [number, number];
  total_pixels: number;
  center_latitude: number;
  center_longitude: number;
  available_channels: string[];
  channel_resolutions_km: Record<string, number>;
  primary_imd_eligible: boolean;
  primary_imd_observation: GroundTruthObs | null;
  secondary_jtwc_observation: GroundTruthObs | null;
  dana_ineligibility_notice: string | null;
  exclusion_reason: string | null;
  model_eligibility: Record<string, boolean>;
  preview_urls: Record<string, Record<string, string>>;
  channel_summaries: Record<string, ChannelSummary>;
}

export interface RadialProfileBin {
  bin_name: string;
  inner_radius_km: number;
  outer_radius_km: number;
  pixel_count: number;
  valid_pixel_count: number;
  clamped_pixel_count: number;
  mean_tb_k: number | null;
  min_tb_k: number | null;
  p25_tb_k: number | null;
  p50_tb_k: number | null;
  p75_tb_k: number | null;
  std_tb_k: number | null;
}

export interface SymmetryMetrics {
  quadrant_means_k?: Record<string, number>;
  quadrant_cold_fractions?: Record<string, number>;
  azimuthal_std_k?: number;
  azimuthal_asymmetry_index?: number;
  core_radius_km?: number;
  scientific_disclaimer?: string;
}

export interface GradientStatistics {
  mean_k_per_km?: number;
  median_k_per_km?: number;
  max_k_per_km?: number;
  p95_k_per_km?: number;
  computation_method?: string;
}

export interface ChannelAnalyticsDetail {
  channel_name: string;
  total_pixels: number;
  valid_pixels: number;
  valid_fraction: number;
  missing_pixels: number;
  missing_fraction: number;
  clamped_pixels: number;
  clamped_fraction: number;
  lut_boundary_kelvin: number;
  is_lut_censored: boolean;
  min_tb_k: number;
  min_non_clamped_tb_k: number;
  max_tb_k: number;
  mean_tb_k: number;
  std_tb_k: number;
  percentiles_tb_k: {
    p10: number;
    p25: number;
    p50: number;
    p75: number;
    p90: number;
  };
  cold_cloud_fractions: ColdCloudFraction[];
  radial_profile: RadialProfileBin[];
  symmetry_metrics?: SymmetryMetrics;
  gradient_statistics?: GradientStatistics;
  azimuthal_asymmetry_index?: number;
  thermal_gradient_k_per_km?: number;
  clamped_boundary_warning?: string | null;
}

export interface DatasetSampleDetail {
  record: DatasetSampleItem;
  channels: Record<
    string,
    {
      channel_name: string;
      native_resolution_km: number;
      delivered_resolution_km: number;
      analytics: ChannelAnalyticsDetail;
    }
  >;
  grid: {
    shape: [number, number];
    total_pixels: number;
    extent_km: number;
    spacing_km: number;
    center_coord: [number, number];
  };
  scientific_integrity: {
    source_sha256: string;
    crop_sha256: string;
    verification_status: string;
    is_calibrated_insat_l1b: boolean;
    dana_policy: string | null;
  };
}

export interface DatasetSummary {
  physical_observations_count: number;
  calibrated_preview_variations_count: number;
  authentic_storms: string[];
  sensor_platforms: string[];
  ocean_basins: string[];
  supported_channels: string[];
  supported_colormaps: string[];
  verified_crops_status: string;
  raw_archive_audit: {
    unregistered_raw_hdf5: Array<{
      storm_name: string;
      filename: string;
      size_bytes: number;
      status: string;
      note: string;
    }>;
    incomplete_downloads: Array<{
      storm_name: string;
      filename: string;
      size_bytes: number;
      status: string;
      note: string;
    }>;
  };
  scientific_disclaimer: string;
}

export interface PixelProbeResult {
  storm: string;
  channel: string;
  pixel_coord: { x: number; y: number };
  distance_from_center_km: number;
  temperature_kelvin: number | null;
  temperature_celsius: number | null;
  is_valid: boolean;
  is_lower_lut_clamped: boolean;
  lut_boundary_k: number;
}

// ============================================================================
// AI Model Lab & Scientific Inference Types
// ============================================================================

export type MLInferenceState =
  | 'VERIFIED_EXPERIMENTAL'
  | 'UNVERIFIED_DATA'
  | 'MODEL_UNAVAILABLE'
  | 'INPUT_INCOMPATIBLE'
  | 'INFERENCE_ERROR';

export interface MLModelMeta {
  model_id: string;
  name: string;
  category: string;
  architecture: string;
  checkpoint_path: string | null;
  trusted_sha256: string | null;
  actual_sha256: string | null;
  checksum_verified: boolean;
  status: MLInferenceState;
  inference_available: boolean;
  training_data_source: string;
  training_storm_count: number;
  input_modality: string;
  label_convention: string;
  evaluation_status: string;
  benchmark_metrics: Record<string, any>;
  baseline_comparison: Record<string, any>;
  insat_cross_domain_findings?: Record<string, any>;
  scientific_limitations: string[];
}

export interface MLRegistryResponse {
  status: string;
  hardware: {
    cuda_available: boolean;
    device_name: string;
    total_vram_mb: number;
    torch_version: string;
  };
  models: {
    satellite_cnn: MLModelMeta;
    convlstm: MLModelMeta;
    track_gru: MLModelMeta;
  };
}

export interface CNNInferenceResponse {
  status: MLInferenceState;
  model_id: string;
  model_name: string;
  storm_name: string;
  channel: string;
  native_label_convention: string;
  predicted_1min_wind_knots: number;
  averaging_period_note: string;
  classifier_predicted_bin: string;
  regression_implied_bin: string;
  heads_in_agreement: boolean;
  head_disagreement_note?: string | null;
  predicted_category_label: string;
  category_probabilities: Record<string, number>;
  estimated_uncertainty_kt: number;
  inference_latency_ms: number;
  source_domain: string;
  scientific_limitations: string;
  message?: string;
}

export interface ConvLSTMInferenceResponse {
  status: MLInferenceState;
  model_id: string;
  sequence_id: string;
  storm_id: string;
  split: string;
  lead_time_hours: number;
  actual_elapsed_seconds?: number;
  actual_elapsed_hours?: number;
  sequence_cadence_note?: string;
  input_frames: string[];
  target_frame_url: string | null;
  past_observed_winds_kt: number[];
  ground_truth_target_wind_kt: number;
  predicted_future_wind_kt: number;
  prediction_absolute_error_kt: number;
  persistence_baseline_error_kt: number;
  reconstructed_next_frame_b64: string | null;
  inference_latency_ms: number;
  scientific_limitations: string[];
  message?: string;
}

export interface TrackForecastItem {
  horizon_h: number;
  gru_predicted: {
    latitude: number;
    longitude: number;
    dx_km: number;
    dy_km: number;
    displacement_total_km: number;
    wind_speed_kt: number;
  };
  geodesic_baseline: {
    latitude: number;
    longitude: number;
    dx_km: number;
    dy_km: number;
    displacement_total_km: number;
    wind_speed_kt: number;
  };
  hybrid_predicted?: {
    latitude: number;
    longitude: number;
    dx_km: number;
    dy_km: number;
    displacement_total_km: number;
    wind_speed_kt: number;
  };
  ground_truth?: {
    latitude: number;
    longitude: number;
    wind_speed_kt: number;
  };
  verification?: {
    gru_track_error_km: number;
    geodesic_track_error_km: number;
    hybrid_track_error_km?: number;
    hybrid_improvement_over_geodesic_km?: number;
    stationary_track_error_km: number;
    gru_wind_error_kt: number;
    persistence_wind_error_kt: number;
    skill_score_vs_geodesic: number;
  };
}

export interface TrackGRUInferenceResponse {
  status: MLInferenceState;
  model_id: string;
  storm_name: string;
  message?: string;
  issue_time?: string;
  observation_index?: number;
  total_fixes?: number;
  forecast_result?: {
    model_id: string;
    model_type: string;
    sha256: string;
    origin_fix: {
      latitude: number;
      longitude: number;
      wind_speed_kt: number;
    };
    horizons: number[];
    forecasts: TrackForecastItem[];
  };
  geodesic_baseline?: {
    status: string;
    endpoint: string;
    methodology: string;
    leakage_protection: string;
  };
  scientific_baseline_comparison?: {
    geodesic_extrapolation: string;
    persistence: string;
    notes: string;
  };
}


