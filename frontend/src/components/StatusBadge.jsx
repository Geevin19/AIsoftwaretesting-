import React from 'react';

export const StatusBadge = ({ status }) => {
  const norm = (status || '').toUpperCase();

  if (norm === 'PASS') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-300">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
        PASS
      </span>
    );
  }

  if (norm === 'FAIL') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-300">
        <span className="w-1.5 h-1.5 rounded-full bg-rose-500"></span>
        FAIL
      </span>
    );
  }

  if (norm === 'ERROR') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-300">
        <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
        ERROR
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-300">
      {status || 'UNKNOWN'}
    </span>
  );
};

export const CategoryBadge = ({ category }) => {
  const cat = (category || 'normal').toLowerCase();

  const config = {
    normal: {
      bg: 'bg-blue-50',
      text: 'text-blue-700',
      border: 'border-blue-200',
      label: 'Normal',
    },
    boundary: {
      bg: 'bg-purple-50',
      text: 'text-purple-700',
      border: 'border-purple-200',
      label: 'Boundary',
    },
    invalid: {
      bg: 'bg-amber-50',
      text: 'text-amber-800',
      border: 'border-amber-200',
      label: 'Invalid Input',
    },
  };

  const style = config[cat] || config.normal;

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${style.bg} ${style.text} ${style.border}`}>
      {style.label}
    </span>
  );
};
