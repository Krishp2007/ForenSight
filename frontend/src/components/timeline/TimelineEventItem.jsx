import React from 'react';
import { 
  ChevronDown, ChevronUp, Cpu, Globe, FileText, Key, Shield, AlertTriangle, ShieldAlert 
} from 'lucide-react';
import TimelineEventDetails from './TimelineEventDetails';

const TimelineEventItem = ({ evt, isExpanded, onToggleExpand }) => {
  const formattedTime = new Date(evt.timestamp).toLocaleString();

  const getEventIcon = (type) => {
    switch (type) {
      case 'process_creation':
        return <Cpu className="w-4 h-4 text-purple-400" />;
      case 'network_connection':
        return <Globe className="w-4 h-4 text-cyan-400" />;
      case 'file_modification':
        return <FileText className="w-4 h-4 text-blue-400" />;
      case 'registry_change':
        return <Key className="w-4 h-4 text-yellow-405" />;
      case 'auth_event':
        return <Shield className="w-4 h-4 text-red-400" />;
      default:
        return <AlertTriangle className="w-4 h-4 text-gray-400" />;
    }
  };

  const getSeverityColor = (sev) => {
    switch (sev) {
      case 'critical':
        return 'bg-red-950/40 border-red-500/50 text-red-400';
      case 'high':
        return 'bg-orange-950/40 border-orange-500/50 text-orange-400';
      case 'medium':
        return 'bg-yellow-950/45 border-yellow-500/50 text-yellow-400';
      case 'low':
        return 'bg-blue-950/40 border-blue-500/50 text-blue-400';
      default:
        return 'bg-gray-800 border-gray-700 text-gray-300';
    }
  };

  return (
    <div className="transition-colors duration-150 bg-gray-950/20 hover:bg-gray-850/10">
      {/* Primary Event Header Line */}
      <div
        onClick={onToggleExpand}
        className="p-5 flex flex-wrap md:flex-nowrap items-center justify-between gap-4 cursor-pointer select-none"
      >
        {/* Timestamp & Icon */}
        <div className="flex items-center gap-3 min-w-[200px]">
          <div className="w-8 h-8 rounded-lg bg-gray-900 border border-gray-800 flex items-center justify-center">
            {getEventIcon(evt.event_type)}
          </div>
          <div>
            <div className="text-[10px] font-mono text-gray-500 font-bold">{formattedTime}</div>
            <div className="text-[9px] font-semibold text-gray-400 uppercase tracking-widest mt-0.5">
              {evt.event_type.replace('_', ' ')}
            </div>
          </div>
        </div>

        {/* Semantic Triple Summary (Subject -> Action -> Object) */}
        <div className="flex-1 min-w-0 font-sans text-xs">
          <div className="flex flex-wrap items-center gap-1.5 leading-relaxed text-gray-300">
            <span className="font-bold text-white max-w-[150px] truncate" title={evt.subject}>
              {evt.subject}
            </span>
            <span className="text-accent/80 font-mono text-[10px] uppercase font-bold py-0.5 px-1 bg-accent/5 rounded">
              {evt.action}
            </span>
            <span className="font-bold text-gray-300 max-w-[200px] truncate" title={evt.object}>
              {evt.object}
            </span>
          </div>
        </div>

        {/* Meta Badges (Threat IDs, Anomalies, Severity) */}
        <div className="flex items-center gap-3 shrink-0">
          {evt.is_anomaly && (
            <span 
              className="flex items-center gap-1 text-[9px] font-bold bg-purple-950/40 border border-purple-500/40 text-purple-300 px-2 py-0.5 rounded-full"
              title={`Outlying probability: ${Math.round(evt.anomaly_score * 100)}%`}
            >
              <ShieldAlert className="w-3 h-3 text-purple-400 animate-bounce" />
              Anomaly
            </span>
          )}

          {evt.mitre_techniques?.map((tech) => (
            <span
              key={tech}
              className="bg-red-950/20 border border-red-500/30 text-red-400 text-[9px] font-mono font-semibold px-2 py-0.5 rounded"
              title="MITRE ATT&CK Tech ID"
            >
              {tech}
            </span>
          ))}

          <span
            className={`text-[9px] font-mono font-bold uppercase tracking-wider px-2.5 py-0.5 border rounded-full ${getSeverityColor(
              evt.severity
            )}`}
          >
            {evt.severity}
          </span>

          <button className="text-gray-500 hover:text-white p-1 transition-colors">
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Expanded Accordion Detail Block */}
      {isExpanded && (
        <TimelineEventDetails
          searchSentence={evt.search_sentence}
          details={evt.details}
        />
      )}
    </div>
  );
};

export default TimelineEventItem;
