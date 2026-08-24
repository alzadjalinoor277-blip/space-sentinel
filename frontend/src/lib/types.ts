export type Severity = 'NORMAL' | 'INFO' | 'WARNING' | 'CRITICAL';
export type AnomalyStatus = 'ACTIVE' | 'INVESTIGATING' | 'RESOLVED';
export type RiskLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
export type DetectionLayer = 'THRESHOLD' | 'STATISTICAL' | 'ML_ISOLATION_FOREST';
export type ScenarioType =
  | 'NORMAL'
  | 'THERMAL_EVENT'
  | 'POWER_INSTABILITY'
  | 'COMMUNICATION_DEGRADATION'
  | 'MULTI_SUBSYSTEM_ANOMALY';
export type Subsystem =
  | 'THERMAL'
  | 'POWER'
  | 'RADIATION'
  | 'COMMUNICATION'
  | 'COMPUTE'
  | 'PROPULSION'
  | 'NAVIGATION';

export interface Spacecraft {
  id: string;
  name: string;
  mission: string;
  status: string;
  orbit: string;
  mission_time_seconds: number;
}

export interface TelemetryPoint {
  timestamp: number;
  temperature_c: number;
  battery_voltage_v: number;
  battery_percent: number;
  power_consumption_w: number;
  radiation_level_msv: number;
  comm_signal_strength_pct: number;
  cpu_load_pct: number;
  memory_usage_pct: number;
  fuel_percent: number;
  altitude_km: number;
  velocity_kms: number;
}

export interface Anomaly {
  id: string;
  timestamp: number;
  subsystem: Subsystem;
  metric: string;
  observed_value: number;
  expected_min: number;
  expected_max: number;
  severity: Severity;
  confidence: number;
  anomaly_score: number;
  detection_layer: DetectionLayer;
  explanation: string;
  recommended_action: string;
  status: AnomalyStatus;
}

export interface RiskBreakdown {
  thermal: number;
  power: number;
  radiation: number;
  communication: number;
  navigation: number;
  propulsion: number;
}

export interface RiskAssessment {
  timestamp: number;
  score: number;
  level: RiskLevel;
  breakdown: RiskBreakdown;
  contributing_anomaly_ids: string[];
  explanation: string;
}

export interface Prediction {
  metric: string;
  subsystem: Subsystem;
  current_value: number;
  threshold: number;
  trend: 'increasing' | 'decreasing' | 'stable';
  trend_rate_per_min: number;
  predicted_value_10min: number;
  confidence: number;
  time_to_threshold_minutes: number | null;
  insight: string;
}

export interface MissionEvent {
  id: string;
  timestamp: number;
  category: string;
  severity: Severity;
  message: string;
}

export interface AIInsight {
  id: string;
  timestamp: number;
  title: string;
  confidence: number;
  analysis: string;
  recommended_action: string;
  related_subsystems: Subsystem[];
  related_anomaly_ids: string[];
}

export interface SimulationStatus {
  running: boolean;
  scenario: ScenarioType;
  elapsed_seconds: number;
  speed: number;
}
