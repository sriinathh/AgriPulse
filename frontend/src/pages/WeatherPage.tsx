import React, { useEffect, useRef, useState } from 'react';
import {
  CloudRain,
  Sun,
  Wind,
  Droplets,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  MapPin,
  Clock,
  Search,
  Thermometer,
  Eye,
  X,
  Navigation,
  Gauge,
  Compass,
  Check,
  Info,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import {
  getAllWeatherObservations,
  getWeatherHistory,
  getFields,
  fetchLiveWeather,
  searchLocations,
  fetchWeatherByCoordinates,
  updateField,
  getErrorMessage,
} from '../services/api';
import type { WeatherData, Field, PlaceResult, SearchedWeather } from '../types';

// ─── Source badge ────────────────────────────────────────────────────────────

function SourceBadge({ obs }: { obs: WeatherData }) {
  if (obs.is_mock) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
        🔶 Simulated Data
      </span>
    );
  }
  if (obs.source === 'openweathermap') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
        🌐 Live OpenWeatherMap
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-semibold bg-slate-100 text-slate-600 border border-slate-200">
      📂 Historical Observation
    </span>
  );
}

// ─── Location search popover ──────────────────────────────────────────────────

interface LocationSearchProps {
  onPick: (place: PlaceResult) => void;
}

