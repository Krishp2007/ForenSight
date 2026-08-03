import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

const CaseMetaHeader = ({ caseObj, onStatusChange }) => {
  return (
    <div className="space-y-4">
      <Link to="/" className="inline-flex items-center gap-2 text-xs font-semibold text-gray-400 hover:text-white transition-colors">
        <ArrowLeft className="w-3.5 h-3.5" />
        Back to list
      </Link>

      <div className="flex flex-col md:flex-row justify-between items-start md:items-center bg-gray-900/40 p-6 border border-gray-800/80 rounded-2xl gap-4 backdrop-blur-md">
        <div className="space-y-1.5 flex-1 min-w-0 pr-8">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold tracking-tight text-white truncate">{caseObj.title}</h1>
            <span className="text-[10px] uppercase font-mono px-2 py-0.5 border border-gray-700 bg-gray-800 text-gray-300 rounded font-bold">
              ID: {caseObj.id.slice(-8)}
            </span>
          </div>
          <p className="text-gray-400 text-xs leading-relaxed max-w-3xl">
            {caseObj.description || 'No description added for this Case container.'}
          </p>
        </div>

        <div className="flex flex-col gap-2 min-w-[150px]">
          <label className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">Triage Tiers</label>
          <select
            value={caseObj.status}
            onChange={(e) => onStatusChange(e.target.value)}
            className="px-3 py-1.5 bg-gray-950 border border-gray-800 rounded-lg text-xs font-semibold text-white focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent cursor-pointer text-center"
          >
            <option value="open">Open (Incident)</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved Case</option>
          </select>
        </div>
      </div>
    </div>
  );
};

export default CaseMetaHeader;
