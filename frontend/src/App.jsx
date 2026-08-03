import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import SidebarLayout from './components/SidebarLayout';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';

// Simple placeholder page for router validation
const CasesPlaceholder = () => (
  <div className="p-8 flex flex-col justify-center items-center h-full">
    <div className="max-w-2xl bg-gray-900 border border-gray-800 rounded-xl p-8 shadow-2xl text-center">
      <h2 className="text-2xl font-bold text-white mb-3">Welcome to ForenSight AI Dashboard</h2>
      <p className="text-gray-400 text-sm mb-6 leading-relaxed">
        Sprint 13 (Core Layout & Authentication) is successfully active. The authentication token handles state transitions, session verification, and API router routing.
      </p>
      <div className="flex gap-4 justify-center">
        <span className="px-3 py-1.5 bg-accent/20 border border-accent/40 text-accent rounded-lg text-xs font-semibold">
          Auth Hook: Active
        </span>
        <span className="px-3 py-1.5 bg-green-500/20 border border-green-500/40 text-green-300 rounded-lg text-xs font-semibold">
          Tailwind v4: Active
        </span>
      </div>
    </div>
  </div>
);

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public Access Routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Secure Workspace Client Outlets */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <SidebarLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<CasesPlaceholder />} />
            {/* Future sprint routes will be mapped here */}
            <Route path="cases/:caseId" element={<div>Case Detail View Placeholder</div>} />
          </Route>

          {/* Catch-all redirects */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
