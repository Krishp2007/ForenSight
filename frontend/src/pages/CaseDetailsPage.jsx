import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import apiClient from '../services/apiClient';
import CaseMetaHeader from '../components/cases/CaseMetaHeader';
import EvidenceIngestionPanel from '../components/evidence/EvidenceIngestionPanel';
import EvidenceRepositoryList from '../components/evidence/EvidenceRepositoryList';
import { Database, HardDrive, Cpu } from 'lucide-react';

import CaseTimeline from '../components/timeline/CaseTimeline';
import CaseGraph from '../components/graph/CaseGraph';
import CaseCopilot from '../components/chat/CaseCopilot';
import CaseReportModal from '../components/reports/CaseReportModal';

const CaseDetailsPage = () => {
  const { caseId } = useParams();
  const [caseObj, setCaseObj] = useState(null);
  const [evidenceList, setEvidenceList] = useState([]);
  
  // State elements
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('evidence');
  const [updateError, setUpdateError] = useState('');
  const [showReport, setShowReport] = useState(false);
  
  const pollingRef = useRef(null);

  const fetchCaseDetails = async () => {
    try {
      const caseRes = await apiClient.get(`/cases/${caseId}`);
      setCaseObj(caseRes.data);
      const evRes = await apiClient.get(`/cases/${caseId}/evidence`);
      setEvidenceList(evRes.data);
    } catch (err) {
      console.error("Failed to query case meta specifications", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchEvidenceOnly = async () => {
    try {
      const res = await apiClient.get(`/cases/${caseId}/evidence`);
      setEvidenceList(res.data);
    } catch (err) {
      console.error("Failed polling evidence values", err);
    }
  };

  useEffect(() => {
    fetchCaseDetails();
    return () => stopPolling();
  }, [caseId]);

  // Monitor parsing runs
  useEffect(() => {
    const isProcessing = evidenceList.some(
      (ev) => ev.status === 'uploaded' || ev.status === 'queued' || ev.status === 'parsing'
    );

    if (isProcessing) {
      startPolling();
    } else {
      stopPolling();
    }
  }, [evidenceList]);

  const startPolling = () => {
    if (pollingRef.current) return;
    pollingRef.current = setInterval(() => {
      fetchEvidenceOnly();
    }, 3000);
  };

  const stopPolling = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  };

  const handleStatusChange = async (newStatus) => {
    setUpdateError('');
    try {
      const res = await apiClient.put(`/cases/${caseId}`, {
        title: caseObj.title,
        description: caseObj.description,
        status: newStatus,
      });
      setCaseObj(res.data);
    } catch (err) {
      setUpdateError(err.response?.data?.detail || 'Failed to update case lifecycle.');
    }
  };

  if (loading) {
    return (
      <div className="h-full flex flex-col justify-center items-center py-24 bg-gray-955">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin mb-3" />
        <span className="text-gray-500 text-xs font-bold uppercase tracking-wider animate-pulse">Resolving Case Metadata...</span>
      </div>
    );
  }

  if (!caseObj) {
    return (
      <div className="p-8 text-center bg-gray-950 min-h-screen">
        <h2 className="text-red-400 font-bold">Failed to load investigation container.</h2>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6 bg-gray-950 min-h-screen">
      {/* Case Meta Header details */}
      <CaseMetaHeader
        caseObj={caseObj}
        onStatusChange={handleStatusChange}
        onOpenReport={() => setShowReport(true)}
      />

      {updateError && (
        <div className="p-3 bg-red-950/20 border border-red-900/30 text-red-400 text-xs rounded-lg text-center">
          {updateError}
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex border-b border-gray-800/60 bg-gray-900/20 p-1.5 rounded-xl border border-gray-800/60 max-w-fit z-10 relative">
        {[
          { id: 'evidence', label: 'Ingested Evidence' },
          { id: 'timeline', label: 'Threat Timeline' },
          { id: 'graph', label: 'Network Graph' },
          { id: 'copilot', label: 'AI Copilot' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              activeTab === tab.id
                ? 'bg-accent/15 border border-accent/40 text-white'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Main Tab Panels */}
      <div className="z-10 relative">
        {activeTab === 'evidence' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="space-y-4 lg:col-span-1">
              <EvidenceIngestionPanel
                caseId={caseId}
                evidenceList={evidenceList}
                onUploadSuccess={fetchEvidenceOnly}
              />
            </div>
            <div className="lg:col-span-2">
              <EvidenceRepositoryList
                evidenceList={evidenceList}
              />
            </div>
          </div>
        )}

        {activeTab === 'timeline' && <CaseTimeline caseId={caseId} />}
        {activeTab === 'graph' && <CaseGraph caseId={caseId} />}
        {activeTab === 'copilot' && <CaseCopilot caseId={caseId} />}
      </div>

      {showReport && (
        <CaseReportModal
          caseId={caseId}
          caseTitle={caseObj.title}
          onClose={() => setShowReport(false)}
        />
      )}
    </div>
  );
};

export default CaseDetailsPage;
