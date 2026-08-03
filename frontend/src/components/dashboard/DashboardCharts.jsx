import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts';

const DashboardCharts = ({ casesData, statusData }) => {
  // Color configuration
  const COLORS = {
    open: '#f59e0b',       // Amber
    in_progress: '#aa3bff', // Accent purple
    resolved: '#10b981'    // Emerald
  };

  const PIE_COLORS = ['#f59e0b', '#aa3bff', '#10b981'];

  // Custom tooltips for cyber theme
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-gray-950/90 border border-gray-800 p-3 rounded-lg shadow-xl backdrop-blur-sm text-[10px] space-y-1">
          <p className="text-gray-400 font-bold">{label || payload[0].payload.name}</p>
          {payload.map((p, idx) => (
            <p key={idx} className="font-mono text-white">
              <span style={{ color: p.color || COLORS[p.payload.status] }}>■</span>{' '}
              {p.name}: <strong className="text-white">{p.value}</strong>
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Case Status Ratio Donut Chart Container */}
      <div className="lg:col-span-1 bg-gray-900/60 border border-gray-808 rounded-2xl p-6 flex flex-col shadow-2xl backdrop-blur-md">
        <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4">
          Triage Status breakdown
        </h3>
        <div className="h-64 relative flex items-center justify-center">
          {statusData && statusData.length > 0 && statusData.some(d => d.value > 0) ? (
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={statusData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {statusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[entry.status] || '#ccc'} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  iconType="circle"
                  formatter={(value, entry) => (
                    <span className="text-[10px] font-bold text-gray-400 uppercase">
                      {entry.payload.name} ({entry.payload.value})
                    </span>
                  )}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-gray-500 text-xs text-center font-bold">No status metrics compiled yet.</div>
          )}
        </div>
      </div>

      {/* Forensic Evidence Volume Bar Chart Container */}
      <div className="lg:col-span-2 bg-gray-900/60 border border-gray-808 rounded-2xl p-6 flex flex-col shadow-2xl backdrop-blur-md">
        <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4">
          Evidence Items count per Case
        </h3>
        <div className="h-64">
          {casesData && casesData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={casesData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                <XAxis
                  dataKey="displayName"
                  stroke="#6b7280"
                  fontSize={9}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  stroke="#6b7280"
                  fontSize={9}
                  tickLine={false}
                  axisLine={false}
                  allowDecimals={false}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="evidenceCount" radius={[6, 6, 0, 0]}>
                  {casesData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[entry.status] || '#aa3bff'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-550 text-xs font-bold">
              Load cases statistics...
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DashboardCharts;
