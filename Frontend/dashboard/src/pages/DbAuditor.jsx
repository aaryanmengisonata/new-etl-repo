import React, { useState, useEffect, useRef } from 'react'
import { useAppContext } from '../store/AppContext'
import {
   Play, Settings, Send,
   FileText, ChevronRight, ChevronDown,
   Sparkles, Cpu,
   CloudUpload, ArrowRight, Zap,
   Database, RefreshCw, Activity, Layers,
   Terminal as TerminalIcon, PlusCircle,
   X, CheckCircle, AlertTriangle, PlayCircle,
   Upload, Image, Trash2, Edit3, Check,
   Undo2, Download
} from 'lucide-react'
import Terminal from '../components/shared/Terminal'
import { api } from '../services/api'

export default function DbAuditor() {
   const {
      featureState, setFeatureState, showAlert, setActivePage, setNavParams
   } = useAppContext()

   // Connection and Tables State
   const [dbConfig, setDbConfig] = useState(null)
   const [tables, setTables] = useState([])
   const [selectedTable, setSelectedTable] = useState(null)
   const [loadingTables, setLoadingTables] = useState(false)
   
   // Recommendations & Assertion Planning State
   const [validationsList, setValidationsList] = useState([]) // customized validations
   const [loadingRecommendations, setLoadingRecommendations] = useState(false)
   const [analysisLogs, setAnalysisLogs] = useState([])
   
   // UI Toggles & File Upload State
   const [explorerTab, setExplorerTab] = useState('explorer')
   const [selectedFile, setSelectedFile] = useState(null)
   const [dragActive, setDragActive] = useState(false)
   const [uploadingDiagram, setUploadingDiagram] = useState(false)
   const [expandedSqlIndex, setExpandedSqlIndex] = useState(null)
   
   // Execution State
   const [isRunning, setIsRunning] = useState(false)
   const [isComplete, setIsComplete] = useState(false)
   const [logs, setLogs] = useState([])
   const [batchResult, setBatchResult] = useState(null)

   // Local Report States
   const [viewingReport, setViewingReport] = useState(false)
   const [exportDropdownOpen, setExportDropdownOpen] = useState(false)

   // Predefined assertion creator states
   const [showPredefinedForm, setShowPredefinedForm] = useState(false)
   const [predefinedCol, setPredefinedCol] = useState('')
   const [predefinedType, setPredefinedType] = useState('null_check')

   // Reset report view when featureState changes
   useEffect(() => {
      setViewingReport(false)
      setExportDropdownOpen(false)
      setShowPredefinedForm(false)
      if (featureState === 'query') {
         setIsComplete(false)
         setBatchResult(null)
         setIsRunning(false)
         setLogs([])
      }
   }, [featureState])

   // Load DB Config and Tables on mount
   useEffect(() => {
      loadDbInfo()
   }, [])

   const loadDbInfo = async () => {
      setLoadingTables(true)
      try {
         const cfg = await api.getDbConfig()
         setDbConfig(cfg)
         
         const res = await api.getDbTables()
         if (res.status === 'success') {
            setTables(res.tables || [])
            if (res.tables && res.tables.length > 0) {
               handleSelectTable(res.tables[0])
            }
         }
      } catch (err) {
         console.error("Failed to load DB info:", err)
      } finally {
         setLoadingTables(false)
      }
   }

   const handleSelectTable = (table) => {
      setSelectedTable(table)
      setValidationsList([])
      setAnalysisLogs([])
      setIsRunning(false)
      setIsComplete(false)
      setBatchResult(null)
      setLogs([])
   }

   const handleGetSuggestions = async () => {
      if (!selectedTable) return
      setLoadingRecommendations(true)
      setAnalysisLogs(["[AI] Initializing database schema parser..."])
      
      try {
         const res = await api.analyzeSchemaDetails(selectedTable.name, selectedTable.columns)
         
         let i = 0
         const logsInterval = setInterval(() => {
            if (i < res.analysis_logs.length) {
               setAnalysisLogs(prev => [...prev, `[AI] ${res.analysis_logs[i]}`])
               i++
            } else {
               clearInterval(logsInterval)
               // Map recommended tests to customized validations
               const mapped = res.recommended_tests.map(test => ({
                  id: test.test_id,
                  type: test.type,
                  description: test.description,
                  query: test.sql,
                  expected_condition: test.expected_condition,
                  expected_value: test.expected_value,
                  enabled: true
               }))
               setValidationsList(mapped)
               setLoadingRecommendations(false)
            }
         }, 300)
      } catch (err) {
         setAnalysisLogs(prev => [...prev, `[ERROR] Analysis failed: ${err.message}`])
         setLoadingRecommendations(false)
         showAlert("Analysis Failed", "Failed to retrieve predefined validations.", "error")
      }
   }

   // Drag and Drop handlers
   const handleDrag = (e) => {
      e.preventDefault()
      e.stopPropagation()
      if (e.type === "dragenter" || e.type === "dragover") {
         setDragActive(true)
      } else if (e.type === "dragleave") {
         setDragActive(false)
      }
   }

   const handleDrop = (e) => {
      e.preventDefault()
      e.stopPropagation()
      setDragActive(false)
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
         const file = e.dataTransfer.files[0]
         if (file.type.startsWith('image/')) {
            setSelectedFile(file)
         } else {
            showAlert("Invalid File", "Please upload an image file (PNG, JPG, JPEG).", "error")
         }
      }
   }

   const handleFileChange = (e) => {
      if (e.target.files && e.target.files[0]) {
         setSelectedFile(e.target.files[0])
      }
   }

   const handleUploadDiagram = async (fileToUpload) => {
      if (!fileToUpload) return
      setUploadingDiagram(true)
      setLoadingRecommendations(true)
      setAnalysisLogs(["[AI] Initializing image-based database schema parser..."])
      
      const formData = new FormData()
      formData.append('file', fileToUpload)
      
      try {
         const res = await api.analyzeSchemaImage(formData)
         
         let i = 0
         const logsInterval = setInterval(() => {
            if (i < res.analysis_logs.length) {
               setAnalysisLogs(prev => [...prev, `[AI] ${res.analysis_logs[i]}`])
               i++
            } else {
               clearInterval(logsInterval)
               const mapped = res.recommended_tests.map(test => ({
                  id: test.test_id,
                  type: test.type,
                  description: test.description,
                  query: test.sql,
                  expected_condition: test.expected_condition,
                  expected_value: test.expected_value,
                  enabled: true
               }))
               setValidationsList(mapped)
               setLoadingRecommendations(false)
               setUploadingDiagram(false)
               showAlert("Success", "AI has successfully parsed your schema diagram and generated validations!", "success")
            }
         }, 300)
      } catch (err) {
         setAnalysisLogs(prev => [...prev, `[ERROR] Image analysis failed: ${err.message}`])
         setLoadingRecommendations(false)
         setUploadingDiagram(false)
         showAlert("Analysis Failed", "Failed to analyze database diagram.", "error")
      }
   }

   const handleToggleValidation = (idx) => {
      setValidationsList(prev => prev.map((v, i) => i === idx ? { ...v, enabled: !v.enabled } : v))
   }

   const handleUpdateValidation = (idx, field, value) => {
      setValidationsList(prev => prev.map((v, i) => i === idx ? { ...v, [field]: value } : v))
   }

   const handleAddCustomValidation = () => {
      const newCustom = {
         id: `DB_CUSTOM_${Date.now().toString().slice(-4)}`,
         type: "Custom SQL Assertion",
         description: "User-defined custom database validation check.",
         query: `SELECT COUNT(*) FROM ${selectedTable?.name || 'table_name'};`,
         expected_condition: "EQUAL",
         expected_value: 0,
         enabled: true
      }
      setValidationsList(prev => [...prev, newCustom])
   }

   const isNumeric = (type) => {
      if (!type) return false
      const t = type.toLowerCase()
      return t.includes('int') || t.includes('num') || t.includes('real') || t.includes('double') || t.includes('float')
   }

   const handleAddManualValidation = (colName, colType, checkType) => {
      if (!selectedTable) return

      let newCheck = null
      const idSuffix = Date.now().toString().slice(-4)
      
      if (checkType === 'null_check') {
         newCheck = {
            id: `DB_NULL_MANUAL_${idSuffix}`,
            type: "Null Value Check",
            description: `Check if '${selectedTable.name}.${colName}' contains any null or empty values.`,
            query: `SELECT COUNT(*) FROM ${selectedTable.name} WHERE ${colName} IS NULL OR ${colName} = '';`,
            expected_condition: "EQUAL",
            expected_value: 0,
            enabled: true
         }
      } else if (checkType === 'unique_check') {
         newCheck = {
            id: `DB_PK_MANUAL_${idSuffix}`,
            type: "Primary Key Check",
            description: `Assert that '${selectedTable.name}.${colName}' is unique and contains no duplicates.`,
            query: `SELECT ${colName}, COUNT(*) FROM ${selectedTable.name} GROUP BY ${colName} HAVING COUNT(*) > 1;`,
            expected_condition: "EQUAL",
            expected_value: 0,
            enabled: true
         }
      } else if (checkType === 'positive_check') {
         newCheck = {
            id: `DB_QUAL_MANUAL_${idSuffix}`,
            type: "Data Quality Check",
            description: `Verify '${selectedTable.name}.${colName}' conforms to positive value constraints.`,
            query: `SELECT COUNT(*) FROM ${selectedTable.name} WHERE ${colName} < 0;`,
            expected_condition: "EQUAL",
            expected_value: 0,
            enabled: true
         }
      }
      
      if (newCheck) {
         setValidationsList(prev => [...prev, newCheck])
         showAlert("Assertion Added", `Manually added ${newCheck.type} for column '${colName}'.`, "success")
      }
   }

   const handleCreatePredefinedCheck = () => {
      if (!selectedTable || !predefinedCol) return
      
      const col = selectedTable.columns.find(c => c.name === predefinedCol)
      const colType = col ? col.type : 'TEXT'
      
      handleAddManualValidation(predefinedCol, colType, predefinedType)
      setShowPredefinedForm(false)
      setPredefinedCol('')
   }

   const handleRemoveValidation = (idx) => {
      setValidationsList(prev => prev.filter((_, i) => i !== idx))
   }

   const handleRunBatchValidations = async () => {
      const activeValidations = validationsList.filter(v => v.enabled)
      if (activeValidations.length === 0) {
         showAlert("No Validations", "Please configure and enable at least one validation check.", "info")
         return
      }

      setIsRunning(true)
      setIsComplete(false)
      setLogs([
         "[SYSTEM] Booting Batch Validation Engine...",
         `[INFO] Target Connection: ${dbConfig?.engine?.toUpperCase()} (${dbConfig?.db_name})`,
         `[PROCESS] Loading ${activeValidations.length} validation checks...`,
      ])

      try {
         const payload = activeValidations.map(v => ({
            query: v.query,
            validation_type: v.type.toLowerCase().includes("primary") ? "primary_key" : 
                             v.type.toLowerCase().includes("null") ? "null_check" : "raw",
            expected_condition: v.expected_condition,
            expected_value: Number(v.expected_value)
         }))

         const res = await api.executeBatchDbValidations(payload)
         
         setTimeout(() => {
            setLogs(prev => [
               ...prev,
               ...res.details.execution_logs,
               "[SYSTEM] Batch verification successfully finalized."
            ])
            setBatchResult(res)
            setIsRunning(false)
            setIsComplete(true)
         }, 1000)

      } catch (err) {
         console.error("Batch validation failed:", err)
         setLogs(prev => [...prev, `[ERROR] Batch run encountered exception: ${err.message}`])
         setIsRunning(false)
      }
   }

   const handleExportPDF = () => {
      if (!batchResult) return
      const passedCount = batchResult.details.results.filter(r => r.passed).length
      const failedCount = batchResult.details.results.filter(r => !r.passed).length
      const status = batchResult.passed ? 'PASSED' : 'FAILED'
      const statusClass = batchResult.passed ? 'passed' : 'failed'
      
      const resultsRows = batchResult.details.results.map((r, idx) => `
         <tr>
            <td style="font-weight:bold; font-family:monospace;">Check #${idx + 1}</td>
            <td><pre style="margin:0; background:#f8fafc; padding:6px; border-radius:4px; font-size:11px; white-space:pre-wrap;">${r.query}</pre></td>
            <td><span class="badge ${r.passed ? 'passed' : 'failed'}">${r.passed ? 'PASS' : 'FAIL'}</span></td>
            <td style="text-align:right;">${r.rows_returned || 0}</td>
            <td>${r.error ? `<span style="color:#e11d48; font-size:11px;">${r.error}</span>` : '<span style="color:#64748b;">-</span>'}</td>
         </tr>
      `).join('')

      const printContent = `
         <html>
         <head>
            <title>Database Validation Report</title>
            <style>
               body { font-family: system-ui, -apple-system, sans-serif; padding: 40px; color: #1e293b; line-height: 1.5; }
               .header { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #e2e8f0; padding-bottom: 20px; margin-bottom: 30px; }
               h1 { font-size: 24px; margin: 0 0 6px 0; color: #0f172a; font-weight: 900; letter-spacing: -0.02em; }
               .subtitle { font-size: 13px; color: #64748b; font-weight: 600; text-transform: uppercase; margin: 0; }
               .badge { display: inline-block; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; }
               .passed { background: #d1fae5; color: #065f46; border: 1px solid #a7f3d0; }
               .failed { background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }
               .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 35px; }
               .kpi-card { background: #f8fafc; border: 1px solid #e2e8f0; padding: 16px; border-radius: 12px; }
               .kpi-label { font-size: 10px; font-weight: 800; text-transform: uppercase; color: #94a3b8; margin: 0 0 6px 0; letter-spacing: 0.05em; }
               .kpi-value { font-size: 20px; font-weight: 800; color: #1e293b; margin: 0; }
               table { width: 100%; border-collapse: collapse; margin-top: 10px; }
               th { text-align: left; padding: 12px; border-bottom: 2px solid #e2e8f0; font-size: 11px; font-weight: 800; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }
               td { padding: 12px; border-bottom: 1px solid #e2e8f0; font-size: 12px; color: #334155; }
               pre { background: #0f172a; color: #f8fafc; padding: 16px; border-radius: 10px; font-family: monospace; font-size: 11px; overflow: auto; max-height: 250px; line-height: 1.6; }
               .section-title { font-size: 14px; font-weight: 800; text-transform: uppercase; color: #475569; margin: 30px 0 15px 0; border-bottom: 1px dashed #e2e8f0; padding-bottom: 8px; letter-spacing: 0.05em; }
               .footer { margin-top: 50px; border-top: 1px solid #e2e8f0; padding-top: 15px; text-align: center; font-size: 11px; color: #94a3b8; font-weight: 600; }
            </style>
         </head>
         <body>
            <div class="header">
               <div>
                  <h1 class="subtitle">IntellQA Database Audit</h1>
                  <h1>Quality Audit Validation Report</h1>
                  <p style="margin: 4px 0 0 0; font-size: 12px; color: #94a3b8;">Generated on ${new Date().toLocaleString()}</p>
               </div>
               <div>
                  <span class="badge ${statusClass}">${status}</span>
               </div>
            </div>

            <div class="kpi-grid">
               <div class="kpi-card">
                  <div class="kpi-label">Total Validations</div>
                  <div class="kpi-value">${batchResult.details.total_validations}</div>
               </div>
               <div class="kpi-card" style="border-color: #a7f3d0;">
                  <div class="kpi-label" style="color: #059669;">Passed Checks</div>
                  <div class="kpi-value" style="color: #059669;">${passedCount}</div>
               </div>
               <div class="kpi-card" style="border-color: #fca5a5;">
                  <div class="kpi-label" style="color: #e11d48;">Failed Checks</div>
                  <div class="kpi-value" style="color: #e11d48;">${failedCount}</div>
               </div>
               <div class="kpi-card">
                  <div class="kpi-label">Target DB Connection</div>
                  <div class="kpi-value" style="font-size: 14px; font-family: monospace; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; padding-top: 4px;">
                     ${dbConfig?.db_name || 'etl_test.db'}
                  </div>
               </div>
            </div>

            <div class="section-title">Assertion Verification Spectrum</div>
            <table>
               <thead>
                  <tr>
                     <th style="width: 12%;">Check</th>
                     <th style="width: 50%;">SQL Query</th>
                     <th style="width: 10%;">Result</th>
                     <th style="width: 13%; text-align: right;">Rows Returned</th>
                     <th style="width: 15%;">Error</th>
                  </tr>
               </thead>
               <tbody>
                  ${resultsRows}
               </tbody>
            </table>

            ${batchResult.details.execution_logs && batchResult.details.execution_logs.length > 0 ? `
               <div class="section-title">Execution Console Trace</div>
               <pre>${batchResult.details.execution_logs.join('\n')}</pre>
            ` : ''}

            <div class="footer">
               Powered by Sonata Software Limited. All Rights Reserved.
            </div>
         </body>
         </html>
      `
      
      const win = window.open('', '_blank')
      win.document.write(printContent)
      win.document.close()
      setTimeout(() => { win.print() }, 500)
   }

   const handleExportCSV = () => {
      if (!batchResult) return
      const headers = ['Assertion Check', 'SQL Query', 'Status', 'Rows Returned', 'Error Message']
      const rows = batchResult.details.results.map((r, idx) => [
         `Check #${idx + 1}`,
         `"${r.query.replace(/"/g, '""')}"`,
         r.passed ? 'PASS' : 'FAIL',
         r.rows_returned || 0,
         r.error ? `"${r.error.replace(/"/g, '""')}"` : ''
      ])
      
      const csvContent = [headers.join(','), ...rows.map(row => row.join(','))].join('\n')
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `db_audit_report_${Date.now()}.csv`
      a.click()
      URL.revokeObjectURL(url)
   }

   const handleExportJSON = () => {
      if (!batchResult) return
      const jsonContent = JSON.stringify(batchResult, null, 2)
      const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8;' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `db_audit_report_${Date.now()}.json`
      a.click()
      URL.revokeObjectURL(url)
   }

   // Render steps based on featureState
   const currentMode = (!featureState || featureState === 'intro') ? 'intro' : featureState

   if (currentMode === 'intro') {
      return (
         <div className="w-full flex flex-col p-8 lg:p-12 animate-in fade-in duration-700 bg-slate-50/30 text-left">
            <div className="max-w-5xl mx-auto w-full pt-4">
               <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                  <div className="md:col-span-2 p-10 rounded-[2rem] bg-white border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
                     <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center mb-6">
                        <Database size={20} className="text-blue-600" />
                     </div>
                     <h2 className="text-xl font-black text-slate-800 mb-4 tracking-tight">Database Testing Wizard</h2>
                     <p className="text-sm font-medium text-slate-500 leading-relaxed max-w-xl">
                        Verify database schemas, retrieve automated recommendations based on table structures, customize constraints, and execute batch assertions against your live SQLite or PostgreSQL connections.
                     </p>
                  </div>

                  <div className="p-8 rounded-[2rem] bg-slate-900 text-white shadow-xl shadow-slate-900/10 flex flex-col justify-between relative overflow-hidden">
                     <div className="absolute top-0 right-0 w-32 h-32 bg-slate-800 rounded-full blur-3xl" />
                     <div className="relative z-10">
                        <Sparkles className="text-indigo-400 mb-6" size={24} />
                        <h3 className="text-sm font-black mb-2 tracking-wide">Interactive DB testing</h3>
                        <p className="text-[10px] font-medium text-slate-400 leading-relaxed">
                           Connect to a generic SQL database, scan tables, fetch schema details, and execute assertions dynamically.
                        </p>
                     </div>
                     <div className="relative z-10 mt-8">
                        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500 mb-1">Configuration Status</p>
                        <p className="text-xs font-bold text-slate-300">
                           {dbConfig ? `${dbConfig.engine.toUpperCase()} / ${dbConfig.db_name}` : 'Not Loaded'}
                        </p>
                     </div>
                  </div>
               </div>

               <div className="flex flex-col items-center justify-center p-12 text-center rounded-[2rem] border border-dashed border-slate-300/60 bg-white/50">
                  <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4">
                     <ChevronRight className="text-slate-400 rotate-90" size={20} />
                  </div>
                  <h3 className="text-lg font-black text-slate-800 mb-2 tracking-tight">Ready to audit your database?</h3>
                  <p className="text-xs font-bold text-slate-400 max-w-sm mx-auto leading-relaxed mb-6">
                     Access settings to configure SQL server credentials, or jump right into scanning database tables.
                  </p>
                  <div className="flex items-center gap-4">
                     <button
                        onClick={() => {
                           setNavParams({ defaultTab: 'database', returnPage: 'db_auditor', returnMode: 'intro' })
                           setActivePage('configuration')
                        }}
                        className="px-8 py-3 rounded-xl border border-slate-200 text-slate-600 bg-white text-[10px] font-black uppercase tracking-widest hover:bg-slate-50 transition-colors shadow-sm"
                     >
                        Configure Connection
                     </button>
                     <button
                        onClick={() => setFeatureState('query')}
                        className="px-8 py-3 rounded-xl bg-blue-600 text-white text-[10px] font-black uppercase tracking-widest hover:bg-blue-700 transition-colors shadow-lg shadow-blue-500/20 active:scale-95"
                     >
                        Connect & Test Tables
                     </button>
                  </div>
               </div>
            </div>
         </div>
      )
   }

   // Query / Workspace Mode
   if (currentMode === 'query') {
      return (
         <div className="w-full h-full flex flex-col bg-gradient-to-br from-slate-50 to-slate-100 animate-in fade-in duration-700 text-left">
            <div className="flex-1 flex gap-8 p-8 overflow-hidden">
               {/* Left Panel: Explorer / Uploader */}
               <div className="w-1/3 h-full flex flex-col bg-white p-6 rounded-[2rem] border border-slate-200 shadow-sm overflow-hidden">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-4">
                     <div className="flex items-center gap-3">
                        <Database size={16} className="text-blue-600" />
                        <h3 className="text-xs font-black uppercase tracking-wider text-slate-900">Database Schema</h3>
                     </div>
                     <button 
                        onClick={loadDbInfo}
                        className="p-1.5 hover:bg-slate-100 rounded-lg text-slate-500 transition-colors"
                        title="Reload Database Schema"
                     >
                        <RefreshCw size={14} className={loadingTables ? 'animate-spin' : ''} />
                     </button>
                  </div>

                  {/* Segmented Tab Switcher */}
                  <div className="flex bg-slate-100 p-1 rounded-xl mb-6">
                     <button
                        onClick={() => setExplorerTab('explorer')}
                        className={`flex-1 py-2 text-[10px] font-black uppercase tracking-wider rounded-lg transition-all ${
                           explorerTab === 'explorer' 
                              ? 'bg-white text-slate-900 shadow-sm' 
                              : 'text-slate-400 hover:text-slate-600'
                        }`}
                     >
                        Table Explorer
                     </button>
                     <button
                        onClick={() => setExplorerTab('upload')}
                        className={`flex-1 py-2 text-[10px] font-black uppercase tracking-wider rounded-lg transition-all ${
                           explorerTab === 'upload' 
                              ? 'bg-white text-slate-900 shadow-sm' 
                              : 'text-slate-400 hover:text-slate-600'
                        }`}
                     >
                        AI Diagram Upload
                     </button>
                  </div>

                  {explorerTab === 'explorer' ? (
                     loadingTables ? (
                        <div className="flex-1 flex items-center justify-center p-12 text-xs font-bold text-slate-400 animate-pulse uppercase tracking-wider">
                           Scanning database...
                        </div>
                     ) : tables.length === 0 ? (
                        <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
                           <AlertTriangle className="text-amber-500 mb-4" size={24} />
                           <p className="text-xs font-bold text-slate-600 mb-4 leading-relaxed">No tables found or failed to connect.</p>
                           <button
                              onClick={() => {
                                 setNavParams({ defaultTab: 'database', returnPage: 'db_auditor', returnMode: 'query' })
                                 setActivePage('configuration')
                              }}
                              className="px-4 py-2 bg-slate-900 text-white rounded-lg text-[10px] font-black uppercase tracking-widest hover:bg-slate-800 transition-colors"
                           >
                              Edit Settings
                           </button>
                        </div>
                     ) : (
                        <div className="flex-1 flex flex-col min-h-0 overflow-y-auto space-y-4 pr-1">
                           <div className="space-y-1">
                              <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Select Target Table</label>
                              <div className="relative group">
                                 <select 
                                    value={selectedTable?.name || ''} 
                                    onChange={(e) => {
                                       const tbl = tables.find(t => t.name === e.target.value)
                                       if (tbl) handleSelectTable(tbl)
                                    }}
                                    className="w-full appearance-none border border-slate-200 rounded-xl px-4 py-3 text-xs font-bold text-slate-800 focus:bg-white outline-none cursor-pointer"
                                 >
                                    {tables.map(t => (
                                       <option key={t.name} value={t.name}>{t.name}</option>
                                    ))}
                                 </select>
                                 <ChevronRight className="absolute right-4 top-1/2 -translate-y-1/2 opacity-30 rotate-90 pointer-events-none" size={14} />
                              </div>
                           </div>

                           {selectedTable && (
                              <div className="flex-1 flex flex-col min-h-0">
                                 <div className="flex items-center justify-between mb-2">
                                    <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Columns & Types</label>
                                    <span className="text-[8px] font-black text-indigo-500 uppercase tracking-wider">Hover to add checks</span>
                                 </div>
                                 <div className="flex-1 overflow-y-auto border border-slate-100 rounded-xl divide-y divide-slate-50 bg-slate-50/50 p-1.5 space-y-1">
                                    {selectedTable.columns.map(col => (
                                       <div key={col.name} className="flex items-center justify-between py-2 px-2.5 text-xs rounded-xl hover:bg-white hover:shadow-sm border border-transparent hover:border-slate-100 transition-all duration-200 group">
                                          <div className="flex flex-col min-w-0 flex-1">
                                             <span className="font-bold text-slate-800 truncate">{col.name}</span>
                                             <span className="text-[9px] font-mono text-slate-400">{col.type}</span>
                                          </div>
                                          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200 shrink-0 ml-2">
                                             <button
                                                onClick={() => handleAddManualValidation(col.name, col.type, 'null_check')}
                                                className="px-1.5 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-600 rounded text-[9px] font-black uppercase tracking-wider transition-all"
                                                title="Add Null Check"
                                             >
                                                + Null
                                             </button>
                                             <button
                                                onClick={() => handleAddManualValidation(col.name, col.type, 'unique_check')}
                                                className="px-1.5 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-600 rounded text-[9px] font-black uppercase tracking-wider transition-all"
                                                title="Add Unique Check"
                                             >
                                                + Unique
                                             </button>
                                             {isNumeric(col.type) && (
                                                <button
                                                   onClick={() => handleAddManualValidation(col.name, col.type, 'positive_check')}
                                                   className="px-1.5 py-1 bg-amber-50 hover:bg-amber-100 text-amber-600 rounded text-[9px] font-black uppercase tracking-wider transition-all"
                                                   title="Add Positive Check"
                                                >
                                                   + Pos
                                                </button>
                                             )}
                                          </div>
                                       </div>
                                    ))}
                                 </div>
                              </div>
                           )}
                        </div>
                     )
                  ) : (
                     /* AI Schema Diagram Upload */
                     <div className="flex-1 flex flex-col min-h-0">
                        {!selectedFile ? (
                           <div className="flex-1 flex flex-col min-h-0 overflow-y-auto pr-1">
                              <div 
                                 onDragEnter={handleDrag}
                                 onDragOver={handleDrag}
                                 onDragLeave={handleDrag}
                                 onDrop={handleDrop}
                                 className={`flex-1 border-2 border-dashed rounded-2xl flex flex-col items-center justify-center p-6 text-center transition-all duration-300 ${
                                    dragActive 
                                       ? 'border-blue-500 bg-blue-50/50 scale-[0.98]' 
                                       : 'border-slate-200 hover:border-slate-300 bg-slate-50/10'
                                 }`}
                              >
                                 <input 
                                    type="file" 
                                    accept="image/*" 
                                    className="hidden" 
                                    id="diagram-file"
                                    onChange={handleFileChange}
                                 />
                                 <div className="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center text-blue-600 mb-4 shadow-sm">
                                    <Upload size={18} />
                                 </div>
                                 <p className="text-xs font-bold text-slate-700 mb-1">Drag and drop diagram</p>
                                 <p className="text-[10px] font-semibold text-slate-400 mb-5">PNG, JPG, JPEG up to 10MB</p>
                                 <label 
                                    htmlFor="diagram-file"
                                    className="px-4 py-2 rounded-lg bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 shadow-sm text-[10px] font-black uppercase tracking-wider cursor-pointer transition-all active:scale-95"
                                 >
                                    Browse Files
                                 </label>
                              </div>
                           </div>
                        ) : (
                           <div className="flex-1 flex flex-col justify-between min-h-0">
                              <div className="flex-1 overflow-y-auto space-y-4 pr-1">
                                 <div className="flex flex-col gap-4 border border-slate-100 bg-slate-50/30 p-4 rounded-2xl">
                                    <div className="flex items-center gap-3 p-3 bg-white border border-slate-100 rounded-xl shadow-sm">
                                       <div className="w-9 h-9 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0">
                                          <Image size={16} />
                                       </div>
                                       <div className="flex-1 min-w-0">
                                          <p className="text-xs font-black text-slate-800 truncate">{selectedFile.name}</p>
                                          <p className="text-[9px] font-bold text-slate-400">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                                       </div>
                                       <button 
                                          onClick={() => setSelectedFile(null)}
                                          className="p-1.5 hover:bg-rose-50 text-slate-400 hover:text-rose-600 rounded-lg transition-all"
                                       >
                                          <Trash2 size={13} />
                                       </button>
                                    </div>
                                    <p className="text-[10px] font-bold text-slate-400 leading-relaxed tracking-tight">
                                       AI diagram analyzer will parse this layout to automatically detect tables, primary/foreign keys, categories and recommend assertions.
                                    </p>
                                 </div>
                              </div>
                              
                              <div className="pt-4 border-t border-slate-100">
                                 <button
                                    onClick={() => handleUploadDiagram(selectedFile)}
                                    disabled={uploadingDiagram}
                                    className="w-full py-3 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:bg-slate-200 text-white text-[10px] font-black uppercase tracking-widest transition-all shadow-lg shadow-blue-500/10 flex items-center justify-center gap-2 active:scale-[0.98]"
                                 >
                                    {uploadingDiagram ? (
                                       <>
                                          <RefreshCw size={12} className="animate-spin" />
                                          Analyzing Diagram...
                                       </>
                                    ) : (
                                       <>
                                          <Sparkles size={12} fill="white" />
                                          Analyze Diagram
                                       </>
                                    )}
                                 </button>
                              </div>
                           </div>
                        )}
                     </div>
                  )}
               </div>

               {/* Right Panel: Assertions & Customizations */}
               <div className="w-2/3 h-full flex flex-col bg-white p-8 rounded-[2rem] border border-slate-200 shadow-sm overflow-hidden justify-between">
                  <div className="flex-1 flex flex-col min-h-0">
                     <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-6">
                        <div className="flex items-center gap-3">
                           <Sparkles size={16} className="text-indigo-600" />
                           <h3 className="text-xs font-black uppercase tracking-wider text-slate-900">Validation Planner</h3>
                           {validationsList.length > 0 && (
                              <span className="text-[9px] font-black px-2 py-0.5 rounded bg-blue-50 border border-blue-100 text-blue-600 uppercase tracking-wider">
                                 {validationsList.filter(v => v.enabled).length} Active
                              </span>
                           )}
                        </div>

                        {((selectedTable && explorerTab === 'explorer') || (selectedFile && explorerTab === 'upload')) && validationsList.length === 0 && (
                           <button
                              onClick={explorerTab === 'explorer' ? handleGetSuggestions : () => handleUploadDiagram(selectedFile)}
                              disabled={loadingRecommendations || uploadingDiagram}
                              className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-[9px] font-black uppercase tracking-widest transition-colors flex items-center gap-1.5 active:scale-95"
                           >
                              <Sparkles size={11} fill="white" />
                              Suggest Validations
                           </button>
                        )}
                     </div>

                     {loadingRecommendations || analysisLogs.length > 0 && validationsList.length === 0 ? (
                        <div className="flex-1 flex flex-col gap-4 min-h-0">
                           <h4 className="text-[10px] font-black uppercase tracking-wider text-slate-400">AI Schema Analyzer Logs</h4>
                           <div className="bg-slate-900 text-slate-300 font-mono text-[10px] p-4 rounded-xl flex-1 overflow-y-auto space-y-1">
                              {analysisLogs.map((l, idx) => <div key={idx}>{l}</div>)}
                              {loadingRecommendations && <div className="text-indigo-400 animate-pulse">Running schema relations parser...</div>}
                           </div>
                        </div>
                     ) : validationsList.length === 0 ? (
                        <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
                           <div className="w-12 h-12 rounded-xl bg-slate-50 flex items-center justify-center text-slate-400 mb-4">
                              <Layers size={18} />
                           </div>
                           <p className="text-xs font-bold text-slate-500 mb-1">No Validations Configured</p>
                           <p className="text-[11px] text-slate-400 max-w-xs leading-relaxed mb-4">
                              {explorerTab === 'explorer' 
                                 ? 'Click "Suggest Validations" to automatically detect data quality constraints based on table columns.' 
                                 : 'Upload a database schema diagram image on the left, then click "Analyze Diagram" to automatically recommend validations.'
                              }
                           </p>
                        </div>
                     ) : (
                        <div className="flex-1 flex flex-col min-h-0 overflow-y-auto space-y-4 pr-2">
                            <div className="flex items-center justify-between">
                               <span className="text-[10px] font-black uppercase tracking-wider text-slate-400">Assertions Configuration</span>
                               <div className="flex items-center gap-3">
                                  <button
                                     onClick={() => setShowPredefinedForm(!showPredefinedForm)}
                                     className="text-indigo-600 hover:text-indigo-700 flex items-center gap-1 text-[9px] font-black uppercase tracking-widest transition-colors"
                                  >
                                     <PlusCircle size={12} /> Add Predefined Check
                                  </button>
                                  <button
                                     onClick={handleAddCustomValidation}
                                     className="text-blue-600 hover:text-blue-700 flex items-center gap-1 text-[9px] font-black uppercase tracking-widest transition-colors"
                                  >
                                     <PlusCircle size={12} /> Add Custom Query
                                  </button>
                               </div>
                            </div>

                            {showPredefinedForm && (
                               <div className="p-5 rounded-2xl border border-indigo-200 bg-indigo-50/20 shadow-sm space-y-4 animate-in slide-in-from-top-2 duration-200 mb-4 text-left">
                                  <div className="flex items-center justify-between">
                                     <h4 className="text-[10px] font-black uppercase tracking-wider text-indigo-600">Add Predefined Assertion</h4>
                                     <button onClick={() => setShowPredefinedForm(false)} className="text-slate-400 hover:text-slate-600">
                                        <X size={14} />
                                     </button>
                                  </div>
                                  <div className="grid grid-cols-2 gap-4">
                                     <div className="space-y-1">
                                        <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Target Column</label>
                                        <select
                                           value={predefinedCol}
                                           onChange={(e) => setPredefinedCol(e.target.value)}
                                           className="w-full bg-white border border-slate-200 rounded-lg px-2.5 py-2 text-xs font-bold text-slate-700 outline-none cursor-pointer focus:border-blue-400"
                                        >
                                           <option value="">-- Select Column --</option>
                                           {selectedTable?.columns.map(c => (
                                              <option key={c.name} value={c.name}>{c.name}</option>
                                           ))}
                                        </select>
                                     </div>
                                     <div className="space-y-1">
                                        <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Check Type</label>
                                        <select
                                           value={predefinedType}
                                           onChange={(e) => setPredefinedType(e.target.value)}
                                           className="w-full bg-white border border-slate-200 rounded-lg px-2.5 py-2 text-xs font-bold text-slate-700 outline-none cursor-pointer focus:border-blue-400"
                                        >
                                           <option value="null_check">Null Value Check</option>
                                           <option value="unique_check">Unique / Primary Key Check</option>
                                           <option value="positive_check">Positive Value Check</option>
                                        </select>
                                     </div>
                                  </div>
                                  <div className="flex justify-end gap-3 pt-2">
                                     <button
                                        onClick={() => setShowPredefinedForm(false)}
                                        className="px-4 py-2 border border-slate-200 text-slate-500 rounded-lg text-[10px] font-black uppercase tracking-wider bg-white hover:bg-slate-50 transition-colors"
                                     >
                                        Cancel
                                     </button>
                                     <button
                                        onClick={handleCreatePredefinedCheck}
                                        disabled={!predefinedCol}
                                        className="px-5 py-2 bg-indigo-600 disabled:bg-slate-200 text-white rounded-lg text-[10px] font-black uppercase tracking-wider hover:bg-indigo-700 transition-colors shadow-md disabled:shadow-none"
                                     >
                                        Add Assertion
                                     </button>
                                  </div>
                               </div>
                            )}

                           <div className="space-y-4">
                              {validationsList.map((val, idx) => {
                                 const isExpanded = expandedSqlIndex === idx;
                                 return (
                                    <div 
                                       key={val.id} 
                                       className={`p-5 rounded-2xl border transition-all duration-300 ${val.enabled ? 'border-slate-200 bg-white shadow-sm hover:shadow' : 'border-slate-100 bg-slate-50/50 opacity-60'}`}
                                    >
                                       <div className="flex items-start justify-between gap-4">
                                          <div className="flex-1 space-y-1">
                                             <div className="flex items-center gap-2 flex-wrap">
                                                <input 
                                                   type="checkbox" 
                                                   checked={val.enabled} 
                                                   onChange={() => handleToggleValidation(idx)}
                                                   className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 cursor-pointer w-4 h-4"
                                                />
                                                <span className="text-[9px] font-black px-2 py-0.5 rounded bg-indigo-50 border border-indigo-100 text-indigo-600 uppercase tracking-widest">{val.id}</span>
                                                <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">{val.type}</span>
                                             </div>
                                             <p className="text-xs font-bold text-slate-800 leading-snug">{val.description}</p>
                                          </div>
                                          <button 
                                             onClick={() => handleRemoveValidation(idx)}
                                             className="text-slate-300 hover:text-rose-600 transition-colors p-1"
                                             title="Remove Test"
                                          >
                                             <X size={14} />
                                          </button>
                                        </div>

                                       {val.enabled && (
                                          <div className="mt-4 pt-4 border-t border-slate-100 space-y-3">
                                             {/* Plain-English Rule Editor Sentence */}
                                             <div className="flex flex-wrap items-center gap-2 text-xs font-bold text-slate-500">
                                                <span>Verify database output is</span>
                                                <select
                                                   value={val.expected_condition}
                                                   onChange={(e) => handleUpdateValidation(idx, "expected_condition", e.target.value)}
                                                   className="bg-white border border-slate-200 rounded-lg px-2.5 py-1 text-xs font-black text-slate-700 outline-none cursor-pointer focus:border-blue-400"
                                                >
                                                   <option value="EQUAL">EQUAL TO</option>
                                                   <option value="GREATER_THAN">GREATER_THAN</option>
                                                </select>
                                                <input
                                                   type="number"
                                                   value={val.expected_value}
                                                   onChange={(e) => handleUpdateValidation(idx, "expected_value", Number(e.target.value))}
                                                   className="w-16 bg-white border border-slate-200 rounded-lg px-2 py-1 text-xs font-black text-slate-700 text-center outline-none focus:border-blue-400"
                                                />
                                             </div>

                                             {/* SQL Query Toggle Details */}
                                             <div>
                                                <button
                                                   type="button"
                                                   onClick={() => setExpandedSqlIndex(isExpanded ? null : idx)}
                                                   className="text-[9px] font-black uppercase tracking-widest text-blue-500 hover:text-blue-600 transition-colors flex items-center gap-1"
                                                >
                                                   {isExpanded ? 'Hide SQL Code' : 'Show SQL Code'}
                                                   <ChevronRight size={10} className={`transform transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
                                                </button>

                                                {isExpanded && (
                                                   <div className="mt-2 bg-slate-900 text-slate-300 font-mono text-[10px] p-3.5 rounded-xl border border-slate-800 animate-in fade-in slide-in-from-top-1 duration-200">
                                                      <textarea
                                                         value={val.query}
                                                         onChange={(e) => handleUpdateValidation(idx, "query", e.target.value)}
                                                         className="w-full bg-transparent text-slate-200 outline-none resize-none"
                                                         rows={3}
                                                      />
                                                   </div>
                                                )}
                                             </div>
                                          </div>
                                       )}
                                    </div>
                                 )
                              })}
                           </div>
                        </div>
                     )}
                  </div>

                  <div className="pt-6 border-t border-slate-100 flex items-center justify-between">
                     <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">
                        Database connected successfully.
                     </p>
                     <button
                        onClick={() => {
                           setFeatureState('execution')
                           handleRunBatchValidations()
                        }}
                        disabled={validationsList.filter(v => v.enabled).length === 0}
                        className="px-10 py-4 rounded-2xl text-[10px] font-black uppercase tracking-[0.2em] bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-300 disabled:text-slate-500 disabled:shadow-none text-white shadow-xl shadow-emerald-500/20 transition-all flex items-center gap-3 active:scale-95"
                     >
                        <Play size={14} fill="white" />
                        Execute Validation Suite
                     </button>
                  </div>
               </div>
            </div>
         </div>
      )
   }

   // Execution Workspace
   if (currentMode === 'execution') {
      if (isRunning) {
         return (
            <div className="flex-1 opacity-95 h-full min-h-0 flex flex-col bg-white">
               <Terminal logs={logs} minHeight="100%" />
            </div>
         )
      }

      if (isComplete && batchResult) {
         const passedCount = batchResult.details.results.filter(r => r.passed).length
         const failedCount = batchResult.details.results.filter(r => !r.passed).length
         const totalCount = batchResult.details.total_validations
         const scorePercent = Math.round((passedCount / totalCount) * 100)
         const overallPassed = batchResult.passed

         // Parse log lines into labeled segments
         const parseLog = (log) => {
            const match = log.match(/\[([A-Z0-9:]+)\]\s*\[([A-Z]+)\]\s*(.+)/)
            if (match) return { time: match[1], tag: match[2], msg: match[3] }
            return { time: null, tag: null, msg: log }
         }

         return (
            <div className="flex-1 overflow-y-auto animate-in fade-in slide-in-from-bottom-4 duration-500 text-left bg-gradient-to-br from-slate-50 to-slate-100/60">
               <div className="max-w-5xl mx-auto px-8 py-8 space-y-6">

                  {/* ── Top Status Banner ── */}
                  <div className={`rounded-[2rem] p-8 flex items-center justify-between relative overflow-hidden shadow-xl ${
                     overallPassed
                        ? 'bg-gradient-to-br from-emerald-600 to-teal-700'
                        : 'bg-gradient-to-br from-rose-600 to-rose-800'
                  }`}>
                     {/* Background glow */}
                     <div className="absolute right-0 top-0 w-64 h-64 rounded-full bg-white/5 blur-3xl" />
                     <div className="absolute -bottom-8 -left-8 w-40 h-40 rounded-full bg-black/10 blur-2xl" />

                     <div className="relative z-10">
                        <div className="flex items-center gap-3 mb-3">
                           {overallPassed
                              ? <CheckCircle size={20} className="text-emerald-200" />
                              : <AlertTriangle size={20} className="text-rose-200" />
                           }
                           <span className="text-[9px] font-black uppercase tracking-[0.25em] text-white/70">
                              Batch Validation Suite
                           </span>
                        </div>
                        <h1 className="text-2xl font-black text-white tracking-tight mb-1">
                           {overallPassed ? 'All Assertions Passed' : 'Integrity Violation Detected'}
                        </h1>
                        <p className="text-[11px] font-semibold text-white/60 uppercase tracking-wider">
                           Target: <span className="text-white/90 font-bold">{dbConfig?.db_name || 'etl_test.db'}</span>
                           &nbsp;·&nbsp;Engine: <span className="text-white/90 font-bold">{dbConfig?.engine?.toUpperCase() || 'SQLITE'}</span>
                        </p>
                     </div>

                     <div className="relative z-10 flex flex-col items-end gap-2">
                        <div className="text-right">
                           <p className="text-5xl font-black text-white leading-none">{scorePercent}%</p>
                           <p className="text-[9px] font-black uppercase tracking-[0.2em] text-white/60 mt-1">Quality Score</p>
                        </div>
                     </div>
                  </div>

                  {/* ── KPI Row ── */}
                  <div className="grid grid-cols-3 gap-4">
                     <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
                        <p className="text-[9px] font-black uppercase tracking-widest text-slate-400 mb-2">Total Assertions</p>
                        <p className="text-3xl font-black text-slate-900">{totalCount}</p>
                        <p className="text-[10px] text-slate-400 font-semibold mt-1">checks scheduled</p>
                     </div>
                     <div className={`rounded-2xl p-5 border shadow-sm ${
                        passedCount === totalCount ? 'bg-emerald-50 border-emerald-200' : 'bg-white border-slate-200'
                     }`}>
                        <p className="text-[9px] font-black uppercase tracking-widest text-emerald-500 mb-2">Passed Checks</p>
                        <p className="text-3xl font-black text-emerald-600">{passedCount}</p>
                        <p className="text-[10px] text-slate-400 font-semibold mt-1">assertions verified ✓</p>
                     </div>
                     <div className={`rounded-2xl p-5 border shadow-sm ${
                        failedCount > 0 ? 'bg-rose-50 border-rose-200' : 'bg-white border-slate-200'
                     }`}>
                        <p className="text-[9px] font-black uppercase tracking-widest text-rose-400 mb-2">Failed Checks</p>
                        <p className={`text-3xl font-black ${failedCount > 0 ? 'text-rose-500' : 'text-slate-400'}`}>{failedCount}</p>
                        <p className="text-[10px] text-slate-400 font-semibold mt-1">integrity violations</p>
                     </div>
                  </div>

                  {/* ── Execution Log Card ── */}
                  <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                     <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                           <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                           <h3 className="text-xs font-black uppercase tracking-wider text-slate-700">Execution Log</h3>
                        </div>
                        <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">
                           {batchResult.details.execution_logs.length} events
                        </span>
                     </div>
                     <div className="divide-y divide-slate-50">
                        {batchResult.details.execution_logs.map((log, idx) => {
                           const { time, tag, msg } = parseLog(log)
                           const isError = tag === 'ERROR' || msg?.toLowerCase().includes('failed')
                           const isValidation = tag === 'VALIDATION'
                           const isResult = tag === 'RESULT'
                           const isInfo = tag === 'INFO'
                           const isHighlight = isResult || msg?.includes('PASSED') || msg?.includes('SUCCEEDED')

                           const tagColors = {
                              'ERROR':      'bg-rose-100 text-rose-700',
                              'VALIDATION': 'bg-indigo-50 text-indigo-600',
                              'RESULT':     overallPassed ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700',
                              'INFO':       'bg-slate-100 text-slate-500',
                              'SYSTEM':     'bg-slate-100 text-slate-500',
                              'PROCESS':    'bg-blue-50 text-blue-600',
                           }
                           const tagColor = tagColors[tag] || 'bg-slate-100 text-slate-500'

                           return (
                              <div key={idx} className={`flex items-start gap-4 px-6 py-3.5 transition-colors group ${
                                 isHighlight ? (overallPassed ? 'bg-emerald-50/40' : 'bg-rose-50/40') : 'hover:bg-slate-50/50'
                              }`}>
                                 {/* Icon */}
                                 <div className="mt-0.5 shrink-0">
                                    {isError ? (
                                       <AlertTriangle size={15} className="text-rose-500" />
                                    ) : isHighlight ? (
                                       <CheckCircle size={15} className="text-emerald-500" />
                                    ) : (
                                       <div className="w-3.5 h-3.5 rounded-full border-2 border-slate-200 bg-white group-hover:border-blue-300 transition-colors" />
                                    )}
                                 </div>

                                 {/* Content */}
                                 <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 flex-wrap">
                                       {tag && (
                                          <span className={`text-[8px] font-black uppercase tracking-widest px-1.5 py-0.5 rounded ${tagColor}`}>
                                             {tag}
                                          </span>
                                       )}
                                       <span className={`text-[11px] leading-relaxed font-medium ${
                                          isError ? 'text-rose-700' : isHighlight ? 'text-emerald-700 font-bold' : 'text-slate-600'
                                       }`}>
                                          {msg || log}
                                       </span>
                                    </div>
                                 </div>

                                 {/* Timestamp */}
                                 {time && (
                                    <span className="text-[9px] font-mono text-slate-300 shrink-0 mt-0.5">{time}</span>
                                 )}
                              </div>
                           )
                        })}
                     </div>
                  </div>

                  {/* ── Action Footer ── */}
                  <div className="flex items-center justify-between pt-2 pb-4">
                     <button
                        onClick={() => {
                           setViewingReport(false)
                           setFeatureState('query')
                        }}
                        className="px-6 py-3 bg-white border border-slate-200 text-slate-600 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-slate-50 transition-colors shadow-sm active:scale-95"
                     >
                        ← Edit Validations
                     </button>
                     <button
                        onClick={() => setViewingReport(true)}
                        className="px-8 py-3 bg-blue-600 text-white rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-blue-700 transition-all shadow-lg shadow-blue-500/20 active:scale-95 flex items-center gap-2"
                     >
                        <FileText size={12} /> View Full Quality Report
                     </button>
                  </div>

               </div>
            </div>
         )
      }
   }

   // Default/Initial State
   if (viewingReport && batchResult) {
      const passedCount = batchResult.details.results.filter(r => r.passed).length
      const failedCount = batchResult.details.results.filter(r => !r.passed).length
      const accuracyScore = Math.round((passedCount / batchResult.details.total_validations) * 100)

      return (
         <div className="flex-1 flex bg-slate-50/50 overflow-hidden text-left p-8">
            <div className="flex-1 flex flex-col bg-white rounded-[2rem] border border-slate-200 shadow-xl overflow-hidden justify-between max-w-6xl mx-auto w-full">
               <div className="flex-1 flex flex-col min-h-0">
                  {/* Report Header */}
                  <div className="flex items-center justify-between p-6 border-b border-slate-100 bg-white">
                     <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-indigo-50 flex items-center justify-center text-indigo-600 shadow-sm shrink-0">
                           <FileText size={22} />
                        </div>
                        <div>
                           <div className="flex items-center gap-3">
                              <h1 className="text-base font-black uppercase tracking-tight text-slate-900">Database Quality Report</h1>
                              <span className={`px-2.5 py-0.5 rounded text-[9px] font-black uppercase border tracking-widest ${
                                 batchResult.passed 
                                    ? 'bg-emerald-50 text-emerald-600 border-emerald-100' 
                                    : 'bg-rose-50 text-rose-600 border-rose-100'
                              }`}>
                                 {batchResult.passed ? 'PASSED' : 'INTEGRITY VIOLATION'}
                              </span>
                           </div>
                           <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mt-1">
                              Target DB: <span className="text-slate-600 font-mono">{dbConfig?.db_name || 'etl_test.db'}</span> &bull; Engine: <span className="text-slate-600">{dbConfig?.engine?.toUpperCase()}</span>
                           </p>
                        </div>
                     </div>

                     <div className="flex items-center gap-3 relative">
                        {/* Go back button */}
                        <button
                           onClick={() => setViewingReport(false)}
                           className="px-4 py-2.5 rounded-xl border border-slate-200 text-slate-500 bg-white text-[10px] font-black uppercase tracking-wider hover:bg-slate-50 transition-colors shadow-sm flex items-center gap-1.5 active:scale-95"
                        >
                           <Undo2 size={13} /> Back to Results
                        </button>

                        {/* Export Dropdown Button */}
                        <div className="relative">
                           <button
                              onClick={() => setExportDropdownOpen(!exportDropdownOpen)}
                              className="px-5 py-2.5 rounded-xl bg-slate-900 text-white text-[10px] font-black uppercase tracking-wider hover:bg-black transition-all shadow-md shadow-slate-900/10 flex items-center gap-2 active:scale-95 animate-in"
                           >
                              <Download size={13} /> Export Report <ChevronDown size={12} className={`transform transition-transform ${exportDropdownOpen ? 'rotate-180' : ''}`} />
                           </button>

                           {exportDropdownOpen && (
                              <>
                                 {/* Backdrop to close the dropdown on click outside */}
                                 <div className="fixed inset-0 z-10" onClick={() => setExportDropdownOpen(false)} />
                                 
                                 <div className="absolute right-0 mt-2 w-52 bg-white border border-slate-100 rounded-2xl shadow-xl z-20 overflow-hidden py-1.5 animate-in zoom-in-95 duration-100 origin-top-right">
                                    <button
                                       onClick={() => {
                                          handleExportPDF();
                                          setExportDropdownOpen(false);
                                       }}
                                       className="w-full text-left px-4 py-2.5 hover:bg-slate-50 text-[10px] font-black uppercase tracking-wider text-slate-700 hover:text-slate-900 flex items-center gap-2.5 transition-colors"
                                    >
                                       <span className="w-2 h-2 rounded-full bg-indigo-500" />
                                       PDF Document (.pdf)
                                    </button>
                                    <button
                                       onClick={() => {
                                          handleExportCSV();
                                          setExportDropdownOpen(false);
                                       }}
                                       className="w-full text-left px-4 py-2.5 hover:bg-slate-50 text-[10px] font-black uppercase tracking-wider text-slate-700 hover:text-slate-900 flex items-center gap-2.5 transition-colors"
                                    >
                                       <span className="w-2 h-2 rounded-full bg-emerald-500" />
                                       CSV Table Data (.csv)
                                    </button>
                                    <button
                                       onClick={() => {
                                          handleExportJSON();
                                          setExportDropdownOpen(false);
                                       }}
                                       className="w-full text-left px-4 py-2.5 hover:bg-slate-50 text-[10px] font-black uppercase tracking-wider text-slate-700 hover:text-slate-900 flex items-center gap-2.5 transition-colors"
                                    >
                                       <span className="w-2 h-2 rounded-full bg-amber-500" />
                                       JSON Raw Data (.json)
                                    </button>
                                 </div>
                              </>
                           )}
                        </div>
                     </div>
                  </div>

                  {/* Scrollable Report Content */}
                  <div className="flex-1 overflow-y-auto p-8 space-y-8">
                     {/* Summary Dashboard Grid */}
                     <div className="grid grid-cols-4 gap-6">
                        <div className="p-5 rounded-2xl bg-slate-50 border border-slate-100 shadow-sm flex flex-col justify-between">
                           <p className="text-[9px] font-black uppercase tracking-widest text-slate-400 mb-1">Total Assertions</p>
                           <p className="text-3xl font-black text-slate-900">{batchResult.details.total_validations}</p>
                        </div>
                        <div className="p-5 rounded-2xl bg-emerald-50/20 border border-emerald-100 shadow-sm flex flex-col justify-between">
                           <p className="text-[9px] font-black uppercase tracking-widest text-emerald-500 mb-1">Passed Checks</p>
                           <p className="text-3xl font-black text-emerald-600">{passedCount}</p>
                        </div>
                        <div className="p-5 rounded-2xl bg-rose-50/20 border border-rose-100 shadow-sm flex flex-col justify-between">
                           <p className="text-[9px] font-black uppercase tracking-widest text-rose-400 mb-1">Failed Checks</p>
                           <p className="text-3xl font-black text-rose-500">{failedCount}</p>
                        </div>
                        <div className="p-5 rounded-2xl bg-blue-50/20 border border-blue-100 shadow-sm flex flex-col justify-between">
                           <p className="text-[9px] font-black uppercase tracking-widest text-blue-500 mb-1">Quality Score</p>
                           <div className="flex items-baseline gap-1">
                              <p className="text-3xl font-black text-blue-600">{accuracyScore}%</p>
                              <span className="text-[10px] font-bold text-slate-400">Success</span>
                           </div>
                        </div>
                     </div>

                     {/* Assertion Items Table */}
                     <div className="border border-slate-200 rounded-2xl overflow-hidden bg-white shadow-sm flex flex-col">
                        <div className="px-5 py-3.5 bg-slate-50 border-b border-slate-100">
                           <h3 className="text-xs font-black uppercase tracking-wider text-slate-500">Assertion Run Detail Spectrum</h3>
                        </div>
                        <div className="divide-y divide-slate-100">
                           {batchResult.details.results.map((r, idx) => (
                              <div key={idx} className="p-6 flex justify-between items-start gap-6 hover:bg-slate-50/15 transition-colors">
                                 <div className="space-y-2 flex-1 min-w-0">
                                    <div className="flex items-center gap-2">
                                       {r.passed ? (
                                          <CheckCircle size={14} className="text-emerald-500 shrink-0" />
                                       ) : (
                                          <AlertTriangle size={14} className="text-rose-500 shrink-0" />
                                       )}
                                       <span className="text-xs font-black text-slate-800">Check #{idx + 1}</span>
                                    </div>
                                    <pre className="text-[10px] font-mono text-slate-200 p-4 bg-slate-900 rounded-xl overflow-x-auto whitespace-pre">{r.query}</pre>
                                    {r.error && (
                                       <div className="text-[10px] font-semibold text-rose-600 p-3 bg-rose-50 border border-rose-100 rounded-xl flex items-center gap-2">
                                          <AlertTriangle size={12} className="shrink-0" />
                                          <span>{r.error}</span>
                                       </div>
                                    )}
                                 </div>
                                 <div className="text-right shrink-0">
                                    <span className={`text-[9px] font-black uppercase tracking-widest px-2.5 py-1 rounded-md border ${
                                       r.passed 
                                          ? 'bg-emerald-50 text-emerald-600 border-emerald-100' 
                                          : 'bg-rose-50 text-rose-600 border-rose-100'
                                    }`}>
                                       {r.passed ? 'PASS' : 'FAIL'}
                                    </span>
                                    <p className="text-[9px] font-bold text-slate-400 mt-2 uppercase tracking-tight">Rows: {r.rows_returned || 0}</p>
                                 </div>
                              </div>
                           ))}
                        </div>
                     </div>

                     {/* Logs Section */}
                     {batchResult.details.execution_logs && batchResult.details.execution_logs.length > 0 && (
                        <div className="space-y-3">
                           <h4 className="text-[10px] font-black uppercase tracking-wider text-slate-400">Execution Console Trace</h4>
                           <div className="bg-slate-950 text-slate-300 font-mono text-[10px] p-5 rounded-2xl overflow-y-auto max-h-56 space-y-1.5 border border-slate-900">
                              {batchResult.details.execution_logs.map((l, idx) => (
                                 <div key={idx} className={l.includes('[ERROR]') ? 'text-rose-400' : l.includes('[SUCCESS]') ? 'text-emerald-400' : ''}>
                                    {l}
                                 </div>
                              ))}
                           </div>
                        </div>
                     )}
                  </div>
               </div>

               {/* Report Footer */}
               <div className="p-6 border-t border-slate-100 flex items-center justify-between bg-slate-50/50">
                  <p className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">
                     IntellQA DB Audit Protocol Finalized
                  </p>
                  <button
                     onClick={() => {
                        setViewingReport(false);
                        setFeatureState('query');
                     }}
                     className="px-6 py-3 bg-slate-900 text-white rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-black transition-all shadow-md active:scale-95"
                  >
                     Done & Edit Validations
                  </button>
               </div>
            </div>
         </div>
      )
   }

   return (
      <div className="flex-1 flex flex-col items-center justify-center text-center p-16">
         <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center mb-6">
            <PlayCircle size={28} className="text-slate-300" />
         </div>
         <h3 className="text-sm font-bold text-slate-700 mb-2">Ready to Run Database Validations</h3>
         <p className="text-xs text-slate-400 max-w-xs leading-relaxed mb-6">Configure SQL queries and check type in the <span className="font-semibold text-slate-500">Query Mode</span>, then click <span className="font-semibold text-slate-500">Run</span> to execute data-integrity audits.</p>
         <button onClick={handleRunBatchValidations} className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold transition-all active:scale-95">
            <Zap size={13} /> Run Validations
         </button>
      </div>
   )
}
