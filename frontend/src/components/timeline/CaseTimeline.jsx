import React, { useState, useEffect } from 'react';
import apiClient from '../../services/apiClient';
import { ShieldAlert, Clock } from 'lucide-react';
import TimelineFilters from './TimelineFilters';
import TimelineEventItem from './TimelineEventItem';

const CaseTimeline = ({ caseId }) => {
  const [events, setEvents] = useState([]);
  const [totalRecords, setTotalRecords] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Query Filters & Pagination State
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [limit, setLimit] = useState(100);
  const [onlyAnomalies, setOnlyAnomalies] = useState(true); // Default to true to show important alerts first
  const [page, setPage] = useState(1);

  // Accordion details toggle states
  const [expandedEventId, setExpandedEventId] = useState(null);

  const fetchEvents = async () => {
    setLoading(true);
    setError('');
    try {
      const params = { page, limit };
      if (severityFilter !== 'all') params.severity = severityFilter;
      if (typeFilter !== 'all') params.event_type = typeFilter;
      if (onlyAnomalies) params.is_anomaly = true;

      const res = await apiClient.get(`/cases/${caseId}/events`, { params });
      setEvents(res.data);
      const totalHeader = res.headers ? res.headers['x-total-count'] : null;
      setTotalRecords(totalHeader ? parseInt(totalHeader, 10) : res.data.length);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to query triage event logs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, [caseId, severityFilter, typeFilter, limit, page, onlyAnomalies]);

  // Reset page pagination back to 1 if filter criteria changes
  useEffect(() => {
    setPage(1);
  }, [severityFilter, typeFilter, limit, onlyAnomalies]);

  const toggleExpandEvent = (id) => {
    setExpandedEventId((prev) => (prev === id ? null : id));
  };

  // Local search filter criteria (Subject, Action, Object details)
  const filteredEvents = events.filter((e) => {
    if (!searchTerm.trim()) return true;

    const term = searchTerm.toLowerCase();
    const subMatch = e.subject?.toLowerCase().includes(term);
    const actMatch = e.action?.toLowerCase().includes(term);
    const objMatch = e.object?.toLowerCase().includes(term);
    const techMatch = e.mitre_techniques?.some(tech => tech.toLowerCase().includes(term));
    const sentenceMatch = e.search_sentence?.toLowerCase().includes(term);
    return subMatch || actMatch || objMatch || techMatch || sentenceMatch;
  });

  return (
    <div className="space-y-6">
      {/* Subcomponent Filters bar */}
      <TimelineFilters
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        severityFilter={severityFilter}
        setSeverityFilter={setSeverityFilter}
        limit={limit}
        setLimit={setLimit}
        onlyAnomalies={onlyAnomalies}
        setOnlyAnomalies={setOnlyAnomalies}
        onReload={fetchEvents}
      />

      {error && (
        <div className="p-4 bg-red-950/20 border border-red-905/35 text-red-400 text-xs rounded-xl text-center">
          {error}
        </div>
      )}

      {/* Timeline Scroll List */}
      <div className="bg-gray-900/40 border border-gray-805/85 rounded-2xl overflow-hidden shadow-2xl backdrop-blur-md">
        <div className="p-4 border-b border-gray-800 bg-gray-900/80 flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400 flex items-center gap-2">
            <Clock className="w-4 h-4 text-accent" />
            Chronological Events Record
          </h3>
          <div className="flex items-center gap-2 shrink-0">
            <span className="text-[9px] bg-accent/15 border border-accent/20 text-accent px-2 py-0.5 rounded font-mono font-black">
              TOTAL RECORDS: {totalRecords}
            </span>
            <span className="text-[9px] bg-gray-950 border border-gray-800 text-gray-400 px-2 py-0.5 rounded font-mono font-bold">
              SHOWN: {filteredEvents.length}
            </span>
          </div>
        </div>

        {loading ? (
          <div className="py-24 flex flex-col items-center justify-center">
            <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin mb-3" />
            <span className="text-gray-505 text-[10px] font-bold tracking-widest uppercase animate-pulse">
              Sorting Forensic Timelines...
            </span>
          </div>
        ) : filteredEvents.length === 0 ? (
          <div className="py-24 text-center">
            <ShieldAlert className="w-10 h-10 text-gray-750 mx-auto mb-3" />
            <h4 className="text-gray-405 font-bold text-xs">No Timeline Events Match Filters</h4>
            <p className="text-gray-500 text-[11px] mt-1">Adjust search parameters or upload missing case artifacts.</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-850 max-h-[600px] overflow-y-auto pr-1">
            {filteredEvents.map((evt) => (
              <TimelineEventItem
                key={evt.id}
                evt={evt}
                isExpanded={expandedEventId === evt.id}
                onToggleExpand={() => toggleExpandEvent(evt.id)}
              />
            ))}
          </div>
        )}

        {/* Footer Pagination Controls */}
        {!loading && events.length > 0 && (
          <div className="p-4 border-t border-gray-800 bg-gray-900/50 flex items-center justify-between text-xs text-gray-400 font-mono">
            <div>
              Showing Page <span className="text-white font-bold">{page}</span> of{" "}
              <span className="text-white font-bold">{Math.ceil(totalRecords / limit) || 1}</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage(prev => Math.max(1, prev - 1))}
                className={`px-3 py-1 rounded border border-gray-808 bg-gray-950 text-[10px] uppercase font-bold tracking-wider hover:bg-gray-850 hover:text-white transition-all cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed`}
              >
                Previous
              </button>
              <button
                disabled={page >= Math.ceil(totalRecords / limit)}
                onClick={() => setPage(prev => prev + 1)}
                className={`px-3 py-1 rounded border border-gray-808 bg-gray-950 text-[10px] uppercase font-bold tracking-wider hover:bg-gray-850 hover:text-white transition-all cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed`}
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CaseTimeline;
