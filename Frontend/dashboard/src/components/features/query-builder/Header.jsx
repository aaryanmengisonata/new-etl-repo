import React from 'react';
import { Sparkles } from 'lucide-react';

export default function Header({ onOpenHistory }) {
  return (
    <header className="flex items-center justify-between px-8 py-6 bg-white border-b border-slate-200">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-purple-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-purple-500/20">
          <Sparkles className="text-white" size={24} />
        </div>
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Query Builder</h1>
          <p className="text-sm text-slate-500 font-medium">AI-powered logic generation</p>
        </div>
      </div>
    </header>
  );
}
