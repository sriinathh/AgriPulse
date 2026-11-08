import React, { useEffect, useState } from 'react';
import {
  Sparkles,
  Droplets,
  Sprout,
  HelpCircle,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Compass,
  Sliders,
  Info,
  Calendar,
  CloudRain,
  Flame,
} from 'lucide-react';
import {
  getCropRecommendation,
  getCropModelMetrics,
  getIrrigationRecommendation,
  getFieldIrrigationRecommendation,
  getFields,
  getErrorMessage,
} from '../services/api';
import type {
  CropRecommendationResponse,
  CropModelMetrics,
  IrrigationRecommendationResponse,
  Field,
} from '../types';

export const RecommendationsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'crop' | 'irrigation'>('crop');

  // Crop Recommendation State
  const [cropForm, setCropForm] = useState({
    N: 90,
    P: 42,
    K: 43,
    temperature: 24.5,
    humidity: 78.0,
    ph: 6.5,
    rainfall: 180.0,
  });
  const [cropResult, setCropResult] = useState<CropRecommendationResponse | null>(null);
  const [cropMetrics, setCropMetrics] = useState<CropModelMetrics | null>(null);
  const [cropLoading, setCropLoading] = useState(false);
  const [cropError, setCropError] = useState<string | null>(null);

  // Irrigation Recommendation State
  const [fields, setFields] = useState<Field[]>([]);
  const [selectedFieldId, setSelectedFieldId] = useState<string>('');
  const [irrigationCustom, setIrrigationCustom] = useState({
    crop_type: 'Rice',
    growth_stage: 'flowering',
    soil_moisture: 22.0,
    temperature: 31.0,
    recent_rainfall_mm: 0.0,
    forecast_rainfall_mm: 0.0,
  });
  const [useFieldLive, setUseFieldLive] = useState(true);
  const [irrigationResult, setIrrigationResult] = useState<IrrigationRecommendationResponse | null>(null);
  const [irrigationLoading, setIrrigationLoading] = useState(false);
  const [irrigationError, setIrrigationError] = useState<string | null>(null);

  useEffect(() => {
    // Load initial model metrics and available fields
    const init = async () => {
      try {
        const [metrics, flds] = await Promise.all([
          getCropModelMetrics(),
          getFields(),
        ]);
        setCropMetrics(metrics);
        setFields(flds);
        if (flds.length > 0) {
          setSelectedFieldId(flds[0].field_id);
        }
      } catch (err) {
        console.error('Failed to load initial advisory data:', err);
      }
    };
    init();
  }, []);

  // Handle Crop Recommendation Submission
  const handleCropSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setCropLoading(true);
      setCropError(null);
      const res = await getCropRecommendation(cropForm);
      setCropResult(res);
    } catch (err) {
      setCropError(getErrorMessage(err));
    } finally {
      setCropLoading(false);
    }
  };

  // Quick preset selector for soil testing
  const applyPreset = (preset: 'rice' | 'maize' | 'chickpea' | 'grapes') => {
    if (preset === 'rice') {
      setCropForm({ N: 90, P: 42, K: 43, temperature: 24.0, humidity: 82.0, ph: 6.5, rainfall: 210.0 });
    } else if (preset === 'maize') {
      setCropForm({ N: 85, P: 58, K: 41, temperature: 26.0, humidity: 65.0, ph: 6.8, rainfall: 90.0 });
    } else if (preset === 'chickpea') {
      setCropForm({ N: 25, P: 68, K: 80, temperature: 18.5, humidity: 16.0, ph: 7.2, rainfall: 65.0 });
    } else if (preset === 'grapes') {
      setCropForm({ N: 22, P: 130, K: 200, temperature: 28.0, humidity: 60.0, ph: 6.2, rainfall: 70.0 });
    }
  };

  // Handle Irrigation Advisory Run
  const handleIrrigationSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setIrrigationLoading(true);
      setIrrigationError(null);
      let res: IrrigationRecommendationResponse;
      if (useFieldLive && selectedFieldId) {
        res = await getFieldIrrigationRecommendation(selectedFieldId);
      } else {
        res = await getIrrigationRecommendation(irrigationCustom);
      }
      setIrrigationResult(res);
    } catch (err) {
      setIrrigationError(getErrorMessage(err));
    } finally {
      setIrrigationLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Agricultural Intelligence &amp; Irrigation Advisory
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Machine learning crop suitability classification and explainable FAO-56 irrigation water management.
          </p>
        </div>
        <div className="flex items-center space-x-2 bg-slate-100 p-1 rounded-xl">
          <button
            onClick={() => setActiveTab('crop')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'crop'
                ? 'bg-white text-emerald-800 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Crop Suitability (ML)
          </button>
          <button
            onClick={() => setActiveTab('irrigation')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'irrigation'
                ? 'bg-white text-emerald-800 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Irrigation Water Deficit (FAO-56)
          </button>
        </div>
      </div>

      {/* ────────────────── TAB 1: CROP RECOMMENDATION ────────────────── */}
      {activeTab === 'crop' && (
        <div className="space-y-6">
          {/* Presets and Guidance */}
          <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="flex items-center space-x-2 text-slate-600">
              <Compass className="w-4 h-4 text-emerald-600" />
              <span className="font-semibold text-slate-800">Quick Soil &amp; Climate Presets:</span>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => applyPreset('rice')}
                className="px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 hover:bg-emerald-100 font-medium"
              >
                Paddy / Rice Conditions
              </button>
              <button
                type="button"
                onClick={() => applyPreset('maize')}
                className="px-2.5 py-1 rounded-lg bg-amber-50 text-amber-700 hover:bg-amber-100 font-medium"
              >
                Maize / Cereal Loam
              </button>
              <button
                type="button"
                onClick={() => applyPreset('chickpea')}
                className="px-2.5 py-1 rounded-lg bg-indigo-50 text-indigo-700 hover:bg-indigo-100 font-medium"
              >
                Semi-Arid Legumes (Chickpea)
              </button>
              <button
                type="button"
                onClick={() => applyPreset('grapes')}
                className="px-2.5 py-1 rounded-lg bg-purple-50 text-purple-700 hover:bg-purple-100 font-medium"
              >
                High-Potassium Orchards (Grapes)
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Input Form */}
            <div className="lg:col-span-1 bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-4">
              <div className="flex items-center space-x-2 pb-3 border-b border-slate-100">
                <Sliders className="w-5 h-5 text-emerald-600" />
                <h3 className="font-bold text-slate-900 text-sm">Soil &amp; Climate Parameters</h3>
              </div>

              {cropError && (
                <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs">
                  {cropError}
                </div>
              )}

              <form onSubmit={handleCropSubmit} className="space-y-3.5">
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 mb-1">Nitrogen (N)</label>
                    <input
                      type="number"
                      step="any"
                      min="0"
                      max="150"
                      value={cropForm.N}
                      onChange={(e) => setCropForm({ ...cropForm, N: parseFloat(e.target.value) || 0 })}
                      className="w-full px-2.5 py-1.5 text-xs rounded-xl border border-slate-200 focus:outline-emerald-600"
                      required
                    />
                    <span className="text-[10px] text-slate-400">kg/ha</span>
                  </div>
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 mb-1">Phosphorus (P)</label>
                    <input
                      type="number"
                      step="any"
                      min="0"
                      max="150"
                      value={cropForm.P}
                      onChange={(e) => setCropForm({ ...cropForm, P: parseFloat(e.target.value) || 0 })}
                      className="w-full px-2.5 py-1.5 text-xs rounded-xl border border-slate-200 focus:outline-emerald-600"
                      required
                    />
                    <span className="text-[10px] text-slate-400">kg/ha</span>
                  </div>
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 mb-1">Potassium (K)</label>
                    <input
                      type="number"
                      step="any"
                      min="0"
                      max="210"
                      value={cropForm.K}
                      onChange={(e) => setCropForm({ ...cropForm, K: parseFloat(e.target.value) || 0 })}
                      className="w-full px-2.5 py-1.5 text-xs rounded-xl border border-slate-200 focus:outline-emerald-600"
                      required
                    />
                    <span className="text-[10px] text-slate-400">kg/ha</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 mb-1">Temperature</label>
                    <input
                      type="number"
                      step="any"
                      min="0"
                      max="50"
                      value={cropForm.temperature}
                      onChange={(e) => setCropForm({ ...cropForm, temperature: parseFloat(e.target.value) || 0 })}
                      className="w-full px-2.5 py-1.5 text-xs rounded-xl border border-slate-200 focus:outline-emerald-600"
                      required
                    />
                    <span className="text-[10px] text-slate-400">°C</span>
                  </div>
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 mb-1">Humidity</label>
                    <input
                      type="number"
                      step="any"
                      min="0"
                      max="100"
                      value={cropForm.humidity}
                      onChange={(e) => setCropForm({ ...cropForm, humidity: parseFloat(e.target.value) || 0 })}
                      className="w-full px-2.5 py-1.5 text-xs rounded-xl border border-slate-200 focus:outline-emerald-600"
                      required
                    />
                    <span className="text-[10px] text-slate-400">%</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 mb-1">Soil pH</label>
                    <input
                      type="number"
                      step="0.1"
                      min="3"
                      max="11"
                      value={cropForm.ph}
                      onChange={(e) => setCropForm({ ...cropForm, ph: parseFloat(e.target.value) || 0 })}
                      className="w-full px-2.5 py-1.5 text-xs rounded-xl border border-slate-200 focus:outline-emerald-600"
                      required
                    />
                    <span className="text-[10px] text-slate-400">0 - 14 scale</span>
                  </div>
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 mb-1">Rainfall</label>
                    <input
                      type="number"
                      step="any"
                      min="0"
                      max="350"
                      value={cropForm.rainfall}
                      onChange={(e) => setCropForm({ ...cropForm, rainfall: parseFloat(e.target.value) || 0 })}
                      className="w-full px-2.5 py-1.5 text-xs rounded-xl border border-slate-200 focus:outline-emerald-600"
                      required
                    />
                    <span className="text-[10px] text-slate-400">mm</span>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={cropLoading}
                  className="w-full py-2.5 px-4 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs rounded-xl shadow-xs transition-colors flex items-center justify-center space-x-1.5"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>{cropLoading ? 'Evaluating Soil Match...' : 'Predict Crop Suitability'}</span>
                </button>
              </form>
            </div>

            {/* Results & Explanations */}
            <div className="lg:col-span-2 space-y-6">
              {cropResult ? (
                <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-5">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                    <div>
                      <span className="text-[11px] font-bold text-emerald-600 uppercase tracking-wider">Top Recommendation</span>
                      <h2 className="text-2xl font-extrabold text-slate-900 capitalize mt-0.5">
                        {cropResult.recommended_crop}
                      </h2>
                    </div>
                    <div className="text-right">
                      <span className="text-[11px] font-medium text-slate-400 block">Confidence</span>
                      <span className="text-xl font-bold text-emerald-600">
                        {(cropResult.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>

                  {/* Agronomic Rationale */}
                  <div className="p-4 rounded-xl bg-emerald-50/70 border border-emerald-100 text-slate-700 text-xs leading-relaxed space-y-1">
                    <div className="font-semibold text-emerald-900 flex items-center space-x-1.5">
                      <Info className="w-4 h-4 text-emerald-600" />
                      <span>Agronomic Suitability Analysis:</span>
                    </div>
                    <p>{cropResult.agronomic_explanation}</p>
                  </div>

                  {/* Candidate Distribution */}
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                      Alternative Candidate Crops
                    </h4>
                    <div className="space-y-2">
                      {cropResult.top_candidates.map((cand, idx) => (
                        <div key={cand.crop} className="flex items-center text-xs">
                          <span className="w-28 font-medium text-slate-800 capitalize">{cand.crop}</span>
                          <div className="flex-1 bg-slate-100 rounded-full h-3 overflow-hidden mr-3">
                            <div
                              className={`h-full rounded-full ${
                                idx === 0 ? 'bg-emerald-600' : idx === 1 ? 'bg-emerald-400' : 'bg-slate-400'
                              }`}
                              style={{ width: `${cand.confidence_pct}%` }}
                            />
                          </div>
                          <span className="w-12 text-right font-mono text-slate-600">{cand.confidence_pct}%</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Limitations Disclaimer */}
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-[11px] text-slate-500">
                    <span className="font-semibold text-slate-700">Advisory Limitations: </span>
                    {cropResult.limitations}
                  </div>
                </div>
              ) : (
                <div className="bg-white p-10 rounded-2xl border border-slate-200/80 shadow-xs text-center flex flex-col items-center justify-center space-y-2 text-slate-400">
                  <Sprout className="w-10 h-10 text-emerald-300" />
                  <p className="text-sm font-medium text-slate-600">No crop recommendation generated yet.</p>
                  <p className="text-xs max-w-sm">
                    Enter your soil nutrient analysis (N, P, K) and field weather conditions to receive multi-class crop recommendations.
                  </p>
                </div>
              )}

              {/* Model Transparency & Governance Card */}
              {cropMetrics && (
                <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="font-bold text-slate-900 text-xs uppercase tracking-wider">
                      Model Governance &amp; Verification
                    </h4>
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-800">
                      Verified On Held-Out Test Set
                    </span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                    <div className="p-3 bg-slate-50 rounded-xl">
                      <div className="text-slate-400 text-[10px]">Test Accuracy</div>
                      <div className="font-bold text-emerald-700 text-base">
                        {(cropMetrics.test_accuracy * 100).toFixed(2)}%
                      </div>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-xl">
                      <div className="text-slate-400 text-[10px]">Macro F1 Score</div>
                      <div className="font-bold text-emerald-700 text-base">
                        {(cropMetrics.macro_f1 * 100).toFixed(2)}%
                      </div>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-xl">
                      <div className="text-slate-400 text-[10px]">Training Split</div>
                      <div className="font-bold text-slate-800 text-base">
                        {cropMetrics.train_samples} rows (80%)
                      </div>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-xl">
                      <div className="text-slate-400 text-[10px]">Evaluation Split</div>
                      <div className="font-bold text-slate-800 text-base">
                        {cropMetrics.test_samples} rows (20%)
                      </div>
                    </div>
                  </div>
                  <div className="text-[11px] text-slate-400 space-y-0.5">
                    <div>Algorithm: <code>{cropMetrics.algorithm}</code></div>
                    <div>Trained on dataset: <code>Crop_recommendationV2 (1).csv</code></div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ────────────────── TAB 2: IRRIGATION ADVISORY ────────────────── */}
      {activeTab === 'irrigation' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Controls */}
          <div className="lg:col-span-1 bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-4">
            <div className="flex items-center space-x-2 pb-3 border-b border-slate-100">
              <Droplets className="w-5 h-5 text-blue-600" />
              <h3 className="font-bold text-slate-900 text-sm">Irrigation Water Deficit Advisor</h3>
            </div>

            {irrigationError && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs">
                {irrigationError}
              </div>
            )}

            <div className="flex items-center space-x-2 p-1 bg-slate-100 rounded-xl text-xs font-medium">
              <button
                type="button"
                onClick={() => setUseFieldLive(true)}
                className={`flex-1 py-1.5 rounded-lg transition-all ${
                  useFieldLive ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-500'
                }`}
              >
                Monitored Field
              </button>
              <button
                type="button"
                onClick={() => setUseFieldLive(false)}
                className={`flex-1 py-1.5 rounded-lg transition-all ${
                  !useFieldLive ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-500'
                }`}
              >
                Manual Parameters
              </button>
            </div>

            <form onSubmit={handleIrrigationSubmit} className="space-y-4">
              {useFieldLive ? (
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Select Field</label>
                  <select
                    value={selectedFieldId}
                    onChange={(e) => setSelectedFieldId(e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-emerald-600"
                    required
                  >
                    {fields.map((f) => (
                      <option key={f.field_id} value={f.field_id}>
                        {f.name} ({f.field_id}) — {f.crop_type}
                      </option>
                    ))}
                    {fields.length === 0 && <option value="">No registered fields found</option>}
                  </select>
                  <p className="text-[11px] text-slate-400 mt-1">
                    Pulls latest TimescaleDB sensor telemetry and OpenWeather observations automatically.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Crop Type</label>
                    <input
                      type="text"
                      value={irrigationCustom.crop_type}
                      onChange={(e) => setIrrigationCustom({ ...irrigationCustom, crop_type: e.target.value })}
                      className="w-full px-3 py-1.5 text-xs rounded-xl border border-slate-200 focus:outline-emerald-600"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Growth Stage</label>
                    <select
                      value={irrigationCustom.growth_stage}
                      onChange={(e) => setIrrigationCustom({ ...irrigationCustom, growth_stage: e.target.value })}
                      className="w-full px-3 py-1.5 text-xs rounded-xl border border-slate-200 focus:outline-emerald-600"
                    >
                      <option value="seedling">Seedling (Moderate watering)</option>
                      <option value="vegetative">Vegetative (Active growth)</option>
                      <option value="flowering">Flowering (Critical reproductive peak)</option>
                      <option value="maturity">Maturity (Pre-harvest drying)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Soil Moisture (%)</label>
                    <input
                      type="number"
                      step="any"
                      min="0"
                      max="100"
                      value={irrigationCustom.soil_moisture}
                      onChange={(e) => setIrrigationCustom({ ...irrigationCustom, soil_moisture: parseFloat(e.target.value) || 0 })}
                      className="w-full px-3 py-1.5 text-xs rounded-xl border border-slate-200 focus:outline-emerald-600"
                      required
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">Recent Rain (mm)</label>
                      <input
                        type="number"
                        step="any"
                        min="0"
                        value={irrigationCustom.recent_rainfall_mm}
                        onChange={(e) => setIrrigationCustom({ ...irrigationCustom, recent_rainfall_mm: parseFloat(e.target.value) || 0 })}
                        className="w-full px-3 py-1.5 text-xs rounded-xl border border-slate-200 focus:outline-emerald-600"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">Temp (°C)</label>
                      <input
                        type="number"
                        step="any"
                        value={irrigationCustom.temperature}
                        onChange={(e) => setIrrigationCustom({ ...irrigationCustom, temperature: parseFloat(e.target.value) || 0 })}
                        className="w-full px-3 py-1.5 text-xs rounded-xl border border-slate-200 focus:outline-emerald-600"
                      />
                    </div>
                  </div>
                </div>
              )}

              <button
                type="submit"
                disabled={irrigationLoading || (useFieldLive && !selectedFieldId)}
                className="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-xl shadow-xs transition-colors flex items-center justify-center space-x-1.5"
              >
                <Droplets className="w-4 h-4" />
                <span>{irrigationLoading ? 'Computing Agronomic Water Deficit...' : 'Calculate Irrigation Requirement'}</span>
              </button>
            </form>
          </div>

          {/* Results */}
          <div className="lg:col-span-2 space-y-6">
            {irrigationResult ? (
              <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-5">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <div>
                    <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                      Agronomic Action
                    </span>
                    <div className="flex items-center space-x-2 mt-1">
                      <span
                        className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-extrabold tracking-wide ${
                          irrigationResult.action === 'IRRIGATE_IMMEDIATELY'
                            ? 'bg-rose-100 text-rose-800'
                            : irrigationResult.action === 'IRRIGATE_LIGHT'
                            ? 'bg-blue-100 text-blue-800'
                            : irrigationResult.action === 'DEFER_DUE_TO_RAIN'
                            ? 'bg-cyan-100 text-cyan-800'
                            : 'bg-emerald-100 text-emerald-800'
                        }`}
                      >
                        {irrigationResult.action.replace(/_/g, ' ')}
                      </span>
                      <span className="text-xs font-semibold text-slate-500">
                        Urgency: {irrigationResult.urgency}
                      </span>
                    </div>
                  </div>

                  <div className="text-right">
                    <span className="text-[11px] font-medium text-slate-400 block">Recommended Water</span>
                    <span className="text-2xl font-black text-slate-900">
                      {irrigationResult.recommended_water_mm} mm
                    </span>
                  </div>
                </div>

                {/* Plain English Reason */}
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-slate-700 text-xs leading-relaxed space-y-1">
                  <div className="font-semibold text-slate-900 flex items-center space-x-1.5">
                    <Info className="w-4 h-4 text-blue-600" />
                    <span>Explainability &amp; Rationale:</span>
                  </div>
                  <p>{irrigationResult.reason}</p>
                </div>

                {/* Factors Evaluated Table */}
                <div>
                  <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                    Evaluated Telemetry Factors
                  </h4>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                    <div className="p-2.5 bg-slate-50 rounded-xl">
                      <div className="text-slate-400 text-[10px]">Current Moisture</div>
                      <div className="font-bold text-slate-800">
                        {irrigationResult.factors_evaluated.current_soil_moisture_pct}%
                      </div>
                    </div>
                    <div className="p-2.5 bg-slate-50 rounded-xl">
                      <div className="text-slate-400 text-[10px]">Critical Threshold</div>
                      <div className="font-bold text-slate-800">
                        {irrigationResult.factors_evaluated.critical_threshold_pct}%
                      </div>
                    </div>
                    <div className="p-2.5 bg-slate-50 rounded-xl">
                      <div className="text-slate-400 text-[10px]">Optimal Target</div>
                      <div className="font-bold text-slate-800">
                        {irrigationResult.factors_evaluated.optimal_target_pct}%
                      </div>
                    </div>
                    <div className="p-2.5 bg-slate-50 rounded-xl">
                      <div className="text-slate-400 text-[10px]">Sensor Freshness</div>
                      <div className="font-bold text-slate-800 capitalize">
                        {irrigationResult.sensor_freshness}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Disclaimer */}
                <div className="p-3 rounded-xl bg-amber-50/70 border border-amber-200 text-[11px] text-amber-900 space-y-0.5">
                  <div className="font-semibold">Safety &amp; Actuation Boundary:</div>
                  <p>{irrigationResult.limitations}</p>
                </div>
              </div>
            ) : (
              <div className="bg-white p-10 rounded-2xl border border-slate-200/80 shadow-xs text-center flex flex-col items-center justify-center space-y-2 text-slate-400">
                <Droplets className="w-10 h-10 text-blue-200" />
                <p className="text-sm font-medium text-slate-600">No irrigation recommendation evaluated yet.</p>
                <p className="text-xs max-w-sm">
                  Select a monitored field or enter custom moisture metrics to calculate water requirement according to FAO-56.
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
