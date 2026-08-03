import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/layout/ProtectedRoute';
import SidebarLayout from './components/layout/SidebarLayout';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import CasesPage from './pages/CasesPage';
import CaseDetailsPage from './pages/CaseDetailsPage';

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
            <Route index element={<CasesPage />} />
            <Route path="cases/:caseId" element={<CaseDetailsPage />} />
          </Route>

          {/* Catch-all redirects */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
