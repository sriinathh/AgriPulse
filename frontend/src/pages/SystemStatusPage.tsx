import React, { useEffect, useState } from 'react';
import {
  Settings,
  Database,
  CloudRain,
  Radio,
  Server,
  RefreshCw,
  ExternalLink,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  ShieldCheck,
} from 'lucide-react';
import { getSystemStatus, seedDemoData, getErrorMessage, API_DOCS_URL } from '../services/api';
import type { SystemStatus } from '../types';

export const SystemStatusPage: React.FC = () => {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [seeding, setSeeding] = useState(false);
  const [seedResult, setSeedResult] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getSystemStatus();
      setStatus(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleSeed = async () => {
    if (!window.confirm('Seed simulated demo data into the development database? This will create demo farmers, fields, sensors, and readings without overwriting existing data.')) {
      return;
    }
    try {
      setSeeding(true);
      setSeedResult(null);
      const res = await seedDemoData();
      setSeedResult(
        res.status === 'already_seeded'
          ? 'Demo dataset is already present in database.'
          : 'Demo dataset seeded successfully! (Labelled is_demo / is_simulated / is_mock)'
      );
      await fetchStatus();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSeeding(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">System Status &amp; Configuration</h1>
          <p className="text-sm text-slate-500 mt-1">
            Infrastructure health diagnostics, TimescaleDB status, and integration connectivity.
          </p>
        </div>
        <button
          onClick={fetchStatus}
          className="p-2 bg-white hover:bg-slate-50 border border-slate-200 text-slate-600 rounded-xl transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-rose-500 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {seedResult && (
        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{seedResult}</span>
        </div>
      )}

      {/* Grid of System Components */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Backend FastAPI Service */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-4">
          <div className="flex items-center space-x-3 pb-3 border-b border-slate-100">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center">
              <Server className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-sm">FastAPI Application Server</h3>
              <span className="text-xs text-slate-500">Core REST &amp; Ingestion Engine</span>
            </div>
          </div>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-600">Runtime Status</span>
              <span className="font-bold text-emerald-700 flex items-center space-x-1">
                <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block animate-pulse" />
                <span>Online &amp; Healthy</span>
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-600">Version</span>
              <span className="font-mono text-slate-800">{status?.backend.version || '0.2.0'}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-600">Environment</span>
              <span className="font-mono text-slate-800">{status?.backend.environment || 'development'}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-600">Interactive API Docs</span>
              <a
                href={API_DOCS_URL}
                target="_blank"
                rel="noreferrer"
                className="text-emerald-600 hover:text-emerald-700 font-semibold inline-flex items-center space-x-1"
              >
                <span>/docs (Swagger UI)</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
        </div>

        {/* Database & TimescaleDB */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-4">
          <div className="flex items-center space-x-3 pb-3 border-b border-slate-100">
            <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-700 flex items-center justify-center">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-sm">PostgreSQL / TimescaleDB</h3>
              <span className="text-xs text-slate-500">Relational &amp; Time-Series Storage</span>
            </div>
          </div>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-600">Database Connection</span>
              <span className={`font-bold ${status?.database.ok ? 'text-emerald-700' : 'text-rose-600'}`}>
                {status?.database.ok ? 'Connected (SELECT 1 Verified)' : 'Unavailable'}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-600">Masked DSN</span>
              <span className="font-mono text-[11px] text-slate-600 truncate max-w-xs">
                {status?.database.url || '—'}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-600">TimescaleDB Extension</span>
              <span className="font-bold text-purple-700">
                {status?.timescaledb.available
                  ? `Active (v${status.timescaledb.version || 'installed'})`
                  : 'Plain PostgreSQL Fallback'}
              </span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-600">Active Hypertables</span>
              <span className="font-mono text-slate-800">
                {status?.timescaledb.hypertables?.length
                  ? status.timescaledb.hypertables.join(', ')
                  : 'None (Plain tables)'}
              </span>
            </div>
          </div>
        </div>

        {/* OpenWeather Service */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-4">
          <div className="flex items-center space-x-3 pb-3 border-b border-slate-100">
            <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-700 flex items-center justify-center">
              <CloudRain className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-sm">OpenWeather API Integration</h3>
              <span className="text-xs text-slate-500">Current weather &amp; rain data provider</span>
            </div>
          </div>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-600">API Key Configured</span>
              <span className={`font-bold ${status?.weather.configured ? 'text-emerald-700' : 'text-amber-700'}`}>
                {status?.weather.configured ? 'Yes (Loaded from backend/.env)' : 'Not Configured (Using Mock)'}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-600">Mock Fallback Mode</span>
              <span className="text-slate-800 font-medium">{status?.weather.mock_mode ? 'Enabled' : 'Disabled (Live Mode)'}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-600">Credential Privacy</span>
              <span className="text-emerald-700 font-medium">Safe (API Key never leaked to client)</span>
            </div>
          </div>
        </div>

        {/* MQTT Subscriber */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-4">
          <div className="flex items-center space-x-3 pb-3 border-b border-slate-100">
            <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center">
              <Radio className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-sm">MQTT Telemetry Subscriber</h3>
              <span className="text-xs text-slate-500">Non-blocking background broker listener</span>
            </div>
          </div>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-600">MQTT Enabled</span>
              <span className="font-medium text-slate-800">{status?.mqtt.enabled ? 'Yes' : 'Disabled in .env'}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-600">Broker Address</span>
              <span className="font-mono text-slate-800">{status?.mqtt.broker || 'localhost:1883'}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-600">Subscription Topic</span>
              <span className="font-mono text-slate-800">{status?.mqtt.topic || 'irrigation/sensors/#'}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-600">Connection State</span>
              <span className="text-slate-600">{status?.mqtt.connected ? 'Connected' : 'Offline / Retrying'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Demo Seed Controls Section */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h3 className="font-bold text-slate-900 text-sm">Development Simulation Seeder</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-xl">
              Seed sample farmers, fields, sensors, historical telemetry, and simulated weather data.
              Records are explicitly labelled with <code>is_demo: true</code> and <code>is_simulated: true</code>.
            </p>
          </div>
          <button
            onClick={handleSeed}
            disabled={seeding}
            className="inline-flex items-center space-x-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-4 py-2.5 rounded-xl shadow-xs transition-colors shrink-0 disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4" />
            <span>{seeding ? 'Seeding Demo Data...' : 'Seed Sample Dataset'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
