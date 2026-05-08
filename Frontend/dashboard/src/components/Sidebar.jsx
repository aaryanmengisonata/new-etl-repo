import React from 'react'
import {
  LayoutDashboard,
  Play,
  FileText,
  Settings,
  ScrollText,
  FlaskConical,
  ChevronRight,
  Database,
  List,
  CloudUpload,
  Zap,
  RefreshCw,
  Undo2,
  ChevronDown,
  Trash2,
  Sparkles,
  Activity,
  ShieldCheck
} from 'lucide-react'
import { useAppContext } from '../store/AppContext'
import logo from "../assets/Images/Sonata_Software_Logo.svg"
import intelqa_logo from "../assets/Images/Intell_Logo.svg"


const globalNav = [
  { id: 'configuration', label: 'Master Configuration', icon: Settings },
  { id: 'test_cases', label: 'Test Case Definition', icon: Database },
  { id: 'run', label: 'Execution Engine', icon: Play },
  { id: 'reports', label: 'Report Management', icon: FileText },
  { id: 'logs', label: 'Execution Details', icon: ScrollText },
]

export default function Sidebar({ activePage, setActivePage, featureState, setFeatureState }) {
  const isFeatureMode = ['fabric_audit'].includes(activePage)

  return (
    <aside className="w-64 flex-shrink-0 bg-white border-r border-slate-200 flex flex-col">
      {/* Corporate Branding Top Bar */}
      <div 
        onClick={() => setActivePage('dashboard')}
        className="h-20 flex items-center gap-3 px-5 border-b border-slate-100 cursor-pointer hover:opacity-80 transition-all"
      >
        <img src={logo} alt="Sonata" className="h-8" />
        <div className="w-px h-6 bg-slate-200" />
        <img src={intelqa_logo} alt="IntellQA" className="h-6" />
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto overflow-x-hidden py-6 px-3 space-y-2 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
        {!isFeatureMode ? (
          globalNav.map((item) => {
            const { id, label, icon: Icon } = item
            const isActive = activePage === id
            
            return (
              <button
                key={id}
                onClick={() => setActivePage(id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-xs font-black uppercase tracking-widest transition-all duration-200 group ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20'
                    : 'text-slate-400 hover:bg-slate-50 hover:text-slate-900'
                }`}
              >
                <Icon size={16} className={isActive ? 'text-white' : 'opacity-40 group-hover:opacity-100'} />
                <span className="flex-1 text-left">{label}</span>
                {isActive && <ChevronRight size={14} className="opacity-40" />}
              </button>
            )
          })
        ) : (
          <FeatureToggle featureState={featureState} setFeatureState={setFeatureState} />
        )}
      </nav>

      <div className="p-4 border-t border-slate-100">
        <p className="text-[9px] font-black uppercase tracking-widest text-center opacity-20">Sonata v2.4.1</p>
      </div>
    </aside>
  )
}

function FeatureToggle({ featureState, setFeatureState }) {
  const { 
    isRunning, toggleExecution, 
    selectedDataset, setSelectedDataset, 
    selectedReport, setSelectedReport,
    uploadedFile, setUploadedFile, handleFileUpload,
  } = useAppContext();

  const isIntro = !featureState || featureState === 'intro';
  const isExecution = featureState === 'execution';
  const isQuery = featureState === 'query';

  const modes = [
    { id: 'query', label: 'Query Mode', icon: List, visible: isIntro || isExecution || featureState === 'validation' },
    { id: 'validation', label: 'Validation', icon: ShieldCheck, visible: isIntro || isExecution || isQuery },
    { id: 'execution', label: 'Execution Mode', icon: Play, visible: isIntro || isQuery || featureState === 'validation' },
  ]

  return (
    <div className="space-y-4">
      {/* Smart Data Branding - High Energy / AI Style */}
      <div className="px-4 py-3 flex items-center gap-4 mb-2 group relative">
        {/* Glowing Background Aura */}
        <div className="absolute left-6 w-8 h-8 bg-indigo-500/20 blur-2xl rounded-full animate-pulse group-hover:bg-fuchsia-500/30 transition-colors" />
        
        <div className="relative w-11 h-11 rounded-xl bg-gradient-to-br from-indigo-600 via-blue-600 to-fuchsia-500 flex items-center justify-center flex-shrink-0 shadow-2xl shadow-indigo-500/40 transition-all duration-500 group-hover:rotate-12 group-hover:scale-110">
          <Sparkles size={20} className="text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.8)] fill-white/10" />
        </div>
        <div className="flex flex-col relative">
          <p className="text-sm font-black leading-tight uppercase tracking-[-0.03em] text-slate-900 group-hover:text-indigo-600 transition-colors">Smart</p>
          <div className="flex items-center gap-1">
            <p className="text-[10px] font-bold leading-tight uppercase tracking-[0.2em] text-fuchsia-600">Data</p>
            <div className="w-1 h-1 rounded-full bg-fuchsia-500 animate-bounce" />
          </div>
        </div>
      </div>

      <div className="px-4">
        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 opacity-60 border-t border-slate-100 pt-4">Module Workspace</p>
      </div>
      <div className="space-y-2">
        {modes.filter(m => m.visible).map((mode) => {
          const isActive = featureState === mode.id || (mode.id === 'query' && isIntro)
          const Icon = mode.icon
          
          return (
            <React.Fragment key={mode.id}>
              <button
                onClick={() => setFeatureState(mode.id)}
                className={`w-full flex items-center justify-between px-4 py-3 rounded-xl transition-all duration-300 group ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20'
                    : 'text-slate-400 hover:bg-slate-50 hover:text-slate-900'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon size={16} className={isActive ? 'text-white' : 'opacity-40 group-hover:opacity-100'} />
                  <span className="text-xs font-black uppercase tracking-widest">
                    {mode.label}
                  </span>
                </div>
                {isActive && <ChevronRight size={14} className="opacity-50" />}
              </button>

              {mode.id === 'validation' && isExecution && (
                <div className="mx-2 mt-4 space-y-4 animate-in slide-in-from-top-2 duration-300">
                  <div className="space-y-1.5">
                    <label className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">Data Layer</label>
                    <div className="relative">
                      <select
                        value={selectedDataset}
                        onChange={(e) => setSelectedDataset(e.target.value)}
                        className="w-full appearance-none text-[11px] font-bold text-slate-700 bg-white border border-slate-200 rounded-lg px-2 py-2 pr-7 outline-none focus:border-blue-400 transition-all cursor-pointer"
                      >
                        <option value="bronze_silver">Bronze → Silver</option>
                        <option value="silver_gold">Silver → Gold</option>
                        {uploadedFile && (
                          <option value={uploadedFile.name}>{uploadedFile.name} (Uploaded)</option>
                        )}
                        <option value="custom">Custom Setup</option>
                      </select>
                      <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" size={12} />
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">Source File</label>
                    <div className="flex gap-2">
                      <label className={`flex-1 flex items-center min-w-0 gap-2 cursor-pointer p-2 rounded-lg border transition-all ${uploadedFile ? 'border-emerald-200 bg-emerald-50/50' : 'border-slate-200 bg-white hover:border-blue-300'}`}>
                        <input type="file" className="hidden" accept=".csv" onChange={handleFileUpload} />
                        <CloudUpload size={14} className={`${uploadedFile ? 'text-emerald-600' : 'text-slate-400'} shrink-0`} />
                        <span className="text-[10px] font-bold text-slate-600 truncate flex-1 min-w-0">{uploadedFile ? uploadedFile.name : 'Upload CSV'}</span>
                      </label>
                      {uploadedFile && (
                        <button 
                          onClick={() => {
                            setUploadedFile(null);
                          }}
                          className="p-2 rounded-lg border border-rose-100 bg-rose-50 text-rose-500 hover:bg-rose-100 transition-all flex items-center justify-center shadow-sm"
                        >
                          <Trash2 size={14} />
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="pt-2">
                    <button
                      onClick={() => {
                        setFeatureState('execution');
                        toggleExecution();
                      }}
                      className={`w-full py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest flex items-center justify-center gap-2 transition-all active:scale-[0.98] ${isRunning
                        ? 'bg-rose-500 hover:bg-rose-600 text-white shadow-lg shadow-rose-500/20'
                        : 'bg-slate-900 hover:bg-black text-white shadow-lg shadow-slate-900/20'
                      }`}
                    >
                      {isRunning ? <><RefreshCw size={12} className="animate-spin" /> Stop</> : <><Zap size={12} /> Run</>}
                    </button>
                  </div>

                  <div className="pt-2 border-t border-slate-100">
                    <label className="text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1.5 block">Report Format</label>
                    <div className="relative">
                      <select
                        value={selectedReport}
                        onChange={(e) => setSelectedReport(e.target.value)}
                        className="w-full appearance-none text-[11px] font-bold text-slate-700 bg-white border border-slate-200 rounded-lg px-2 py-2 pr-7 outline-none focus:border-blue-400 transition-all cursor-pointer shadow-sm"
                      >
                        <option value="none">Select Report...</option>
                        <option value="allure">Allure Report</option>
                        <option value="custom">Custom Report</option>
                      </select>
                      <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" size={12} />
                    </div>
                  </div>
                </div>
              )}
            </React.Fragment>
          )
        })}
      </div>
    </div>
  )
}
