import React, { useState } from 'react';
import { Cpu, Copy, Play, Brush, Sparkles, MessageSquare, Terminal, Check, Info } from 'lucide-react';

export default function OutputPanel({ query, setQuery, onExplain, onRefine, onRun, onFormat, onOpenHistory, onLogs }) {
  const [activeTab, setActiveTab] = useState('SQL');
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(query);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const tabs = [
    { id: 'SQL', icon: <Terminal size={14} />, action: () => setActiveTab('SQL') },
    { id: 'Logs', icon: <MessageSquare size={14} />, action: onLogs },
    { id: 'History', icon: <Info size={14} />, action: onOpenHistory },
  ];

  return (
    <div className="flex flex-col h-full rounded-2xl border border-slate-200 bg-white shadow-lg overflow-hidden transition-all duration-300">
      <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-100 flex items-center justify-center">
            <Cpu size={18} className="text-emerald-600" />
          </div>
          <span className="text-sm text-slate-500 uppercase tracking-wide font-semibold">Logic Workspace</span>
        </div>
        
        <div className="flex items-center bg-slate-200/50 p-1 rounded-lg">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={tab.action}
              className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-xs font-semibold transition-all duration-200 ${
                activeTab === tab.id 
                  ? 'bg-white text-slate-900 shadow-sm' 
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              {tab.icon}
              {tab.id}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 p-6 flex flex-col gap-4">
        <div className="flex-1 relative flex flex-col">
          {query ? (
            <div className="flex-1 flex flex-col rounded-xl bg-slate-900 overflow-hidden group">
              <div className="flex items-center justify-between px-4 py-2 bg-slate-800/50 border-b border-slate-700/50">
                <span className="text-[10px] text-slate-400 font-mono uppercase tracking-widest">PostgreSQL</span>
                <div className="flex gap-2">
                  <button 
                    onClick={handleCopy}
                    className="p-1.5 rounded-md hover:bg-slate-700 text-slate-400 hover:text-white transition-all"
                    title="Copy to clipboard"
                  >
                    {copied ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
                  </button>
                  <button 
                    onClick={onFormat}
                    className="p-1.5 rounded-md hover:bg-slate-700 text-slate-400 hover:text-white transition-all"
                    title="Format Code"
                  >
                    <Brush size={14} />
                  </button>
                </div>
              </div>
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="flex-1 p-6 bg-transparent outline-none resize-none text-sm font-mono leading-relaxed text-emerald-400 placeholder:text-slate-700"
                spellCheck="false"
              />
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center border-2 border-dashed border-slate-200 rounded-xl bg-slate-50/50">
              <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4">
                <Terminal size={24} className="text-slate-300" />
              </div>
              <h3 className="text-sm font-semibold text-slate-600">Your generated SQL will appear here</h3>
              <p className="text-xs text-slate-400 mt-1 max-w-[200px]">Enter a prompt on the left to begin generation.</p>
            </div>
          )}
        </div>

        <div className="flex items-center justify-between gap-4">
          <div className="flex gap-2">
            <button 
              onClick={onExplain}
              disabled={!query}
              className="flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50 hover:border-slate-300 transition-all disabled:opacity-50 disabled:grayscale"
            >
              <Info size={14} />
              Explain Query
            </button>
            <button 
              onClick={onRefine}
              disabled={!query}
              className="flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50 hover:border-slate-300 transition-all disabled:opacity-50 disabled:grayscale"
            >
              <Sparkles size={14} />
              Refine Query
            </button>
          </div>
          
          <button 
            onClick={onRun}
            disabled={!query}
            className="flex items-center gap-2 px-6 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-md active:scale-95 transition-all disabled:opacity-50"
          >
            <Play size={14} className="fill-white" />
            Run Query
          </button>
        </div>
      </div>
    </div>
  );
}
