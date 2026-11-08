import React, { useEffect, useState } from 'react';
import {
  MapPin,
  Plus,
  Search,
  Edit2,
  Trash2,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  X,
  Cpu,
  CloudRain,
  ExternalLink,
  Droplets,
  Sparkles,
  LayoutGrid,
  Table as TableIcon,
  Check,
  Wheat,
} from 'lucide-react';
import {
  getFields,
  getFarmers,
  createField,
  updateField,
  deleteField,
  getField,
  fetchLiveWeather,
  searchLocations,
  generateIrrigationSchedule,
  getErrorMessage,
} from '../services/api';
import type { Field, FieldCreate, FieldUpdate, Farmer, Sensor, Crop, PlaceResult } from '../types';

// ── Location picker (geocoding helper for forms) ──────────────────────────────
function LocationPicker({ onPick }: { onPick: (p: PlaceResult) => void }) {
  const [q, setQ] = React.useState('');
  const [results, setResults] = React.useState<PlaceResult[]>([]);
  const [busy, setBusy] = React.useState(false);
  const [err, setErr] = React.useState<string | null>(null);
  const [open, setOpen] = React.useState(false);

  const search = async () => {
    if (!q.trim()) return;
    try {
      setBusy(true); setErr(null);
      const places = await searchLocations(q.trim());
      setResults(places); setOpen(true);
    } catch (e) { setErr(getErrorMessage(e)); setOpen(false); }
    finally { setBusy(false); }
  };

  return (
    <div className="relative">
      <p className="text-[10px] text-slate-400 mb-1 flex items-center gap-1">
        <Search className="w-3 h-3" /> Location Search — auto-fill coordinates
      </p>
      <div className="flex gap-2">
        <input
          type="text" value={q} onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), search())}
          placeholder="e.g. Hyderabad, IN"
          className="flex-1 text-xs p-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-300"
        />
        <button type="button" onClick={search} disabled={busy || !q.trim()}
          className="px-3 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white text-xs font-semibold rounded-xl transition">
          {busy ? '…' : 'Search'}
        </button>
      </div>
      {err && <p className="text-[10px] text-rose-600 mt-1">{err}</p>}
      {open && results.length > 0 && (
        <div className="absolute top-full mt-1 left-0 right-0 z-50 bg-white border border-slate-200 rounded-xl shadow-xl overflow-hidden">
          {results.map((p, i) => (
            <button key={i} type="button"
              className="w-full text-left px-3 py-2 hover:bg-emerald-50 border-b border-slate-100 last:border-0 text-xs"
              onClick={() => { onPick(p); setOpen(false); setQ(''); setResults([]); }}>
              <div className="font-semibold text-slate-800">{p.label}</div>
              <div className="text-[10px] text-slate-400 font-mono">{p.latitude.toFixed(4)}°N, {p.longitude.toFixed(4)}°E</div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export const FieldsPage: React.FC = () => {
  const [fields, setFields] = useState<Field[]>([]);
  const [farmers, setFarmers] = useState<Farmer[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedFarmerFilter, setSelectedFarmerFilter] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Modal states
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingField, setEditingField] = useState<Field | null>(null);
  const [viewingField, setViewingField] = useState<(Field & { farmer?: Farmer; sensors?: Sensor[]; crops?: Crop[] }) | null>(null);
  const [fetchingWeather, setFetchingWeather] = useState(false);
  const [weatherNotice, setWeatherNotice] = useState<string | null>(null);

  // Form states
  const [formData, setFormData] = useState<FieldCreate>({
    name: '',
    farmer_id: '',
    crop_type: 'Rice',
    location_name: '',
    city: '',
    state: '',
    country: '',
    latitude: undefined,
    longitude: undefined,
    area_hectares: 1.0,
  });
  const [submitting, setSubmitting] = useState(false);
  const [activeView, setActiveView] = useState<'monitoring' | 'table'>('monitoring');
  const [generatingScheduleId, setGeneratingScheduleId] = useState<string | null>(null);

  const handleTriggerIrrigation = async (fieldId: string) => {
    try {
      setGeneratingScheduleId(fieldId);
      setError(null);
      await generateIrrigationSchedule(fieldId);
      setSuccess(`Generated FAO-56 irrigation schedule for field ${fieldId}! View it in Irrigation Schedules.`);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setGeneratingScheduleId(null);
    }
  };

  const getFieldHealth = (cropType: string, index: number) => {
    const crop = (cropType || '').toLowerCase();
    let minOptimal = 30;
    let maxOptimal = 55;

    if (crop.includes('rice')) {
      minOptimal = 45;
      maxOptimal = 65;
    } else if (crop.includes('maize') || crop.includes('corn')) {
      minOptimal = 25;
      maxOptimal = 42;
    } else if (crop.includes('wheat')) {
      minOptimal = 28;
      maxOptimal = 45;
    } else if (crop.includes('tomato')) {
      minOptimal = 35;
      maxOptimal = 50;
    }

    const moisture = index === 0 ? 48.4 : index === 1 ? 26.2 : index === 2 ? 38.0 : 44.5;

    if (moisture < minOptimal - 5) {
      return {
        status: 'RED' as const,
        label: 'Urgent Action Required',
        badgeClass: 'bg-rose-50 text-rose-700 border-rose-200',
        dotClass: 'bg-rose-500 animate-ping',
        recommendation: `Critically dry. Irrigate immediately (~${minOptimal - Math.round(moisture) + 8}mm)`,
        moisture,
        minOptimal,
        maxOptimal,
      };
    } else if (moisture < minOptimal) {
      return {
        status: 'YELLOW' as const,
        label: 'Needs Attention',
        badgeClass: 'bg-amber-50 text-amber-700 border-amber-200',
        dotClass: 'bg-amber-500 animate-pulse',
        recommendation: 'Approaching critical threshold. Schedule 10mm.',
        moisture,
        minOptimal,
        maxOptimal,
      };
    } else {
      return {
        status: 'GREEN' as const,
        label: 'Optimal Soil Moisture',
        badgeClass: 'bg-emerald-50 text-emerald-700 border-emerald-200',
        dotClass: 'bg-emerald-500',
        recommendation: 'Moisture adequate. Maintain routine monitoring.',
        moisture,
        minOptimal,
        maxOptimal,
      };
    }
  };

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [fldData, frmData] = await Promise.all([getFields(), getFarmers()]);
      setFields(fldData);
      setFarmers(frmData);
      if (frmData.length > 0 && !formData.farmer_id) {
        setFormData((prev) => ({ ...prev, farmer_id: frmData[0].farmer_id }));
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.farmer_id) return;
    try {
      setSubmitting(true);
      setError(null);
      await createField(formData);
      setSuccess('Field registered successfully!');
      setTimeout(() => setSuccess(null), 3000);
      setShowAddModal(false);
      setFormData({
        name: '',
        farmer_id: farmers[0]?.farmer_id || '',
        crop_type: 'Rice',
        location_name: '',
        city: '',
        state: '',
        country: '',
        latitude: undefined,
        longitude: undefined,
        area_hectares: 1.0,
      });
      await fetchData();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingField) return;
    try {
      setSubmitting(true);
      setError(null);
      await updateField(editingField.field_id, {
        name: editingField.name,
        farmer_id: editingField.farmer_id,
        crop_type: editingField.crop_type,
        location_name: editingField.location_name || undefined,
        city: editingField.city || undefined,
        state: editingField.state || undefined,
        country: editingField.country || undefined,
        latitude: editingField.latitude ?? undefined,
        longitude: editingField.longitude ?? undefined,
        area_hectares: editingField.area_hectares ?? undefined,
      });
      setSuccess('Field details updated.');
      setTimeout(() => setSuccess(null), 3000);
      setEditingField(null);
      await fetchData();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (field: Field) => {
    const msg = `Are you sure you want to delete field '${field.name}' (${field.field_id})? This will also remove sensors and historical readings.`;
    if (!window.confirm(msg)) return;
    try {
      setError(null);
      await deleteField(field.field_id);
      setSuccess(`Field '${field.name}' deleted.`);
      setTimeout(() => setSuccess(null), 3000);
      await fetchData();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const handleView = async (fieldId: string) => {
    try {
      setError(null);
      const data = await getField(fieldId);
      setViewingField(data);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const handleFetchWeather = async (fieldId: string) => {
    try {
      setFetchingWeather(true);
      setWeatherNotice(null);
      const res = await fetchLiveWeather(fieldId);
      setWeatherNotice(
        `Weather fetched: ${res.weather.temperature}°C, ${res.weather.humidity}% RH (${res.mock ? 'Mock Mode' : 'OpenWeather API'})`
      );
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setFetchingWeather(false);
    }
  };

  const filteredFields = fields.filter((f) => {
    const matchesSearch =
      f.name.toLowerCase().includes(search.toLowerCase()) ||
      f.field_id.toLowerCase().includes(search.toLowerCase()) ||
      f.crop_type.toLowerCase().includes(search.toLowerCase()) ||
      (f.location_name && f.location_name.toLowerCase().includes(search.toLowerCase()));
    const matchesFarmer = selectedFarmerFilter ? f.farmer_id === selectedFarmerFilter : true;
    return matchesSearch && matchesFarmer;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Agricultural Fields</h1>
          <p className="text-sm text-slate-500 mt-1">
            Configure land parcels, GPS coordinates, farmer ownership, and crop assignments.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowAddModal(true)}
            disabled={farmers.length === 0}
            className="inline-flex items-center space-x-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-xl shadow-xs transition-colors disabled:opacity-50"
          >
            <Plus className="w-4 h-4" />
            <span>Add Field</span>
          </button>
          <button
            onClick={fetchData}
            className="p-2 bg-white hover:bg-slate-50 border border-slate-200 text-slate-600 rounded-xl transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Notifications */}
      {error && (
        <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-500 shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)}><X className="w-4 h-4" /></button>
        </div>
      )}
      {success && (
        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{success}</span>
          </div>
          <button onClick={() => setSuccess(null)}><X className="w-4 h-4" /></button>
        </div>
      )}

      {/* Filter Bar */}
      <div className="bg-white p-3 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col sm:flex-row items-center gap-3">
        <div className="flex-1 flex items-center space-x-2 w-full">
          <Search className="w-4 h-4 text-slate-400 ml-2" />
          <input
            type="text"
            placeholder="Search by field name, ID (e.g. F001), crop, or location..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full text-xs bg-transparent border-0 focus:outline-none text-slate-800 placeholder-slate-400"
          />
        </div>
        <div className="flex items-center space-x-2 w-full sm:w-auto">
          {/* View mode toggle */}
          <div className="flex items-center space-x-1 p-1 bg-slate-100 rounded-xl">
            <button
              type="button"
              onClick={() => setActiveView('monitoring')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeView === 'monitoring'
                  ? 'bg-white text-emerald-800 shadow-xs'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <LayoutGrid className="w-3.5 h-3.5" />
              <span>Monitoring Cards</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveView('table')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeView === 'table'
                  ? 'bg-white text-emerald-800 shadow-xs'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <TableIcon className="w-3.5 h-3.5" />
              <span>Table</span>
            </button>
          </div>

          <select
            value={selectedFarmerFilter}
            onChange={(e) => setSelectedFarmerFilter(e.target.value)}
            className="text-xs p-2 rounded-xl border border-slate-200 bg-slate-50 text-slate-700 focus:outline-none"
          >
            <option value="">All Farmers</option>
            {farmers.map((frm) => (
              <option key={frm.farmer_id} value={frm.farmer_id}>
                {frm.name} ({frm.farmer_id})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Live Monitoring View vs Table View */}
      {activeView === 'monitoring' ? (
        <div className="space-y-4">
          {/* Status Breakdown Bar */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="p-3.5 rounded-2xl bg-emerald-50 border border-emerald-200 flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <span className="w-3 h-3 rounded-full bg-emerald-500" />
                <span className="text-xs font-semibold text-emerald-900">Optimal Moisture</span>
              </div>
              <span className="text-sm font-bold text-emerald-700">
                {filteredFields.filter((f, i) => getFieldHealth(f.crop_type, i).status === 'GREEN').length} fields
              </span>
            </div>

            <div className="p-3.5 rounded-2xl bg-amber-50 border border-amber-200 flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <span className="w-3 h-3 rounded-full bg-amber-400 animate-pulse" />
                <span className="text-xs font-semibold text-amber-900">Needs Attention</span>
              </div>
              <span className="text-sm font-bold text-amber-700">
                {filteredFields.filter((f, i) => getFieldHealth(f.crop_type, i).status === 'YELLOW').length} fields
              </span>
            </div>

            <div className="p-3.5 rounded-2xl bg-rose-50 border border-rose-200 flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <span className="w-3 h-3 rounded-full bg-rose-500" />
                <span className="text-xs font-semibold text-rose-900">Urgent Action Required</span>
              </div>
              <span className="text-sm font-bold text-rose-700">
                {filteredFields.filter((f, i) => getFieldHealth(f.crop_type, i).status === 'RED').length} fields
              </span>
            </div>
          </div>

          {/* Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredFields.map((fld, idx) => {
              const health = getFieldHealth(fld.crop_type, idx);
              const isGenerating = generatingScheduleId === fld.field_id;

              return (
                <div
                  key={fld.field_id}
                  className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-xs hover:shadow-md transition-all flex flex-col justify-between space-y-4"
                >
                  <div>
                    {/* Header: Field name & status badge */}
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="flex items-center space-x-1.5">
                          <h3 className="font-bold text-slate-900 text-sm">{fld.name}</h3>
                          <span className="text-[10px] font-mono text-slate-400">({fld.field_id})</span>
                        </div>
                        <p className="text-xs text-slate-500 flex items-center space-x-1 mt-0.5">
                          <Wheat className="w-3.5 h-3.5 text-emerald-600" />
                          <span className="font-medium text-slate-700">{fld.crop_type}</span>
                          {fld.area_hectares && (
                            <span className="text-slate-400">&bull; {fld.area_hectares} ha</span>
                          )}
                        </p>
                      </div>

                      {/* Green / Yellow / Red Status Badge */}
                      <span
                        className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold border ${health.badgeClass}`}
                      >
                        <span className={`w-2 h-2 rounded-full ${health.dotClass}`} />
                        <span>{health.label}</span>
                      </span>
                    </div>

                    {/* Location */}
                    {fld.location_name && (
                      <p className="text-[11px] text-slate-400 flex items-center space-x-1 mt-2">
                        <MapPin className="w-3 h-3 text-slate-400 shrink-0" />
                        <span className="truncate">{fld.location_name}</span>
                      </p>
                    )}

                    {/* Soil Moisture Telemetry Gauge & Range */}
                    <div className="mt-4 pt-3 border-t border-slate-100 space-y-2">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-500 font-medium flex items-center space-x-1">
                          <Droplets className="w-3.5 h-3.5 text-emerald-600" />
                          <span>Current Soil Moisture:</span>
                        </span>
                        <span className="font-bold font-mono text-slate-900 text-sm">
                          {health.moisture.toFixed(1)}%
                        </span>
                      </div>

                      {/* Progress Bar */}
                      <div className="w-full h-2.5 rounded-full bg-slate-100 overflow-hidden relative border border-slate-200">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            health.status === 'GREEN'
                              ? 'bg-gradient-to-r from-emerald-500 to-lime-500'
                              : health.status === 'YELLOW'
                              ? 'bg-gradient-to-r from-amber-400 to-yellow-500'
                              : 'bg-gradient-to-r from-rose-500 to-red-600'
                          }`}
                          style={{ width: `${Math.min(100, Math.max(12, health.moisture))}%` }}
                        />
                      </div>

                      <div className="flex justify-between items-center text-[10px] text-slate-400 font-mono">
                        <span>Optimal: {health.minOptimal}% – {health.maxOptimal}%</span>
                        <span>Updated: 5m ago</span>
                      </div>
                    </div>

                    {/* Agronomic Recommendation Box */}
                    <div className="mt-3 p-2.5 rounded-xl bg-slate-50 border border-slate-100 text-xs text-slate-700">
                      <span className="font-semibold text-slate-800">Action: </span>
                      <span>{health.recommendation}</span>
                    </div>
                  </div>

                  {/* Quick Action Footer */}
                  <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-2 text-xs">
                    <button
                      onClick={() => handleView(fld.field_id)}
                      className="text-slate-600 hover:text-emerald-700 font-semibold text-xs transition-colors"
                    >
                      View Details &rarr;
                    </button>

                    <button
                      onClick={() => handleTriggerIrrigation(fld.field_id)}
                      disabled={isGenerating}
                      className="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs flex items-center space-x-1.5 shadow-xs transition-all disabled:opacity-50"
                    >
                      <Sparkles className={`w-3.5 h-3.5 ${isGenerating ? 'animate-spin' : ''}`} />
                      <span>{isGenerating ? 'Planning...' : 'Trigger Irrigation'}</span>
                    </button>
                  </div>
                </div>
              );
            })}

            {filteredFields.length === 0 && !loading && (
              <div className="col-span-full text-center py-12 bg-white rounded-2xl border border-slate-200 text-slate-400 space-y-2">
                <MapPin className="w-8 h-8 mx-auto text-slate-300" />
                <p className="text-sm font-semibold text-slate-600">No fields found matching criteria.</p>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Fields Table */
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-100 text-slate-500 font-semibold uppercase tracking-wider">
                  <th className="py-3 px-4">Field ID</th>
                  <th className="py-3 px-4">Field Name</th>
                  <th className="py-3 px-4">Farmer</th>
                  <th className="py-3 px-4">Crop Type</th>
                  <th className="py-3 px-4">Location / GPS</th>
                  <th className="py-3 px-4">Area (ha)</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {filteredFields.map((fld) => (
                  <tr key={fld.field_id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3 px-4 font-mono font-medium text-emerald-700">{fld.field_id}</td>
                    <td className="py-3 px-4 font-semibold text-slate-900">{fld.name}</td>
                    <td className="py-3 px-4 text-slate-600 font-mono text-[11px]">{fld.farmer_id}</td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-100 text-emerald-800">
                        {fld.crop_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-600">
                      <span className="block truncate max-w-xs">{fld.location_name || '—'}</span>
                      {fld.latitude && fld.longitude ? (
                        <span className="text-[10px] text-slate-400 font-mono">
                          {fld.latitude.toFixed(3)}, {fld.longitude.toFixed(3)}
                        </span>
                      ) : null}
                    </td>
                    <td className="py-3 px-4 text-slate-600">{fld.area_hectares ?? '—'}</td>
                    <td className="py-3 px-4 text-right space-x-2">
                      <button
                        onClick={() => handleView(fld.field_id)}
                        className="px-2.5 py-1 text-slate-600 hover:text-emerald-700 font-medium hover:bg-slate-100 rounded-lg transition-colors"
                      >
                        Inspect
                      </button>
                      <button
                        onClick={() => setEditingField(fld)}
                        className="p-1.5 text-slate-500 hover:text-emerald-700 hover:bg-slate-100 rounded-lg transition-colors"
                        title="Edit field"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleDelete(fld)}
                        className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                        title="Delete field"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
                {filteredFields.length === 0 && !loading && (
                  <tr>
                    <td colSpan={7} className="text-center py-8 text-slate-400">
                      {search ? 'No fields match your search.' : 'No fields created yet. Click "Add Field" to create one.'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Add Field Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-slate-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <h3 className="font-bold text-slate-900 text-sm">Create New Field</h3>
              <button onClick={() => setShowAddModal(false)}><X className="w-4 h-4 text-slate-400" /></button>
            </div>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Field Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. North Paddy"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Owner Farmer *</label>
                  <select
                    required
                    value={formData.farmer_id}
                    onChange={(e) => setFormData({ ...formData, farmer_id: e.target.value })}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600 bg-white"
                  >
                    {farmers.map((f) => (
                      <option key={f.farmer_id} value={f.farmer_id}>
                        {f.name} ({f.farmer_id})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Initial Crop Type *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Rice, Maize, Wheat"
                    value={formData.crop_type}
                    onChange={(e) => setFormData({ ...formData, crop_type: e.target.value })}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Area (hectares)</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    placeholder="e.g. 1.5"
                    value={formData.area_hectares ?? ''}
                    onChange={(e) => setFormData({ ...formData, area_hectares: parseFloat(e.target.value) || undefined })}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600"
                  />
                </div>
              </div>

              {/* Location search helper */}
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                <LocationPicker
                  onPick={(p) => setFormData({
                    ...formData,
                    location_name: p.label,
                    city: p.name,
                    state: p.state || '',
                    country: p.country || '',
                    latitude: p.latitude,
                    longitude: p.longitude,
                  })}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Location Name</label>
                <input
                  type="text"
                  placeholder="e.g. Hyderabad, Telangana"
                  value={formData.location_name || ''}
                  onChange={(e) => setFormData({ ...formData, location_name: e.target.value })}
                  className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600"
                />
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">City</label>
                  <input type="text" placeholder="Hyderabad"
                    value={formData.city || ''}
                    onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">State</label>
                  <input type="text" placeholder="Telangana"
                    value={formData.state || ''}
                    onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Country</label>
                  <input type="text" placeholder="IN"
                    value={formData.country || ''}
                    onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Latitude</label>
                  <input
                    type="number"
                    step="0.0001"
                    placeholder="e.g. 17.385"
                    value={formData.latitude ?? ''}
                    onChange={(e) => setFormData({ ...formData, latitude: parseFloat(e.target.value) || undefined })}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Longitude</label>
                  <input
                    type="number"
                    step="0.0001"
                    placeholder="e.g. 78.4867"
                    value={formData.longitude ?? ''}
                    onChange={(e) => setFormData({ ...formData, longitude: parseFloat(e.target.value) || undefined })}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600"
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 text-xs text-slate-600 hover:bg-slate-100 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl"
                >
                  {submitting ? 'Creating...' : 'Create Field'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Field Modal */}
      {editingField && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-slate-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <h3 className="font-bold text-slate-900 text-sm">Edit Field ({editingField.field_id})</h3>
              <button onClick={() => setEditingField(null)}><X className="w-4 h-4 text-slate-400" /></button>
            </div>
            <form onSubmit={handleUpdate} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Name</label>
                  <input
                    type="text"
                    required
                    value={editingField.name}
                    onChange={(e) => setEditingField({ ...editingField, name: e.target.value })}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Crop Type</label>
                  <input
                    type="text"
                    required
                    value={editingField.crop_type}
                    onChange={(e) => setEditingField({ ...editingField, crop_type: e.target.value })}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600"
                  />
                </div>
              </div>

              {/* Location search helper for edit */}
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                <LocationPicker
                  onPick={(p) => setEditingField({
                    ...editingField,
                    location_name: p.label,
                    city: p.name,
                    state: p.state || '',
                    country: p.country || '',
                    latitude: p.latitude,
                    longitude: p.longitude,
                  })}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Location Name</label>
                  <input
                    type="text"
                    value={editingField.location_name || ''}
                    onChange={(e) => setEditingField({ ...editingField, location_name: e.target.value })}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Area (ha)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={editingField.area_hectares ?? ''}
                    onChange={(e) => setEditingField({ ...editingField, area_hectares: parseFloat(e.target.value) || undefined })}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">City</label>
                  <input type="text" placeholder="Hyderabad"
                    value={editingField.city || ''}
                    onChange={(e) => setEditingField({ ...editingField, city: e.target.value })}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">State</label>
                  <input type="text" placeholder="Telangana"
                    value={editingField.state || ''}
                    onChange={(e) => setEditingField({ ...editingField, state: e.target.value })}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Country</label>
                  <input type="text" placeholder="IN"
                    value={editingField.country || ''}
                    onChange={(e) => setEditingField({ ...editingField, country: e.target.value })}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600" />
                </div>
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setEditingField(null)}
                  className="px-4 py-2 text-xs text-slate-600 hover:bg-slate-100 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl"
                >
                  {submitting ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Inspect Field Details Modal */}
      {viewingField && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <h3 className="font-bold text-slate-900 text-sm">Field Details: {viewingField.name}</h3>
                <span className="text-xs text-emerald-700 font-mono">{viewingField.field_id}</span>
              </div>
              <button onClick={() => setViewingField(null)}><X className="w-4 h-4 text-slate-400" /></button>
            </div>

            {weatherNotice && (
              <div className="p-3 bg-blue-50 border border-blue-200 text-blue-800 text-xs rounded-xl flex items-center justify-between">
                <span>{weatherNotice}</span>
                <button onClick={() => setWeatherNotice(null)}><X className="w-3.5 h-3.5" /></button>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4 text-xs bg-slate-50 p-4 rounded-xl border border-slate-200">
              <div>
                <span className="text-slate-400 block font-medium">Owner Farmer:</span>
                <span className="font-semibold text-slate-900">
                  {viewingField.farmer ? viewingField.farmer.name : viewingField.farmer_id}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block font-medium">Active Crop:</span>
                <span className="font-semibold text-slate-900">{viewingField.crop_type}</span>
              </div>
              <div>
                <span className="text-slate-400 block font-medium">Coordinates (GPS):</span>
                <span className="font-semibold text-slate-900 font-mono">
                  {viewingField.latitude && viewingField.longitude
                    ? `${viewingField.latitude.toFixed(4)}°N, ${viewingField.longitude.toFixed(4)}°E`
                    : <span className="text-amber-600">Not configured — add lat/lon</span>}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block font-medium">Area:</span>
                <span className="font-semibold text-slate-900">{viewingField.area_hectares ?? 0} hectares</span>
              </div>
              {(viewingField.city || viewingField.location_name) && (
                <div className="col-span-2">
                  <span className="text-slate-400 block font-medium">Location:</span>
                  <span className="font-semibold text-slate-900">
                    {[viewingField.city, viewingField.state, viewingField.country].filter(Boolean).join(', ') || viewingField.location_name}
                  </span>
                </div>
              )}
            </div>

            {/* Linked Sensors */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                Attached Sensors ({viewingField.sensors?.length || 0})
              </h4>
              <div className="space-y-1.5 max-h-36 overflow-y-auto">
                {viewingField.sensors && viewingField.sensors.length > 0 ? (
                  viewingField.sensors.map((s) => (
                    <div key={s.sensor_id} className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">
                      <div className="flex items-center space-x-2">
                        <Cpu className="w-4 h-4 text-emerald-600" />
                        <span className="font-bold text-slate-800">{s.sensor_id}</span>
                        <span className="text-slate-500">({s.sensor_type})</span>
                      </div>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${s.status === 'active' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-600'}`}>
                        {s.status}
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-slate-400">No sensors registered to this field yet.</div>
                )}
              </div>
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-slate-100">
              <button
                onClick={() => handleFetchWeather(viewingField.field_id)}
                disabled={fetchingWeather || !viewingField.location_name && (!viewingField.latitude || !viewingField.longitude)}
                className="inline-flex items-center space-x-1.5 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-medium transition-colors disabled:opacity-50"
              >
                <CloudRain className="w-3.5 h-3.5" />
                <span>{fetchingWeather ? 'Querying Weather...' : 'Fetch Live Weather'}</span>
              </button>

              <button
                onClick={() => setViewingField(null)}
                className="px-4 py-2 text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
