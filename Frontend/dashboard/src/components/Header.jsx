import React from 'react'
import { Settings, Sparkles } from 'lucide-react'
import { useAppContext } from '../store/AppContext'
import logo from "../assets/Images/Sonata_Software_Logo.svg"
import intelqa_logo from "../assets/Images/Intell_Logo.svg"

const pageTitles = {
  dashboard: { title: 'Dashboard', subtitle: 'Select a validation feature to begin' },
  test_cases: { title: 'Test Case Definition', subtitle: 'Define and manage CSV/Excel test skeletons' },
  run: { title: 'Execution Engine', subtitle: 'Trigger automated validations and stream terminal output' },
  reports: { title: 'Report Management', subtitle: 'Audit historical runs and compare results' },
  configuration: { title: 'Master Configuration', subtitle: 'Manage connection strings and environment variables' },
  fabric_audit: { title: 'Fabric Validation', subtitle: 'Enterprise Data Auditing Platform' },
}

export default function Header({ activePage }) {
  const { setIsSettingsOpen, featureState } = useAppContext();
  let { title, subtitle } = pageTitles[activePage] || { title: 'Platform', subtitle: 'Enterprise Logic' }
  
  const isQueryMode = activePage === 'fabric_audit' && featureState === 'query'
  if (isQueryMode) {
    title = 'Query Builder'
    subtitle = 'AI-powered logic generation'
  }

  return (
    <header className="h-20 flex-shrink-0 bg-white border-b border-slate-100 flex items-center justify-between px-8 z-50">
      {/* Module Title */}
      <div>
         <h2 className="text-sm font-black text-slate-900 tracking-tight uppercase">{title}</h2>
         <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">{subtitle}</p>
      </div>

      {/* ---------- Actions ---------- */}
      <div className="flex items-center gap-4">
        {(!featureState || featureState === 'intro') && (
          <button 
            onClick={() => setIsSettingsOpen(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl border text-[10px] font-black uppercase tracking-widest transition-all bg-white border-slate-200 text-slate-500 hover:bg-slate-50 hover:border-blue-500/50 shadow-sm"
          >
            <Settings size={14} className="text-blue-500" />
            Settings
          </button>
        )}
      </div>
    </header>
  )
}
