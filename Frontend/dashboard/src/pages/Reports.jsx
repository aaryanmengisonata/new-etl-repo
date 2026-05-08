import React, { useState, useEffect } from 'react'
import { 
  FileText, CheckCircle, XCircle, Clock, 
  Download, BarChart3, FileDown, Search, Filter, Loader2, ArrowRightLeft
} from 'lucide-react'

export default function Reports() {
  const [reports, setReports] = useState([])
  const [selectedReport, setSelectedReport] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('http://localhost:8000/recent-reports')
      .then(res => res.json())
      .then(data => {
        setReports(Array.isArray(data) ? data : [])
        setLoading(false)
      })
      .catch(err => {
        console.error("Failed to fetch reports:", err)
        setLoading(false)
      })
  }, [])

  if (loading) return (
    <div className="h-full flex flex-col items-center justify-center space-y-4">
      <Loader2 size={32} className="animate-spin text-blue-600" />
      <p className="text-[10px] font-black uppercase tracking-[0.3em] opacity-30 text-slate-900">Retrieving Archives...</p>
    </div>
  )

  return (
    <div className="h-full flex flex-col lg:flex-row gap-8 animate-in fade-in duration-700 text-left">
      <div className="flex-1 space-y-6 flex flex-col min-h-0">
        <div className="flex items-center justify-between p-6 rounded-2xl border border-slate-200 bg-white shadow-xl">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-blue-50 flex items-center justify-center text-blue-600">
              <BarChart3 size={24} />
            </div>
            <div>
              <h1 className="text-xl font-black uppercase tracking-tight text-slate-900">Audit Repository</h1>
              <p className="text-xs font-medium uppercase tracking-tighter text-slate-400">Historical structural validation results</p>
            </div>
          </div>
          <button className="px-6 py-3 rounded-xl bg-blue-600 text-white text-[10px] font-black uppercase tracking-widest shadow-lg shadow-blue-500/20 hover:bg-blue-700 transition-all">
            Generate Master Summary
          </button>
        </div>

        <div className="flex-1 border border-slate-200 rounded-2xl overflow-hidden bg-white shadow-2xl flex flex-col min-h-0">
          <div className="overflow-y-auto flex-1">
            <table className="w-full text-left border-collapse">
              <thead className="sticky top-0 bg-slate-50 border-b border-slate-100 z-10">
                <tr className="uppercase text-[10px] font-black text-slate-400">
                  <th className="px-8 py-5">Run ID</th>
                  <th className="px-8 py-5">Timestamp</th>
                  <th className="px-8 py-5">Scenario Type</th>
                  <th className="px-8 py-5">Validation</th>
                  <th className="px-8 py-5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="text-[11px] font-bold divide-y divide-slate-50">
                {reports.map(r => (
                  <tr key={r.id} className="hover:bg-slate-50/50 transition-colors group">
                    <td className="px-8 py-5 text-blue-600 font-mono tracking-tighter">#{r.id}</td>
                    <td className="px-8 py-5 text-slate-400 font-medium">{r.timestamp}</td>
                    <td className="px-8 py-5 text-slate-900 uppercase tracking-tighter">{r.type || 'Undefined'}</td>
                    <td className="px-8 py-5">
                      <span className={`px-2 py-1 rounded-md text-[9px] uppercase font-black tracking-widest ${
                        r.status === 'passed' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'
                      }`}>
                        {r.status || 'Unknown'}
                      </span>
                    </td>
                    <td className="px-8 py-5 text-right">
                      <button 
                        onClick={() => setSelectedReport(r)} 
                        className="text-blue-600 hover:text-blue-800 transition-colors uppercase tracking-widest text-[10px]"
                      >
                        Inspect Detail
                      </button>
                    </td>
                  </tr>
                ))}
                {reports.length === 0 && (
                  <tr>
                    <td colSpan="5" className="px-8 py-20 text-center opacity-30 uppercase tracking-[0.2em] font-black">No records found in storage</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {selectedReport && (
        <div className="lg:w-[400px] border border-slate-200 rounded-3xl p-8 space-y-8 bg-white shadow-2xl animate-in slide-in-from-right-4 duration-500 relative flex flex-col">
          <button 
             onClick={() => setSelectedReport(null)}
             className="absolute top-6 right-6 p-2 rounded-full hover:bg-slate-100 text-slate-400 transition-colors"
          >
            <X size={16} />
          </button>

          <div className="space-y-6">
            <h2 className="text-sm font-black uppercase tracking-[0.2em] text-blue-600 py-2 border-b border-blue-50">Audit Detail Spectrum</h2>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100">
                <p className="text-[8px] font-black uppercase tracking-widest text-slate-400 mb-1">Status</p>
                <p className={`text-xs font-black uppercase ${selectedReport.status === 'passed' ? 'text-emerald-600' : 'text-rose-600'}`}>{selectedReport.status}</p>
              </div>
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100">
                <p className="text-[8px] font-black uppercase tracking-widest text-slate-400 mb-1">Engine</p>
                <p className="text-xs font-black uppercase text-slate-900">{selectedReport.type}</p>
              </div>
            </div>

            <div className="space-y-4">
               <div>
                  <p className="text-[8px] font-black uppercase tracking-widest text-slate-400 mb-2">Technical Summary</p>
                  <p className="text-[11px] font-bold text-slate-700 leading-relaxed">
                    Automated validation process executed against historical buffer. All schema invariants were analyzed for structural integrity and data quality compliance.
                  </p>
               </div>
               
               <div className="pt-4 border-t border-slate-50 space-y-3">
                 <div className="flex items-center justify-between text-[10px] font-bold text-slate-900">
                    <span className="flex items-center gap-2 font-black uppercase tracking-widest text-slate-400"><CheckCircle size={12} className="text-emerald-500"/> Schema Check</span>
                    <span>100% Valid</span>
                 </div>
                 <div className="flex items-center justify-between text-[10px] font-bold text-slate-900">
                    <span className="flex items-center gap-2 font-black uppercase tracking-widest text-slate-400"><CheckCircle size={12} className="text-emerald-500"/> Null Analysis</span>
                    <span>No Anomalies</span>
                 </div>
               </div>
            </div>
          </div>

          <div className="pt-8 flex flex-col gap-3">
             <button className="w-full py-4 rounded-2xl bg-slate-900 text-white text-[10px] font-black uppercase tracking-[0.2em] shadow-xl hover:bg-black transition-all flex items-center justify-center gap-3">
               <FileDown size={14}/> Export full PDF
             </button>
             <button className="w-full py-4 rounded-2xl bg-white border border-slate-200 text-slate-900 text-[10px] font-black uppercase tracking-[0.2em] hover:bg-slate-50 transition-all flex items-center justify-center gap-3">
               <Download size={14}/> Download raw CSV
             </button>
          </div>
        </div>
      )}
    </div>
  )
}
