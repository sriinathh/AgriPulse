export interface Farmer {
  farmer_id: string;
  name: string;
  phone?: string | null;
  email?: string | null;
  is_demo?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface FarmerCreate {
  farmer_id?: string;
  name: string;
  phone?: string;
  email?: string;
}

export interface FarmerUpdate {
  name?: string;
  phone?: string;
  email?: string;
}

export interface Field {
  field_id: string;
  farmer_id: string;
  name: string;
  location_name?: string | null;
  location?: string | null;
  city?: string | null;
  state?: string | null;
  country?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  crop_type: string;
  area_hectares?: number | null;
  is_demo?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface FieldCreate {
  field_id?: string;
  farmer_id: string;
  name: string;
  location_name?: string;
  city?: string;
  state?: string;
  country?: string;
  latitude?: number;
  longitude?: number;
  crop_type: string;
  area_hectares?: number;
}

export interface FieldUpdate {
  name?: string;
  farmer_id?: string;
  location_name?: string;
  city?: string;
  state?: string;
  country?: string;
  latitude?: number;
  longitude?: number;
  crop_type?: string;
  area_hectares?: number;
}

export interface Crop {
  crop_id: string;
  field_id: string;
  crop_type: string;
  variety?: string | null;
  planting_date?: string | null;
  growth_stage?: string | null;
  notes?: string | null;
  is_demo?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface CropCreate {
  crop_id?: string;
  field_id: string;
  crop_type: string;
  variety?: string;
  planting_date?: string;
  growth_stage?: string;
  notes?: string;
}

export interface CropPatch {
  crop_type?: string;
  variety?: string;
  planting_date?: string;
  growth_stage?: string;
  notes?: string;
  field_id?: string;
}

export interface Sensor {
  sensor_id: string;
  field_id: string;
  sensor_type: string;
  unit?: string | null;
  status: 'active' | 'inactive';
  last_seen_at?: string | null;
  is_simulated?: boolean;
  is_demo?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface SensorCreate {
  sensor_id?: string;
  field_id: string;
  sensor_type?: string;
  unit?: string;
  status?: string;
  is_simulated?: boolean;
}

export interface SensorUpdate {
  field_id?: string;
  sensor_type?: string;
  unit?: string;
  status?: string;
  is_simulated?: boolean;
}

export interface SensorReading {
  reading_id: number;
  sensor_id: string;
  field_id: string;
  timestamp: string;
  soil_moisture?: number | null;
  measurement_type?: string | null;
  value?: number | null;
  unit?: string | null;
  quality_status?: string | null;
  quality_flags?: string | null;
  temperature?: number | null;
  humidity?: number | null;
  soil_ph?: number | null;
  rainfall?: number | null;
  water_level?: number | null;
  flow_rate?: number | null;
  is_simulated?: boolean;
  ingested_at?: string;
}

export interface SensorReadingIn {
  sensor_id: string;
  field_id?: string;
  timestamp?: string;
  soil_moisture?: number;
  measurement_type?: string;
  value?: number;
  unit?: string;
  temperature?: number;
  humidity?: number;
  soil_ph?: number;
  rainfall?: number;
  water_level?: number;
  flow_rate?: number;
  is_simulated?: boolean;
}

export interface WeatherData {
  weather_id: number;
  field_id: string;
  timestamp: string;    // provider observation time (UTC)
  fetched_at?: string | null;  // when our backend called the API
  temperature: number;
  humidity: number;
  rainfall: number;
  wind_speed?: number | null;
  condition?: string | null;
  source: string;
  is_mock: boolean;
}

export interface PlaceResult {
  name: string;
  state?: string | null;
  country?: string | null;
  latitude: number;
  longitude: number;
  label: string;
}

export interface WeatherFetchResponse {
  status: string;
  weather: WeatherData;
  mock: boolean;
  requested_coordinates?: { latitude: number; longitude: number } | null;
  provider_coordinates?: { latitude: number; longitude: number } | null;
  provider_location?: string | null;
}

export interface SearchedWeather {
  latitude: number;
  longitude: number;
  location_name?: string | null;
  timestamp: string;
  fetched_at: string;
  temperature: number;
  humidity: number;
  rainfall: number;
  wind_speed?: number | null;
  condition?: string | null;
  source: string;
  is_mock: boolean;
  provider_coordinates?: { latitude: number; longitude: number } | null;
  provider_location?: string | null;
}

export interface DataQualityStats {
  readings_stored: number;
  valid_readings: number;
  simulated_readings: number;
  out_of_order_stored: number;
  ingestion_failures: number;
  invalid_readings: number;
  missing_value_count: number;
  duplicate_count: number;
  out_of_range_count: number;
  invalid_timestamp_count: number;
  weather_observations: number;
  weather_mock_observations: number;
  weather_ingestion_failures: number;
  events_by_type: Record<string, number>;
  events_by_source: Record<string, number>;
  notes: string[];
}

export interface DataQualityEvent {
  event_id: number;
  event_type: string;
  source: string;
  sensor_id?: string | null;
  field_id?: string | null;
  message: string;
  details?: string | null;
  created_at: string;
}

export interface SystemStatus {
  backend: {
    ok: boolean;
    version: string;
    environment: string;
  };
  database: {
    ok: boolean;
    error?: string | null;
    url: string;
  };
  timescaledb: {
    available: boolean;
    version?: string | null;
    hypertables: string[];
    reason?: string | null;
  };
  weather: {
    configured: boolean;
    mock_mode: boolean;
    provider: string;
  };
  mqtt: {
    enabled: boolean;
    configured: boolean;
    connected: boolean;
    broker?: string | null;
    topic?: string | null;
    last_error?: string | null;
  };
  docs: string;
}

export interface DashboardSummary {
  farmers: number;
  fields: number;
  sensors: number;
  active_sensors: number;
  readings_stored: number;
  valid_readings: number;
  simulated_readings: number;
  ingestion_failures: number;
  weather_observations: number;
  timescale_active: boolean;
  latest_readings: SensorReading[];
  latest_weather?: WeatherData | null;
}

export interface CropCandidate {
  crop: string;
  probability: number;
  confidence_pct: number;
}

export interface CropRecommendationRequest {
  N: number;
  P: number;
  K: number;
  temperature: number;
  humidity: number;
  ph: number;
  rainfall: number;
  soil_moisture?: number;
}

export interface CropRecommendationResponse {
  recommended_crop: string;
  confidence: number;
  top_candidates: Array<{ crop: string; probability: number; confidence_pct: number }>;
  agronomic_explanation: string;
  input_parameters: Record<string, number>;
  model_metadata: Record<string, any>;
  limitations: string;
}

export interface CropModelMetrics {
  model_name: string;
  algorithm: string;
  train_samples: number;
  test_samples: number;
  test_accuracy: number;
  macro_f1: number;
  feature_names: string[];
  feature_importances: Record<string, number>;
  trained_at: string;
  notes: string[];
}

export interface IrrigationRecommendationRequest {
  field_id?: string;
  crop_type?: string;
  growth_stage?: string;
  soil_moisture?: number;
  temperature?: number;
  recent_rainfall_mm?: number;
  forecast_rainfall_mm?: number;
}

export interface IrrigationRecommendationResponse {
  action: 'IRRIGATE_IMMEDIATELY' | 'IRRIGATE_LIGHT' | 'MAINTAIN_MONITORING' | 'DEFER_DUE_TO_RAIN';
  recommended_water_mm: number;
  urgency: 'HIGH' | 'MODERATE' | 'LOW' | 'NONE';
  reason: string;
  factors_evaluated: Record<string, any>;
  recommendation_engine: string;
  sensor_freshness: string;
  limitations: string;
}

export interface IrrigationSchedule {
  schedule_id: string;
  field_id: string;
  recommended_date: string;
  recommended_time: string;
  duration_minutes: number;
  water_quantity_liters: number;
  priority?: string | null;
  reason?: string | null;
  status: 'pending' | 'completed' | 'skipped';
  created_at: string;
  updated_at: string;
}

export interface IrrigationScheduleCreate {
  field_id: string;
  recommended_date: string;
  recommended_time: string;
  duration_minutes: number;
  water_quantity_liters: number;
  priority?: string;
  reason?: string;
}

export interface FarmAlert {
  id: string;
  type: 'drought_risk' | 'low_moisture' | 'over_irrigation' | 'sensor_offline' | 'weather_alert';
  severity: 'critical' | 'warning' | 'info';
  title: string;
  message: string;
  field_name?: string;
  timestamp: string;
  read: boolean;
}
export interface FarmerDashboard {
  farmer_name?: string;
  farmer_email?: string;
  total_fields?: number;
  fields_needing_irrigation?: number;
  average_soil_moisture?: number;
  total_water_used_liters?: number;
  weather_summary?: {
    temperature?: number;
    humidity?: number;
    rainfall?: number;
    timestamp?: string;
  } | null;
}
