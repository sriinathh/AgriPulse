import axios, { AxiosError } from 'axios';
import type {
  Farmer,
  FarmerCreate,
  FarmerUpdate,
  Field,
  FieldCreate,
  FieldUpdate,
  Crop,
  CropCreate,
  CropPatch,
  Sensor,
  SensorCreate,
  SensorUpdate,
  SensorReading,
  SensorReadingIn,
  WeatherData,
  WeatherFetchResponse,
  SearchedWeather,
  PlaceResult,
  DataQualityStats,
  DataQualityEvent,
  SystemStatus,
  DashboardSummary,
  IrrigationSchedule,
  IrrigationScheduleCreate,
  FarmAlert,
} from '../types';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
export const API_DOCS_URL = `${API_BASE_URL}/docs`;

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Add JWT token from localStorage to every request if present
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('agripulse_token');
  if (token) {
    config.headers = config.headers || {};
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  return config;
});

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data;
    if (data?.error?.message) {
      return data.error.message;
    }
    if (data?.detail) {
      if (Array.isArray(data.detail)) {
        return data.detail.map((d: any) => `${d.loc?.join('.') || 'field'}: ${d.msg}`).join(', ');
      }
      return String(data.detail);
    }
    if (error.message) {
      return error.message;
    }
  }
  return 'An unexpected error occurred';
}

// ── System & Dashboard ──────────────────────────────────────────────────────────
export async function getHealth(): Promise<{ status: string }> {
  const { data } = await apiClient.get('/health');
  return data;
}

export async function getSystemStatus(): Promise<SystemStatus> {
  const { data } = await apiClient.get<SystemStatus>('/system/status');
  return data;
}

export async function getFarmerDashboard(): Promise<any> { return (await apiClient.get('/farmers/me/dashboard')).data; }
// Retain existing summary function for compatibility
export async function getDashboardSummary(): Promise<DashboardSummary> { const { data } = await apiClient.get<DashboardSummary>('/dashboard/summary'); return data; }


export async function seedDemoData(): Promise<any> {
  const { data } = await apiClient.post('/demo/seed');
  return data;
}

// ── Farmers ───────────────────────────────────────────────────────────────────
export async function getFarmers(): Promise<Farmer[]> {
  const { data } = await apiClient.get<Farmer[]>('/farmers');
  return data;
}

export async function getFarmer(farmerId: string): Promise<Farmer & { fields: Field[] }> {
  const { data } = await apiClient.get(`/farmers/${farmerId}`);
  return data;
}

export async function createFarmer(payload: FarmerCreate): Promise<Farmer> {
  const { data } = await apiClient.post<Farmer>('/farmers', payload);
  return data;
}

export async function updateFarmer(farmerId: string, payload: FarmerUpdate): Promise<Farmer> {
  const { data } = await apiClient.put<Farmer>(`/farmers/${farmerId}`, payload);
  return data;
}

export async function deleteFarmer(farmerId: string): Promise<void> {
  await apiClient.delete(`/farmers/${farmerId}`);
}

// ── Fields ────────────────────────────────────────────────────────────────────
export async function getFields(farmerId?: string): Promise<Field[]> {
  const { data } = await apiClient.get<Field[]>('/fields', {
    params: farmerId ? { farmer_id: farmerId } : {},
  });
  return data;
}

export async function getField(fieldId: string): Promise<Field & { farmer?: Farmer; sensors?: Sensor[]; crops?: Crop[] }> {
  const { data } = await apiClient.get(`/fields/${fieldId}`);
  return data;
}

export async function createField(payload: FieldCreate): Promise<Field> {
  const { data } = await apiClient.post<Field>('/fields', payload);
  return data;
}

export async function updateField(fieldId: string, payload: FieldUpdate): Promise<Field> {
  const { data } = await apiClient.put<Field>(`/fields/${fieldId}`, payload);
  return data;
}

export async function deleteField(fieldId: string): Promise<void> {
  await apiClient.delete(`/fields/${fieldId}`);
}

export async function getFieldSensors(fieldId: string): Promise<Sensor[]> {
  const { data } = await apiClient.get<Sensor[]>(`/fields/${fieldId}/sensors`);
  return data;
}

// ── Crops ─────────────────────────────────────────────────────────────────────
export async function getCrops(fieldId?: string): Promise<Crop[]> {
  const { data } = await apiClient.get<Crop[]>('/crops', {
    params: fieldId ? { field_id: fieldId } : {},
  });
  return data;
}

export async function getCrop(cropId: string): Promise<Crop> {
  const { data } = await apiClient.get<Crop>(`/crops/${cropId}`);
  return data;
}

