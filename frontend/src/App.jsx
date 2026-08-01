import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import useAuth from './hooks/useAuth'

import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import OrganizationSetupPage from './pages/OrganizationSetupPage'
import DashboardPage from './pages/DashboardPage'
import CaseDetailPage from './pages/CaseDetailPage'
import ProfilePage from './pages/ProfilePage'
import AppShell from './components/layout/AppShell'

// Only redirect to login if there is NO token at all
const Protected = ({ children }) => {
  const { token } = useAuth()
  const location = useLocation()
  if (!token) return <Navigate to="/login" state={{ from: location }} replace />
  return children
}

const AppRoutes = () => {
  const { token, fetchMe } = useAuth()

  // Silently try to load the user profile on mount if token exists
  // Failure is ignored — the app stays on the protected route
  useEffect(() => {
    if (token) fetchMe()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <Routes>
      <Route path="/login"    element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/setup"    element={<OrganizationSetupPage />} />

      <Route element={<Protected><AppShell /></Protected>}>
        <Route path="/dashboard"          element={<DashboardPage />} />
        <Route path="/profile"            element={<ProfilePage />} />
        <Route path="/cases/:caseId/:tab" element={<CaseDetailPage />} />
        <Route path="/"                 element={<Navigate to="/dashboard" replace />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

const App = () => (
  <BrowserRouter>
    <AppRoutes />
  </BrowserRouter>
)

export default App
