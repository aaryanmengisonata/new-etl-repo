import React from 'react';

export function Card({ children, className = '' }) {
  return (
    <div className={`p-10 rounded-[2.5rem] border border-slate-200 bg-white shadow-2xl shadow-slate-200/50 ${className}`}>
      {children}
    </div>
  );
}

export function CardHeader({ title, subtitle, action }) {
  return (
    <div className="flex items-start justify-between mb-8">
      <div>
        <h3 className="text-xl font-black uppercase tracking-tight text-slate-900">{title}</h3>
        {subtitle && <p className="text-xs font-medium opacity-40 mt-1">{subtitle}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}
