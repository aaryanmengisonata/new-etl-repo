import React from 'react';
import { X, Trash2, RotateCcw, Clock, ExternalLink } from 'lucide-react';

export default function HistoryDrawer({ isOpen, onClose, history, onRestore, onDelete, onClearAll }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end animate-in fade-in duration-300">
      <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" onClick={onClose} />
      
      <div className="relative w-full max-w-md bg-white h-full shadow-2xl flex flex-col animate-in slide-in-from-right duration-300">
        <div className="flex items-center justify-between px-6 py-6 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center">
              <Clock size={18} className="text-slate-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-slate-900 leading-none">History</h2>
              <p className="text-[11px] text-slate-400 font-bold mt-1 uppercase tracking-wider">Last 20 generations</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-all"
          >
            <X size={20} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {history.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center p-8 opacity-50">
              <div className="w-16 h-16 rounded-full bg-slate-50 flex items-center justify-center mb-4 border border-dashed border-slate-300">
                <Clock size={24} className="text-slate-300" />
              </div>
              <p className="text-sm font-medium text-slate-500">No query history found</p>
            </div>
          ) : (
            history.map((item, index) => (
              <div 
                key={item.id || index}
                className="group p-4 rounded-xl border border-slate-200 bg-white hover:border-purple-300 hover:shadow-md transition-all duration-200"
              >
                <div className="flex justify-between items-start mb-2">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{item.timestamp}</span>
                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button 
                      onClick={() => onRestore(item)}
                      className="p-1.5 rounded-md hover:bg-emerald-50 text-slate-400 hover:text-emerald-600"
                      title="Restore"
                    >
                      <RotateCcw size={14} />
                    </button>
                    <button 
                      onClick={() => onDelete(item.id)}
                      className="p-1.5 rounded-md hover:bg-rose-50 text-slate-400 hover:text-rose-600"
                      title="Delete"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
                
                <p className="text-xs text-slate-600 font-medium line-clamp-2 mb-3 px-2 py-1 bg-slate-50 rounded border border-slate-100">
                  {item.prompt}
                </p>
                
                <div className="relative">
                  <pre className="text-[10px] font-mono text-emerald-600 bg-slate-900 p-3 rounded-lg overflow-hidden line-clamp-3">
                    {item.query}
                  </pre>
                  <div className="absolute inset-0 flex items-center justify-center bg-slate-900/60 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg">
                     <button 
                       onClick={() => onRestore(item)}
                       className="flex items-center gap-2 px-4 py-1.5 rounded-full bg-white text-[10px] font-bold text-slate-900 shadow-xl"
                     >
                        <ExternalLink size={12} />
                        LOAD QUERY
                     </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {history.length > 0 && (
          <div className="p-6 border-t border-slate-100 bg-slate-50/50">
            <button 
              onClick={onClearAll}
              className="w-full py-3 rounded-xl border border-slate-200 text-xs font-bold text-rose-500 hover:bg-rose-50 hover:border-rose-200 transition-all flex items-center justify-center gap-2"
            >
              <Trash2 size={14} />
              CLEAR ALL HISTORY
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
