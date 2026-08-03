import React, { useState, useEffect } from 'react';
import apiClient from '../services/apiClient';
import DashboardMetrics from '../components/dashboard/DashboardMetrics';
import DashboardCharts from '../components/dashboard/DashboardCharts';
import RecentActivity from '../components/dashboard/RecentActivity';
import { Activity, Shield } from 'lucide-react';

const DashboardPage = () => {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Summarized metrics state
  const [metrics, setMetrics] = useState({
    totalCases: 0,
    activeCases: 0,
    resolvedCases: 0,
    totalEvidence: 0
  });

  const [casesStats, setCasesStats] = useState([]);
  const [statusRatio, setStatusRatio] = useState([]);
  const [recentEvidence, setRecentEvidence] = useState([]);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError('');
    try {
      // 1. Fetch all cases
      const casesRes = await apiClient.get('/cases/');
      const casesList = casesRes.data || [];
      setCases(casesList);

      // Initialize status counts
      const statusCounts = { open: 0, in_progress: 0, resolved: 0 };
      let activeCount = 0;
      let resolvedCount = 0;

      // 2. Fetch evidence counts across cases to construct volume statistics
      const statsList = [];
      let globalEvidenceCount = 0;
      let allEvidenceItems = [];

      await Promise.all(
        casesList.map(async (c) => {
          // Increment status trackers
          if (c.status === 'open' || c.status === 'in_progress') activeCount++;
          if (c.status === 'resolved') resolvedCount++;
          if (statusCounts[c.status] !== undefined) {
            statusCounts[c.status] += 1;
          }

          try {
            const evRes = await apiClient.get(`/cases/${c.id}/evidence`);
            const evData = evRes.data || [];
            globalEvidenceCount += evData.length;

            // Map evidence items for cross-case ingestion logs feed
            const mappedEv = evData.map((ev) => ({
              ...ev,
              caseId: c.id,
              caseTitle: c.title
            }));
            allEvidenceItems = [...allEvidenceItems, ...mappedEv];

            statsList.push({
              id: c.id,
              name: c.title,
              displayName: c.title.length > 18 ? `${c.title.slice(0, 15)}...` : c.title,
              evidenceCount: evData.length,
              status: c.status
            });
          } catch (err) {
            console.error(`Failed fetching evidence items for case ${c.id}`, err);
            statsList.push({
              id: c.id,
              name: c.title,
              displayName: c.title.length > 18 ? `${c.title.slice(0, 15)}...` : c.title,
              evidenceCount: 0,
              status: c.status
            });
          }
        })
      );

      // Sort evidence items to display recent ones (using fallback indexes or metadata)
      const sortedEvidence = allEvidenceItems.slice(0, 4);

      // Set state fields
      setMetrics({
        totalCases: casesList.length,
        activeCases: activeCount,
        resolvedCases: resolvedCount,
        totalEvidence: globalEvidenceCount
      });

      setCasesStats(statsList);
      setRecentEvidence(sortedEvidence);

      // Map status ratio representation for Donut
      setStatusRatio([
        { name: 'Open Incidents', value: statusCounts.open, status: 'open' },
        { name: 'In Progress', value: statusCounts.in_progress, status: 'in_progress' },
        { name: 'Resolved Cases', value: statusCounts.resolved, status: 'resolved' }
      ]);

    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to assemble dashboard metrics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  return (
    <div className="p-8 space-y-6">
      {/* Dashboard Top Header bar */}
      <div className="flex justify-between items-center bg-gray-900/40 p-6 border border-gray-800/80 rounded-2xl backdrop-blur-md">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Activity className="w-6 h-6 text-accent animate-pulse" />
            Security Operations Dashboard
          </h1>
          <p className="text-gray-400 text-xs mt-1">Real-time incident forensics and telemetry ingest status</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-950 border border-gray-800 rounded-lg text-xs font-mono font-bold text-gray-400">
          <Shield className="w-3.5 h-3.5 text-accent" />
          SOC ENGINE ONLINE
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-955/20 border border-red-900/30 text-red-400 text-xs rounded-xl text-center">
          {error}
        </div>
      )}

      {loading ? (
        <div className="py-32 flex flex-col justify-center items-center">
          <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin mb-3" />
          <span className="text-gray-550 text-xs font-bold uppercase tracking-widest animate-pulse">
            Analyzing telemetry store...
          </span>
        </div>
      ) : (
        <>
          {/* Metrics summary widgets */}
          <DashboardMetrics
            totalCases={metrics.totalCases}
            activeCases={metrics.activeCases}
            totalEvidence={metrics.totalEvidence}
            resolvedCases={metrics.resolvedCases}
          />

          {/* Visualization Board */}
          <DashboardCharts
            casesData={casesStats}
            statusData={statusRatio}
          />

          {/* Activity Logs feed */}
          <RecentActivity
            cases={cases}
            recentEvidence={recentEvidence}
          />
        </>
      )}
    </div>
  );
};

export default DashboardPage;
