import React, { useState, useEffect } from 'react'
import { useAppContext } from '../store/AppContext'
import { api } from '../services/api'
import {
   Play, Settings, Send,
   FileText, ChevronRight,
   Sparkles, MessageSquare, Cpu,
   CloudUpload, ArrowRight, Zap,
   Database, RefreshCw, Activity, Layers,
   Terminal as TerminalIcon, PlusCircle,
   Undo2, AlertCircle, CheckCircle as CheckCircleIcon,
   ChevronDown, X, Maximize2
} from 'lucide-react'
import Terminal from '../components/shared/Terminal'

// Query Builder Components
import QueryHeader from '../components/features/query-builder/Header'
import InputPanel from '../components/features/query-builder/InputPanel'
import OutputPanel from '../components/features/query-builder/OutputPanel'
import HistoryDrawer from '../components/features/query-builder/HistoryDrawer'
import ValidationPanel from '../components/features/query-builder/ValidationPanel'

export default function FabricAudit({ setActivePage, setNavParams, featureState, setFeatureState }) {
   const {
      isRunning, logs, showLogs, selectedDataset, selectedReport, uploadedFile,
      isComplete, setIsComplete,
      reportData, setReportData,
      gridColumns, gridData, gridSourceFile,
      updateGridCell, addGridRow, deleteGridRow,
      addGridColumn, deleteGridColumn,
      toggleExecution, handleFileUpload,
      showAlert, setCustomAlert
   } = useAppContext()

   // Query Mode State
   const [prompt, setPrompt] = useState('')
   const [queryBuffer, setQueryBuffer] = useState('')
   const [isLlmLoading, setIsLlmLoading] = useState(false)
   const [saveStatus, setSaveStatus] = useState('idle') // 'idle', 'saving', 'saved'
   
   // History State
   const [history, setHistory] = useState(() => {
      const saved = localStorage.getItem('query_history');
      return saved ? JSON.parse(saved) : [];
   });
   const [isHistoryOpen, setIsHistoryOpen] = useState(false);
   
   // Cell Editing State
   const [activeCellEdit, setActiveCellEdit] = useState(null); // { r, c, val }

   useEffect(() => {
      localStorage.setItem('query_history', JSON.stringify(history));
   }, [history]);

   const currentMode = (!featureState || featureState === 'intro') ? 'intro' : featureState

   // --- LLM LOGIC ---
   const handleGenerateQuery = async () => {
      if (!prompt.trim()) return
      setIsLlmLoading(true)

      try {
         const data = await api.generateQuery(prompt, queryBuffer)
         const result = data.query
         
         setQueryBuffer(result)
         setIsLlmLoading(false)

         // Add to history
         const newItem = {
            id: Date.now(),
            prompt: prompt,
            query: result,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ', ' + new Date().toLocaleDateString([], { month: 'short', day: 'numeric' })
         };
         setHistory(prev => [newItem, ...prev].slice(0, 20));
      } catch (error) {
         console.error("Query generation failed:", error)
         showAlert("Generation Failed", "Failed to generate query. Please check if the backend is running.", "error")
         setIsLlmLoading(false)
      }
   }

   const handleRestoreHistory = (item) => {
      setPrompt(item.prompt);
      setQueryBuffer(item.query);
      setIsHistoryOpen(false);
   };

   const handleDeleteHistory = (id) => {
      setHistory(prev => prev.filter(item => item.id !== id));
   };

   const handleClearHistory = () => {
      showAlert(
         "Clear History",
         "Are you sure you want to clear all query history? This action cannot be undone.",
         "confirm",
         () => setHistory([])
      );
   };


   const openSettings = () => {
      setNavParams({ defaultTab: 'fabric', returnPage: 'fabric_audit', returnMode: 'query' })
      setActivePage('configuration')
   }

   const handleSave = () => {
      setSaveStatus('saving')
      setTimeout(() => {
         setSaveStatus('saved')
         setTimeout(() => setSaveStatus('idle'), 3000)
      }, 1000)
   }

   const handleExport = (type = 'csv') => {
      if (type === 'pdf') {
         window.print();
         return;
      }

      if (type === 'html' && selectedReport !== 'none') {
         const link = document.createElement('a');
         link.href = `/reports/${selectedReport}.html`;
         link.download = `${selectedReport}_report.html`;
         link.click();
         return;
      }

      // Default CSV export logic
      let content = "";
      let filename = "";

      if (reportData && !isReportMode) {
         content = "Record ID,Field,Source,Target,Risk\n" +
            reportData.mismatchDetails.map(m => `${m.id},${m.field},${m.source},${m.target},${m.risk}`).join("\n");
         filename = `Audit_Results_${datasetLabel}_${new Date().toISOString().slice(0,10)}.csv`;
      } else {
         content = gridColumns.join(",") + "\n" + 
                  gridData.map(row => row.map(cell => `"${cell}"`).join(",")).join("\n");
         filename = `Fabric_Data_Export_${new Date().toISOString().slice(0,10)}.csv`;
      }

      const blob = new Blob([content], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
   };


   // --- RENDER INTRO MODE ---
   if (currentMode === 'intro') {
      return (
         <div className="w-full flex flex-col p-8 lg:p-12 animate-in fade-in duration-700 bg-slate-50/30">
            <div className="max-w-5xl mx-auto w-full pt-4">
               {/* Core Bento Overview */}
               <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                  {/* Main Description */}
                  <div className="md:col-span-2 p-10 rounded-[2rem] bg-white border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
                     <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center mb-6">
                        <Sparkles size={20} className="text-blue-600" />
                     </div>
                     <h2 className="text-xl font-black text-slate-800 mb-4 tracking-tight">AI-Driven Reconciliation</h2>
                     <p className="text-sm font-medium text-slate-500 leading-relaxed max-w-xl">
                        Welcome to the high-performance validation core. Construct intelligent queries using natural language or seamlessly execute enormous, large-scale data reconciliations across your Bronze, Silver, and Gold delta layers with sub-second accuracy.
                     </p>
                  </div>

                  {/* Quick Stats / Info */}
                  <div className="p-8 rounded-[2rem] bg-slate-900 text-white shadow-xl shadow-slate-900/10 flex flex-col justify-between relative overflow-hidden">
                     <div className="absolute top-0 right-0 w-32 h-32 bg-slate-800 rounded-full blur-3xl" />
                     <div className="relative z-10">
                        <Database className="text-slate-400 mb-6" size={24} />
                        <h3 className="text-sm font-black mb-2 tracking-wide">Lakehouse Integrated</h3>
                        <p className="text-[10px] font-medium text-slate-400 leading-relaxed">
                           Direct connection to Sonata Fabric Models. Delta logs tracked automatically.
                        </p>
                     </div>
                     <div className="relative z-10 mt-8 group cursor-default">
                        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500 mb-1">Architecture</p>
                        <p className="text-sm font-bold text-slate-300 group-hover:text-emerald-400 transition-colors">Medallion Native</p>
                     </div>
                  </div>
               </div>

               {/* Getting Started Guide */}
               <div className="flex flex-col items-center justify-center p-12 text-center rounded-[2rem] border border-dashed border-slate-300/60 bg-white/50">
                  <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4">
                     <ChevronRight className="text-slate-400 rotate-90" size={20} />
                  </div>
                  <h3 className="text-lg font-black text-slate-800 mb-2 tracking-tight">Ready to initiate an audit?</h3>
                  <p className="text-xs font-bold text-slate-400 max-w-sm mx-auto leading-relaxed mb-6">
                     Select either <span className="text-blue-600">Query Mode</span> to start building logic, or <span className="text-emerald-600">Execution Mode</span> to run existing pipelines using the sidebar toggle.
                  </p>
                  <button
                     onClick={() => setFeatureState('query')}
                     className="px-8 py-3 rounded-xl bg-blue-600 text-white text-[10px] font-black uppercase tracking-widest hover:bg-blue-700 transition-colors shadow-lg shadow-blue-500/20 active:scale-95"
                  >
                     Launch Query Workspace
                  </button>
               </div>

            </div>
         </div>
      )
   }

   // --- RENDER QUERY MODE ---
   if (currentMode === 'query') {
      return (
         <div className="w-full h-full flex flex-col bg-gradient-to-br from-slate-50 to-slate-100 animate-in fade-in duration-700">
            <div className="flex-1 flex gap-8 p-8 overflow-hidden">
               {/* Left Panel: Input (50%) */}
               <div className="w-1/2 h-full">
                  <InputPanel 
                     prompt={prompt} 
                     setPrompt={setPrompt} 
                     onGenerate={handleGenerateQuery} 
                     isLoading={isLlmLoading} 
                  />
               </div>

               {/* Right Panel: Logic Workspace (50%) */}
               <div className="w-1/2 h-full">
                  <OutputPanel 
                     query={queryBuffer} 
                     setQuery={setQueryBuffer}
                     onExplain={() => showAlert('AI Explanation', 'This query joins the Bronze and Silver medallion layers on ID to identify record discrepancies.', 'info')} 
                     onRefine={() => showAlert('AI Refinement Workspace', 'Opening AI Refinement Dialog...', 'info')} 
                     onRun={() => {
                         setFeatureState('validation')
                      }} 
                     onFormat={() => showAlert('Success', 'Code formatted successfully!', 'success')}
                     onOpenHistory={() => setIsHistoryOpen(true)}
                     onLogs={() => showAlert('System Logs', 'No active logic execution logs found. Please run the query first.', 'info')}
                  />
               </div>
            </div>

            <HistoryDrawer 
               isOpen={isHistoryOpen}
               onClose={() => setIsHistoryOpen(false)}
               history={history}
               onRestore={handleRestoreHistory}
               onDelete={handleDeleteHistory}
               onClearAll={handleClearHistory}
            />
         </div>
      )
   }

   // --- RENDER VALIDATION MODE ---
   if (currentMode === 'validation') {
      return (
         <ValidationPanel 
            onProceed={() => {
               setFeatureState('execution')
               toggleExecution(queryBuffer)
            }}
         />
      )
   }

   // --- RENDER EXECUTION MODE ---
   const isReportMode = selectedReport && selectedReport !== 'none';
   const showPreview = (isReportMode || (selectedDataset && (selectedDataset !== 'custom' || uploadedFile))) && !isRunning && !isComplete;

   const datasetLabel = isReportMode 
      ? (selectedReport === 'allure' ? 'Allure Report' : 'Custom Report')
      : selectedDataset === 'bronze_silver' ? 'Bronze → Silver'
      : selectedDataset === 'silver_gold' ? 'Silver → Gold'
      : uploadedFile ? uploadedFile.name : 'Custom'


   return (
      <div className="flex-1 flex bg-white overflow-hidden">

         {/* ── Main Workspace ── */}
         <div className="flex-1 flex flex-col min-w-0 bg-white">

            {showPreview ? (
               <div className="flex-1 flex flex-col overflow-hidden animate-in fade-in duration-300">
                  {/* Dataset Header */}
                  <div className="px-6 py-3 border-b border-slate-100 flex items-center justify-between bg-white">
                     <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-md bg-blue-50 flex items-center justify-center">
                           <Database size={15} className="text-blue-500" />
                        </div>
                        <div>
                           <h2 className="text-sm font-black text-slate-800 leading-none">{datasetLabel}</h2>
                           <p className="text-[10px] text-slate-400 font-bold mt-1 uppercase tracking-tighter">
                              {gridSourceFile ? gridSourceFile : 'Lakehouse · Medallion'}
                           </p>
                        </div>
                     </div>
                     <div className="flex items-center gap-2">
                        {!isReportMode ? (
                           <>
                              <button 
                                 onClick={() => addGridColumn()}
                                 className="h-9 px-4 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all border border-slate-200 text-slate-600 hover:bg-slate-50 hover:border-slate-300"
                              >
                                 <Layers size={14} className="text-blue-500" />
                                 Add Column
                              </button>
                              <button 
                                 onClick={addGridRow}
                                 className="h-9 px-4 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all border border-slate-200 text-slate-600 hover:bg-slate-50 hover:border-slate-300"
                              >
                                 <PlusCircle size={14} className="text-emerald-500" />
                                 Add Record
                              </button>
                              <button 
                                 onClick={handleSave}
                                 disabled={saveStatus === 'saving'}
                                 className={`h-9 px-4 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all border ${
                                    saveStatus === 'saved' 
                                    ? 'bg-emerald-50 border-emerald-200 text-emerald-600' 
                                    : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50 hover:border-slate-300'
                                 }`}
                              >
                                 {saveStatus === 'saving' ? <RefreshCw size={14} className="animate-spin text-slate-400" /> : <Database size={14} />}
                                 {saveStatus === 'saving' ? 'Saving...' : saveStatus === 'saved' ? 'Saved' : 'Save Changes'}
                              </button>
                           </>
                        ) : (
                           <div className="flex items-center gap-1.5 p-1 bg-slate-100 rounded-lg border border-slate-200">
                              <button onClick={() => handleExport('pdf')} className="h-7 px-3 rounded-md text-[11px] font-bold flex items-center gap-2 transition-all bg-white text-slate-700 shadow-sm hover:text-rose-600 hover:shadow">
                                 <Activity size={12} className="text-rose-500" />
                                 Export PDF
                              </button>
                              <button onClick={() => handleExport('csv')} className="h-7 px-3 rounded-md text-[11px] font-bold flex items-center gap-2 transition-all bg-white text-slate-700 shadow-sm hover:text-emerald-600 hover:shadow">
                                 <Database size={12} className="text-emerald-500" />
                                 Export CSV
                              </button>
                              <button onClick={() => handleExport('html')} className="h-7 px-3 rounded-md text-[11px] font-bold flex items-center gap-2 transition-all bg-white text-slate-700 shadow-sm hover:text-blue-600 hover:shadow">
                                 <FileText size={12} className="text-blue-500" />
                                 Export HTML
                              </button>
                           </div>
                        )}
                     </div>
                  </div>



                  {/* Workspace Area: Grid or embedded HTML Report */}
                  <div className="flex-1 overflow-auto bg-[#e6e6e6] p-0 relative border-t border-slate-200 flex flex-col">
                     {isReportMode ? (
                        <iframe 
                           src={`/reports/${selectedReport}.html`} 
                           title={`${selectedReport} report preview`}
                           className="w-full flex-1 border-0 bg-white"
                        />
                     ) : (
                        <table className="min-w-full w-max text-left border-collapse bg-white cursor-cell">
                        <thead className="sticky top-0 z-20">
                           <tr className="bg-[#e6f2eb]">
                              {/* Top Left Corner */}
                              <th className="w-[38px] sticky left-0 z-30 border-r border-b border-[#c8cccf] bg-[#e6f2eb] p-0">
                                 <div className="absolute right-0 bottom-0 w-0 h-0 border-b-[8px] border-b-[#a3d0b2] border-l-[8px] border-l-transparent"></div>
                              </th>
                              {/* Action Column Header Spacer */}
                              <th className="w-[40px] sticky left-[38px] z-30 border-r border-b border-[#c8cccf] bg-[#e6f2eb] p-0"></th>
                              {gridColumns.map((col, idx) => (
                                 <th key={`${col}-${idx}`} className="min-w-[120px] border-r border-b border-[#c8cccf] bg-[#e6f2eb] text-center py-1 px-2 select-none group relative">
                                    <span className="text-[11px] font-medium text-[#107c41] block">{String.fromCharCode(65 + idx)}</span>
                                    {!isReportMode && (
                                       <button 
                                          onClick={() => deleteGridColumn(idx)}
                                          className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 p-0.5 rounded bg-rose-50 text-rose-500 hover:bg-rose-100 transition-all"
                                          title="Delete Column"
                                       >
                                          <Activity size={8} />
                                       </button>
                                    )}
                                 </th>
                              ))}
                           </tr>
                           <tr className="bg-white">
                              <th className="w-[38px] sticky left-0 z-30 border-r border-b border-[#c8cccf] bg-[#f3f2f1] text-center select-none py-1">
                                 <span className="text-[11px] font-medium text-[#605e5c] block">1</span>
                              </th>
                              {/* Row Actions Header */}
                              <th className="w-[40px] sticky left-[38px] z-30 border-r border-b border-[#c8cccf] bg-white text-center">
                                 {!isReportMode && (
                                    <button onClick={addGridRow} className="p-1 hover:bg-green-50 rounded-full text-green-600 transition-colors" title="Add Row">
                                       <PlusCircle size={14} />
                                    </button>
                                 )}
                              </th>
                              {gridColumns.map((col) => (
                                 <th key={`${col}-name`} className="border-r border-b border-[#c8cccf] px-2 py-1 bg-white whitespace-nowrap text-left font-bold text-slate-800 text-[11px]">
                                    {col}
                                 </th>
                              ))}
                           </tr>
                        </thead>
                        <tbody className="relative z-0">
                           {gridData.map((row, rowIndex) => (
                              <tr key={rowIndex} className="group">
                                 {/* Row Number */}
                                 <td className="w-[38px] sticky left-0 z-10 border-r border-b border-[#c8cccf] bg-[#f3f2f1] text-center select-none py-1">
                                    <span className="text-[11px] font-medium text-[#605e5c] block">{rowIndex + 2}</span>
                                 </td>
                                 {/* Row Actions (Modify indicator and Delete) */}
                                 <td className="w-[40px] sticky left-[38px] z-20 border-r border-b border-[#c8cccf] bg-white text-center flex items-center justify-center gap-1 py-1">
                                    {!isReportMode && (
                                       <button 
                                          onClick={() => deleteGridRow(rowIndex)} 
                                          className="p-1 hover:bg-rose-50 rounded-md text-rose-400 hover:text-rose-600 transition-colors" 
                                          title="Delete Row"
                                       >
                                          <Activity size={12} />
                                       </button>
                                    )}
                                 </td>
                                 {row.map((cell, colIndex) => (
                                    <td key={colIndex} className="p-0 border-r border-b border-[#c8cccf] bg-white focus-within:ring-2 focus-within:ring-green-500 focus-within:z-10 relative group/cell">
                                       <div className="relative w-full h-full flex items-center">
                                          <input 
                                             value={cell} 
                                             readOnly={isReportMode}
                                             onChange={(e) => updateGridCell(rowIndex, colIndex, e.target.value)}
                                             onDoubleClick={() => !isReportMode && setActiveCellEdit({ r: rowIndex, c: colIndex, val: cell })}
                                             className={`w-full h-full bg-transparent px-2 py-1.5 outline-none text-[11px] text-slate-800 font-medium text-ellipsis ${isReportMode ? 'cursor-default' : ''}`}
                                          />
                                          {!isReportMode && (
                                             <button
                                                onClick={() => setActiveCellEdit({ r: rowIndex, c: colIndex, val: cell })}
                                                className="absolute right-1 p-1 bg-white shadow-sm border border-slate-200 rounded opacity-0 group-hover/cell:opacity-100 hover:bg-slate-50 transition-opacity z-20"
                                                title="Expand Cell"
                                             >
                                                <Maximize2 size={10} className="text-slate-500" />
                                             </button>
                                          )}
                                       </div>
                                    </td>
                                 ))}
                              </tr>
                           ))}
                           {/* Empty Spacer Row for better UX */}
                           <tr className="h-20 bg-[#e6e6e6]/10">
                              <td colSpan={gridColumns.length + 2}></td>
                           </tr>
                        </tbody>
                     </table>
                     )}
                  </div>

                  {/* Footer */}
                  <div className="px-6 py-3 border-t border-slate-100 bg-slate-50/50 flex items-center justify-between">
                     <p className="text-[11px] text-slate-400">
                        {saveStatus === 'saved' ? (
                           <span className="text-emerald-600 font-bold flex items-center gap-1.5 animate-in fade-in zoom-in duration-300">
                              <CheckCircleIcon size={12} /> Modifications saved to Lakehouse catalog
                           </span>
                        ) : null}
                     </p>
                  </div>
               </div>

            ) : (isComplete && reportData) ? (
               <div className="flex-1 overflow-y-auto animate-in fade-in slide-in-from-bottom-2 duration-500">
                  {/* Report Header */}
                  <div className="px-6 py-2 border-b border-slate-100 flex items-center justify-between">
                     <div>
                        <h2 className="text-sm font-bold text-slate-800">Audit Results — {datasetLabel}</h2>
                        <p className="text-[11px] text-slate-400 mt-0.5">Reconciliation completed · {new Date().toLocaleDateString()}</p>
                     </div>
                     <button onClick={handleExport} className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50 hover:border-slate-300 transition-all">
                        <FileText size={13} /> Export Report
                     </button>
                  </div>

                  {/* KPI Strip */}
                  <div className="grid grid-cols-3 divide-x divide-slate-100 border-b border-slate-100">
                     <div className="px-8 py-5">
                        <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Accuracy Score</p>
                        <p className="text-2xl font-bold text-emerald-600">{reportData.accuracy}<span className="text-sm text-slate-400 font-normal">%</span></p>
                     </div>
                     <div className="px-8 py-5">
                        <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Records Matched</p>
                        <p className="text-2xl font-bold text-slate-800">{reportData.matches.toLocaleString()}</p>
                     </div>
                     <div className="px-8 py-5">
                        <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Variances Found</p>
                        <p className={`text-2xl font-bold ${reportData.mismatches > 0 ? 'text-rose-500' : 'text-slate-400'}`}>{reportData.mismatches}</p>
                     </div>
                  </div>

                  {/* Variance Table */}
                  <div className="px-8 py-6">
                     <div className="border border-slate-100 rounded-xl overflow-hidden">
                        <div className="px-5 py-3.5 bg-slate-50/80 border-b border-slate-100 flex items-center justify-between">
                           <h3 className="text-xs font-bold text-slate-600">Variance Log</h3>
                           <span className="text-[10px] text-slate-400">{reportData.mismatchDetails.length} discrepancies</span>
                        </div>
                        <table className="w-full text-left">
                           <thead>
                              <tr className="border-b border-slate-100">
                                 {['Record ID', 'Field', 'Source (Bronze)', 'Target (Silver)', 'Severity'].map(col => (
                                    <th key={col} className="px-5 py-3 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">{col}</th>
                                 ))}
                              </tr>
                           </thead>
                           <tbody className="divide-y divide-slate-50">
                              {reportData.mismatchDetails.map((m, i) => (
                                 <tr key={i} className="hover:bg-slate-50/50 transition-colors">
                                    <td className="px-5 py-3.5 font-mono text-xs font-semibold text-slate-700">{m.id}</td>
                                    <td className="px-5 py-3.5 text-xs text-slate-500 uppercase tracking-tight font-medium">{m.field}</td>
                                    <td className="px-5 py-3.5 text-xs font-semibold text-emerald-600">{m.source}</td>
                                    <td className="px-5 py-3.5 text-xs font-semibold text-rose-500">{m.target}</td>
                                    <td className="px-5 py-3.5">
                                       <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold border ${
                                          m.risk === 'Critical' ? 'bg-rose-50 text-rose-600 border-rose-100' :
                                          m.risk === 'High' ? 'bg-orange-50 text-orange-600 border-orange-100' :
                                          'bg-blue-50 text-blue-600 border-blue-100'
                                       }`}>{m.risk}</span>
                                    </td>
                                 </tr>
                              ))}
                           </tbody>
                        </table>
                     </div>
                  </div>
               </div>

            ) : (isRunning || showLogs) ? (
               <div className="flex-1 opacity-95">
                  <Terminal logs={logs} minHeight="100%" />
               </div>

            ) : (
               <div className="flex-1 flex flex-col items-center justify-center text-center p-16">
                  <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center mb-6">
                     <Cpu size={28} className="text-slate-300" />
                  </div>
                  <h3 className="text-sm font-bold text-slate-700 mb-2">Ready to Audit</h3>
                  <p className="text-xs text-slate-400 max-w-xs leading-relaxed mb-6">Select a data layer from the <span className="font-semibold text-slate-500">sidebar configuration</span>, then click <span className="font-semibold text-slate-500">Run</span> to begin reconciliation.</p>
                  <button onClick={toggleExecution} className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold transition-all active:scale-95">
                     <Zap size={13} /> Run
                  </button>
               </div>
            )}
         </div>

         {/* Expanding Cell Edit Modal */}
         {activeCellEdit && (
            <div className="fixed inset-0 z-[100] flex animate-in fade-in duration-200">
               <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" onClick={() => setActiveCellEdit(null)} />
               <div className="relative m-auto w-full max-w-2xl bg-white rounded-xl shadow-2xl flex flex-col animate-in zoom-in-95 duration-200">
                  <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50 rounded-t-xl">
                     <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                        <Maximize2 size={16} className="text-blue-600" />
                        Edit Cell Content
                     </h3>
                     <button 
                        onClick={() => setActiveCellEdit(null)}
                        className="p-1.5 rounded-lg hover:bg-slate-200 text-slate-400 transition-colors"
                     >
                        <X size={16} />
                     </button>
                  </div>
                  <div className="p-6">
                     <textarea
                        value={activeCellEdit.val}
                        autoFocus
                        onChange={(e) => setActiveCellEdit({ ...activeCellEdit, val: e.target.value })}
                        className="w-full h-64 p-4 text-sm font-mono leading-relaxed text-slate-700 bg-slate-50 border border-slate-200 rounded-lg outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all resize-none"
                        placeholder="Enter large payload or complex query..."
                     />
                  </div>
                  <div className="px-6 py-4 border-t border-slate-100 bg-slate-50/50 rounded-b-xl flex items-center justify-end gap-3">
                     <button 
                        onClick={() => setActiveCellEdit(null)}
                        className="px-4 py-2 rounded-lg text-xs font-bold text-slate-600 hover:bg-slate-200 transition-colors"
                     >
                        Cancel
                     </button>
                     <button 
                        onClick={() => {
                           updateGridCell(activeCellEdit.r, activeCellEdit.c, activeCellEdit.val)
                           setActiveCellEdit(null)
                        }}
                        className="px-6 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-md shadow-blue-600/20 transition-all active:scale-95"
                     >
                        Save Content
                     </button>
                  </div>
               </div>
            </div>
         )}
      </div>
   )
}


