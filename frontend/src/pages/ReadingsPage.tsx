import React, { useEffect, useState } from 'react';
import {
  Activity,
  Download,
  Filter,
  RefreshCw,
  Search,
  Calendar,
  AlertCircle,
  CheckCircle2,
  TrendingDown,
  Layers,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import {
  getSensorReadings,
  getSensors,
  getFields,
  getExportReadingsUrl,
  getErrorMessage,
} from '../services/api';
import type { SensorReading, Sensor, Field } from '../types';

export const ReadingsPage: React.FC = () => {
  const [readings, setReadings] = useState<SensorReading[]>([]);
  const [sensors, setSensors] = useState<Sensor[]>([]);
  const [fields, setFields] = useState<Field[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedSensor, setSelectedSensor] = useState('');
  const [selectedField, setSelectedField] = useState('');
  const [selectedType, setSelectedType] = useState('');
  const [limit, setLimit] = useState(50);
  const [page, setPage] = useState(0);

  const fetchFilters = async () => {
    try {
      const [sns, flds] = await Promise.all([getSensors(), getFields()]);
      setSensors(sns);
      setFields(flds);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchReadings = async () => {
    try {
      setLoading(true);
      setError(null);
      const fieldParam = selectedSensor ? undefined : (selectedField || undefined);
      const data = await getSensorReadings({
        sensor_id: selectedSensor || undefined,
        field_id: fieldParam,
        measurement_type: selectedType || undefined,
        limit,
        offset: page * limit,
      });
      setReadings(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFilters();
  }, []);

  useEffect(() => {
    fetchReadings();
  }, [selectedSensor, selectedField, selectedType, limit, page]);

  const chartData = [...readings].reverse().map((r) => ({
    time: new Date(r.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    val: r.soil_moisture ?? r.value ?? 0,
    sensor: r.sensor_id,
  }));

  const exportUrl = getExportReadingsUrl({
    sensor_id: selectedSensor || undefined,
    field_id: selectedField || undefined,
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Sensor Readings &amp; Telemetry</h1>
          <p className="text-sm text-slate-500 mt-1">
            Historical soil moisture and ambient measurements with data-quality validation flags.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <a
            href={exportUrl}
            target="_blank"
            rel="noreferrer"
            download="sensor_readings.csv"
            className="inline-flex items-center space-x-1.5 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-xl shadow-xs transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </a>
          <button
            onClick={fetchReadings}
            className="p-2 bg-white hover:bg-slate-50 border border-slate-200 text-slate-600 rounded-xl transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-rose-500 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Filters Strip */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs flex flex-wrap items-center gap-3">
        <div className="flex items-center space-x-1 text-xs font-semibold text-slate-500 mr-2">
          <Filter className="w-3.5 h-3.5" />
          <span>Filters:</span>
        </div>

        {/* Sensor filter */}
        <select
          value={selectedSensor}
          onChange={(e) => {
            setSelectedSensor(e.target.value);
            setPage(0);
          }}
          className="text-xs p-2 rounded-xl border border-slate-200 bg-slate-50 text-slate-700 focus:outline-none"
        >
          <option value="">All Sensors</option>
          {sensors.map((s) => (
            <option key={s.sensor_id} value={s.sensor_id}>
              {s.sensor_id} ({s.sensor_type})
            </option>
          ))}
        </select>

        {/* Field filter */}
        <select
          value={selectedField}
          onChange={(e) => {
            setSelectedField(e.target.value);
            setPage(0);
          }}
          className="text-xs p-2 rounded-xl border border-slate-200 bg-slate-50 text-slate-700 focus:outline-none"
        >
          <option value="">All Fields</option>
          {fields.map((f) => (
            <option key={f.field_id} value={f.field_id}>
              {f.name} ({f.field_id})
            </option>
          ))}
        </select>

        {/* Measurement Type filter */}
        <select
          value={selectedType}
          onChange={(e) => {
            setSelectedType(e.target.value);
            setPage(0);
          }}
          className="text-xs p-2 rounded-xl border border-slate-200 bg-slate-50 text-slate-700 focus:outline-none"
        >
          <option value="">All Measurement Types</option>
          <option value="soil_moisture">Soil Moisture</option>
          <option value="temperature">Temperature</option>
          <option value="humidity">Humidity</option>
          <option value="soil_ph">Soil pH</option>
          <option value="rainfall">Rainfall</option>
          <option value="water_level">Water Level</option>
          <option value="flow_rate">Flow Rate</option>
        </select>

        {/* Page Limit */}
        <select
          value={limit}
          onChange={(e) => {
            setLimit(Number(e.target.value));
            setPage(0);
          }}
          className="text-xs p-2 rounded-xl border border-slate-200 bg-slate-50 text-slate-700 focus:outline-none ml-auto"
        >
          <option value={25}>25 per page</option>
          <option value={50}>50 per page</option>
          <option value={100}>100 per page</option>
        </select>
      </div>

      {/* Visual Chart */}
      {readings.length > 0 && (
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
          <h3 className="font-bold text-slate-900 text-sm mb-1">Time-Series Telemetry Trend</h3>
          <p className="text-xs text-slate-500 mb-4">Values plotted in chronological order</p>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="time" stroke="#94a3b8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '12px', fontSize: '12px' }}
                  formatter={(val: any) => [val, 'Measurement']}
                />
                <Line type="monotone" dataKey="val" stroke="#059669" strokeWidth={2} dot={{ r: 2 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Historical Readings Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-100 text-slate-500 font-semibold uppercase tracking-wider">
                <th className="py-3 px-4">ID</th>
                <th className="py-3 px-4">Timestamp (UTC)</th>
                <th className="py-3 px-4">Sensor ID</th>
                <th className="py-3 px-4">Field ID</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Primary Value</th>
                <th className="py-3 px-4">Quality Status</th>
                <th className="py-3 px-4">Quality Flags</th>
                <th className="py-3 px-4">Simulated</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {readings.map((r) => (
                <tr key={r.reading_id} className="hover:bg-slate-50/70 transition-colors">
                  <td className="py-3 px-4 font-mono text-slate-400">{r.reading_id}</td>
                  <td className="py-3 px-4 font-mono text-[11px] text-slate-600">
                    {new Date(r.timestamp).toLocaleString()}
                  </td>
                  <td className="py-3 px-4 font-mono font-medium text-emerald-700">{r.sensor_id}</td>
                  <td className="py-3 px-4 font-mono text-slate-600">{r.field_id}</td>
                  <td className="py-3 px-4 font-medium text-slate-800">{r.measurement_type}</td>
                  <td className="py-3 px-4 font-bold text-slate-900">
                    {r.soil_moisture !== null && r.soil_moisture !== undefined
                      ? `${r.soil_moisture}%`
                      : r.value !== null && r.value !== undefined
                      ? `${r.value} ${r.unit || ''}`
                      : '—'}
                  </td>
                  <td className="py-3 px-4">
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-800">
                      {r.quality_status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-500 font-mono text-[10px]">
                    {r.quality_flags || '—'}
                  </td>
                  <td className="py-3 px-4">
                    {r.is_simulated ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-amber-50 text-amber-700 border border-amber-200">
                        Simulated
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-slate-100 text-slate-600">
                        Hardware
                      </span>
                    )}
                  </td>
                </tr>
              ))}
              {readings.length === 0 && !loading && (
                <tr>
                  <td colSpan={9} className="text-center py-8 text-slate-400">
                    No readings found matching criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination bar */}
        <div className="p-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
          <span>Page {page + 1} (showing up to {limit} entries)</span>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-40"
            >
              Previous
            </button>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={readings.length < limit}
              className="px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
