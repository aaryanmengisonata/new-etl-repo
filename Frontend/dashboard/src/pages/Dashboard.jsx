import React from 'react'
import { 
  Globe, Database, Activity, Share2, ArrowRightLeft, 
  FileSpreadsheet, ChevronRight, Sparkles
} from 'lucide-react'

const features = [
  {
    id: 'fabric',
    title: 'Fabric Validation',
    description: 'AI-driven reconciliation for Microsoft Fabric Lakehouse. Validate Bronze, Silver, and Gold layers with zero code.',
    icon: Share2,
    color: 'emerald',
    tags: ['MS FABRIC', 'AI READY'],
    popular: true
  },
  {
    id: 'test_cases',
    title: 'Data Testing Case',
    description: 'Define and manage complex Data test skeletons. Skeleton-based validation for high-throughput data pipelines.',
    icon: Database,
    color: 'blue',
    tags: ['SKELETONS', 'CSV/XL']
  },
  {
    id: 'etl',
    title: 'Pipeline Auditor',
    description: 'Professional-grade Data pipeline validation. Verify transformations and data integrity across your entire stack.',
    icon: Activity,
    color: 'violet',
    tags: ['PIPELINES', 'LAKEHOUSE']
  },
  {
    id: 'api',
    title: 'Endpoint Sentry',
    description: 'Advanced REST endpoint validation. Monitor schemas, status codes, and latency in real-time.',
    icon: Globe,
    color: 'blue',
    tags: ['REST', 'PROD']
  },
  {
    id: 'source_target',
    title: 'System Reconciler',
    description: 'Bit-perfect comparison between disparate systems. Detailed reconciliation reports for multi-petabyte datasets.',
    icon: ArrowRightLeft,
    color: 'rose',
    tags: ['RECON', 'DIFF']
  }
]

export default function Dashboard({ setActivePage, featureState, setFeatureState }) {
  const handleFeatureSelect = (id) => {
    const map = { api: 'run', etl: 'run', fabric: 'fabric_audit', source_target: 'reports', test_cases: 'test_cases' }
    // Reset feature state when navigating from home
    setFeatureState('')
    setActivePage(map[id] || 'dashboard')
  }

  return (
    <div className="min-h-full flex flex-col items-center animate-in fade-in zoom-in duration-1000 relative pb-20 bg-white text-slate-800 text-center">
      
      {/* Background Ambience */}
      <div className="absolute inset-x-0 top-0 h-[500px] pointer-events-none overflow-hidden select-none">
        <div className="absolute top-[-10%] left-[20%] w-[600px] h-[600px] rounded-full blur-[120px] opacity-20 bg-blue-200" />
        <div className="absolute top-[10%] right-[10%] w-[400px] h-[400px] rounded-full blur-[100px] opacity-10 bg-purple-200" />
      </div>

      {/* Hero Section */}
      <div className="relative flex flex-col items-center pt-24 pb-16 px-6 z-10">
        <div className="mb-8 px-5 py-2 rounded-full border border-blue-100 bg-white text-blue-600 shadow-xl flex items-center gap-3 text-[10px] font-black uppercase tracking-[0.25em]">
          <Sparkles size={14} className="animate-pulse" />
          The Intelligence Layer of Data Quality
        </div>

        <h1 className="text-5xl md:text-7xl font-black tracking-tighter mb-8 leading-tight text-slate-900">
          Scale Your <span className="bg-gradient-to-r from-blue-600 via-indigo-500 to-purple-500 bg-clip-text text-transparent">Reliability</span>
        </h1>

        <p className="text-base font-medium leading-relaxed max-w-2xl mx-auto opacity-50 mb-12 text-slate-600">
          Orchestrate your data quality with precision. Select a mission-critical workspace to begin your automated validation journey.
        </p>
      </div>

      {/* Grid Section */}
      <div className="relative w-full max-w-6xl mx-auto px-6 z-10 pb-20">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
           {features.map(f => (
             <div 
                key={f.id}
                onClick={() => handleFeatureSelect(f.id)}
                className="group relative flex flex-col p-10 rounded-[2.5rem] border border-slate-200 bg-white hover:border-blue-500/20 hover:shadow-2xl shadow-slate-200/50 transition-all duration-500 cursor-pointer overflow-hidden text-left"
             >
                <div className="w-14 h-14 rounded-2xl mb-8 flex items-center justify-center transition-all duration-500 group-hover:scale-110 group-hover:rotate-6 bg-slate-50 text-blue-600">
                  <f.icon size={28} />
                </div>

                <div className="space-y-3 mb-8">
                  <h3 className="text-xl font-black uppercase tracking-tight text-slate-900">{f.title}</h3>
                  <p className="text-xs leading-relaxed opacity-40 font-medium text-slate-600">{f.description}</p>
                </div>

                <div className="mt-auto pt-6 border-t border-dashed border-slate-500/10 flex items-center justify-between">
                  <div className="flex gap-2">
                    {f.tags.map(t => (
                      <span key={t} className="text-[9px] font-bold px-3 py-1 rounded-lg bg-slate-50 text-slate-400">{t}</span>
                    ))}
                  </div>
                  <div className="w-8 h-8 rounded-full flex items-center justify-center transition-all opacity-0 -translate-x-4 group-hover:opacity-100 group-hover:translate-x-0 bg-blue-600 text-white shadow-lg shadow-blue-500/20">
                    <ChevronRight size={16} />
                  </div>
                </div>
             </div>
           ))}
        </div>
      </div>
    </div>
  )
}
