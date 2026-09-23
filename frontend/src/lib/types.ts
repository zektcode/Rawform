export type Severity = "low" | "medium" | "high";

export interface Finding {
  category: string;
  title: string;
  severity: Severity;
  confidence: number;
  frequency_range: [number, number] | null;
  time_range: [number, number] | null;
  evidence: string[];
  explanation: string;
  recommendations: string[];
}

export interface BandEnergy {
  range_hz: [number, number];
  label?: string;
  energy_db: number;
  relative_energy: number;
}

export interface AnalysisResult {
  metadata: {
    filename: string;
    duration_seconds: number;
    sample_rate: number;
    bit_depth: number | null;
    channels: number;
    format: string;
    subtype: string | null;
    file_size_bytes: number;
    bpm: number | null;
    bpm_confidence: number;
    bpm_note: string | null;
    key: string | null;
    key_confidence: number;
    key_note: string | null;
  };
  loudness: {
    integrated_lufs: number | null;
    loudness_range_lu: number | null;
    momentary_lufs_timeseries: { time_s: number[]; lufs: (number | null)[] } | null;
    short_term_lufs_timeseries: { time_s: number[]; lufs: (number | null)[] } | null;
    rms_dbfs: number | null;
    sample_peak_dbfs: number | null;
    true_peak_dbtp: number | null;
    true_peak_headroom_db: number | null;
    peak_to_lufs_db: number | null;
    findings_notes: string[];
  };
  dynamics: {
    crest_factor_db: number | null;
    peak_to_rms_db: number | null;
    rms_over_time: { time_s: number[]; rms_dbfs: number[] } | null;
    dynamic_variation_db: number | null;
    notes: string[];
  };
  spectrum: {
    bands: BandEnergy[];
    averaged_spectrum: { frequencies_hz: number[]; magnitude_db: number[] } | null;
    spectral_centroid_hz: number | null;
    spectral_rolloff_hz: number | null;
    spectral_flatness: number | null;
    spectral_slope: number | null;
    spectral_flux_mean: number | null;
    spectrum_over_time: { time_s: number[]; band_labels: string[]; band_energy_db: number[][] } | null;
    notes: string[];
  };
  low_end: {
    bands: BandEnergy[];
    sub_energy_relative: number | null;
    bass_energy_relative: number | null;
    low_mid_energy_relative: number | null;
    low_frequency_stereo_correlation: number | null;
    low_frequency_mono_compatible: boolean | null;
    energy_consistency: number | null;
    dominant_region_hz: [number, number] | null;
    notes: string[];
  };
  kick_bass: {
    kick_count: number;
    kick_detection_confidence: number;
    kick_times_s: number[];
    kick_fundamental_hz_median: number | null;
    bass_sustain_relative_energy: number | null;
    kick_bass_overlap_events: { time_s: number; frequency_range_hz: [number, number]; relative_intensity: number }[];
    overall_overlap_confidence: number;
    notes: string[];
  };
  stereo: {
    is_stereo: boolean;
    left_rms_dbfs: number | null;
    right_rms_dbfs: number | null;
    lr_balance_db: number | null;
    phase_correlation: number | null;
    mono_compatible: boolean | null;
    mid_energy_relative: number | null;
    side_energy_relative: number | null;
    side_to_mid_ratio_db: number | null;
    correlation_over_time: { time_s: number[]; correlation: number[] } | null;
    width_by_band: { range_hz: [number, number]; side_ratio: number }[] | null;
    notes: string[];
  };
  clipping: {
    clipped_sample_count: number;
    clipping_events: { start_time_s: number; end_time_s: number; sample_count: number }[];
    clipping_detected: boolean;
    peak_linear: number | null;
    intersample_peak_concern: boolean;
    notes: string[];
  };
  transients: {
    transient_count: number;
    transient_times_s: number[];
    transient_density_per_10s: number | null;
    mean_transient_strength: number | null;
    notes: string[];
  };
  resonances: {
    frequency_hz: number;
    amplitude_above_baseline_db: number;
    estimated_bandwidth_hz: number;
    persistence: number;
    confidence: number;
  }[];
  findings: Finding[];
  mix_health: {
    overall_score: number | null;
    category_scores: Record<string, number>;
    methodology_note: string;
  };
  genre: {
    id: string;
    display_name: string;
    subprofile: string;
    subprofile_label: string;
  };
  recommendations: string[];
  processing_time_seconds: number;
  engine_version: string;
  disclaimers: string[];
}

export interface AnalysisRecord {
  id: string;
  filename: string;
  genre: string;
  subprofile: string | null;
  status: "pending" | "processing" | "complete" | "failed";
  progress_stage: string | null;
  progress_pct: number;
  error_message: string | null;
  mix_health_score: number | null;
  duration_seconds: number | null;
  created_at: string;
  result?: AnalysisResult;
}

export interface ComparisonMetric {
  your_track: number | null;
  reference: number | null;
  difference: number | null;
}

export interface ComparisonResult {
  status: "complete" | "pending";
  your_track_status?: string;
  reference_status?: string;
  comparison?: {
    your_track: { filename: string };
    reference: { filename: string };
    loudness: {
      integrated_lufs: ComparisonMetric;
      true_peak_dbtp: ComparisonMetric;
    };
    dynamics: {
      crest_factor_db: ComparisonMetric;
    };
    stereo: {
      phase_correlation: ComparisonMetric;
      side_to_mid_ratio_db: ComparisonMetric;
    };
    frequency_bands: {
      range_hz: [number, number];
      your_track_db: number;
      reference_db: number;
      difference_db: number | null;
    }[];
  };
}
export interface GenreOption {
  id: string;
  display_name: string;
  default_subprofile: string;
  subprofiles: { id: string; label: string }[];
}
