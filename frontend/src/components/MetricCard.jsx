import React from 'react';

export const MetricCard = ({ title, value, subtitle, icon: Icon, color = 'indigo' }) => {
  const colorMap = {
    indigo: {
      border: 'border-slate-200',
      bg: 'bg-white',
      iconBg: 'bg-indigo-50',
      iconText: 'text-indigo-600',
      valueColor: 'text-indigo-900',
    },
    emerald: {
      border: 'border-slate-200',
      bg: 'bg-white',
      iconBg: 'bg-emerald-50',
      iconText: 'text-emerald-600',
      valueColor: 'text-emerald-700',
    },
    rose: {
      border: 'border-slate-200',
      bg: 'bg-white',
      iconBg: 'bg-rose-50',
      iconText: 'text-rose-600',
      valueColor: 'text-rose-700',
    },
    amber: {
      border: 'border-slate-200',
      bg: 'bg-white',
      iconBg: 'bg-amber-50',
      iconText: 'text-amber-600',
      valueColor: 'text-amber-800',
    },
    blue: {
      border: 'border-slate-200',
      bg: 'bg-white',
      iconBg: 'bg-blue-50',
      iconText: 'text-blue-600',
      valueColor: 'text-blue-900',
    },
  };

  const scheme = colorMap[color] || colorMap.indigo;

  return (
    <div className={`p-5 rounded-xl border ${scheme.border} ${scheme.bg} shadow-sm hover:shadow-md transition-all`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{title}</span>
        {Icon && (
          <div className={`p-2 rounded-lg ${scheme.iconBg}`}>
            <Icon className={`w-5 h-5 ${scheme.iconText}`} />
          </div>
        )}
      </div>
      <div className="mt-3 flex items-baseline gap-2">
        <span className={`text-3xl font-bold tracking-tight ${scheme.valueColor}`}>{value}</span>
      </div>
      {subtitle && (
        <p className="mt-1 text-xs text-slate-500">{subtitle}</p>
      )}
    </div>
  );
};