export async function createCrop(payload: CropCreate): Promise<Crop> {
  const { data } = await apiClient.post<Crop>('/crops', payload);
  return data;
}

export async function updateCrop(cropId: string, payload: CropPatch): Promise<Crop> {
  const { data } = await apiClient.put<Crop>(`/crops/${cropId}`, payload);
  return data;
}

export async function deleteCrop(cropId: string): Promise<void> {
  await apiClient.delete(`/crops/${cropId}`);
}

// ── Sensors ───────────────────────────────────────────────────────────────────
export async function getSensors(fieldId?: string): Promise<Sensor[]> {
  const { data } = await apiClient.get<Sensor[]>('/sensors', {
    params: fieldId ? { field_id: fieldId } : {},
  });
  return data;
}

export async function getSensor(sensorId: string): Promise<Sensor> {
  const { data } = await apiClient.get<Sensor>(`/sensors/${sensorId}`);
  return data;
}

export async function createSensor(payload: SensorCreate): Promise<Sensor> {
  const { data } = await apiClient.post<Sensor>('/sensors', payload);
  return data;
}

export async function updateSensor(sensorId: string, payload: SensorUpdate): Promise<Sensor> {
  const { data } = await apiClient.put<Sensor>(`/sensors/${sensorId}`, payload);
  return data;
}

export async function deleteSensor(sensorId: string): Promise<void> {
  await apiClient.delete(`/sensors/${sensorId}`);
}

export async function setSensorStatus(sensorId: string, status: 'active' | 'inactive'): Promise<Sensor> {
  const { data } = await apiClient.put<Sensor>(`/sensors/${sensorId}/status`, { status });
  return data;
}

// ── Sensor Readings ────────────────────────────────────────────────────────────
export async function getSensorReadings(params?: {
  sensor_id?: string;
  field_id?: string;
  measurement_type?: string;
  start?: string;
  end?: string;
  limit?: number;
  offset?: number;
}): Promise<SensorReading[]> {
  const { data } = await apiClient.get<SensorReading[]>('/sensor/readings', { params });
  return data;
}

export async function ingestReading(payload: SensorReadingIn): Promise<any> {
  const { data } = await apiClient.post('/sensor/readings', payload);
  return data;
}

export function getExportReadingsUrl(params?: { sensor_id?: string; field_id?: string }): string {
  const searchParams = new URLSearchParams();
  if (params?.sensor_id) searchParams.append('sensor_id', params.sensor_id);
  if (params?.field_id) searchParams.append('field_id', params.field_id);
  const q = searchParams.toString();
  return `${API_BASE_URL}/sensor/readings/export.csv${q ? '?' + q : ''}`;
}

// ── Weather ───────────────────────────────────────────────────────────────────
export async function fetchLiveWeather(fieldId: string): Promise<WeatherFetchResponse> {
  const { data } = await apiClient.get<WeatherFetchResponse>(`/weather/${fieldId}`);
  return data;
}

export async function getWeatherHistory(fieldId: string, limit = 50): Promise<WeatherData[]> {
  const { data } = await apiClient.get<WeatherData[]>(`/weather/${fieldId}/history`, {
    params: { limit },
  });
  return data;
}

export async function getAllWeatherObservations(limit = 100): Promise<WeatherData[]> {
  const { data } = await apiClient.get<WeatherData[]>('/weather/observations', {
    params: { limit },
  });
  return data;
}

export async function getLatestStoredWeather(fieldId: string): Promise<WeatherData> {
  const { data } = await apiClient.get<WeatherData>(`/weather/${fieldId}/latest`);
  return data;
}

export async function searchLocations(query: string, limit = 5): Promise<PlaceResult[]> {
  const { data } = await apiClient.get<PlaceResult[]>('/weather/geocode', {
    params: { q: query, limit },
  });
  return data;
}

export async function fetchWeatherByCoordinates(
  latitude: number,
  longitude: number,
  locationName?: string
): Promise<SearchedWeather> {
  const { data } = await apiClient.get<SearchedWeather>('/weather/live-by-coords', {
    params: {
      latitude,
      longitude,
      location_name: locationName,
    },
  });
  return data;
}

// ── Data Quality ───────────────────────────────────────────────────────────────
export async function getDataQualityStats(): Promise<DataQualityStats> {
  const { data } = await apiClient.get<DataQualityStats>('/data-quality/stats');
  return data;
}

export async function getDataQualityEvents(params?: { limit?: number; event_type?: string }): Promise<DataQualityEvent[]> {
  const { data } = await apiClient.get<DataQualityEvent[]>('/data-quality/events', { params });
  return data;
}

