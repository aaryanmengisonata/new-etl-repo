import React, { useState, useEffect } from 'react'
import { 
  Play, Square, GitBranch, Globe, Database, Zap, 
  Box, Activity, Loader2, Server, Command
} from 'lucide-react'
import Terminal from '../components/shared/Terminal'

const engines = [
  { id: 'etl', title: 'Data Pipeline', icon: GitBranch, color: 'blue', desc: 'Bronze → Silver validation' },
  { id: 'api', title: 'API Gateway', icon: Globe, color: 'blue', desc: 'REST endpoint auditing' },
  { id: 'db', title: 'Database Unit', icon: Database, color: 'blue', desc: 'SQL integrity checks' },
  { id: 'integration', title: 'Cross-System', icon: Zap, color: 'blue', desc: 'E2E flow validation' },
]

export default function RunTests() {
  const [selectedEngine, setSelectedEngine] = useState(null)
  const [selectedSuite, setSelectedSuite] = useState(null)
  const [suites, setSuites] = useState([])
  const [running, setRunning] = useState(false)
  const [logs, setLogs] = useState([])
  const [loadingSuites, setLoadingSuites] = useState(false)

  useEffect(() => {
    if (selectedEngine === 'etl') {
      setLoadingSuites(true)
      fetch('http://localhost:8000/api/suites').then(res => res.json()).then(data => {
        setSuites(data); setLoadingSuites(false)
      }).catch(() => setLoadingSuites(false))
    } else setSuites([])
  }, [selectedEngine])

  const startExecution = () => {
    if (!selectedEngine) return
    setRunning(true)
    setLogs([`$ Initializing ${selectedEngine.toUpperCase()} engine...`])
    const url = selectedSuite ? `http://localhost:8000/stream-logs/${selectedEngine}?suite=${selectedSuite}` : `http://localhost:8000/stream-logs/${selectedEngine}`
    const ev = new EventSource(url)
    ev.addEventListener('log', (e) => setLogs(prev => [...prev, JSON.parse(e.data).msg]))
    ev.addEventListener('done', (e) => { 
      setLogs(prev => [...prev, `[SYSTEM] Execution finished.`]); setRunning(false); ev.close() 
    })
    ev.onerror = () => { setRunning(false); ev.close() }
  }

  const stopExecution = async () => {
    await fetch(`http://localhost:8000/api/stop-test/${selectedEngine}`, { method: 'POST' })
    setRunning(false)
  }

  return (
    <div className="max-w-7xl animate-in fade-in slide-in-from-top-4 duration-500 flex flex-col gap-6 text-left">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {engines.map((e) => (
          <EngineCard key={e.id} engine={e} active={selectedEngine === e.id} onSelect={setSelectedEngine} />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <ConfigPanel 
          selectedEngine={selectedEngine} suites={suites} selectedSuite={selectedSuite} 
          setSelectedSuite={setSelectedSuite} running={running} onStart={startExecution} 
          onStop={stopExecution} 
        />
        <StatusPanel running={running} />
      </div>

      <Terminal logs={logs} minHeight="450px" />
    </div>
  )
}

function EngineCard({ engine, active, onSelect }) {
  const Icon = engine.icon
  return (
    <button 
      onClick={() => onSelect(engine.id)} 
      className={`text-left p-6 rounded-2xl border transition-all duration-300 ${
        active 
          ? 'bg-blue-600 border-blue-500 shadow-xl shadow-blue-500/20 text-white' 
          : 'bg-white border-slate-200 text-slate-600 hover:border-blue-400 hover:bg-slate-50'
      }`}
    >
      <div className={`w-10 h-10 rounded-xl mb-4 flex items-center justify-center ${active ? 'bg-white/20' : 'bg-slate-100'}`}>
        <Icon size={20} className={active ? 'text-white' : 'text-slate-500'} />
      </div>
      <p className={`text-[9px] font-black uppercase tracking-widest mb-1 ${active ? 'text-white/60' : 'text-slate-400'}`}>Engine Unit</p>
      <h3 className="text-sm font-black uppercase tracking-tight">{engine.title}</h3>
    </button>
  )
}

function ConfigPanel({ selectedEngine, suites, selectedSuite, setSelectedSuite, running, onStart, onStop }) {
  if (!selectedEngine) return (
    <div className="lg:col-span-2 border border-slate-200 rounded-[2rem] bg-white p-12 flex flex-col items-center justify-center text-center space-y-4 shadow-xl shadow-slate-200/50">
       <div className="w-16 h-16 rounded-3xl bg-slate-50 flex items-center justify-center text-slate-200 border border-slate-100">
         <Command size={32} />
       </div>
       <div className="space-y-1">
         <p className="text-xs font-black uppercase tracking-widest text-slate-900">Config Protocol Locked</p>
         <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">Initialize an engine to begin deployment</p>
       </div>
    </div>
  )
  return (
    <div className="lg:col-span-2 border border-slate-200 rounded-[2rem] bg-white p-8 shadow-xl shadow-slate-200/50 flex flex-col">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-8 h-8 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600 border border-blue-100">
          <Box size={16} />
        </div>
        <h3 className="text-xs font-black uppercase tracking-widest text-slate-900">Deployment Config</h3>
      </div>

      <div className="space-y-8 flex-1">
        <div className="space-y-3">
          <p className="text-[9px] font-black uppercase tracking-[0.2em] text-slate-400 px-1">Selected Scenarios</p>
          <div className="flex flex-wrap gap-2">
            <SuiteBtn label="Master Suite" active={selectedSuite === null} onClick={() => setSelectedSuite(null)} />
            {suites.map(s => <SuiteBtn key={s} label={s} active={selectedSuite === s} onClick={() => setSelectedSuite(s)} />)}
          </div>
        </div>

        <div className="pt-8 border-t border-slate-50 flex items-center justify-between">
           <div className="flex items-center gap-4">
              <div className="w-8 h-8 rounded-full bg-slate-50 flex items-center justify-center text-slate-400">
                <Server size={14} />
              </div>
              <div>
                <p className="text-[8px] font-black uppercase tracking-widest text-slate-400">Target Object</p>
                <p className="text-xs font-bold text-slate-900">{selectedSuite || 'Full Structural Audit'}</p>
              </div>
           </div>

           <button 
             onClick={running ? onStop : onStart} 
             className={`px-10 py-4 rounded-2xl text-[10px] font-black uppercase tracking-[0.2em] transition-all duration-300 flex items-center gap-3 shadow-xl ${
               running 
                 ? 'bg-rose-600 text-white shadow-rose-500/20 animate-pulse' 
                 : 'bg-emerald-600 text-white shadow-emerald-500/20 hover:bg-emerald-700'
             }`}
           >
             {running ? <Square size={14} fill="white" /> : <Play size={14} fill="white" />}
             {running ? 'Halt Protocol' : 'Deploy Engine'}
           </button>
        </div>
      </div>
    </div>
  )
}

function SuiteBtn({ label, active, onClick }) {
  return (
    <button 
      onClick={onClick} 
      className={`px-4 py-2.5 rounded-xl border text-[10px] font-black uppercase tracking-widest transition-all ${
        active 
          ? 'bg-blue-600 border-blue-500 text-white shadow-lg shadow-blue-500/10' 
          : 'bg-white border-slate-200 text-slate-400 hover:border-blue-300 hover:text-blue-600'
      }`}
    >
      {label}
    </button>
  )
}

function StatusPanel({ running }) {
  return (
    <div className="border border-slate-200 rounded-[2rem] bg-white p-8 shadow-xl shadow-slate-200/50">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-8 h-8 rounded-xl bg-slate-50 flex items-center justify-center text-slate-500 border border-slate-100">
          <Activity size={16} />
        </div>
        <h3 className="text-xs font-black uppercase tracking-widest text-slate-900">System Metrics</h3>
      </div>

      <div className="space-y-4">
        {['Backend Service', 'Runtime Core', 'Event Bridge'].map(label => (
          <div key={label} className="p-4 rounded-2xl bg-slate-50 border border-slate-100/50 flex items-center justify-between">
            <span className="text-[9px] font-black uppercase tracking-widest text-slate-400">{label}</span>
            <div className="flex items-center gap-3">
              <span className={`text-[8px] font-black uppercase ${running || label === 'Backend Service' ? 'text-emerald-600' : 'text-slate-300'}`}>
                {running || label === 'Backend Service' ? 'Active' : 'Standby'}
              </span>
              <div className={`w-2 h-2 rounded-full ${running || label === 'Backend Service' ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-slate-200'}`} />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
