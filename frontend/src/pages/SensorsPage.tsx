import React, { useEffect, useState } from 'react';
import {
  Cpu,
  Plus,
  Search,
  Power,
  Trash2,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  X,
  Droplets,
  Activity,
  Edit2,
} from 'lucide-react';
import {
  getSensors,
  getFields,
  createSensor,
  updateSensor,
  deleteSensor,
  setSensorStatus,
  getSensorReadings,
  getErrorMessage,
} from '../services/api';
import type { Sensor, SensorCreate, SensorUpdate, Field, SensorReading } from '../types';

export const SensorsPage: React.FC = () => {
  const [sensors, setSensors] = useState<Sensor[]>([]);
  const [fields, setFields] = useState<Field[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [fieldFilter, setFieldFilter] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Modals
  const [showAddModal, setShowAddModal] = useState(false);
  const [viewingReadings, setViewingReadings] = useState<{ sensor: Sensor; readings: SensorReading[] } | null>(null);
  const [loadingReadings, setLoadingReadings] = useState(false);

  // Form state
  const [formData, setFormData] = useState<SensorCreate>({
    field_id: '',
    sensor_type: 'soil_moisture',
    unit: '%',
    status: 'active',
    is_simulated: false,
  });
  const [submitting, setSubmitting] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [snsData, fldData] = await Promise.all([getSensors(), getFields()]);
      setSensors(snsData);
      setFields(fldData);
      if (fldData.length > 0 && !formData.field_id) {
        setFormData((prev) => ({ ...prev, field_id: fldData[0].field_id }));
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
    if (!formData.field_id) return;
    try {
      setSubmitting(true);
      setError(null);
      await createSensor(formData);
      setSuccess('Sensor registered successfully.');
      setTimeout(() => setSuccess(null), 3000);
      setShowAddModal(false);
      setFormData({
        field_id: fields[0]?.field_id || '',
        sensor_type: 'soil_moisture',
        unit: '%',
        status: 'active',
        is_simulated: false,
      });
      await fetchData();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleStatus = async (sensor: Sensor) => {
    const nextStatus = sensor.status === 'active' ? 'inactive' : 'active';
    try {
      setError(null);
      await setSensorStatus(sensor.sensor_id, nextStatus);
      setSuccess(`Sensor '${sensor.sensor_id}' status set to ${nextStatus}.`);
      setTimeout(() => setSuccess(null), 2500);
      await fetchData();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const handleDelete = async (sensor: Sensor) => {
    if (!window.confirm(`Delete sensor '${sensor.sensor_id}' and all associated historical readings?`)) return;
    try {
      setError(null);
      await deleteSensor(sensor.sensor_id);
      setSuccess(`Sensor '${sensor.sensor_id}' deleted.`);
      setTimeout(() => setSuccess(null), 3000);
      await fetchData();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const handleInspectReadings = async (sensor: Sensor) => {
    try {
      setLoadingReadings(true);
      setError(null);
      const readings = await getSensorReadings({ sensor_id: sensor.sensor_id, limit: 30 });
      setViewingReadings({ sensor, readings });
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoadingReadings(false);
    }
  };

  const filteredSensors = sensors.filter((s) => {
    const matchesSearch =
      s.sensor_id.toLowerCase().includes(search.toLowerCase()) ||
      s.sensor_type.toLowerCase().includes(search.toLowerCase()) ||
      s.field_id.toLowerCase().includes(search.toLowerCase());
    const matchesField = fieldFilter ? s.field_id === fieldFilter : true;
    return matchesSearch && matchesField;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">IoT Sensor Registry</h1>
          <p className="text-sm text-slate-500 mt-1">
            Register hardware and simulated probes, manage field placement, and monitor connectivity status.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowAddModal(true)}
            disabled={fields.length === 0}
            className="inline-flex items-center space-x-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-xl shadow-xs transition-colors disabled:opacity-50"
          >
            <Plus className="w-4 h-4" />
            <span>Register Sensor</span>
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
            placeholder="Search sensor ID (e.g. SM001), type, or field..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full text-xs bg-transparent border-0 focus:outline-none text-slate-800 placeholder-slate-400"
          />
        </div>
        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <select
            value={fieldFilter}
            onChange={(e) => setFieldFilter(e.target.value)}
            className="text-xs p-2 rounded-xl border border-slate-200 bg-slate-50 text-slate-700 focus:outline-none"
          >
            <option value="">All Fields</option>
            {fields.map((fld) => (
              <option key={fld.field_id} value={fld.field_id}>
                {fld.name} ({fld.field_id})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-100 text-slate-500 font-semibold uppercase tracking-wider">
                <th className="py-3 px-4">Sensor ID</th>
                <th className="py-3 px-4">Field ID</th>
                <th className="py-3 px-4">Measurement Type</th>
                <th className="py-3 px-4">Unit</th>
                <th className="py-3 px-4">Operational Status</th>
                <th className="py-3 px-4">Connectivity Mode</th>
                <th className="py-3 px-4">Last Seen</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {filteredSensors.map((s) => (
                <tr key={s.sensor_id} className="hover:bg-slate-50/70 transition-colors">
                  <td className="py-3 px-4 font-mono font-medium text-emerald-700">{s.sensor_id}</td>
                  <td className="py-3 px-4 font-mono text-slate-600">{s.field_id}</td>
                  <td className="py-3 px-4 font-semibold text-slate-900">{s.sensor_type}</td>
                  <td className="py-3 px-4 text-slate-600">{s.unit || '—'}</td>
                  <td className="py-3 px-4">
                    <button
                      onClick={() => handleToggleStatus(s)}
                      className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-[10px] font-semibold transition-colors ${
                        s.status === 'active'
                          ? 'bg-emerald-100 text-emerald-800 hover:bg-emerald-200'
                          : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                      }`}
                    >
                      <Power className="w-3 h-3" />
                      <span>{s.status === 'active' ? 'Active' : 'Inactive'}</span>
                    </button>
                  </td>
                  <td className="py-3 px-4">
                    {s.is_simulated ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-amber-50 text-amber-700 border border-amber-200">
                        Simulated Probe
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-slate-100 text-slate-700">
                        Hardware IoT
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4 font-mono text-[11px] text-slate-500">
                    {s.last_seen_at ? new Date(s.last_seen_at).toLocaleString() : 'Never'}
                  </td>
                  <td className="py-3 px-4 text-right space-x-2">
                    <button
                      onClick={() => handleInspectReadings(s)}
                      className="px-2.5 py-1 text-slate-600 hover:text-emerald-700 font-medium hover:bg-slate-100 rounded-lg transition-colors"
                    >
                      Telemetry
                    </button>
                    <button
                      onClick={() => handleDelete(s)}
                      className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                      title="Delete sensor"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
              {filteredSensors.length === 0 && !loading && (
                <tr>
                  <td colSpan={8} className="text-center py-8 text-slate-400">
                    {search ? 'No sensors match your query.' : 'No sensors registered yet.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Register Sensor Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <h3 className="font-bold text-slate-900 text-sm">Register IoT Sensor</h3>
              <button onClick={() => setShowAddModal(false)}><X className="w-4 h-4 text-slate-400" /></button>
            </div>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Assigned Field *</label>
                <select
                  required
                  value={formData.field_id}
                  onChange={(e) => setFormData({ ...formData, field_id: e.target.value })}
                  className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600 bg-white"
                >
                  {fields.map((fld) => (
                    <option key={fld.field_id} value={fld.field_id}>
                      {fld.name} ({fld.field_id})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Measurement Type *</label>
                <select
                  value={formData.sensor_type}
                  onChange={(e) => {
                    const st = e.target.value;
                    let u = '%';
                    if (st === 'temperature') u = '°C';
                    else if (st === 'humidity') u = '%';
                    else if (st === 'soil_ph') u = 'pH';
                    else if (st === 'rainfall') u = 'mm';
                    else if (st === 'water_level') u = 'm';
                    else if (st === 'flow_rate') u = 'L/min';
                    setFormData({ ...formData, sensor_type: st, unit: u });
                  }}
                  className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600 bg-white"
                >
                  <option value="soil_moisture">Soil Moisture (volumetric %)</option>
                  <option value="temperature">Temperature (°C)</option>
                  <option value="humidity">Relative Humidity (%)</option>
                  <option value="soil_ph">Soil pH</option>
                  <option value="rainfall">Rainfall (mm)</option>
                  <option value="water_level">Water Level (m)</option>
                  <option value="flow_rate">Flow Rate (L/min)</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Unit of Measurement</label>
                  <input
                    type="text"
                    value={formData.unit || ''}
                    onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Initial Status</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600 bg-white"
                  >
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                  </select>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                <label className="flex items-center space-x-2 text-xs text-slate-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_simulated}
                    onChange={(e) => setFormData({ ...formData, is_simulated: e.target.checked })}
                    className="rounded text-emerald-600 focus:ring-emerald-500"
                  />
                  <span>Mark as development simulated sensor (not hardware)</span>
                </label>
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
                  {submitting ? 'Registering...' : 'Register Sensor'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Inspect Readings Modal */}
      {viewingReadings && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <h3 className="font-bold text-slate-900 text-sm">
                  Telemetry Readings: {viewingReadings.sensor.sensor_id}
                </h3>
                <span className="text-xs text-slate-500">
                  Type: {viewingReadings.sensor.sensor_type} &bull; Field: {viewingReadings.sensor.field_id}
                </span>
              </div>
              <button onClick={() => setViewingReadings(null)}><X className="w-4 h-4 text-slate-400" /></button>
            </div>

            <div className="max-h-72 overflow-y-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-100">
                    <th className="py-2.5 px-3">Timestamp (UTC)</th>
                    <th className="py-2.5 px-3">Moisture (%)</th>
                    <th className="py-2.5 px-3">Value</th>
                    <th className="py-2.5 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {viewingReadings.readings.map((r) => (
                    <tr key={r.reading_id}>
                      <td className="py-2 px-3 font-mono text-[11px] text-slate-600">
                        {new Date(r.timestamp).toLocaleString()}
                      </td>
                      <td className="py-2 px-3 font-semibold text-emerald-700">
                        {r.soil_moisture !== null && r.soil_moisture !== undefined ? `${r.soil_moisture}%` : '—'}
                      </td>
                      <td className="py-2 px-3 text-slate-600">
                        {r.value !== null && r.value !== undefined ? `${r.value} ${r.unit || ''}` : '—'}
                      </td>
                      <td className="py-2 px-3">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-100 text-emerald-800">
                          {r.quality_status}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {viewingReadings.readings.length === 0 && (
                    <tr>
                      <td colSpan={4} className="text-center py-6 text-slate-400">
                        No telemetry points recorded yet for this sensor.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="flex justify-end pt-2 border-t border-slate-100">
              <button
                onClick={() => setViewingReadings(null)}
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
