import React from 'react';
import { Search, RefreshCw } from 'lucide-react';

const TimelineFilters = ({
  searchTerm,
  setSearchTerm,
  severityFilter,
  setSeverityFilter,
  limit,
  setLimit,
  onlyAnomalies,
  setOnlyAnomalies,
  onReload
}) => {
  return (
    <div className="bg-gray-900/40 border border-gray-800/80 p-5 rounded-2xl backdrop-blur-md space-y-4">
      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        {/* Search input field */}
        <div className="relative w-full md:w-96">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-505" />
          <input
            type="text"
            placeholder="Search actions, hashes, endpoints, or rules..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-gray-955 border border-gray-800 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent"
          />
        </div>

        {/* Action controllers */}
        <div className="flex flex-wrap gap-3 items-center justify-end w-full md:w-auto">
          {/* Limit selector dropdown */}
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="bg-gray-955 border border-gray-808 text-gray-300 text-xs px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent rounded-lg cursor-pointer font-semibold"
          >
            <option value={50}>Limit: 50</option>
            <option value={100}>Limit: 100</option>
            <option value={500}>Limit: 500</option>
            <option value={1000}>Limit: 1000</option>
          </select>

          {/* Anomaly check trigger */}
          <label className="flex items-center gap-2 cursor-pointer bg-gray-955/40 hover:bg-gray-955 border border-gray-800 py-1.5 px-3 rounded-lg transition-colors group">
            <input
              type="checkbox"
              checked={onlyAnomalies}
              onChange={(e) => setOnlyAnomalies(e.target.checked)}
              className="rounded border-gray-700 bg-gray-900 text-accent focus:ring-accent/50 accent-accent cursor-pointer"
            />
            <span className="text-xs font-semibold text-gray-400 group-hover:text-white transition-colors">
              Anomalies Only
            </span>
          </label>

          {/* Reload button */}
          <button
            onClick={onReload}
            title="Reload Timeline Events"
            className="p-2 border border-gray-800 bg-gray-955/40 hover:bg-gray-955 text-gray-450 hover:text-white rounded-lg transition-colors cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Severity sorting pills list */}
      <div className="flex flex-wrap gap-2 items-center text-xs">
        <span className="text-gray-500 font-bold uppercase tracking-wider text-[10px] mr-2">Severity:</span>
        {['all', 'critical', 'high', 'medium', 'low', 'info'].map((sev) => (
          <button
            key={sev}
            onClick={() => setSeverityFilter(sev)}
            className={`px-3 py-1 rounded-lg font-bold border transition-all cursor-pointer ${
              severityFilter === sev
                ? 'bg-accent/15 border-accent text-white'
                : 'bg-gray-955/40 border-gray-850 text-gray-400 hover:text-white hover:border-gray-700'
            }`}
          >
            {sev.charAt(0).toUpperCase() + sev.slice(1)}
          </button>
        ))}
      </div>
    </div>
  );
};

export default TimelineFilters;
