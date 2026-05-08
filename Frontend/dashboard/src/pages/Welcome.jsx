import React from 'react'
import { Zap, ShieldCheck } from 'lucide-react'

export default function Welcome() {
  return (
    <div className="h-full flex items-center justify-center p-6 animate-in fade-in zoom-in duration-1000">
      <div className="max-w-md w-full p-10 rounded-[2.5rem] bg-white/40 backdrop-blur-xl border border-white/20 shadow-2xl shadow-slate-200/50 flex flex-col items-center text-center space-y-6">
        <div className="relative">
          <div className="absolute inset-0 bg-blue-500 blur-2xl opacity-10 animate-pulse" />
          <div className="relative w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-xl shadow-blue-500/20">
             <ShieldCheck size={32} className="text-white fill-white/10" />
          </div>
        </div>

        <div className="space-y-2">
          <h1 className="text-2xl font-black tracking-tight text-slate-900">
            Smart <span className="text-blue-600">Data</span>
          </h1>
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">
            Enterprise Validation Protocol
          </p>
        </div>
        
        <p className="text-xs font-bold text-slate-500 leading-relaxed max-w-[280px]">
          Sonata Software's premium data validation platform. Select a module from the sidebar to initialize testing.
        </p>

        <div className="w-full h-px bg-slate-100" />

        <div className="flex items-center gap-3 px-5 py-3 rounded-full bg-slate-50 border border-slate-100/50">
           <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-ping" />
           <p className="text-[9px] font-black uppercase tracking-widest text-slate-400">
             Awaiting Module Initialization
           </p>
        </div>
      </div>
    </div>
  )
}
