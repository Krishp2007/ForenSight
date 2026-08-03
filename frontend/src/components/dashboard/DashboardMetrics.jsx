import React from 'react';
import { Shield, HardDrive, AlertTriangle, CheckCircle2 } from 'lucide-react';

const DashboardMetrics = ({ totalCases, activeCases, totalEvidence, resolvedCases }) => {
  const cards = [
    {
      label: 'TOTAL INVESTIGATIONS',
      value: totalCases,
      icon: Shield,
      color: 'text-blue-400 border-blue-500/20 bg-blue-950/10',
      glow: 'shadow-[0_0_15px_rgba(59,130,246,0.1)]'
    },
    {
      label: 'ACTIVE INCIDENTS',
      value: activeCases,
      icon: AlertTriangle,
      color: 'text-amber-400 border-amber-500/20 bg-amber-950/10',
      glow: 'shadow-[0_0_15px_rgba(245,158,11,0.15)]'
    },
    {
      label: 'INGESTED EVIDENCE',
      value: totalEvidence,
      icon: HardDrive,
      color: 'text-accent border-accent/25 bg-accent/5',
      glow: 'shadow-[0_0_15px_rgba(170,59,255,0.15)]'
    },
    {
      label: 'RESOLVED THREATS',
      value: resolvedCases,
      icon: CheckCircle2,
      color: 'text-emerald-400 border-emerald-500/20 bg-emerald-950/10',
      glow: 'shadow-[0_0_15px_rgba(16,185,129,0.1)]'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
      {cards.map((card, i) => {
        const Icon = card.icon;
        return (
          <div
            key={i}
            className={`p-6 rounded-2xl border transition-all duration-300 hover:scale-[1.02] flex items-center justify-between bg-gray-900/40 backdrop-blur-md ${card.color} ${card.glow}`}
          >
            <div className="space-y-1">
              <span className="text-[10px] uppercase tracking-wider text-gray-500 font-bold font-mono">
                {card.label}
              </span>
              <h2 className="text-2xl font-black text-white">{card.value}</h2>
            </div>
            <div className={`p-3 rounded-xl border bg-gray-950/60 border-current/10 shrink-0`}>
              <Icon className="w-5 h-5" />
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default DashboardMetrics;
