// Navbar component with backend status, seed demo action, Swagger link, and Logout button
import React, { useEffect, useState } from 'react';
import { Sprout, Sparkles, ExternalLink, LogOut } from 'lucide-react';
import { Link } from 'react-router-dom';
import './Navbar.css';
import { useAuth } from '../../context/AuthContext';
import { getHealth, seedDemoData, API_DOCS_URL } from '../../services/api';

interface NavbarProps {
  onRefresh?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onRefresh }) => {
  const { user, logout } = useAuth();
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [seeding, setSeeding] = useState(false);
  const [seedNotice, setSeedNotice] = useState<string | null>(null);

  const checkStatus = async () => {
    try {
      const res = await getHealth();
      setBackendOnline(res?.status === 'ok');
    } catch {
      setBackendOnline(false);
    }
  };

  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleSeed = async () => {
    if (!window.confirm('Load sample simulated demo data? All records will be clearly marked as is_demo/is_simulated.')) {
      return;
    }
    setSeeding(true);
    try {
      const res = await seedDemoData();
      setSeedNotice(res.status === 'already_seeded' ? 'Demo records already present.' : 'Demo records loaded!');
      setTimeout(() => setSeedNotice(null), 4000);
      if (onRefresh) onRefresh();
    } catch {
      setSeedNotice('Failed to seed demo data');
      setTimeout(() => setSeedNotice(null), 4000);
    } finally {
      setSeeding(false);
    }
  };

  return (
    <header className="sticky top-0 z-40 bg-white border-b border-emerald-100/80 shadow-xs">
      <div className="flex items-center justify-between px-6 py-3">
        {/* Logo and branding */}
        <div className="flex items-center space-x-3">
          <Link to="/" className="flex items-center space-x-2.5 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-700 to-emerald-500 flex items-center justify-center text-white shadow-sm shadow-emerald-500/20 group-hover:scale-105 transition-transform">
              <Sprout className="w-6 h-6" />
            </div>
            <div>
              <span className="font-bold text-lg text-slate-800 tracking-tight block leading-none">
                AgriPulse <span className="text-emerald-600 font-semibold text-sm"></span>
              </span>
              <span className="text-[11px] text-slate-600 font-medium">Smart Irrigation & Water Management</span>
            </div>
          </Link>
        </div>
        {/* Right side controls */}
        <div className="flex items-center space-x-3">
          {/* Backend status pill */}
          <div
            className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium border ${
              backendOnline === true
                ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                : backendOnline === false
                ? 'bg-rose-50 border-rose-200 text-rose-800'
                : 'bg-slate-50 border-slate-200 text-slate-600'
            }`}
          >
            {backendOnline === true ? (
              <>
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span>Backend Connected</span>
              </>
            ) : backendOnline === false ? (
              <>
                <span className="w-2 h-2 rounded-full bg-rose-500" />
                <span>Backend Offline</span>
              </>
            ) : (
              <span>Checking...</span>
            )}
          </div>
          {/* Load Demo Data button */}
          <button
            onClick={handleSeed}
            disabled={seeding || backendOnline === false}
            title="Seed simulated test dataset"
            className={`inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-md transition-colors 
              ${seeding ? 'bg-emerald-700 text-white' : 'bg-emerald-600 text-white'}
              ${(!seeding && (backendOnline === false)) ? 'bg-emerald-300 text-emerald-600 cursor-not-allowed' : ''}
            `}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{seeding ? 'Seeding...' : 'Load Demo Data'}</span>
          </button>

          {seedNotice && <span className="text-xs text-slate-500">{seedNotice}</span>}
          {/* Swagger API link */}
          <a
            href={API_DOCS_URL}
            target="_blank"
            rel="noreferrer"
            className="swagger-api-link"
          >
            <span>Swagger API</span>
            <ExternalLink />
          </a>
          {/* Logout button if authenticated */}
          {user ? (
            <button
              onClick={logout}
              className="flex items-center space-x-1 px-2.5 py-1.5 text-xs text-red-700 bg-red-50 border border-red-200 rounded-md hover:bg-red-100 font-semibold focus:outline-none focus-visible:ring-2 focus-visible:ring-red-500 transition-colors"
            >
              <LogOut className="w-3 h-3" />
              <span>Logout</span>
            </button>
          ) : (
            <Link
              to="/signin"
              className="flex items-center space-x-1 px-3 py-1.5 text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-md hover:bg-emerald-100 font-semibold transition-colors"
            >
              <span>Sign In</span>
            </Link>
          )}
        </div>
      </div>
    </header>
  );
};
