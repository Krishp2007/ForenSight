import React from 'react';
import { Clock, CircleDot, CheckCircle2 } from 'lucide-react';

const CasesMetrics = ({ totalCasesCount, activeCasesCount, resolvedCasesCount }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* Total Incidents CARD */}
      <div className="bg-gray-900 border border-gray-800/60 p-6 rounded-2xl flex items-center justify-between shadow-xl">
        <div>
          <span className="text-gray-400 text-xs font-bold uppercase tracking-wider">Total Incidents</span>
          <h3 className="text-3xl font-extrabold text-white mt-2">{totalCasesCount}</h3>
        </div>
        <div className="w-12 h-12 bg-gray-800 border border-gray-700/60 rounded-xl flex items-center justify-center text-gray-300">
          <Clock className="w-5 h-5 text-blue-400" />
        </div>
      </div>

      {/* Active cases CARD */}
      <div className="bg-gray-900 border border-gray-800/60 p-6 rounded-2xl flex items-center justify-between shadow-xl">
        <div>
          <span className="text-gray-400 text-xs font-bold uppercase tracking-wider">Active Triage</span>
          <h3 className="text-3xl font-extrabold text-white mt-2">{activeCasesCount}</h3>
        </div>
        <div className="w-12 h-12 bg-gray-800 border border-gray-700/60 rounded-xl flex items-center justify-center text-gray-300">
          <CircleDot className="w-5 h-5 text-accent animate-pulse" />
        </div>
      </div>

      {/* Resolved cases CARD */}
      <div className="bg-gray-900 border border-gray-800/60 p-6 rounded-2xl flex items-center justify-between shadow-xl">
        <div>
          <span className="text-gray-400 text-xs font-bold uppercase tracking-wider">Resolved Cases</span>
          <h3 className="text-3xl font-extrabold text-white mt-2">{resolvedCasesCount}</h3>
        </div>
        <div className="w-12 h-12 bg-gray-800 border border-gray-700/60 rounded-xl flex items-center justify-center text-gray-300">
          <CheckCircle2 className="w-5 h-5 text-green-400" />
        </div>
      </div>
    </div>
  );
};

export default CasesMetrics;