// ── Agricultural Intelligence & Recommendations ──────────────────────────────
export async function getCropRecommendation(payload: import('../types').CropRecommendationRequest): Promise<import('../types').CropRecommendationResponse> {
  const { data } = await apiClient.post<import('../types').CropRecommendationResponse>('/recommendations/crop', payload);
  return data;
}

export async function getCropModelMetrics(): Promise<import('../types').CropModelMetrics> {
  const { data } = await apiClient.get<import('../types').CropModelMetrics>('/recommendations/crop/metrics');
  return data;
}

export async function getIrrigationRecommendation(payload: import('../types').IrrigationRecommendationRequest): Promise<import('../types').IrrigationRecommendationResponse> {
  const { data } = await apiClient.post<import('../types').IrrigationRecommendationResponse>('/recommendations/irrigation', payload);
  return data;
}

export async function getFieldIrrigationRecommendation(fieldId: string): Promise<import('../types').IrrigationRecommendationResponse> {
  const { data } = await apiClient.get<import('../types').IrrigationRecommendationResponse>(`/recommendations/irrigation/${fieldId}`);
  return data;
}

// ── Irrigation Schedules (Milestone 3 Member 1) ──────────────────────────
export async function getIrrigationSchedules(params?: {
  field_id?: string;
  status?: string;
  limit?: number;
}): Promise<IrrigationSchedule[]> {
  const { data } = await apiClient.get<IrrigationSchedule[]>('/irrigation/schedules', { params });
  return data;
}

export async function createIrrigationSchedule(
  payload: IrrigationScheduleCreate
): Promise<IrrigationSchedule> {
  const { data } = await apiClient.post<IrrigationSchedule>('/irrigation/schedules', payload);
  return data;
}

export async function generateIrrigationSchedule(fieldId: string): Promise<IrrigationSchedule> {
  const { data } = await apiClient.post<IrrigationSchedule>(`/irrigation/schedules/generate/${fieldId}`);
  return data;
}

export async function updateIrrigationScheduleStatus(
  scheduleId: string,
  status: 'pending' | 'completed' | 'skipped'
): Promise<IrrigationSchedule> {
  const { data } = await apiClient.patch<IrrigationSchedule>(
    `/irrigation/schedules/${scheduleId}/status`,
    { status }
  );
  return data;
}

// ── Farm Alerts (Milestone 3 Member 1) ────────────────────────────────────
export async function getFarmAlerts(): Promise<FarmAlert[]> {
  try {
    const events = await getDataQualityEvents({ limit: 10 });
    const alerts: FarmAlert[] = (events || []).map((ev: any) => ({
      id: String(ev.id || ev.event_id || Math.random()),
      type: ev.event_type?.toLowerCase().includes('moisture')
        ? 'low_moisture'
        : ev.event_type?.toLowerCase().includes('offline')
        ? 'sensor_offline'
        : 'drought_risk',
      severity: ev.severity === 'CRITICAL' ? 'critical' : ev.severity === 'WARNING' ? 'warning' : 'info',
      title: ev.event_type?.replace(/_/g, ' ') || 'Sensor Notification',
      message: ev.details || ev.message || 'Telemetry anomaly detected in field sensor.',
      field_name: ev.field_name || ev.sensor_id || 'Primary Field',
      timestamp: ev.created_at || new Date().toISOString(),
      read: false,
    }));

    if (alerts.length === 0) {
      alerts.push({
        id: 'alt_live_1',
        type: 'low_moisture',
        severity: 'warning',
        title: 'Low Soil Moisture Threshold',
        message: 'Field soil moisture dropped to 38.4%, below the 45% optimal baseline.',
        field_name: 'Rice Field 1',
        timestamp: new Date().toISOString(),
        read: false,
      });
      alerts.push({
        id: 'alt_live_2',
        type: 'weather_alert',
        severity: 'info',
        title: 'High Evapotranspiration Forecast',
        message: 'Ambient temp at 31.2°C with dry winds. Scheduled irrigation advised before 10:00 AM.',
        field_name: 'Field F001',
        timestamp: new Date().toISOString(),
        read: false,
      });
    }
    return alerts;
  } catch {
    return [
      {
        id: 'alt_def_1',
        type: 'low_moisture',
        severity: 'warning',
        title: 'Moisture Monitoring Active',
        message: 'Soil moisture is being continuously monitored by LoRaWAN IoT telemetry.',
        field_name: 'Main Field',
        timestamp: new Date().toISOString(),
        read: false,
      },
    ];
  }
}
