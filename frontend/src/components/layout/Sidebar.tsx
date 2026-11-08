import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  MapPin,
  Wheat,
  Cpu,
  Activity,
  CloudRain,
  ShieldCheck,
  Settings,
  Sparkles,
  User,
  LogOut,
  UserCircle,
  CalendarClock,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/schedules', label: 'Irrigation Schedules', icon: CalendarClock },
  { to: '/fields', label: 'Field Monitoring', icon: MapPin },
  { to: '/recommendations', label: 'AI Advisory & Crops', icon: Sparkles },
  { to: '/farmers', label: 'Farmers', icon: Users },
  { to: '/crops', label: 'Crops', icon: Wheat },
  { to: '/sensors', label: 'Sensors', icon: Cpu },
  { to: '/readings', label: 'Readings History', icon: Activity },
  { to: '/weather', label: 'Weather Data', icon: CloudRain },
  { to: '/data-quality', label: 'Data Quality', icon: ShieldCheck },
  { to: '/status', label: 'System Status', icon: Settings },
];

export const Sidebar: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <aside className="w-64 bg-emerald-950 text-emerald-100 flex flex-col shrink-0 min-h-[calc(100vh-61px)] shadow-md">
      {/* Clickable Profile Card leading to /profile */}
      {user ? (
        <div className="p-4 border-b border-emerald-900/60 bg-emerald-900/30">
          <div className="flex items-center space-x-3">
            <NavLink
              to="/profile"
              className="flex items-center space-x-3 min-w-0 flex-1 group"
              title="View your profile"
            >
              <div className="w-10 h-10 rounded-full bg-emerald-500/20 border border-emerald-400/40 flex items-center justify-center text-emerald-300 font-bold text-base shrink-0 group-hover:scale-105 transition-transform">
                {user.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-semibold text-white truncate group-hover:text-emerald-300 transition-colors">
                  {user.full_name}
                </p>
                <p className="text-[11px] text-emerald-400/80 truncate">
                  {user.email}
                </p>
                <div className="flex items-center space-x-1.5 mt-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-lime-400 inline-block animate-pulse" />
                  <span className="text-[10px] text-emerald-300 font-medium tracking-wide">View Profile &rarr;</span>
                </div>
              </div>
            </NavLink>
            <button
              onClick={logout}
              title="Sign out"
              className="p-1.5 text-emerald-400 hover:text-rose-400 hover:bg-emerald-900/60 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      ) : (
        <div className="p-4 border-b border-emerald-900/60 bg-emerald-900/30">
          <NavLink
            to="/profile"
            className="flex items-center space-x-2 text-xs font-medium text-emerald-300 hover:text-white"
          >
            <UserCircle className="w-5 h-5 text-emerald-400" />
            <span>Profile</span>
          </NavLink>
        </div>
      )}

      <nav className="p-3 space-y-1 flex-1">
        <div className="px-3 py-2 text-[10px] font-bold uppercase tracking-wider text-emerald-400/80">
          Irrigation Operations
        </div>

        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center space-x-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-emerald-600 text-white shadow-sm shadow-emerald-900/50'
                    : 'text-emerald-300 hover:text-white hover:bg-emerald-900/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="p-4 border-t border-emerald-900/60 text-[11px] text-emerald-400/70">
        <p className="mt-0.5">IoT Ingestion &bull; Relational Data &bull; TimescaleDB &bull; Data Quality</p>
      </div>
    </aside>
  );
};
