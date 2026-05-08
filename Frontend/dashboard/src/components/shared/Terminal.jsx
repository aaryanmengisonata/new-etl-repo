import React, { useRef, useEffect } from 'react'
import { Terminal as TerminalIcon, Database } from 'lucide-react'

export default function Terminal({ logs, minHeight = "400px" }) {
  const logEndRef = useRef(null)

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  return (
    <div 
      className="flex-1 rounded-2xl border border-slate-200 shadow-2xl overflow-hidden flex flex-col transition-all bg-white"
      style={{ minHeight }}
    >
      <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
        <div className="flex items-center gap-2">
          <TerminalIcon size={16} className="text-slate-500" />
          <h2 className="text-xs font-black uppercase tracking-widest text-slate-900">Live Pipeline Stream</h2>
        </div>
      </div>
      
      <div 
        className="p-6 flex-1 font-mono text-[11px] overflow-y-auto space-y-1.5 bg-slate-50 text-slate-600"
        style={{ minHeight }}
      >
        {logs.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center opacity-20 py-20">
             <Database size={48} className="mb-4" />
             <p className="uppercase tracking-[0.3em] font-black text-center">Awaiting Transmission...</p>
          </div>
        ) : (
          logs.map((log, i) => (
            <div key={i} className={`flex gap-3 leading-relaxed transition-all animate-in slide-in-from-left-2 ${
              log.includes('PASSED') ? 'text-emerald-600 font-bold' : 
              log.includes('FAILED') ? 'text-rose-600 font-bold' : ''
            }`}>
              <span className="opacity-30 flex-shrink-0">{(i + 1).toString().padStart(3, '0')}</span>
              <span className="break-all">{log}</span>
            </div>
          ))
        )}
        <div ref={logEndRef} />
      </div>
    </div>
  )
}
