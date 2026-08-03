import React, { useState, useEffect } from 'react';
import apiClient from '../../services/apiClient';
import { ShieldAlert, Clock } from 'lucide-react';
import TimelineFilters from './TimelineFilters';
import TimelineEventItem from './TimelineEventItem';

const CaseTimeline = ({ caseId }) => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Query Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [limit, setLimit] = useState(100);
  const [onlyAnomalies, setOnlyAnomalies] = useState(false);

  // Accordion details toggle states
  const [expandedEventId, setExpandedEventId] = useState(null);

  const fetchEvents = async () => {
    setLoading(true);
    setError('');
    try {
      const params = {};
      if (severityFilter !== 'all') params.severity = severityFilter;
      if (typeFilter !== 'all') params.event_type = typeFilter;
      params.limit = limit;

      const res = await apiClient.get(`/cases/${caseId}/events`, { params });
      setEvents(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to query triage event logs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, [caseId, severityFilter, typeFilter, limit]);

  const toggleExpandEvent = (id) => {
    setExpandedEventId((prev) => (prev === id ? null : id));
  };

  // Local search filter criteria (Subject, Action, Object details)
  const filteredEvents = events.filter((e) => {
    if (onlyAnomalies && !e.is_anomaly) return false;
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
        <div className="p-4 bg-red-950/20 border border-red-900/30 text-red-400 text-xs rounded-xl text-center">
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
          <span className="text-[10px] bg-gray-955 border border-gray-800 text-gray-500 px-2 py-0.5 rounded font-mono font-bold">
            Parsed: {filteredEvents.length}
          </span>
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
      </div>
    </div>
  );
};

export default CaseTimeline;
