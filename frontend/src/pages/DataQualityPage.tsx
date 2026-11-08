import React, { useEffect, useState } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  FileSpreadsheet,
  RefreshCw,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  Layers,
} from 'lucide-react';
import { getDataQualityStats, getDataQualityEvents, getErrorMessage } from '../services/api';
import type { DataQualityStats, DataQualityEvent } from '../types';

export const DataQualityPage: React.FC = () => {
  const [stats, setStats] = useState<DataQualityStats | null>(null);
  const [events, setEvents] = useState<DataQualityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [eventTypeFilter, setEventTypeFilter] = useState('');
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [st, ev] = await Promise.all([
        getDataQualityStats(),
        getDataQualityEvents({ limit: 100, event_type: eventTypeFilter || undefined }),
      ]);
      setStats(st);
      setEvents(ev);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [eventTypeFilter]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Data Quality &amp; Validation Pipeline</h1>
          <p className="text-sm text-slate-500 mt-1">
            Auditable sensor sanity verification, boundary enforcement, and anomaly rejection logs.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={fetchData}
            className="p-2 bg-white hover:bg-slate-50 border border-slate-200 text-slate-600 rounded-xl transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs">
          {error}
        </div>
      )}

      {/* Primary KPI Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Total Processed</div>
          <div className="text-2xl font-bold text-slate-900">{stats?.readings_stored ?? '—'}</div>
          <span className="text-xs text-emerald-600 font-medium mt-2 block">100% Validated</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Rejection Anomalies</div>
          <div className="text-2xl font-bold text-rose-600">{stats?.invalid_readings ?? 0}</div>
          <span className="text-xs text-slate-400 mt-2 block">Never silently imputed</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Duplicate Interceptions</div>
          <div className="text-2xl font-bold text-amber-600">{stats?.duplicate_count ?? 0}</div>
          <span className="text-xs text-slate-400 mt-2 block">Unique key constraints</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Weather Anomalies</div>
          <div className="text-2xl font-bold text-blue-600">{stats?.weather_ingestion_failures ?? 0}</div>
          <span className="text-xs text-slate-400 mt-2 block">Downtime &amp; rate limits</span>
        </div>
      </div>

      {/* Detailed Diagnostics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs space-y-3">
          <h3 className="font-bold text-xs uppercase tracking-wider text-slate-700">Sensor Boundary Checks</h3>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-600">Out-of-Range Rejections</span>
              <span className="font-bold text-slate-900">{stats?.out_of_range_count ?? 0}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-600">Missing Mandatory Values</span>
              <span className="font-bold text-slate-900">{stats?.missing_value_count ?? 0}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-600">Invalid / Future Timestamps</span>
              <span className="font-bold text-slate-900">{stats?.invalid_timestamp_count ?? 0}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-600">Out-of-Order Sequenced</span>
              <span className="font-bold text-slate-900">{stats?.out_of_order_stored ?? 0}</span>
            </div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs space-y-3">
          <h3 className="font-bold text-xs uppercase tracking-wider text-slate-700">Telemetry Origin</h3>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-600">Hardware / Live Readings</span>
              <span className="font-bold text-emerald-700">
                {(stats?.readings_stored ?? 0) - (stats?.simulated_readings ?? 0)}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-600">Simulated Development Readings</span>
              <span className="font-bold text-amber-700">{stats?.simulated_readings ?? 0}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-600">OpenWeather Live Observations</span>
              <span className="font-bold text-blue-700">
                {(stats?.weather_observations ?? 0) - (stats?.weather_mock_observations ?? 0)}
              </span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-600">Simulated Weather Observations</span>
              <span className="font-bold text-slate-600">{stats?.weather_mock_observations ?? 0}</span>
            </div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs space-y-3">
          <h3 className="font-bold text-xs uppercase tracking-wider text-slate-700">Pipeline Invariants</h3>
          <ul className="space-y-2 text-[11px] text-slate-600">
            <li className="flex items-start space-x-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
              <span>Zero is treated as a valid numeric reading, never confused with null.</span>
            </li>
            <li className="flex items-start space-x-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
              <span>No fabrication of missing data; faulty values are rejected and logged.</span>
            </li>
            <li className="flex items-start space-x-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
              <span>Auditable events table records the exact rejection code and timestamp.</span>
            </li>
          </ul>
        </div>
      </div>

      {/* Filter and Event Log Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div>
            <h3 className="font-bold text-slate-900 text-xs">Quality Event Audit Trail</h3>
            <p className="text-[11px] text-slate-500">Chronological pipeline rejection events</p>
          </div>
          <div className="flex items-center space-x-2">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={eventTypeFilter}
              onChange={(e) => setEventTypeFilter(e.target.value)}
              className="text-xs p-1.5 rounded-lg border border-slate-200 bg-slate-50 text-slate-700"
            >
              <option value="">All Event Types</option>
              <option value="out_of_range">out_of_range</option>
              <option value="missing_value">missing_value</option>
              <option value="duplicate">duplicate</option>
              <option value="invalid_timestamp">invalid_timestamp</option>
              <option value="weather_timeout">weather_timeout</option>
              <option value="weather_provider_error">weather_provider_error</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-100 text-slate-500 font-semibold uppercase tracking-wider">
                <th className="py-3 px-4">Event ID</th>
                <th className="py-3 px-4">Logged At (UTC)</th>
                <th className="py-3 px-4">Event Type</th>
                <th className="py-3 px-4">Source</th>
                <th className="py-3 px-4">Sensor / Field</th>
                <th className="py-3 px-4">Validation Message</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {events.map((ev) => (
                <tr key={ev.event_id} className="hover:bg-slate-50/70 transition-colors">
                  <td className="py-3 px-4 font-mono text-slate-400">#{ev.event_id}</td>
                  <td className="py-3 px-4 font-mono text-[11px] text-slate-600">
                    {new Date(ev.created_at).toLocaleString()}
                  </td>
                  <td className="py-3 px-4">
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                      {ev.event_type}
                    </span>
                  </td>
                  <td className="py-3 px-4 uppercase font-bold text-[10px] text-slate-600">{ev.source}</td>
                  <td className="py-3 px-4 font-mono text-slate-600">
                    {ev.sensor_id || ev.field_id || '—'}
                  </td>
                  <td className="py-3 px-4 text-slate-800">{ev.message}</td>
                </tr>
              ))}
              {events.length === 0 && !loading && (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-slate-400">
                    No data-quality rejection events recorded.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
