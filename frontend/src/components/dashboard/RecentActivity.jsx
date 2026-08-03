import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye, Shield, FileCode, CheckCircle2, Clock } from 'lucide-react';

const RecentActivity = ({ cases, recentEvidence }) => {
  const navigate = useNavigate();

  // Status mapping colors helper
  const STATUS_TAGS = {
    open: 'bg-amber-950/40 text-amber-400 border-amber-800/30',
    in_progress: 'bg-purple-950/40 text-purple-400 border-purple-800/30',
    resolved: 'bg-emerald-950/40 text-emerald-400 border-emerald-800/30'
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Target cases feed */}
      <div className="bg-gray-900/60 border border-gray-808 rounded-2xl p-6 flex flex-col shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 border-b border-gray-800/80 pb-4 mb-4 justify-between">
          <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest flex items-center gap-2">
            <Shield className="w-4 h-4 text-accent" />
            Recent Investigations
          </h3>
          <button
            onClick={() => navigate('/cases')}
            className="text-[10px] text-accent hover:underline font-bold uppercase tracking-wider cursor-pointer"
          >
            View All
          </button>
        </div>

        <div className="flex-1 space-y-3">
          {cases && cases.length > 0 ? (
            cases.slice(0, 4).map((c) => (
              <div
                key={c.id}
                onClick={() => navigate(`/cases/${c.id}`)}
                className="group p-4 bg-gray-950/40 hover:bg-gray-950 border border-gray-850/60 hover:border-gray-800 rounded-xl transition-all cursor-pointer flex items-center justify-between"
              >
                <div className="space-y-1 pr-4 min-w-0">
                  <h4 className="text-xs font-bold text-white group-hover:text-accent transition-colors truncate">
                    {c.title}
                  </h4>
                  <p className="text-[10px] text-gray-500 truncate max-w-md">
                    {c.description || 'No case summary described.'}
                  </p>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className={`text-[9px] uppercase font-mono px-2 py-0.5 border rounded font-semibold ${STATUS_TAGS[c.status] || 'text-gray-400'}`}>
                    {c.status.replace('_', ' ')}
                  </span>
                  <Eye className="w-3.5 h-3.5 text-gray-600 group-hover:text-white transition-colors" />
                </div>
              </div>
            ))
          ) : (
            <div className="py-8 text-center text-gray-500 text-xs font-bold">No active cases are listed.</div>
          )}
        </div>
      </div>

      {/* Cross-case recent evidence files ingest log feed */}
      <div className="bg-gray-900/60 border border-gray-808 rounded-2xl p-6 flex flex-col shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 border-b border-gray-800/80 pb-4 mb-4">
          <FileCode className="w-4 h-4 text-accent" />
          <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest">
            Latest Evidence Log Ingestions
          </h3>
        </div>

        <div className="flex-1 space-y-3">
          {recentEvidence && recentEvidence.length > 0 ? (
            recentEvidence.map((ev, i) => (
              <div
                key={i}
                onClick={() => navigate(`/cases/${ev.caseId}`)}
                className="group p-4 bg-gray-950/40 hover:bg-gray-950 border border-gray-850/60 hover:border-gray-800 rounded-xl transition-all cursor-pointer flex items-center justify-between"
              >
                <div className="space-y-1 pr-4 min-w-0">
                  <h4 className="text-xs font-mono font-bold text-gray-250 truncate group-hover:text-accent transition-colors">
                    {ev.filename}
                  </h4>
                  <p className="text-[9px] text-gray-500 truncate">
                    Case: <strong className="text-gray-400 font-semibold">{ev.caseTitle}</strong> • {ev.file_type}
                  </p>
                </div>
                <div className="flex items-center gap-2 text-gray-500 text-[10px] shrink-0 font-mono">
                  <Clock className="w-3 h-3 text-gray-600" />
                  {ev.processed ? (
                    <span className="text-emerald-400 font-bold flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                      Compiled
                    </span>
                  ) : (
                    <span className="text-amber-400 font-bold animate-pulse">Processing</span>
                  )}
                </div>
              </div>
            ))
          ) : (
            <div className="py-8 text-center text-gray-550 text-xs font-bold">
              No evidence logs ingested yet.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RecentActivity;
