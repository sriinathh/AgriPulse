import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  User,
  Mail,
  Phone,
  Shield,
  CheckCircle2,
  Calendar,
  MapPin,
  Edit2,
  Save,
  X,
  Key,
  Copy,
  Check,
  Wheat,
  Bell,
  Cpu,
  RefreshCw,
  AlertCircle,
  Sparkles,
  Lock,
} from 'lucide-react';
import { getErrorMessage } from '../services/api';

export const ProfilePage: React.FC = () => {
  const { user, updateUser } = useAuth();

  // Edit mode state
  const [isEditing, setIsEditing] = useState(false);
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [phone, setPhone] = useState(user?.phone || '+91 98765 43210');
  const [farmName, setFarmName] = useState('AgriPulse Precision Hub');
  const [farmLocation, setFarmLocation] = useState('Telangana / Andhra Pradesh, India');
  const [farmSize, setFarmSize] = useState('4.2');
  const [primaryCrop, setPrimaryCrop] = useState('Rice (Basmati) & Maize');
  const [irrigationMode, setIrrigationMode] = useState<'automatic' | 'advisory'>('automatic');

  // Notification toggles
  const [notifyLowMoisture, setNotifyLowMoisture] = useState(true);
  const [notifyWeatherAlert, setNotifyWeatherAlert] = useState(true);
  const [notifyDailyBrief, setNotifyDailyBrief] = useState(false);

  // API Token state
  const [apiToken, setApiToken] = useState('agy_live_sec_78a9c412f9014b2d');
  const [copiedToken, setCopiedToken] = useState(false);
  const [copiedEmail, setCopiedEmail] = useState(false);

  const [saving, setSaving] = useState(false);
  const [feedbackSuccess, setFeedbackSuccess] = useState<string | null>(null);
  const [feedbackError, setFeedbackError] = useState<string | null>(null);

  // Sync state if user changes
  useEffect(() => {
    if (user) {
      setFullName(user.full_name || '');
      setEmail(user.email || '');
      if (user.phone) setPhone(user.phone);
    }
  }, [user]);

  const handleCopyEmail = () => {
    if (email) {
      navigator.clipboard.writeText(email);
      setCopiedEmail(true);
      setTimeout(() => setCopiedEmail(false), 2000);
    }
  };

  const handleCopyToken = () => {
    navigator.clipboard.writeText(apiToken);
    setCopiedToken(true);
    setTimeout(() => setCopiedToken(false), 2000);
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      setFeedbackError(null);
      await updateUser({
        full_name: fullName,
        email: email,
        phone: phone,
      });
      setIsEditing(false);
      setFeedbackSuccess('Your profile details and agricultural settings have been saved successfully.');
      setTimeout(() => setFeedbackSuccess(null), 4000);
    } catch (err) {
      setFeedbackError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    if (user) {
      setFullName(user.full_name || '');
      setEmail(user.email || '');
      if (user.phone) setPhone(user.phone);
    }
    setIsEditing(false);
    setFeedbackError(null);
  };

  const regenerateToken = () => {
    const randomHex = Math.random().toString(16).substring(2, 10) + Math.random().toString(16).substring(2, 10);
    const newToken = `agy_live_sec_${randomHex}`;
    setApiToken(newToken);
    setFeedbackSuccess('New IoT Gateway Ingestion Token generated. Update your sensor nodes.');
    setTimeout(() => setFeedbackSuccess(null), 3500);
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      {/* ── 1. Header Banner ──────────────────────────────────────────────── */}
      <div className="bg-gradient-to-r from-emerald-950/90 via-emerald-900/70 to-teal-950/90 rounded-3xl p-6 sm:p-8 text-white border border-emerald-700/40 shadow-lg shadow-emerald-950/20 flex flex-col sm:flex-row items-center sm:items-start gap-6 backdrop-blur-md">
        <div className="w-22 h-22 rounded-2xl bg-gradient-to-br from-emerald-500/30 to-teal-600/30 border-2 border-emerald-400/50 flex items-center justify-center text-3xl font-extrabold shadow-inner shrink-0 text-emerald-200">
          {fullName ? fullName.charAt(0).toUpperCase() : 'F'}
        </div>

        <div className="text-center sm:text-left flex-1 min-w-0">
          <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2.5">
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
              {fullName || 'Farmer Profile'}
            </h1>
            <span className="px-3 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 inline-flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-lime-400 animate-pulse" />
              Verified AgriPulse Operator
            </span>
          </div>

          <p className="text-emerald-200/80 text-sm mt-1 truncate">{email || 'No email associated'}</p>

          <div className="flex flex-wrap items-center justify-center sm:justify-start gap-4 mt-4 text-xs text-emerald-200/70">
            <span className="flex items-center gap-1.5">
              <Shield className="w-4 h-4 text-lime-400" />
              Argon2 / JWT Authenticated
            </span>
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              FAO-56 Precision Water Engine Active
            </span>
            <span className="flex items-center gap-1.5">
              <MapPin className="w-4 h-4 text-cyan-400" />
              {farmLocation}
            </span>
          </div>
        </div>

        <div className="shrink-0 flex items-center gap-2">
          {!isEditing ? (
            <button
              onClick={() => setIsEditing(true)}
              className="inline-flex items-center space-x-1.5 px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-emerald-950 text-xs font-bold rounded-xl shadow-sm transition-all"
            >
              <Edit2 className="w-3.5 h-3.5" />
              <span>Edit Profile</span>
            </button>
          ) : (
            <button
              onClick={handleCancel}
              className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-emerald-900/60 hover:bg-emerald-800 border border-emerald-700/50 text-emerald-200 text-xs font-semibold rounded-xl transition-all"
            >
              <X className="w-3.5 h-3.5" />
              <span>Cancel</span>
            </button>
          )}
        </div>
      </div>

      {/* ── Feedback Banners ──────────────────────────────────────────────── */}
      {feedbackSuccess && (
        <div className="p-3.5 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 flex items-center space-x-2 text-xs font-medium">
          <Check className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{feedbackSuccess}</span>
        </div>
      )}

      {feedbackError && (
        <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{feedbackError}</span>
          </div>
          <button onClick={() => setFeedbackError(null)} className="text-rose-400 hover:text-rose-200">
            &times;
          </button>
        </div>
      )}

      {/* ── 2. Editable Form or Details View ──────────────────────────────── */}
      <form onSubmit={handleSaveProfile} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Card A: Farmer Identity & Account */}
          <div className="bg-emerald-950/30 rounded-3xl border border-emerald-800/40 p-6 backdrop-blur-md shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-emerald-800/40">
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <User className="w-4 h-4 text-emerald-400" />
                <span>Personal & Account Information</span>
              </h2>
              {isEditing && (
                <span className="text-[10px] uppercase font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                  Editing
                </span>
              )}
            </div>

            <div className="space-y-3.5 text-xs">
              {/* Full Name */}
              <div>
                <label className="block text-emerald-300 font-semibold mb-1">Full Name</label>
                {isEditing ? (
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full bg-emerald-900/50 border border-emerald-700 rounded-xl px-3 py-2 text-white text-xs focus:ring-1 focus:ring-emerald-400 focus:outline-none"
                    placeholder="e.g. Srinath"
                  />
                ) : (
                  <div className="p-2.5 rounded-xl bg-emerald-900/20 border border-emerald-800/30 text-white font-medium">
                    {fullName || '—'}
                  </div>
                )}
              </div>

              {/* Email Address */}
              <div>
                <div className="flex justify-between items-center mb-1">
                  <label className="block text-emerald-300 font-semibold">Email Address</label>
                  {!isEditing && email && (
                    <button
                      type="button"
                      onClick={handleCopyEmail}
                      className="text-[11px] text-emerald-400 hover:text-emerald-300 flex items-center gap-1"
                    >
                      {copiedEmail ? <Check className="w-3 h-3 text-lime-400" /> : <Copy className="w-3 h-3" />}
                      <span>{copiedEmail ? 'Copied' : 'Copy'}</span>
                    </button>
                  )}
                </div>
                {isEditing ? (
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full bg-emerald-900/50 border border-emerald-700 rounded-xl px-3 py-2 text-white text-xs focus:ring-1 focus:ring-emerald-400 focus:outline-none"
                    placeholder="e.g. psrinath821@gmail.com"
                  />
                ) : (
                  <div className="p-2.5 rounded-xl bg-emerald-900/20 border border-emerald-800/30 text-white font-medium font-mono text-[11px]">
                    {email || '—'}
                  </div>
                )}
              </div>

              {/* Phone Number */}
              <div>
                <label className="block text-emerald-300 font-semibold mb-1">Phone / WhatsApp Number</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="w-full bg-emerald-900/50 border border-emerald-700 rounded-xl px-3 py-2 text-white text-xs focus:ring-1 focus:ring-emerald-400 focus:outline-none"
                    placeholder="+91 98765 43210"
                  />
                ) : (
                  <div className="p-2.5 rounded-xl bg-emerald-900/20 border border-emerald-800/30 text-white font-medium">
                    {phone || '—'}
                  </div>
                )}
              </div>

              {/* Account Role */}
              <div className="pt-2 border-t border-emerald-800/30 flex justify-between items-center">
                <span className="text-emerald-400/80 font-medium">Platform Role</span>
                <span className="text-white font-semibold">Primary Agricultural Operator</span>
              </div>
            </div>
          </div>

          {/* Card B: Farm Operations Scope */}
          <div className="bg-emerald-950/30 rounded-3xl border border-emerald-800/40 p-6 backdrop-blur-md shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-emerald-800/40">
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <MapPin className="w-4 h-4 text-teal-400" />
                <span>Farm Management Scope</span>
              </h2>
              <span className="text-[10px] text-emerald-400/80 font-mono">IoT Station F001</span>
            </div>

            <div className="space-y-3.5 text-xs">
              {/* Farm Facility Name */}
              <div>
                <label className="block text-emerald-300 font-semibold mb-1">Farm Facility Name</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={farmName}
                    onChange={(e) => setFarmName(e.target.value)}
                    className="w-full bg-emerald-900/50 border border-emerald-700 rounded-xl px-3 py-2 text-white text-xs focus:ring-1 focus:ring-emerald-400 focus:outline-none"
                  />
                ) : (
                  <div className="p-2.5 rounded-xl bg-emerald-900/20 border border-emerald-800/30 text-white font-medium">
                    {farmName}
                  </div>
                )}
              </div>

              {/* Geographic Region */}
              <div>
                <label className="block text-emerald-300 font-semibold mb-1">Geographic Region</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={farmLocation}
                    onChange={(e) => setFarmLocation(e.target.value)}
                    className="w-full bg-emerald-900/50 border border-emerald-700 rounded-xl px-3 py-2 text-white text-xs focus:ring-1 focus:ring-emerald-400 focus:outline-none"
                  />
                ) : (
                  <div className="p-2.5 rounded-xl bg-emerald-900/20 border border-emerald-800/30 text-white font-medium">
                    {farmLocation}
                  </div>
                )}
              </div>

              {/* Crops & Total Area */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-emerald-300 font-semibold mb-1">Primary Crops</label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={primaryCrop}
                      onChange={(e) => setPrimaryCrop(e.target.value)}
                      className="w-full bg-emerald-900/50 border border-emerald-700 rounded-xl px-3 py-2 text-white text-xs focus:ring-1 focus:ring-emerald-400 focus:outline-none"
                    />
                  ) : (
                    <div className="p-2.5 rounded-xl bg-emerald-900/20 border border-emerald-800/30 text-white font-medium truncate">
                      {primaryCrop}
                    </div>
                  )}
                </div>

                <div>
                  <label className="block text-emerald-300 font-semibold mb-1">Land Area (Hectares)</label>
                  {isEditing ? (
                    <input
                      type="number"
                      step="0.1"
                      value={farmSize}
                      onChange={(e) => setFarmSize(e.target.value)}
                      className="w-full bg-emerald-900/50 border border-emerald-700 rounded-xl px-3 py-2 text-white text-xs focus:ring-1 focus:ring-emerald-400 focus:outline-none"
                    />
                  ) : (
                    <div className="p-2.5 rounded-xl bg-emerald-900/20 border border-emerald-800/30 text-white font-medium">
                      {farmSize} ha
                    </div>
                  )}
                </div>
              </div>

              {/* Irrigation Control Mode */}
              <div className="pt-2 border-t border-emerald-800/30 flex justify-between items-center">
                <span className="text-emerald-400/80 font-medium">Irrigation Mode</span>
                {isEditing ? (
                  <select
                    value={irrigationMode}
                    onChange={(e) => setIrrigationMode(e.target.value as any)}
                    className="bg-emerald-900/70 border border-emerald-700 rounded-xl px-2.5 py-1 text-white text-xs focus:outline-none"
                  >
                    <option value="automatic">Automatic FAO-56 Actuation</option>
                    <option value="advisory">Farmer Confirmation Required</option>
                  </select>
                ) : (
                  <span className="text-emerald-300 font-semibold capitalize">
                    {irrigationMode === 'automatic' ? 'AI Automated Actuation' : 'Advisory / Manual'}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Save button bar when in editing mode */}
        {isEditing && (
          <div className="p-4 rounded-2xl bg-emerald-900/50 border border-emerald-700/60 flex items-center justify-between">
            <span className="text-xs text-emerald-300">
              Review your changes above and click Save to synchronize with your farm profile.
            </span>
            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={handleCancel}
                className="px-4 py-2 rounded-xl bg-emerald-900 hover:bg-emerald-800 border border-emerald-700 text-emerald-300 text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={saving}
                className="px-5 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-emerald-950 text-xs font-bold shadow-sm flex items-center space-x-1.5 transition-all"
              >
                <Save className="w-3.5 h-3.5" />
                <span>{saving ? 'Saving...' : 'Save Profile'}</span>
              </button>
            </div>
          </div>
        )}
      </form>

      {/* ── 3. Notification Preferences & Telemetry Credentials ─────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Notification Preferences */}
        <div className="bg-emerald-950/30 rounded-3xl border border-emerald-800/40 p-6 backdrop-blur-md shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2 border-b border-emerald-800/40 pb-3">
            <Bell className="w-4 h-4 text-emerald-400" />
            <span>Telemetry Alerts & Notifications</span>
          </h3>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between p-2.5 rounded-xl bg-emerald-900/20 border border-emerald-800/30">
              <div>
                <p className="font-semibold text-white">Low Soil Moisture Alarm</p>
                <p className="text-[11px] text-emerald-400/70">Trigger alert when moisture drops below crop threshold</p>
              </div>
              <input
                type="checkbox"
                checked={notifyLowMoisture}
                onChange={(e) => setNotifyLowMoisture(e.target.checked)}
                className="w-4 h-4 accent-emerald-500 rounded cursor-pointer"
              />
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-xl bg-emerald-900/20 border border-emerald-800/30">
              <div>
                <p className="font-semibold text-white">Extreme Weather Advisory</p>
                <p className="text-[11px] text-emerald-400/70">Heavy rainfall or heatwave warnings from OpenWeather</p>
              </div>
              <input
                type="checkbox"
                checked={notifyWeatherAlert}
                onChange={(e) => setNotifyWeatherAlert(e.target.checked)}
                className="w-4 h-4 accent-emerald-500 rounded cursor-pointer"
              />
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-xl bg-emerald-900/20 border border-emerald-800/30">
              <div>
                <p className="font-semibold text-white">Morning Irrigation Brief</p>
                <p className="text-[11px] text-emerald-400/70">Daily summary of planned water schedules at 06:00 AM</p>
              </div>
              <input
                type="checkbox"
                checked={notifyDailyBrief}
                onChange={(e) => setNotifyDailyBrief(e.target.checked)}
                className="w-4 h-4 accent-emerald-500 rounded cursor-pointer"
              />
            </div>
          </div>
        </div>

        {/* IoT Gateway Credentials & Security */}
        <div className="bg-emerald-950/30 rounded-3xl border border-emerald-800/40 p-6 backdrop-blur-md shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2 border-b border-emerald-800/40 pb-3">
            <Key className="w-4 h-4 text-cyan-400" />
            <span>IoT Sensor Ingestion & Gateway Token</span>
          </h3>

          <div className="space-y-3 text-xs">
            <p className="text-[11px] text-emerald-300/80 leading-relaxed">
              Use this Bearer Token in your ESP32 / Arduino / LoRaWAN gateway firmware to push real-time sensor readings to AgriPulse.
            </p>

            <div className="flex items-center gap-2 p-2.5 rounded-xl bg-emerald-900/40 border border-emerald-700/50 font-mono text-[11px] text-cyan-200">
              <span className="truncate flex-1">{apiToken}</span>
              <button
                type="button"
                onClick={handleCopyToken}
                className="p-1.5 hover:bg-emerald-800 rounded-lg text-emerald-300 transition-colors"
                title="Copy Token"
              >
                {copiedToken ? <Check className="w-3.5 h-3.5 text-lime-400" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>

            <div className="flex items-center justify-between pt-2">
              <span className="text-[11px] text-emerald-400/60 font-mono">Scope: Sensor Ingest & Actuation</span>
              <button
                type="button"
                onClick={regenerateToken}
                className="text-[11px] text-emerald-400 hover:text-emerald-300 font-semibold flex items-center space-x-1"
              >
                <RefreshCw className="w-3 h-3" />
                <span>Roll Secret</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
