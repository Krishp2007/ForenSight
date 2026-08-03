import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import apiClient from '../services/apiClient';
import { Shield, Mail, User, Lock, Building, Plus } from 'lucide-react';

const RegisterPage = () => {
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('investigator');
  
  // Organization States
  const [organizations, setOrganizations] = useState([]);
  const [selectedOrgId, setSelectedOrgId] = useState('');
  const [showNewOrgInput, setShowNewOrgInput] = useState(false);
  const [newOrgName, setNewOrgName] = useState('');
  
  // Message States
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { register } = useAuth();
  const navigate = useNavigate();

  // Load organizations on load
  useEffect(() => {
    const fetchOrgs = async () => {
      try {
        const res = await apiClient.get('/organizations/');
        setOrganizations(res.data);
        if (res.data.length > 0) {
          setSelectedOrgId(res.data[0].id);
        } else {
          setShowNewOrgInput(true);
        }
      } catch (err) {
        console.error("Failed to load organizations", err);
        setShowNewOrgInput(true);
      }
    };
    fetchOrgs();
  }, []);

  const handleCreateOrg = async (e) => {
    e.preventDefault();
    if (!newOrgName.trim()) return;
    setError('');

    try {
      const res = await apiClient.post('/organizations/', { name: newOrgName });
      const createdOrg = res.data;
      setOrganizations((prev) => [...prev, createdOrg]);
      setSelectedOrgId(createdOrg.id);
      setNewOrgName('');
      setShowNewOrgInput(false);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create organization.');
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    
    // Validate organization
    const orgId = selectedOrgId;
    if (!orgId) {
      setError('Please select or register an organization first.');
      return;
    }

    setIsSubmitting(true);
    try {
      await register(email, username, orgId, password, role);
      setSuccess(true);
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (err) {
      setError(err);
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900 px-4 py-8">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(170,59,255,0.1),transparent_50%)] pointer-events-none" />

      <div className="w-full max-w-md z-10">
        <div className="bg-gray-800/80 backdrop-blur-md border border-gray-700/60 rounded-2xl shadow-2xl p-8">
          <div className="flex flex-col items-center mb-6">
            <div className="w-12 h-12 bg-accent/20 border border-accent/40 rounded-xl flex items-center justify-center mb-3">
              <Shield className="w-6 h-6 text-accent" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center justify-center gap-2">
              Investigator Signup
            </h1>
            <p className="text-gray-400 text-sm mt-1">Join the ForenSight Incident Team</p>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-900/30 border border-red-500/50 rounded-lg text-red-200 text-sm text-center">
              {error}
            </div>
          )}

          {success && (
            <div className="mb-4 p-3 bg-green-900/30 border border-green-500/50 rounded-lg text-green-200 text-sm text-center">
              Account created successfully! Redirecting to login...
            </div>
          )}

          {!success && (
            <form onSubmit={handleRegister} className="space-y-4">
              <div>
                <label className="block text-gray-300 text-xs font-semibold uppercase tracking-wider mb-2">
                  Username
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-500">
                    <User className="w-4 h-4" />
                  </span>
                  <input
                    type="text"
                    required
                    placeholder="alice_analyst"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full pl-9 pr-4 py-2 bg-gray-900/80 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent transition-all text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-gray-300 text-xs font-semibold uppercase tracking-wider mb-2">
                  Email Address
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-500">
                    <Mail className="w-4 h-4" />
                  </span>
                  <input
                    type="email"
                    required
                    placeholder="analyst@forensight.org"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-9 pr-4 py-2 bg-gray-900/80 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent transition-all text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-gray-300 text-xs font-semibold uppercase tracking-wider mb-2">
                  Password
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-500">
                    <Lock className="w-4 h-4" />
                  </span>
                  <input
                    type="password"
                    required
                    placeholder="••••••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-9 pr-4 py-2 bg-gray-900/80 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent transition-all text-sm"
                  />
                </div>
              </div>

              {/* Organization Picker / Creation */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="block text-gray-300 text-xs font-semibold uppercase tracking-wider">
                    Organization Context
                  </label>
                  <button
                    type="button"
                    onClick={() => setShowNewOrgInput(!showNewOrgInput)}
                    className="text-xs text-accent hover:text-accent-hover flex items-center gap-1 font-semibold focus:outline-none cursor-pointer"
                  >
                    <Plus className="w-3 h-3" />
                    {showNewOrgInput ? 'Select Existing' : 'Create New'}
                  </button>
                </div>

                {showNewOrgInput ? (
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-500">
                        <Building className="w-4 h-4" />
                      </span>
                      <input
                        type="text"
                        placeholder="Security Ops Corp"
                        value={newOrgName}
                        onChange={(e) => setNewOrgName(e.target.value)}
                        className="w-full pl-9 pr-4 py-2 bg-gray-900/80 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent transition-all text-sm"
                      />
                    </div>
                    <button
                      type="button"
                      onClick={handleCreateOrg}
                      className="px-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-xs font-bold transition-colors cursor-pointer"
                    >
                      Save
                    </button>
                  </div>
                ) : (
                  <div className="relative">
                    <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-500">
                      <Building className="w-4 h-4" />
                    </span>
                    <select
                      value={selectedOrgId}
                      onChange={(e) => setSelectedOrgId(e.target.value)}
                      className="w-full pl-9 pr-4 py-2 bg-gray-900/80 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent transition-all text-sm"
                    >
                      {organizations.map((org) => (
                        <option key={org.id} value={org.id}>
                          {org.name}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-gray-300 text-xs font-semibold uppercase tracking-wider mb-2">
                  System Role
                </label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-900/80 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent transition-all text-sm"
                >
                  <option value="investigator">Investigator (Read / Write)</option>
                  <option value="admin">Administrator (Full Access)</option>
                  <option value="viewer">Viewer (Read Only)</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-2.5 bg-accent hover:bg-accent-hover text-white font-semibold rounded-lg shadow-lg hover:shadow-accent/20 transition-all focus:outline-none focus:ring-2 focus:ring-accent/50 text-sm flex items-center justify-center cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Registering...' : 'Submit Credentials'}
              </button>
            </form>
          )}

          <div className="mt-6 text-center text-sm text-gray-400">
            Already have an account?{' '}
            <Link to="/login" className="text-accent hover:underline font-medium">
              Click to Sign In
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
