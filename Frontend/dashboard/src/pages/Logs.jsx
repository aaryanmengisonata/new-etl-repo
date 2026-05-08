import React, { useState, useEffect, useRef } from 'react'
import { ScrollText, Terminal, RefreshCw, Pause, Play, Trash2, Search, Activity } from 'lucide-react'

export default function Logs() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [paused, setPaused] = useState(false)
  const [filter, setFilter] = useState('ALL')
  const [search, setSearch] = useState('')
  const bottomRef = useRef(null)

  const fetchLogs = async () => {
    try {
      const res = await fetch('http://localhost:8000/logs')
      const data = await res.json()
      if (data && data.logs) {
        setLogs(data.logs)
      }
    } catch (err) {
      console.error("Failed to fetch logs:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLogs()
    const interval = setInterval(() => {
      if (!paused) fetchLogs()
    }, 3000)
    return () => clearInterval(interval)
  }, [paused])

  useEffect(() => {
    if (!paused) bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs, paused])

  const filteredLogs = logs.filter(log => {
    const l = log.toUpperCase()
    const matchesFilter = filter === 'ALL' || l.includes(filter)
    const matchesSearch = !search || l.includes(search.toUpperCase())
    return matchesFilter && matchesSearch
  })

  return (
    <div className="space-y-6 h-full flex flex-col animate-in fade-in slide-in-from-top-4 duration-500 text-left">
      {/* Header Banner */}
      <div className="p-6 border border-slate-200 rounded-2xl flex items-center justify-between bg-white shadow-xl">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <ScrollText size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-xl font-black uppercase tracking-tight text-slate-900">Execution Detail Logs</h1>
            <p className="text-xs font-medium uppercase tracking-tighter text-slate-400">Historical Event Stream</p>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="relative group">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 opacity-20 group-focus-within:opacity-100 transition-opacity" size={14} />
            <input 
              type="text" 
              placeholder="Search logs..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10 pr-4 py-2 rounded-xl border border-slate-200 bg-white text-[10px] font-black uppercase outline-none focus:border-blue-500/50 w-48 transition-all"
            />
          </div>

          <div className="flex items-center gap-1 border border-slate-200 rounded-lg p-1 bg-white shadow-sm">
            {['ALL', 'INFO', 'PASS', 'WARN', 'ERROR'].map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1.5 rounded-md text-[10px] font-black uppercase tracking-widest transition-all ${
                  filter === f 
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20' 
                    : 'text-slate-400 hover:text-slate-900'
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Terminal View */}
      <div className="border border-slate-200 rounded-2xl shadow-2xl overflow-hidden flex flex-col flex-1 bg-white min-h-0">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-2">
            <Terminal size={14} className="text-blue-600" />
            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Framework persistent buffer</span>
          </div>
          <div className="flex items-center gap-4">
             <button 
                onClick={() => setPaused(!paused)}
                className={`flex items-center gap-2 text-[10px] font-black uppercase tracking-widest transition-colors ${
                  paused ? 'text-emerald-600' : 'text-slate-500 hover:text-blue-600'
                }`}
             >
                {paused ? <Play size={12} /> : <Pause size={12} />}
                {paused ? 'Resume Stream' : 'Pause Stream'}
             </button>
             <div className="w-px h-4 bg-slate-200" />
             <button 
                onClick={() => { setLogs([]); fetchLogs(); }}
                className="text-slate-400 hover:text-rose-600 transition-colors"
                title="Clear Logs"
             >
                <Trash2 size={14} />
             </button>
          </div>
        </div>
        
        <div className="p-6 font-mono text-[11px] flex-1 overflow-y-auto bg-slate-50/50">
          {loading && logs.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 opacity-50 space-y-4">
              <RefreshCw size={32} className="animate-spin text-blue-500" />
              <p className="uppercase tracking-[0.2em] font-black">Connecting to engine...</p>
            </div>
          ) : filteredLogs.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 opacity-50 space-y-3 py-20">
               <ScrollText size={40} />
               <p className="uppercase tracking-[0.2em] font-black">No matching events</p>
            </div>
          ) : (
            <div className="space-y-1">
              {filteredLogs.map((log, i) => {
                const l = log.toUpperCase()
                const isError = l.includes('ERROR') || l.includes('FAILED')
                const isWarn = l.includes('WARNING') || l.includes('WARN')
                const isPass = l.includes('PASSED') || l.includes('SUCCESS')
                
                return (
                  <div key={i} className="group flex gap-4 hover:bg-slate-900/[0.02] -mx-4 px-4 transition-colors">
                     <span className="text-slate-300 w-10 text-right select-none opacity-50 group-hover:opacity-100">{i+1}</span>
                     <span className={`flex-1 whitespace-pre-wrap ${
                       isError ? 'text-rose-600 font-bold' : 
                       isWarn ? 'text-amber-600 font-bold' : 
                       isPass ? 'text-emerald-600 font-bold' : 'text-slate-600 font-medium'
                     }`}>{log}</span>
                  </div>
                )
              })}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        <div className="px-6 py-3 border-t border-slate-100 bg-slate-50 text-slate-400 flex items-center justify-between text-[10px] font-black uppercase tracking-widest">
           <div className="flex items-center gap-4">
              <span>Buffer: {logs.length} events</span>
              <span className="opacity-30">|</span>
              <span>Showing: {filteredLogs.length}</span>
           </div>
           <div className="flex items-center gap-2">
              <Activity size={10} className="text-emerald-500 animate-pulse" />
              <span className="text-[9px]">Engine Status: Active</span>
           </div>
        </div>
      </div>
    </div>
  )
}
