import React, { useEffect, useState, useMemo } from 'react';
import {
  CalendarClock,
  CheckCircle2,
  XCircle,
  Clock,
  Plus,
  RefreshCw,
  Droplets,
  AlertTriangle,
  Sparkles,
  Filter,
  Check,
  Calendar,
} from 'lucide-react';
import {
  getIrrigationSchedules,
  generateIrrigationSchedule,
  updateIrrigationScheduleStatus,
  createIrrigationSchedule,
  getFields,
  getErrorMessage,
} from '../services/api';
import type { IrrigationSchedule, Field } from '../types';

export const IrrigationSchedulePage: React.FC = () => {
  const [schedules, setSchedules] = useState<IrrigationSchedule[]>([]);
  const [fields, setFields] = useState<Field[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [generating, setGenerating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Filter states
  const [statusFilter, setStatusFilter] = useState<'all' | 'pending' | 'completed' | 'skipped'>('all');
  const [selectedFieldId, setSelectedFieldId] = useState<string>('all');
  const [showOnlyToday, setShowOnlyToday] = useState<boolean>(false);

  // Manual modal state
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [newSchedule, setNewSchedule] = useState({
    field_id: '',
    recommended_date: new Date().toISOString().split('T')[0],
    recommended_time: '06:00',
    duration_minutes: 30,
    water_quantity_liters: 1200,
    priority: 'normal',
    reason: 'Routine scheduled irrigation',
  });

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [schedList, fieldList] = await Promise.all([
        getIrrigationSchedules(),
        getFields(),
      ]);
      setSchedules(schedList);
      setFields(fieldList);
      if (fieldList.length > 0 && !newSchedule.field_id) {
        setNewSchedule((prev) => ({ ...prev, field_id: fieldList[0].field_id }));
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

  const handleStatusChange = async (scheduleId: string, newStatus: 'pending' | 'completed' | 'skipped') => {
    try {
      setError(null);
      const updated = await updateIrrigationScheduleStatus(scheduleId, newStatus);
      setSchedules((prev) =>
        prev.map((s) => (s.schedule_id === scheduleId ? updated : s))
      );
      setSuccessMsg(`Schedule status marked as ${newStatus}.`);
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const handleGenerateSchedule = async (fieldId: string) => {
    try {
      setGenerating(true);
      setError(null);
      const gen = await generateIrrigationSchedule(fieldId);
      setSchedules((prev) => [gen, ...prev.filter((s) => s.schedule_id !== gen.schedule_id)]);
      setSuccessMsg(`Generated AI/FAO-56 Irrigation Schedule for field ${fieldId}!`);
      setTimeout(() => setSuccessMsg(null), 3500);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setGenerating(false);
    }
  };

  const handleCreateManual = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSchedule.field_id) {
      setError('Please select a target field');
      return;
    }
    try {
      setLoading(true);
      const created = await createIrrigationSchedule({
        field_id: newSchedule.field_id,
        recommended_date: newSchedule.recommended_date,
        recommended_time: newSchedule.recommended_time,
        duration_minutes: Number(newSchedule.duration_minutes),
        water_quantity_liters: Number(newSchedule.water_quantity_liters),
        priority: newSchedule.priority,
        reason: newSchedule.reason,
      });
      setSchedules((prev) => [created, ...prev]);
      setShowAddModal(false);
      setSuccessMsg('Irrigation event scheduled successfully.');
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const todayStr = useMemo(() => new Date().toISOString().split('T')[0], []);

  const filteredSchedules = useMemo(() => {
    return schedules.filter((s) => {
      if (statusFilter !== 'all' && s.status !== statusFilter) return false;
      if (selectedFieldId !== 'all' && s.field_id !== selectedFieldId) return false;
      if (showOnlyToday) {
        const itemDate = (s.recommended_date || '').split('T')[0];
        if (itemDate !== todayStr) return false;
      }
      return true;
    });
  }, [schedules, statusFilter, selectedFieldId, showOnlyToday, todayStr]);

  // Aggregate metrics
  const todaySchedules = schedules.filter((s) => (s.recommended_date || '').split('T')[0] === todayStr);
  const pendingCount = schedules.filter((s) => s.status === 'pending').length;
  const completedCount = schedules.filter((s) => s.status === 'completed').length;
  const totalWaterPending = schedules
    .filter((s) => s.status === 'pending')
    .reduce((acc, curr) => acc + (curr.water_quantity_liters || 0), 0);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-10">
      {/* Header section */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <CalendarClock className="w-6 h-6" />
            </span>
            <h1 className="text-2xl font-bold text-white tracking-tight">Today's Irrigation Schedule</h1>
          </div>
          <p className="text-sm text-emerald-300/70 mt-1">
            Automated FAO-56 crop water scheduling, event tracking, and pump actuation management
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center space-x-2 px-3 py-2 rounded-xl bg-emerald-900/40 hover:bg-emerald-900/70 border border-emerald-700/50 text-emerald-300 text-xs font-medium transition-all"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          {fields.length > 0 && (
            <button
              onClick={() => handleGenerateSchedule(fields[0].field_id)}
              disabled={generating}
              className="flex items-center space-x-2 px-3 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-semibold shadow-sm shadow-emerald-950 transition-all disabled:opacity-50"
            >
              <Sparkles className={`w-3.5 h-3.5 ${generating ? 'animate-spin' : ''}`} />
              <span>AI Auto-Schedule</span>
            </button>
          )}

          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center space-x-1.5 px-3 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-emerald-950 text-xs font-bold transition-all shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Schedule</span>
          </button>
        </div>
      </div>

      {/* Alert banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 flex items-center justify-between text-sm">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-rose-400 hover:text-rose-200">
            &times;
          </button>
        </div>
      )}

      {successMsg && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 flex items-center space-x-2 text-xs font-medium">
          <Check className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-emerald-950/40 border border-emerald-800/40 backdrop-blur-md">
          <div className="flex items-center justify-between">
            <p className="text-xs font-medium text-emerald-400/80">Scheduled Today</p>
            <Calendar className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-2xl font-bold text-white mt-2">{todaySchedules.length} <span className="text-xs font-normal text-emerald-400/70">events</span></p>
          <p className="text-[11px] text-emerald-400/60 mt-1">Synchronized with FAO-56 model</p>
        </div>

        <div className="p-4 rounded-2xl bg-emerald-950/40 border border-emerald-800/40 backdrop-blur-md">
          <div className="flex items-center justify-between">
            <p className="text-xs font-medium text-amber-400/90">Pending Actions</p>
            <Clock className="w-4 h-4 text-amber-400" />
          </div>
          <p className="text-2xl font-bold text-amber-300 mt-2">{pendingCount}</p>
          <p className="text-[11px] text-amber-400/70 mt-1">Awaiting pump actuation</p>
        </div>

        <div className="p-4 rounded-2xl bg-emerald-950/40 border border-emerald-800/40 backdrop-blur-md">
          <div className="flex items-center justify-between">
            <p className="text-xs font-medium text-emerald-400/80">Completed Runs</p>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-2xl font-bold text-emerald-300 mt-2">{completedCount}</p>
          <p className="text-[11px] text-emerald-400/60 mt-1">Water delivery verified</p>
        </div>

        <div className="p-4 rounded-2xl bg-emerald-950/40 border border-emerald-800/40 backdrop-blur-md">
          <div className="flex items-center justify-between">
            <p className="text-xs font-medium text-cyan-400/80">Water to Dispense</p>
            <Droplets className="w-4 h-4 text-cyan-400" />
          </div>
          <p className="text-2xl font-bold text-cyan-300 mt-2">
            {totalWaterPending.toLocaleString()} <span className="text-xs font-normal text-cyan-400/70">L</span>
          </p>
          <p className="text-[11px] text-cyan-400/60 mt-1">Optimal root zone replenishment</p>
        </div>
      </div>

      {/* Filter and Control Bar */}
      <div className="p-3.5 rounded-2xl bg-emerald-950/30 border border-emerald-800/30 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center space-x-1 px-2.5 py-1.5 rounded-xl bg-emerald-900/40 text-emerald-300 border border-emerald-700/40">
            <Filter className="w-3.5 h-3.5 text-emerald-400" />
            <span className="font-semibold text-[11px]">Filters:</span>
          </div>

          <button
            onClick={() => setShowOnlyToday(!showOnlyToday)}
            className={`px-3 py-1.5 rounded-xl font-medium transition-all ${
              showOnlyToday
                ? 'bg-emerald-500 text-emerald-950 font-bold'
                : 'bg-emerald-900/40 text-emerald-300 hover:bg-emerald-900/60'
            }`}
          >
            Today's Only
          </button>

          {(['all', 'pending', 'completed', 'skipped'] as const).map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`capitalize px-3 py-1.5 rounded-xl font-medium transition-all ${
                statusFilter === status
                  ? 'bg-emerald-600 text-white font-bold'
                  : 'bg-emerald-900/40 text-emerald-300 hover:bg-emerald-900/60'
              }`}
            >
              {status}
            </button>
          ))}
        </div>

        <div className="flex items-center space-x-2">
          <label className="text-emerald-400/80 text-[11px] font-medium">Field:</label>
          <select
            value={selectedFieldId}
            onChange={(e) => setSelectedFieldId(e.target.value)}
            className="bg-emerald-900/60 border border-emerald-700/50 rounded-xl px-2.5 py-1 text-emerald-200 text-xs focus:ring-1 focus:ring-emerald-400 focus:outline-none"
          >
            <option value="all">All Fields</option>
            {fields.map((f) => (
              <option key={f.field_id} value={f.field_id}>
                {f.name} ({f.crop_type})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Schedule Table / List */}
      <div className="rounded-2xl border border-emerald-800/40 bg-emerald-950/30 overflow-hidden shadow-sm">
        <div className="px-5 py-4 border-b border-emerald-800/40 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-emerald-200">
            Irrigation Plan & Actuation Logs ({filteredSchedules.length})
          </h2>
          <span className="text-[11px] text-emerald-400/70">
            Status: <span className="text-amber-300 font-medium">Pending</span> &bull;{' '}
            <span className="text-emerald-300 font-medium">Completed</span> &bull;{' '}
            <span className="text-slate-400 font-medium">Skipped</span>
          </span>
        </div>

        {loading ? (
          <div className="p-12 text-center text-emerald-400/70 space-y-3">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto text-emerald-400" />
            <p className="text-xs">Loading irrigation schedules...</p>
          </div>
        ) : filteredSchedules.length === 0 ? (
          <div className="p-12 text-center text-emerald-400/70 space-y-3">
            <CalendarClock className="w-10 h-10 mx-auto text-emerald-600/50" />
            <p className="text-sm font-medium text-emerald-300">No irrigation schedules found matching your filter</p>
            <p className="text-xs text-emerald-400/60 max-w-sm mx-auto">
              Generate a recommendation using AI or add a manual irrigation schedule for your field.
            </p>
            {fields.length > 0 && (
              <button
                onClick={() => handleGenerateSchedule(fields[0].field_id)}
                className="mt-3 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold"
              >
                Auto-Generate for {fields[0].name}
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-emerald-900/40 text-emerald-300/80 font-semibold uppercase text-[10px] tracking-wider border-b border-emerald-800/40">
                <tr>
                  <th className="px-4 py-3">Schedule ID / Target</th>
                  <th className="px-4 py-3">Date & Time</th>
                  <th className="px-4 py-3">Duration & Volume</th>
                  <th className="px-4 py-3">Priority</th>
                  <th className="px-4 py-3">Agronomic Reason</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Quick Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-emerald-800/30 text-emerald-100">
                {filteredSchedules.map((item) => {
                  const targetField = fields.find((f) => f.field_id === item.field_id);
                  const isPending = item.status === 'pending';
                  const isCompleted = item.status === 'completed';
                  const isSkipped = item.status === 'skipped';

                  return (
                    <tr
                      key={item.schedule_id}
                      className="hover:bg-emerald-900/20 transition-colors"
                    >
                      <td className="px-4 py-3.5 font-medium">
                        <div className="flex flex-col">
                          <span className="text-white font-semibold">
                            {targetField ? targetField.name : item.field_id}
                          </span>
                          <span className="text-[10px] text-emerald-400/70 font-mono">
                            {item.schedule_id} &bull; {targetField?.crop_type || 'Crop'}
                          </span>
                        </div>
                      </td>

                      <td className="px-4 py-3.5">
                        <div className="flex flex-col">
                          <span className="text-emerald-200">
                            {(item.recommended_date || '').split('T')[0]}
                          </span>
                          <span className="text-[10px] text-emerald-400/70 font-mono">
                            {item.recommended_time || '06:00'} hrs
                          </span>
                        </div>
                      </td>

                      <td className="px-4 py-3.5">
                        <div className="flex flex-col">
                          <span className="text-white font-medium">
                            {item.water_quantity_liters?.toLocaleString()} L
                          </span>
                          <span className="text-[10px] text-emerald-400/70">
                            {item.duration_minutes} mins run
                          </span>
                        </div>
                      </td>

                      <td className="px-4 py-3.5">
                        <span
                          className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                            item.priority === 'high'
                              ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                              : item.priority === 'medium'
                              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                              : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                          }`}
                        >
                          {item.priority || 'normal'}
                        </span>
                      </td>

                      <td className="px-4 py-3.5 max-w-xs">
                        <p className="text-xs text-emerald-200/90 truncate" title={item.reason || ''}>
                          {item.reason || 'Optimal soil moisture balancing'}
                        </p>
                      </td>

                      <td className="px-4 py-3.5">
                        <span
                          className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-[11px] font-semibold ${
                            isCompleted
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                              : isPending
                              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                              : 'bg-slate-700/40 text-slate-400 border border-slate-600/40'
                          }`}
                        >
                          {isCompleted && <CheckCircle2 className="w-3 h-3 text-emerald-400" />}
                          {isPending && <Clock className="w-3 h-3 text-amber-400" />}
                          {isSkipped && <XCircle className="w-3 h-3 text-slate-400" />}
                          <span className="capitalize">{item.status}</span>
                        </span>
                      </td>

                      <td className="px-4 py-3.5 text-right">
                        <div className="flex items-center justify-end space-x-1.5">
                          {isPending && (
                            <>
                              <button
                                onClick={() => handleStatusChange(item.schedule_id, 'completed')}
                                title="Mark as Completed"
                                className="px-2.5 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] font-medium transition-colors flex items-center space-x-1"
                              >
                                <Check className="w-3 h-3" />
                                <span>Complete</span>
                              </button>
                              <button
                                onClick={() => handleStatusChange(item.schedule_id, 'skipped')}
                                title="Skip schedule"
                                className="px-2.5 py-1 rounded-lg bg-emerald-900/60 hover:bg-rose-900/60 border border-emerald-700/40 hover:border-rose-700/40 text-emerald-300 hover:text-rose-200 text-[11px] transition-colors"
                              >
                                Skip
                              </button>
                            </>
                          )}
                          {!isPending && (
                            <button
                              onClick={() => handleStatusChange(item.schedule_id, 'pending')}
                              title="Re-open schedule"
                              className="text-[10px] text-emerald-400/80 hover:text-emerald-200 underline"
                            >
                              Reset to Pending
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Manual Schedule Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl bg-emerald-950 border border-emerald-700/60 p-6 shadow-2xl text-white space-y-4">
            <div className="flex items-center justify-between border-b border-emerald-800/60 pb-3">
              <h3 className="text-base font-bold text-white flex items-center space-x-2">
                <CalendarClock className="w-5 h-5 text-emerald-400" />
                <span>Create Irrigation Schedule</span>
              </h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-emerald-400 hover:text-white text-lg font-bold"
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleCreateManual} className="space-y-4 text-xs">
              <div>
                <label className="block text-emerald-300 font-medium mb-1">Target Field *</label>
                <select
                  value={newSchedule.field_id}
                  onChange={(e) => setNewSchedule({ ...newSchedule, field_id: e.target.value })}
                  className="w-full bg-emerald-900/60 border border-emerald-700 rounded-xl px-3 py-2 text-white text-xs focus:ring-1 focus:ring-emerald-400"
                  required
                >
                  {fields.map((f) => (
                    <option key={f.field_id} value={f.field_id}>
                      {f.name} ({f.crop_type}) - {f.location_name || f.field_id}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-emerald-300 font-medium mb-1">Date *</label>
                  <input
                    type="date"
                    value={newSchedule.recommended_date}
                    onChange={(e) => setNewSchedule({ ...newSchedule, recommended_date: e.target.value })}
                    className="w-full bg-emerald-900/60 border border-emerald-700 rounded-xl px-3 py-2 text-white text-xs focus:ring-1 focus:ring-emerald-400"
                    required
                  />
                </div>
                <div>
                  <label className="block text-emerald-300 font-medium mb-1">Time (24h) *</label>
                  <input
                    type="time"
                    value={newSchedule.recommended_time}
                    onChange={(e) => setNewSchedule({ ...newSchedule, recommended_time: e.target.value })}
                    className="w-full bg-emerald-900/60 border border-emerald-700 rounded-xl px-3 py-2 text-white text-xs focus:ring-1 focus:ring-emerald-400"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-emerald-300 font-medium mb-1">Duration (Minutes)</label>
                  <input
                    type="number"
                    min="1"
                    value={newSchedule.duration_minutes}
                    onChange={(e) => setNewSchedule({ ...newSchedule, duration_minutes: Number(e.target.value) })}
                    className="w-full bg-emerald-900/60 border border-emerald-700 rounded-xl px-3 py-2 text-white text-xs focus:ring-1 focus:ring-emerald-400"
                    required
                  />
                </div>
                <div>
                  <label className="block text-emerald-300 font-medium mb-1">Water Quantity (Liters)</label>
                  <input
                    type="number"
                    min="1"
                    value={newSchedule.water_quantity_liters}
                    onChange={(e) => setNewSchedule({ ...newSchedule, water_quantity_liters: Number(e.target.value) })}
                    className="w-full bg-emerald-900/60 border border-emerald-700 rounded-xl px-3 py-2 text-white text-xs focus:ring-1 focus:ring-emerald-400"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-emerald-300 font-medium mb-1">Priority</label>
                  <select
                    value={newSchedule.priority}
                    onChange={(e) => setNewSchedule({ ...newSchedule, priority: e.target.value })}
                    className="w-full bg-emerald-900/60 border border-emerald-700 rounded-xl px-3 py-2 text-white text-xs focus:ring-1 focus:ring-emerald-400"
                  >
                    <option value="normal">Normal</option>
                    <option value="medium">Medium</option>
                    <option value="high">High (Urgent)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-emerald-300 font-medium mb-1">Agronomic Reason</label>
                  <input
                    type="text"
                    value={newSchedule.reason}
                    onChange={(e) => setNewSchedule({ ...newSchedule, reason: e.target.value })}
                    className="w-full bg-emerald-900/60 border border-emerald-700 rounded-xl px-3 py-2 text-white text-xs focus:ring-1 focus:ring-emerald-400"
                    placeholder="e.g. Vegetative moisture top-up"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end space-x-2 pt-3 border-t border-emerald-800/60">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3.5 py-2 rounded-xl bg-emerald-900/40 hover:bg-emerald-900/70 border border-emerald-700/50 text-emerald-300 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-emerald-950 text-xs font-bold transition-all shadow-sm"
                >
                  Save Schedule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

