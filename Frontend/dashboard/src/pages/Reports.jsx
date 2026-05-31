import React, { useState, useEffect } from 'react'
import {
  FileText, CheckCircle, XCircle, Clock,
  Download, BarChart3, FileDown, Search, Filter, Loader2, ArrowRightLeft,
  X, Trash2, RefreshCw, TrendingUp, AlertTriangle
} from 'lucide-react'
import { api } from '../services/api'

export default function Reports() {
  const [reports, setReports] = useState([])
  const [selectedReport, setSelectedReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [summaryData, setSummaryData] = useState(null)
  const [showSummary, setShowSummary] = useState(false)
  const [summaryLoading, setSummaryLoading] = useState(false)

  const fetchReports = () => {
    setLoading(true)
    api.getRecentReports()
      .then(data => {
        setReports(Array.isArray(data) ? data : [])
        setLoading(false)
      })
      .catch(err => {
        console.error("Failed to fetch reports:", err)
        setReports([])
        setLoading(false)
      })
  }

  useEffect(() => {
    fetchReports()
  }, [])

  const handleGenerateSummary = async () => {
    setSummaryLoading(true)
    setShowSummary(true)
    try {
      const data = await api.getReportSummary()
      setSummaryData(data)
    } catch (err) {
      console.error("Failed to generate summary:", err)
      setSummaryData(null)
    }
    setSummaryLoading(false)
  }

  const handleExportCSV = async () => {
    try {
      await api.exportReportsCSV()
    } catch (err) {
      console.error("Failed to export CSV:", err)
    }
  }

  const handleDeleteReport = async (reportId) => {
    try {
      await api.deleteReport(reportId)
      setReports(prev => prev.filter(r => r.id !== reportId))
      if (selectedReport?.id === reportId) setSelectedReport(null)
    } catch (err) {
      console.error("Failed to delete report:", err)
    }
  }

  const handleExportPDF = () => {
    // Open a printable view in new window
    const printContent = selectedReport
      ? `
        <html><head><title>Report #${selectedReport.id}</title>
        <style>body{font-family:system-ui,sans-serif;padding:40px;color:#1e293b}
        h1{font-size:24px;margin-bottom:8px} h2{font-size:16px;color:#64748b;margin-bottom:24px}
        .badge{display:inline-block;padding:4px 12px;border-radius:6px;font-size:12px;font-weight:700;text-transform:uppercase}
        .passed{background:#d1fae5;color:#059669} .failed{background:#ffe4e6;color:#e11d48}
        table{width:100%;border-collapse:collapse;margin-top:16px} td,th{text-align:left;padding:8px 12px;border-bottom:1px solid #e2e8f0;font-size:13px}
        th{color:#94a3b8;font-size:11px;text-transform:uppercase;letter-spacing:0.1em}
        pre{background:#f8fafc;padding:16px;border-radius:8px;font-size:12px;overflow:auto;max-height:400px}
        </style></head><body>
        <h1>Report #${selectedReport.id}</h1>
        <h2>${selectedReport.type} — ${selectedReport.timestamp}</h2>
        <span class="badge ${selectedReport.status}">${selectedReport.status}</span>
        <p style="margin-top:16px;color:#64748b;font-size:14px">${selectedReport.summary || 'No summary available.'}</p>
        ${selectedReport.details ? `<h3 style="margin-top:24px">Execution Details</h3><pre>${typeof selectedReport.details === 'string' ? selectedReport.details : JSON.stringify(JSON.parse(selectedReport.details), null, 2)}</pre>` : ''}
        </body></html>`
      : ''
    const win = window.open('', '_blank')
    win.document.write(printContent)
    win.document.close()
    setTimeout(() => { win.print() }, 400)
  }

  if (loading) return (
    <div className="h-full flex flex-col items-center justify-center space-y-4">
      <Loader2 size={32} className="animate-spin text-blue-600" />
      <p className="text-[10px] font-black uppercase tracking-[0.3em] opacity-30 text-slate-900">Retrieving Archives...</p>
    </div>
  )

  // Parse details JSON safely
  const parseDetails = (report) => {
    if (!report?.details) return null
    try {
      return typeof report.details === 'string' ? JSON.parse(report.details) : report.details
    } catch {
      return null
    }
  }

  const selectedDetails = parseDetails(selectedReport)

  return (
    <div className="h-full flex flex-col lg:flex-row gap-8 animate-in fade-in duration-700 text-left">
      <div className="flex-1 space-y-6 flex flex-col min-h-0">
        {/* Header */}
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
          <div className="flex items-center gap-3">
            <button
              onClick={fetchReports}
              className="p-3 rounded-xl border border-slate-200 text-slate-400 hover:text-slate-900 hover:bg-slate-50 transition-all"
              title="Refresh"
            >
              <RefreshCw size={16} />
            </button>
            <button
              onClick={handleGenerateSummary}
              className="px-6 py-3 rounded-xl bg-blue-600 text-white text-[10px] font-black uppercase tracking-widest shadow-lg shadow-blue-500/20 hover:bg-blue-700 transition-all"
            >
              Generate Master Summary
            </button>
          </div>
        </div>

        {/* Summary Modal */}
        {showSummary && (
          <div className="border border-blue-100 rounded-2xl bg-gradient-to-br from-blue-50/50 to-indigo-50/30 p-6 space-y-4 animate-in slide-in-from-top-2 duration-300 shadow-lg">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-black uppercase tracking-[0.15em] text-blue-700 flex items-center gap-2">
                <TrendingUp size={16} /> Master Summary
              </h2>
              <button onClick={() => setShowSummary(false)} className="p-1 rounded-lg hover:bg-blue-100 text-blue-400 transition-colors">
                <X size={16} />
              </button>
            </div>
            {summaryLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 size={24} className="animate-spin text-blue-500" />
              </div>
            ) : summaryData ? (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-xl bg-white border border-slate-100 shadow-sm">
                  <p className="text-[8px] font-black uppercase tracking-widest text-slate-400 mb-1">Total Runs</p>
                  <p className="text-2xl font-black text-slate-900">{summaryData.total_runs}</p>
                </div>
                <div className="p-4 rounded-xl bg-white border border-emerald-100 shadow-sm">
                  <p className="text-[8px] font-black uppercase tracking-widest text-emerald-500 mb-1">Passed</p>
                  <p className="text-2xl font-black text-emerald-600">{summaryData.passed}</p>
                </div>
                <div className="p-4 rounded-xl bg-white border border-rose-100 shadow-sm">
                  <p className="text-[8px] font-black uppercase tracking-widest text-rose-400 mb-1">Failed</p>
                  <p className="text-2xl font-black text-rose-600">{summaryData.failed}</p>
                </div>
                <div className="p-4 rounded-xl bg-white border border-blue-100 shadow-sm">
                  <p className="text-[8px] font-black uppercase tracking-widest text-blue-400 mb-1">Pass Rate</p>
                  <p className="text-2xl font-black text-blue-600">{summaryData.pass_rate}%</p>
                </div>
                {summaryData.by_type && Object.keys(summaryData.by_type).length > 0 && (
                  <div className="col-span-full p-4 rounded-xl bg-white border border-slate-100 shadow-sm">
                    <p className="text-[8px] font-black uppercase tracking-widest text-slate-400 mb-3">Breakdown by Type</p>
                    <div className="flex flex-wrap gap-3">
                      {Object.entries(summaryData.by_type).map(([type, counts]) => (
                        <div key={type} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-50 border border-slate-100">
                          <span className="text-[10px] font-black uppercase tracking-wider text-slate-600">{type}</span>
                          <span className="text-[9px] font-bold text-emerald-600">✓ {counts.passed || 0}</span>
                          <span className="text-[9px] font-bold text-rose-500">✗ {counts.failed || 0}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8">
                <AlertTriangle size={20} className="text-amber-400 mx-auto mb-2" />
                <p className="text-xs font-bold text-slate-400">No data available. Run some tests first.</p>
              </div>
            )}
          </div>
        )}

        {/* Reports Table */}
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
                  <tr key={r.id} className={`hover:bg-slate-50/50 transition-colors group ${selectedReport?.id === r.id ? 'bg-blue-50/30' : ''}`}>
                    <td className="px-8 py-5 text-blue-600 font-mono tracking-tighter">#{r.id}</td>
                    <td className="px-8 py-5 text-slate-400 font-medium">{r.timestamp}</td>
                    <td className="px-8 py-5 text-slate-900 uppercase tracking-tighter">{r.type || 'Undefined'}</td>
                    <td className="px-8 py-5">
                      <span className={`px-2 py-1 rounded-md text-[9px] uppercase font-black tracking-widest ${r.status === 'passed' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'
                        }`}>
                        {r.status || 'Unknown'}
                      </span>
                    </td>
                    <td className="px-8 py-5 text-right flex items-center justify-end gap-3">
                      <button
                        onClick={() => setSelectedReport(r)}
                        className="text-blue-600 hover:text-blue-800 transition-colors uppercase tracking-widest text-[10px]"
                      >
                        Inspect
                      </button>
                      <button
                        onClick={() => handleDeleteReport(r.id)}
                        className="text-slate-300 hover:text-rose-500 transition-colors opacity-0 group-hover:opacity-100"
                        title="Delete report"
                      >
                        <Trash2 size={14} />
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

      {/* Detail Panel */}
      {selectedReport && (
        <div className="lg:w-[400px] border border-slate-200 rounded-3xl p-8 space-y-8 bg-white shadow-2xl animate-in slide-in-from-right-4 duration-500 relative flex flex-col overflow-y-auto">
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
                <p className="text-[8px] font-black uppercase tracking-widest text-slate-400 mb-2">Summary</p>
                <p className="text-[11px] font-bold text-slate-700 leading-relaxed">
                  {selectedReport.summary || 'No summary available for this report.'}
                </p>
              </div>

              {/* Validation Logs from details */}
              {selectedDetails?.validation_logs && selectedDetails.validation_logs.length > 0 && (
                <div className="pt-4 border-t border-slate-50 space-y-3">
                  <p className="text-[8px] font-black uppercase tracking-widest text-slate-400">Validation Results</p>
                  {selectedDetails.validation_logs.map((log, i) => (
                    <div key={i} className="flex items-center justify-between text-[10px] font-bold text-slate-900">
                      <span className="flex items-center gap-2 font-black uppercase tracking-widest text-slate-400">
                        <CheckCircle size={12} className={selectedReport.status === 'passed' ? 'text-emerald-500' : 'text-rose-400'} />
                        Check {i + 1}
                      </span>
                      <span className="text-right max-w-[200px] truncate">{log}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Execution Logs from details */}
              {selectedDetails?.execution_logs && selectedDetails.execution_logs.length > 0 && (
                <div className="pt-4 border-t border-slate-50 space-y-2">
                  <p className="text-[8px] font-black uppercase tracking-widest text-slate-400">Execution Trace</p>
                  <div className="bg-slate-900 rounded-xl p-4 max-h-48 overflow-y-auto">
                    {selectedDetails.execution_logs.map((log, i) => (
                      <p key={i} className="text-[10px] font-mono text-emerald-400 leading-relaxed">{log}</p>
                    ))}
                  </div>
                </div>
              )}

              {/* Mismatch Details for ETL reports */}
              {selectedDetails?.mismatchDetails && selectedDetails.mismatchDetails.length > 0 && (
                <div className="pt-4 border-t border-slate-50 space-y-3">
                  <p className="text-[8px] font-black uppercase tracking-widest text-slate-400">Mismatch Details</p>
                  <div className="space-y-2">
                    {selectedDetails.mismatchDetails.slice(0, 5).map((m, i) => (
                      <div key={i} className="p-3 rounded-xl bg-rose-50/50 border border-rose-100 text-[10px]">
                        <div className="flex justify-between items-center mb-1">
                          <span className="font-black text-slate-700">{m.id}</span>
                          <span className={`px-2 py-0.5 rounded text-[8px] font-black uppercase ${m.risk === 'Critical' ? 'bg-rose-200 text-rose-800' : m.risk === 'High' ? 'bg-amber-200 text-amber-800' : 'bg-slate-200 text-slate-600'}`}>{m.risk}</span>
                        </div>
                        <p className="text-slate-500"><span className="font-bold text-slate-600">{m.field}:</span> {m.source} → {m.target}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* API Test specific: status code, latency */}
              {selectedDetails?.status_code !== undefined && (
                <div className="pt-4 border-t border-slate-50 space-y-3">
                  <div className="flex items-center justify-between text-[10px] font-bold text-slate-900">
                    <span className="flex items-center gap-2 font-black uppercase tracking-widest text-slate-400">
                      <CheckCircle size={12} className="text-blue-500" /> HTTP Status
                    </span>
                    <span>{selectedDetails.status_code}</span>
                  </div>
                  <div className="flex items-center justify-between text-[10px] font-bold text-slate-900">
                    <span className="flex items-center gap-2 font-black uppercase tracking-widest text-slate-400">
                      <Clock size={12} className="text-blue-500" /> Latency
                    </span>
                    <span>{selectedDetails.latency_ms}ms</span>
                  </div>
                </div>
              )}

              {/* DB Audit specific: row count */}
              {selectedDetails?.row_count !== undefined && (
                <div className="pt-4 border-t border-slate-50">
                  <div className="flex items-center justify-between text-[10px] font-bold text-slate-900">
                    <span className="flex items-center gap-2 font-black uppercase tracking-widest text-slate-400">
                      <CheckCircle size={12} className="text-blue-500" /> Records Scanned
                    </span>
                    <span>{selectedDetails.row_count}</span>
                  </div>
                </div>
              )}

              {/* ETL specific: accuracy */}
              {selectedDetails?.accuracy !== undefined && (
                <div className="pt-4 border-t border-slate-50">
                  <div className="flex items-center justify-between text-[10px] font-bold text-slate-900">
                    <span className="flex items-center gap-2 font-black uppercase tracking-widest text-slate-400">
                      <TrendingUp size={12} className="text-blue-500" /> Accuracy
                    </span>
                    <span className={selectedDetails.accuracy >= 95 ? 'text-emerald-600' : 'text-rose-600'}>{selectedDetails.accuracy}%</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="pt-8 flex flex-col gap-3">
            <button
              onClick={handleExportPDF}
              className="w-full py-4 rounded-2xl bg-slate-900 text-white text-[10px] font-black uppercase tracking-[0.2em] shadow-xl hover:bg-black transition-all flex items-center justify-center gap-3"
            >
              <FileDown size={14} /> Export full PDF
            </button>
            <button
              onClick={handleExportCSV}
              className="w-full py-4 rounded-2xl bg-white border border-slate-200 text-slate-900 text-[10px] font-black uppercase tracking-[0.2em] hover:bg-slate-50 transition-all flex items-center justify-center gap-3"
            >
              <Download size={14} /> Download raw CSV
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