function LocationSearch({ onPick }: LocationSearchProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<PlaceResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleSearch = async () => {
    if (!query.trim()) return;
    try {
      setSearching(true);
      setSearchError(null);
      const places = await searchLocations(query.trim(), 5);
      setResults(places);
      setOpen(true);
    } catch (err) {
      setSearchError(getErrorMessage(err));
      setResults([]);
      setOpen(false);
    } finally {
      setSearching(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch();
    if (e.key === 'Escape') setOpen(false);
  };

  return (
    <div ref={ref} className="relative w-full max-w-sm">
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400 pointer-events-none" />
          <input
            id="location-search-input"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search city, e.g. Hyderabad, IN"
            className="w-full pl-8 pr-3 py-2 text-xs rounded-xl border border-slate-200 bg-white text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-300 transition"
          />
          {query && (
            <button onClick={() => { setQuery(''); setResults([]); setOpen(false); }} className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
              <X className="w-3 h-3" />
            </button>
          )}
        </div>
        <button
          id="location-search-btn"
          onClick={handleSearch}
          disabled={searching || !query.trim()}
          className="px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-semibold rounded-xl transition"
        >
          {searching ? '…' : 'Search'}
        </button>
      </div>

      {searchError && (
        <p className="mt-1 text-[10px] text-rose-600 flex items-center gap-1">
          <AlertCircle className="w-3 h-3" />{searchError}
        </p>
      )}

      {open && results.length > 0 && (
        <div className="absolute top-full mt-1 left-0 right-0 z-50 bg-white border border-slate-200 rounded-xl shadow-xl overflow-hidden">
          {results.map((p, i) => (
            <button
              key={i}
              className="w-full text-left px-4 py-2.5 hover:bg-blue-50 transition-colors border-b border-slate-100 last:border-0"
              onClick={() => { onPick(p); setOpen(false); setQuery(''); setResults([]); }}
            >
              <div className="text-xs font-semibold text-slate-800">{p.label}</div>
              <div className="text-[10px] text-slate-400 mt-0.5 font-mono">
                {p.latitude.toFixed(4)}°N, {p.longitude.toFixed(4)}°E
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export const WeatherPage: React.FC = () => {
  const [fieldObservations, setFieldObservations] = useState<WeatherData[]>([]);
  const [fields, setFields] = useState<Field[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [selectedField, setSelectedField] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [fetchingLive, setFetchingLive] = useState(false);
  const [pickedPlace, setPickedPlace] = useState<PlaceResult | null>(null);
  const [searchedWeather, setSearchedWeather] = useState<SearchedWeather | null>(null);
  const [searchingWeather, setSearchingWeather] = useState(false);
  const [searchedWeatherError, setSearchedWeatherError] = useState<string | null>(null);
  const [assigningLocation, setAssigningLocation] = useState(false);
  const searchSeq = useRef(0);
  const obsSeq = useRef(0);

  const loadObservations = async (fieldId: string) => {
    const seq = ++obsSeq.current;
    try {
      setLoadingHistory(true);
      if (fieldId) {
        const data = await getWeatherHistory(fieldId, 100);
        if (seq === obsSeq.current) {
          setFieldObservations(data);
        }
      } else {
        const data = await getAllWeatherObservations(100);
        if (seq === obsSeq.current) {
          setFieldObservations(data);
        }
      }
    } catch (err) {
      if (seq === obsSeq.current) {
        setError(getErrorMessage(err));
      }
    } finally {
      if (seq === obsSeq.current) {
        setLoadingHistory(false);
      }
    }
  };

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      setError(null);
      const flds = await getFields();
      setFields(flds);
      const defaultField = flds.length > 0 ? flds[0].field_id : '';
      setSelectedField(defaultField);
      await loadObservations(defaultField);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInitialData();
  }, []);

  const handleClosePreview = () => {
    setPickedPlace(null);
    setSearchedWeather(null);
    setSearchedWeatherError(null);
  };

  const handleFieldChange = async (fieldId: string) => {
    setSelectedField(fieldId);
    handleClosePreview();
    setError(null);
    setSuccess(null);
    await loadObservations(fieldId);
  };

  const handlePickPlace = async (place: PlaceResult) => {
    const seq = ++searchSeq.current;
    setPickedPlace(place);
    setSearchedWeather(null);
    setSearchedWeatherError(null);
    setSearchingWeather(true);
    try {
      const weather = await fetchWeatherByCoordinates(place.latitude, place.longitude, place.label);
      if (seq === searchSeq.current) {
        setSearchedWeather(weather);
      }
    } catch (err) {
      if (seq === searchSeq.current) {
        setSearchedWeatherError(getErrorMessage(err));
      }
    } finally {
      if (seq === searchSeq.current) {
        setSearchingWeather(false);
      }
    }
  };

  const handleAssignSearchedToField = async () => {
    if (!selectedField || !pickedPlace) return;
    const targetField = fields.find((f) => f.field_id === selectedField);
    if (!targetField) return;

    const confirmed = window.confirm(
      `Update field "${targetField.name}" (${targetField.field_id}) location to "${pickedPlace.label}" (${pickedPlace.latitude.toFixed(4)}°N, ${pickedPlace.longitude.toFixed(4)}°E)?\n\nThis will update the field's saved coordinates in PostgreSQL and fetch live weather for the new location.`
    );
    if (!confirmed) return;

    try {
      setAssigningLocation(true);
      setError(null);
      await updateField(selectedField, {
        latitude: pickedPlace.latitude,
        longitude: pickedPlace.longitude,
        location_name: pickedPlace.label,
        city: pickedPlace.name,
        state: pickedPlace.state || undefined,
        country: pickedPlace.country || undefined,
      });
      // Refresh field data from PostgreSQL through API
      const updatedFields = await getFields();
      setFields(updatedFields);

      // Automatically fetch live weather for the updated field using its newly saved coordinates
      const res = await fetchLiveWeather(selectedField);
      const statusText = res.status === 'already_stored' ? 'latest observation confirmed' : 'observation stored';
      const stationText = res.provider_location ? ` [Station: ${res.provider_location}]` : '';
      setSuccess(
        `Field "${targetField.name}" location updated to ${pickedPlace.label}. Live weather saved: ${res.weather.temperature}°C, ${res.weather.humidity}% RH${stationText} (${statusText}).`
      );
      setTimeout(() => setSuccess(null), 8000);
      handleClosePreview();
      await loadObservations(selectedField);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setAssigningLocation(false);
    }
  };

  const handleFetchLive = async () => {
    if (!selectedField) return;
    try {
      setFetchingLive(true);
      setError(null);
      const res = await fetchLiveWeather(selectedField);
      const field = fields.find((f) => f.field_id === selectedField);
      const loc = field?.location_name || field?.city || selectedField;
      const statusText = res.status === 'already_stored' ? 'already stored (latest observation confirmed)' : 'new record stored';
      const stationText = res.provider_location ? ` [Station: ${res.provider_location}]` : '';
      setSuccess(
        `${res.mock ? '🔶 Mock' : '🌐 Live'} observation stored for ${field?.name || selectedField}: ${res.weather.temperature}°C, ${res.weather.humidity}% RH @ ${loc}${stationText} (${statusText})`
      );
      setTimeout(() => setSuccess(null), 7000);
      await loadObservations(selectedField);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setFetchingLive(false);
    }
  };

  const selectedFieldObj = fields.find((f) => f.field_id === selectedField) || null;
  const latest = fieldObservations[0] || null;

  const chartData = [...fieldObservations].reverse().map((o) => ({
    time: new Date(o.timestamp).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }),
    temp: o.temperature,
    humidity: o.humidity,
    rain: o.rainfall,
  }));

  const hasCoordinates = selectedFieldObj?.latitude != null && selectedFieldObj?.longitude != null;

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Weather Intelligence</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time meteorological feeds via OpenWeatherMap — verified geographic coordinates.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            id="fetch-live-weather-btn"
            onClick={handleFetchLive}
            disabled={fetchingLive || !selectedField || !hasCoordinates}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-xl shadow-sm transition disabled:opacity-40"
          >
            <CloudRain className="w-4 h-4" />
            {fetchingLive ? 'Syncing…' : 'Fetch Live Weather'}
          </button>
          <button
            id="refresh-weather-btn"
            onClick={() => loadObservations(selectedField)}
            className="p-2 bg-white hover:bg-slate-50 border border-slate-200 text-slate-600 rounded-xl transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading || loadingHistory ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* ── Alerts ── */}
      {error && (
        <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-500 shrink-0" />
          <span>{error}</span>
        </div>
      )}
      {success && (
        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{success}</span>
        </div>
      )}

      {/* ── Controls Row ── */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm">
        <div className="flex flex-col lg:flex-row gap-4">

          {/* Field selector */}
          <div className="flex items-center gap-2 min-w-0">
            <MapPin className="w-4 h-4 text-slate-400 shrink-0" />
            <span className="text-xs font-semibold text-slate-700 whitespace-nowrap">Monitored Field:</span>
            <select
              id="field-select"
              value={selectedField}
              onChange={(e) => handleFieldChange(e.target.value)}
              className="text-xs px-2 py-2 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-200 min-w-[200px]"
            >
              <option value="">— All Fields —</option>
              {fields.map((f) => (
                <option key={f.field_id} value={f.field_id}>
                  {f.name} ({f.field_id})
                </option>
              ))}
            </select>
          </div>

          {/* Divider */}
          <div className="hidden lg:block w-px bg-slate-100 self-stretch" />

          {/* Location search */}
          <div className="flex items-center gap-2 flex-1">
            <Search className="w-4 h-4 text-slate-400 shrink-0" />
            <span className="text-xs font-semibold text-slate-700 whitespace-nowrap hidden sm:block">Location Search:</span>
            <div className="flex-1">
              <LocationSearch key={selectedField} onPick={handlePickPlace} />
            </div>
          </div>
        </div>

        {/* ── Location & GPS Status Bar ── */}
        <div className="mt-3 pt-3 border-t border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-2 text-[11px]">
          {/* Saved Field GPS */}
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
            {selectedFieldObj ? (
              hasCoordinates ? (
                <>
                  <span className="flex items-center gap-1 text-emerald-700 font-semibold">
                    <Navigation className="w-3.5 h-3.5" /> Saved Field GPS ({selectedFieldObj.name}):
                  </span>
                  <span className="font-mono text-slate-800 font-medium">
                    {selectedFieldObj.latitude?.toFixed(4)}°N, {selectedFieldObj.longitude?.toFixed(4)}°E
                  </span>
                  {selectedFieldObj.location_name && (
                    <span className="text-slate-600">📍 {selectedFieldObj.location_name}</span>
                  )}
                  {selectedFieldObj.city && !selectedFieldObj.location_name?.toLowerCase().includes(selectedFieldObj.city.toLowerCase()) && (
                    <span className="text-slate-500">🏙 {selectedFieldObj.city}</span>
                  )}
                </>
              ) : (
                <span className="flex items-center gap-1 text-amber-600 font-semibold">
                  <AlertCircle className="w-3.5 h-3.5" /> Saved Field GPS ({selectedFieldObj.name}): No coordinates configured in PostgreSQL
                </span>
              )
            ) : (
              <span className="text-slate-400">Select a monitored field to view its configured GPS coordinates.</span>
            )}
          </div>

          {/* Searched Location GPS Badge (Active Search Preview) */}
          {pickedPlace && (
            <div className="flex items-center gap-2 bg-blue-50/90 px-2.5 py-1 rounded-xl border border-blue-200 text-blue-900 shadow-xs">
              <span className="font-semibold flex items-center gap-1 text-blue-800">
                <Search className="w-3 h-3 text-blue-600" /> Searched City GPS:
              </span>
              <span className="font-mono font-medium text-blue-950">
                {pickedPlace.latitude.toFixed(4)}°N, {pickedPlace.longitude.toFixed(4)}°E
              </span>
              <span className="text-blue-700 truncate max-w-[180px]" title={pickedPlace.label}>
                ({pickedPlace.name})
              </span>
              <button
                onClick={handleClosePreview}
                className="text-blue-400 hover:text-blue-700 ml-0.5 p-0.5 rounded hover:bg-blue-100 transition"
                title="Close search preview"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* ── GPS Missing Warning Alert ── */}
      {selectedFieldObj && !hasCoordinates && !pickedPlace && (
        <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-start gap-3 shadow-sm">
          <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="flex-1">
            <h4 className="font-bold text-amber-900">GPS Coordinates Required for Field "{selectedFieldObj.name}"</h4>
            <p className="mt-0.5 text-amber-800 leading-relaxed">
              This field has no geographic coordinates in the database. Live weather observations cannot be queried without valid coordinates.
              Search for your city above and click <strong>"Assign to Field"</strong>, or update coordinates directly on the Fields page.
            </p>
          </div>
        </div>
      )}

      {/* ── Search Fetching / Error Banners ── */}
      {searchingWeather && (
        <div className="p-5 rounded-2xl bg-blue-50/80 border border-blue-200 text-blue-900 flex items-center justify-center gap-3">
          <RefreshCw className="w-4 h-4 text-blue-600 animate-spin" />
          <span className="text-xs font-semibold">Fetching live weather for {pickedPlace?.label}...</span>
        </div>
      )}

      {searchedWeatherError && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>Search error: {searchedWeatherError}</span>
          </div>
          <button onClick={handleClosePreview} className="text-slate-400 hover:text-slate-600 p-1">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* ── Single Primary Weather Card (Strictly One Card Rendered) ── */}
      {searchedWeather && pickedPlace ? (
        /* Preview Card (Search Preview Mode) */
        <div className="bg-gradient-to-br from-slate-900 via-blue-950 to-indigo-950 rounded-2xl p-6 text-white shadow-xl border border-blue-400/30">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-4 border-b border-white/10">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/20 text-blue-300 border border-blue-400/30 flex items-center gap-1.5">
                  <Search className="w-3 h-3 text-blue-400" />
                  Search Preview — Not Stored in Database
                </span>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-400/30">
                  🌐 Live OpenWeatherMap
                </span>
              </div>
              <h2 className="text-xl font-bold mt-2">{pickedPlace.label}</h2>
              <p className="text-xs text-blue-200 mt-1 flex items-center gap-1 font-mono">
                <Compass className="w-3.5 h-3.5 text-blue-400" />
                {searchedWeather.latitude.toFixed(4)}°N, {searchedWeather.longitude.toFixed(4)}°E
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {selectedFieldObj && (
                <button
                  id="assign-location-to-field-btn"
                  onClick={handleAssignSearchedToField}
                  disabled={assigningLocation}
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-xl shadow-sm transition disabled:opacity-50"
                >
                  <Check className="w-3.5 h-3.5" />
                  {assigningLocation ? 'Assigning…' : `Assign to Field "${selectedFieldObj.name}"`}
                </button>
              )}
              <button
                onClick={handleClosePreview}
                className="inline-flex items-center gap-1.5 px-3 py-2 bg-white/10 hover:bg-white/20 text-white text-xs font-medium rounded-xl transition"
                title="Return to field observation"
              >
                <X className="w-3.5 h-3.5" /> Close Preview
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6">
            <div className="bg-white/5 p-4 rounded-xl border border-white/10 hover:bg-white/10 transition">
              <span className="text-xs text-blue-200 block flex items-center gap-1">
                <Thermometer className="w-3 h-3 text-amber-400" /> Temperature
              </span>
              <span className="text-2xl font-bold">{searchedWeather.temperature}°C</span>
              {searchedWeather.condition && (
                <span className="text-[10px] text-blue-300 capitalize block mt-0.5">{searchedWeather.condition}</span>
              )}
            </div>
            <div className="bg-white/5 p-4 rounded-xl border border-white/10 hover:bg-white/10 transition">
              <span className="text-xs text-blue-200 block flex items-center gap-1">
                <Droplets className="w-3 h-3 text-blue-400" /> Humidity
              </span>
              <span className="text-2xl font-bold">{searchedWeather.humidity}%</span>
            </div>
            <div className="bg-white/5 p-4 rounded-xl border border-white/10 hover:bg-white/10 transition">
              <span className="text-xs text-blue-200 block flex items-center gap-1">
                <CloudRain className="w-3 h-3 text-cyan-400" /> Rainfall (1h)
              </span>
              <span className="text-2xl font-bold">{searchedWeather.rainfall} mm</span>
            </div>
            <div className="bg-white/5 p-4 rounded-xl border border-white/10 hover:bg-white/10 transition">
              <span className="text-xs text-blue-200 block flex items-center gap-1">
                <Wind className="w-3 h-3 text-teal-400" /> Wind Speed
              </span>
              <span className="text-2xl font-bold">
                {searchedWeather.wind_speed != null ? `${searchedWeather.wind_speed} m/s` : '—'}
              </span>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap gap-4 text-[11px] text-blue-200/80">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3 text-blue-300" />
              <strong>Observed:</strong>&nbsp;{new Date(searchedWeather.timestamp).toLocaleString()} UTC (provider observation)
            </span>
            <span className="flex items-center gap-1">
              <Eye className="w-3 h-3 text-blue-300" />
              <strong>Fetched:</strong>&nbsp;{new Date(searchedWeather.fetched_at).toLocaleString()} (API call time)
            </span>
          </div>
        </div>
      ) : latest ? (
        /* Stored Field Observation Card (Field Mode) */
        <div className="bg-gradient-to-br from-blue-900 via-indigo-900 to-slate-900 rounded-2xl p-6 text-white shadow-xl">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-4 border-b border-white/10">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-400/30 flex items-center gap-1.5">
                  <MapPin className="w-3 h-3 text-indigo-400" />
                  Stored Field Observation
                </span>
                {latest.is_mock ? (
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-amber-400/20 text-amber-300 border border-amber-400/30">
                    🔶 Simulated / Mock
                  </span>
                ) : (
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-400/20 text-emerald-300 border border-emerald-400/30">
                    🌐 Live OpenWeatherMap
                  </span>
                )}
              </div>
              <h2 className="text-xl font-bold mt-2">
                {selectedFieldObj ? `${selectedFieldObj.name} (${latest.field_id})` : `Field ${latest.field_id}`}
              </h2>
              {selectedFieldObj && (
                <p className="text-xs text-blue-200 mt-1 flex items-center gap-1">
                  <MapPin className="w-3 h-3 text-blue-400" />
                  {selectedFieldObj.location_name || selectedFieldObj.city || 'Field Location'}
                  {hasCoordinates && (
                    <span className="font-mono text-blue-300 ml-1">
                      ({selectedFieldObj.latitude?.toFixed(4)}°N, {selectedFieldObj.longitude?.toFixed(4)}°E)
                    </span>
                  )}
                </p>
              )}
            </div>
            <div className="flex items-center gap-2">
              <button
                id="fetch-live-weather-card-btn"
                onClick={handleFetchLive}
                disabled={fetchingLive || !selectedField || !hasCoordinates}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-xl shadow-sm transition disabled:opacity-40"
              >
                <CloudRain className="w-3.5 h-3.5" />
                {fetchingLive ? 'Syncing…' : 'Sync Live Weather'}
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6">
            <div className="bg-white/5 p-4 rounded-xl border border-white/10 hover:bg-white/10 transition">
              <span className="text-xs text-blue-200 block flex items-center gap-1">
                <Thermometer className="w-3 h-3 text-amber-400" /> Temperature
              </span>
              <span className="text-2xl font-bold">{latest.temperature}°C</span>
              {latest.condition && (
                <span className="text-[10px] text-blue-300 capitalize block mt-0.5">{latest.condition}</span>
              )}
            </div>
            <div className="bg-white/5 p-4 rounded-xl border border-white/10 hover:bg-white/10 transition">
              <span className="text-xs text-blue-200 block flex items-center gap-1">
                <Droplets className="w-3 h-3 text-blue-400" /> Humidity
              </span>
              <span className="text-2xl font-bold">{latest.humidity}%</span>
            </div>
            <div className="bg-white/5 p-4 rounded-xl border border-white/10 hover:bg-white/10 transition">
              <span className="text-xs text-blue-200 block flex items-center gap-1">
                <CloudRain className="w-3 h-3 text-cyan-400" /> Rainfall (1h)
              </span>
              <span className="text-2xl font-bold">{latest.rainfall} mm</span>
            </div>
            <div className="bg-white/5 p-4 rounded-xl border border-white/10 hover:bg-white/10 transition">
              <span className="text-xs text-blue-200 block flex items-center gap-1">
                <Wind className="w-3 h-3 text-teal-400" /> Wind Speed
              </span>
              <span className="text-2xl font-bold">
                {latest.wind_speed != null ? `${latest.wind_speed} m/s` : '—'}
              </span>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap gap-4 text-[11px] text-blue-200/80">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3 text-blue-300" />
              <strong>Observed:</strong>&nbsp;{new Date(latest.timestamp).toLocaleString()} UTC (provider observation)
            </span>
            {latest.fetched_at && (
              <span className="flex items-center gap-1">
                <Eye className="w-3 h-3 text-blue-300" />
                <strong>Fetched:</strong>&nbsp;{new Date(latest.fetched_at).toLocaleString()} (backend API call)
              </span>
            )}
          </div>
        </div>
      ) : (
        /* Empty State Primary Card */
        <div className="bg-white rounded-2xl p-8 border border-slate-200/80 shadow-sm text-center">
          <CloudRain className="w-10 h-10 text-emerald-600 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800">
            No Stored Weather Observations for {selectedFieldObj ? `Field "${selectedFieldObj.name}"` : 'Selected Field'}
          </h3>
          <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
            {hasCoordinates
              ? 'This field has valid GPS coordinates in PostgreSQL. Click "Fetch Live Weather" to query and store the latest observation from OpenWeatherMap.'
              : 'This field has no GPS coordinates configured yet. Search for a location above and click "Assign to Field", or edit coordinates on the Fields page.'}
          </p>
          {hasCoordinates && (
            <button
              onClick={handleFetchLive}
              disabled={fetchingLive}
              className="mt-4 inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-xl shadow-sm transition disabled:opacity-40"
            >
              <CloudRain className="w-4 h-4" />
              {fetchingLive ? 'Syncing…' : 'Fetch Live Weather Now'}
            </button>
          )}
        </div>
      )}

      {/* ── Historical Charts Section (Consistent with Display Mode) ── */}
      {searchedWeather && pickedPlace ? (
        /* Preview Mode Notification Banner */
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm text-center">
          <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-3">
            <Info className="w-6 h-6" />
          </div>
          <h4 className="text-sm font-bold text-slate-900">Historical Trends Unavailable for Search Preview</h4>
          <p className="text-xs text-slate-500 mt-1 max-w-lg mx-auto">
            You are viewing a live search preview for <strong>{pickedPlace.label}</strong>. Continuous time-series and sensor correlation charts are stored and tracked for registered monitored fields only.
          </p>
          <div className="mt-4 flex items-center justify-center gap-3">
            <button
              onClick={handleClosePreview}
              className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition"
            >
              Return to {selectedFieldObj?.name || 'Selected Field'} History
            </button>
            {selectedFieldObj && (
              <button
                onClick={handleAssignSearchedToField}
                disabled={assigningLocation}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-xl transition"
              >
                Assign {pickedPlace.name} to Field "{selectedFieldObj.name}"
              </button>
            )}
          </div>
        </div>
      ) : (
        /* Field Mode Charts & Table */
        <>
          {fieldObservations.length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
                <h3 className="font-bold text-slate-900 text-sm mb-1 flex items-center gap-1.5">
                  <Thermometer className="w-4 h-4 text-amber-500" /> Temperature History (°C)
                </h3>
                <p className="text-xs text-slate-400 mb-4">Ambient temperature over time — provider observation timestamps</p>
                <div className="h-56 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                      <XAxis dataKey="time" stroke="#94a3b8" fontSize={10} tickLine={false} tick={{ fill: '#94a3b8' }} />
                      <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '12px', fontSize: '12px' }}
                        formatter={(val: any) => [`${val}°C`, 'Temperature']}
                      />
                      <Line type="monotone" dataKey="temp" stroke="#f59e0b" strokeWidth={2.5} dot={false} activeDot={{ r: 4 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
                <h3 className="font-bold text-slate-900 text-sm mb-1 flex items-center gap-1.5">
                  <Droplets className="w-4 h-4 text-blue-500" /> Humidity & Rainfall
                </h3>
                <p className="text-xs text-slate-400 mb-4">Atmospheric moisture and precipitation over time</p>
                <div className="h-56 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                      <XAxis dataKey="time" stroke="#94a3b8" fontSize={10} tickLine={false} tick={{ fill: '#94a3b8' }} />
                      <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '12px', fontSize: '12px' }}
                        formatter={(val: any, name?: any) => [
                          name === 'humidity' ? `${val}%` : `${val} mm`,
                          name === 'humidity' ? 'Humidity' : 'Rainfall',
                        ]}
                      />
                      <Legend formatter={(v) => v === 'humidity' ? 'Humidity (%)' : 'Rainfall (mm)'} wrapperStyle={{ fontSize: '11px' }} />
                      <Line type="monotone" dataKey="humidity" stroke="#3b82f6" strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
                      <Line type="monotone" dataKey="rain" stroke="#06b6d4" strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          )}

          {/* ── History Table ── */}
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
            <div className="p-4 border-b border-slate-100 flex items-center justify-between">
              <span className="font-bold text-slate-900 text-xs">
                Weather Observation Records ({fieldObservations.length})
              </span>
              {selectedFieldObj && hasCoordinates && (
                <span className="text-[10px] text-slate-400 font-mono">
                  {selectedFieldObj.latitude?.toFixed(4)}°N, {selectedFieldObj.longitude?.toFixed(4)}°E
                </span>
              )}
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-100 text-slate-500 font-semibold uppercase tracking-wider text-[10px]">
                    <th className="py-3 px-4">ID</th>
                    <th className="py-3 px-4">Observation Time (Provider UTC)</th>
                    <th className="py-3 px-4">Fetched At (Backend)</th>
                    <th className="py-3 px-4">Field</th>
                    <th className="py-3 px-4">Temp (°C)</th>
                    <th className="py-3 px-4">Humidity (%)</th>
                    <th className="py-3 px-4">Rain (mm)</th>
                    <th className="py-3 px-4">Wind (m/s)</th>
                    <th className="py-3 px-4">Condition</th>
                    <th className="py-3 px-4">Source</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {fieldObservations.map((o: WeatherData) => (
                    <tr key={o.weather_id} className="hover:bg-slate-50/70 transition-colors">
                      <td className="py-3 px-4 font-mono text-slate-400">{o.weather_id}</td>
                      <td className="py-3 px-4 font-mono text-[11px] text-slate-600">
                        {new Date(o.timestamp).toLocaleString()}
                      </td>
                      <td className="py-3 px-4 font-mono text-[11px] text-slate-400">
                        {o.fetched_at ? new Date(o.fetched_at).toLocaleString() : '—'}
                      </td>
                      <td className="py-3 px-4 font-mono font-medium text-emerald-700">{o.field_id}</td>
                      <td className="py-3 px-4 font-bold text-slate-900">{o.temperature}°C</td>
                      <td className="py-3 px-4 text-slate-600">{o.humidity}%</td>
                      <td className="py-3 px-4 text-slate-600">{o.rainfall} mm</td>
                      <td className="py-3 px-4 text-slate-600">{o.wind_speed ?? '—'}</td>
                      <td className="py-3 px-4 text-slate-600 capitalize">{o.condition || '—'}</td>
                      <td className="py-3 px-4">
                        <SourceBadge obs={o} />
                      </td>
                    </tr>
                  ))}
                  {fieldObservations.length === 0 && !loading && (
                    <tr>
                      <td colSpan={10} className="text-center py-12 text-slate-400">
                        <div className="flex flex-col items-center gap-2">
                          <CloudRain className="w-8 h-8 opacity-30" />
                          {!hasCoordinates && selectedField
                            ? 'This field has no GPS coordinates. Edit the field to add latitude and longitude first.'
                            : 'No observations yet. Select a field with GPS and click "Fetch Live Weather".'}
                        </div>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
