import React from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Shield, FolderOpen, LogOut, User } from 'lucide-react';

const SidebarLayout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex h-screen w-screen bg-gray-950 text-gray-100 overflow-hidden font-sans">
      {/* Absolute background glowing accent */}
      <div className="absolute top-0 left-0 w-96 h-96 bg-accent/5 rounded-full filter blur-3xl pointer-events-none" />

      {/* Sidebar Navigation */}
      <aside className="w-64 bg-gray-900/80 backdrop-blur-md border-r border-gray-800/80 flex flex-col justify-between z-10">
        <div>
          {/* Sidebar Header */}
          <div className="p-6 flex items-center gap-3 border-b border-gray-800/60">
            <div className="w-10 h-10 bg-accent/20 border border-accent/40 rounded-lg flex items-center justify-center">
              <Shield className="w-5 h-5 text-accent animate-pulse" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white tracking-wide">ForenSight AI</h2>
              <span className="text-[10px] text-accent font-semibold uppercase tracking-widest">
                SOC Core Engine
              </span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-4 space-y-1">
            <NavLink
              to="/"
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition-all duration-200 cursor-pointer ${
                  isActive
                    ? 'bg-accent/15 text-accent border-l-4 border-accent shadow-[inset_0_0_8px_rgba(170,59,255,0.05)]'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
                }`
              }
            >
              <FolderOpen className="w-4 h-4" />
              Investigations
            </NavLink>
          </nav>
        </div>

        {/* Analyst Profile Section */}
        <div className="p-4 border-t border-gray-800/60 bg-gray-900/40">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-gray-800 border border-gray-700 rounded-full flex items-center justify-center text-gray-400 shadow-inner">
              <User className="w-5 h-5" />
            </div>
            <div className="min-w-0 flex-1">
              <h4 className="text-xs font-bold text-white truncate">
                {user?.username || 'Analyst'}
              </h4>
              <span className="text-[9px] px-1.5 py-0.5 bg-gray-800 border border-gray-700 text-gray-300 rounded font-mono uppercase tracking-wider">
                {user?.role || 'investigator'}
              </span>
            </div>
          </div>

          {/* Logout Action */}
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 py-2 px-4 border border-red-500/30 hover:border-red-500 bg-red-950/20 hover:bg-red-900/30 text-red-200 hover:text-white text-xs font-semibold rounded-lg transition-all duration-200 cursor-pointer"
          >
            <LogOut className="w-3.5 h-3.5" />
            Sign Out Session
          </button>
        </div>
      </aside>

      {/* Main Viewport Content right component */}
      <main className="flex-1 flex flex-col overflow-y-auto relative z-0">
        <Outlet />
      </main>
    </div>
  );
};

export default SidebarLayout;
