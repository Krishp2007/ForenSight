import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../services/apiClient';
import CasesMetrics from '../components/cases/CasesMetrics';
import CaseListItem from '../components/cases/CaseListItem';
import NewCaseModal from '../components/cases/NewCaseModal';
import { FolderPlus, Filter, ShieldAlert, Activity } from 'lucide-react';

const CasesPage = () => {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Status tab filtering
  const [statusFilter, setStatusFilter] = useState('all');
  const [showModal, setShowModal] = useState(false);
  const navigate = useNavigate();

  const fetchCases = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/cases/');
      setCases(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch forensic cases.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, []);

  const handleCreateCase = async ({ title, description }) => {
    setError('');
    try {
      await apiClient.post('/cases/', {
        title,
        description,
        status: 'open',
      });
      setShowModal(false);
      fetchCases();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create case.');
    }
  };

  // Filtered case mapping
  const filteredCases = cases.filter((c) => {
    if (statusFilter === 'all') return true;
    return c.status === statusFilter;
  });

  // Calculate summary metrics
  const activeCasesCount = cases.filter((c) => c.status === 'open' || c.status === 'in_progress').length;
  const resolvedCasesCount = cases.filter((c) => c.status === 'resolved').length;
  const totalCasesCount = cases.length;

  return (
    <div className="p-8 space-y-6">
      {/* Page Header */}
      <div className="flex justify-between items-center bg-gray-900/40 p-6 border border-gray-800/80 rounded-2xl backdrop-blur-md">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Activity className="w-6 h-6 text-accent" />
            Case Investigations Board
          </h1>
          <p className="text-gray-400 text-xs mt-1">Scope-wide active incident triage and evidentiary containers</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2 bg-accent hover:bg-accent-hover text-white text-xs font-semibold rounded-lg shadow-lg hover:shadow-accent/30 transition-all flex items-center gap-2 cursor-pointer animate-none"
        >
          <FolderPlus className="w-4 h-4" />
          New Investigation
        </button>
      </div>

      {/* Metrics Summary Grid */}
      <CasesMetrics
        totalCasesCount={totalCasesCount}
        activeCasesCount={activeCasesCount}
        resolvedCasesCount={resolvedCasesCount}
      />

      {/* Filter and Content Card */}
      <div className="bg-gray-900/60 border border-gray-800/80 rounded-2xl overflow-hidden shadow-2xl backdrop-blur-md">
        {/* Navigation Tabs */}
        <div className="flex border-b border-gray-800 bg-gray-900/80 p-3 justify-between items-center">
          <div className="flex gap-2">
            {[
              { id: 'all', label: 'All Cases' },
              { id: 'open', label: 'Open' },
              { id: 'in_progress', label: 'In Progress' },
              { id: 'resolved', label: 'Resolved' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setStatusFilter(tab.id)}
                className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                  statusFilter === tab.id
                    ? 'bg-gray-800 text-white shadow-inner border border-gray-700/60'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
          <Filter className="w-4 h-4 text-gray-500 mr-3" />
        </div>

        {error && (
          <div className="p-4 bg-red-955/20 border-b border-red-900/30 text-red-400 text-xs text-center">
            {error}
          </div>
        )}

        {loading ? (
          <div className="py-20 flex flex-col justify-center items-center">
            <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin mb-3" />
            <span className="text-gray-500 text-xs font-bold uppercase tracking-widest animate-pulse">Querying cases store...</span>
          </div>
        ) : filteredCases.length === 0 ? (
          <div className="py-24 text-center">
            <ShieldAlert className="w-12 h-12 text-gray-600 mx-auto mb-4 animate-bounce" />
            <h4 className="text-gray-300 font-bold text-sm">No Investigations Found</h4>
            <p className="text-gray-500 text-xs mt-1">Create a new forensic container to ingest evidence logs.</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-800/60">
            {filteredCases.map((c) => (
              <CaseListItem
                key={c.id}
                c={c}
                onClick={() => navigate(`/cases/${c.id}`)}
              />
            ))}
          </div>
        )}
      </div>

      {/* New Case Modal Backdrop */}
      <NewCaseModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onCreate={handleCreateCase}
      />
    </div>
  );
};

export default CasesPage;
