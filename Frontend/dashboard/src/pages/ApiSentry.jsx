import React, { useState, useEffect } from 'react'
import { useAppContext } from '../store/AppContext'
import {
   Play, Settings, Send,
   FileText, ChevronRight,
   Sparkles, Cpu,
   CloudUpload, ArrowRight, Zap,
   Database, RefreshCw, Activity, Layers,
   Terminal as TerminalIcon, PlusCircle,
   X, CheckCircle, AlertTriangle, PlayCircle
} from 'lucide-react'
import Terminal from '../components/shared/Terminal'

export default function ApiSentry() {
   const {
      featureState, setFeatureState, showAlert, setActivePage, setNavParams
   } = useAppContext()

   const [url, setUrl] = useState('https://fakestoreapi.com/products')
   const [method, setMethod] = useState('GET')
   const [payload, setPayload] = useState('{\n  "title": "Test Product",\n  "price": 13.5,\n  "description": "lorem ipsum set",\n  "image": "https://i.pravatar.cc",\n  "category": "electronic"\n}')
   const [validationType, setValidationType] = useState('status_code') // status_code, contains_text, latency
   const [expectedValue, setExpectedValue] = useState('200')
   
   const [isRunning, setIsRunning] = useState(false)
   const [isComplete, setIsComplete] = useState(false)
   const [logs, setLogs] = useState([])
   const [resultData, setResultData] = useState(null)

   const currentMode = (!featureState || featureState === 'intro') ? 'intro' : featureState

   const handleRunTest = async () => {
      setIsRunning(true)
      setIsComplete(false)
      setLogs([
         "[SYSTEM] Initializing API Sentry Engine...",
         `[INFO] Target URL: ${url}`,
         `[INFO] HTTP Method: ${method}`,
         "[PROCESS] Preparing HTTP request headers...",
         "[PROCESS] Resolving request body payload...",
         "[PROCESS] Dispatching transaction packet..."
      ])

      try {
         const res = await fetch('http://localhost:8000/api/interactive-api-test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
               url,
               method,
               payload: method !== 'GET' ? payload : null,
               validation_type: validationType,
               expected_value: expectedValue
            })
         })
         
         const data = await res.json()
         
         // Simulated timeline logging
         setTimeout(() => {
            setLogs(prev => [
               ...prev,
               ...(data.execution_logs || []),
               "[SYSTEM] Audit complete."
            ])
            setResultData(data)
            setIsRunning(false)
            setIsComplete(true)
         }, 1500)
         
      } catch (error) {
         console.error("API test failed:", error)
         setLogs(prev => [...prev, `[ERROR] Connection failed: ${error.message}`])
         setIsRunning(false)
      }
   }

   // --- RENDER INTRO MODE ---
   if (currentMode === 'intro') {
      return (
         <div className="w-full flex flex-col p-8 lg:p-12 animate-in fade-in duration-700 bg-slate-50/30">
            <div className="max-w-5xl mx-auto w-full pt-4">
               <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                  <div className="md:col-span-2 p-10 rounded-[2rem] bg-white border border-slate-200 shadow-sm hover:shadow-md transition-shadow text-left">
                     <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center mb-6">
                        <Sparkles size={20} className="text-blue-600" />
                     </div>
                     <h2 className="text-xl font-black text-slate-800 mb-4 tracking-tight">REST Endpoint Sentry</h2>
                     <p className="text-sm font-medium text-slate-500 leading-relaxed max-w-xl">
                        Validate HTTP endpoints, inspect response payload structures, and assert contracts without writing code. Set up automated validation checks for latency, status codes, and payload values.
                     </p>
                  </div>

                  <div className="p-8 rounded-[2rem] bg-slate-900 text-white shadow-xl shadow-slate-900/10 flex flex-col justify-between relative overflow-hidden text-left">
                     <div className="absolute top-0 right-0 w-32 h-32 bg-slate-800 rounded-full blur-3xl" />
                     <div className="relative z-10">
                        <Cpu className="text-slate-400 mb-6" size={24} />
                        <h3 className="text-sm font-black mb-2 tracking-wide">REST Gateway Testing</h3>
                        <p className="text-[10px] font-medium text-slate-400 leading-relaxed">
                           Validate GET, POST, PUT, and DELETE routes instantly. Run contract checks automatically.
                        </p>
                     </div>
                     <div className="relative z-10 mt-8">
                        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500 mb-1">Architecture</p>
                        <p className="text-sm font-bold text-slate-300">Contract & Schema Validation</p>
                     </div>
                  </div>
               </div>

               <div className="flex flex-col items-center justify-center p-12 text-center rounded-[2rem] border border-dashed border-slate-300/60 bg-white/50">
                  <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4">
                     <ChevronRight className="text-slate-400 rotate-90" size={20} />
                  </div>
                  <h3 className="text-lg font-black text-slate-800 mb-2 tracking-tight">Ready to verify an endpoint?</h3>
                  <p className="text-xs font-bold text-slate-400 max-w-sm mx-auto leading-relaxed mb-6">
                     Select <span className="text-blue-600">Query Mode</span> in the sidebar to configure request payload parameters, or <span className="text-emerald-600">Execution Mode</span> to run tests.
                  </p>
                  <div className="flex items-center gap-4">
                     <button
                        onClick={() => {
                           setNavParams({ defaultTab: 'api_sentry', returnPage: 'api_sentry', returnMode: 'intro' })
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
                        Configure REST Request
                     </button>
                  </div>
               </div>
            </div>
         </div>
      )
   }

   // --- RENDER QUERY MODE (DESIGN/CONFIGURE) ---
   if (currentMode === 'query') {
      return (
         <div className="w-full h-full flex flex-col bg-gradient-to-br from-slate-50 to-slate-100 animate-in fade-in duration-700 text-left">
            <div className="flex-1 flex gap-8 p-8 overflow-hidden">
               {/* Left Panel: Request Parameters */}
               <div className="w-1/2 h-full flex flex-col gap-4 bg-white p-8 rounded-[2rem] border border-slate-200 shadow-sm">
                  <h3 className="text-xs font-black uppercase tracking-wider text-slate-400 flex items-center gap-2">
                     <Send size={14} className="text-blue-600" />
                     Configure REST Endpoint
                  </h3>
                  
                  <div className="space-y-4 flex-1 overflow-y-auto pr-2">
                     <div className="grid grid-cols-4 gap-4">
                        <div className="col-span-1 flex flex-col gap-2">
                           <label className="text-[10px] font-black uppercase tracking-wider text-slate-400">Method</label>
                           <select 
                              value={method} 
                              onChange={(e) => setMethod(e.target.value)} 
                              className="w-full border border-slate-200 rounded-xl px-4 py-3.5 text-xs font-black text-slate-800 focus:bg-white focus:ring-1 focus:ring-blue-500/20 outline-none cursor-pointer"
                           >
                              <option value="GET">GET</option>
                              <option value="POST">POST</option>
                              <option value="PUT">PUT</option>
                              <option value="DELETE">DELETE</option>
                           </select>
                        </div>
                        <div className="col-span-3 flex flex-col gap-2">
                           <label className="text-[10px] font-black uppercase tracking-wider text-slate-400">URL Endpoint</label>
                           <input 
                              type="text" 
                              value={url} 
                              onChange={(e) => setUrl(e.target.value)}
                              placeholder="https://api.example.com/endpoint" 
                              className="w-full border border-slate-200 rounded-xl px-5 py-3.5 text-xs font-bold text-slate-800 focus:bg-white focus:ring-1 focus:ring-blue-500/20 outline-none"
                           />
                        </div>
                     </div>

                     {method !== 'GET' && (
                        <div className="flex flex-col gap-2">
                           <label className="text-[10px] font-black uppercase tracking-wider text-slate-400">JSON Payload</label>
                           <textarea 
                              value={payload} 
                              onChange={(e) => setPayload(e.target.value)}
                              className="w-full border border-slate-200 rounded-xl px-5 py-4 text-xs font-mono text-slate-800 h-64 resize-none focus:bg-white focus:ring-1 focus:ring-blue-500/20 outline-none"
                           />
                        </div>
                     )}
                  </div>
               </div>

               {/* Right Panel: Assertions & Deploy */}
               <div className="w-1/2 h-full flex flex-col gap-6 bg-white p-8 rounded-[2rem] border border-slate-200 shadow-sm justify-between">
                  <div className="space-y-6">
                     <h3 className="text-xs font-black uppercase tracking-wider text-slate-400 flex items-center gap-2">
                        <Sparkles size={14} className="text-indigo-600" />
                        Verification Constraints
                     </h3>

                     <div className="grid grid-cols-2 gap-6">
                        <div className="flex flex-col gap-2">
                           <label className="text-[10px] font-black uppercase tracking-wider text-slate-400">Validation Type</label>
                           <select 
                              value={validationType} 
                              onChange={(e) => {
                                 setValidationType(e.target.value)
                                 setExpectedValue(e.target.value === 'status_code' ? '200' : e.target.value === 'latency' ? '1000' : 'category')
                              }} 
                              className="w-full border border-slate-200 rounded-xl px-4 py-3.5 text-xs font-black text-slate-800 focus:bg-white focus:ring-1 focus:ring-blue-500/20 outline-none cursor-pointer"
                           >
                              <option value="status_code">Status Code assertion</option>
                              <option value="contains_text">Response contains string</option>
                              <option value="latency">Maximum latency check</option>
                           </select>
                        </div>
                        <div className="flex flex-col gap-2">
                           <label className="text-[10px] font-black uppercase tracking-wider text-slate-400">Expected Value</label>
                           <input 
                              type="text" 
                              value={expectedValue} 
                              onChange={(e) => setExpectedValue(e.target.value)}
                              className="w-full border border-slate-200 rounded-xl px-5 py-3.5 text-xs font-bold text-slate-800 focus:bg-white focus:ring-1 focus:ring-blue-500/20 outline-none"
                           />
                        </div>
                     </div>
                  </div>

                  <div className="pt-6 border-t border-slate-100 flex items-center justify-between">
                     <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">
                        Will execute assertion: <span className="text-blue-600 font-black">{validationType.replace('_', ' ').toUpperCase()} == {expectedValue}</span>
                     </p>
                     <button
                        onClick={() => {
                           setFeatureState('execution')
                           handleRunTest()
                        }}
                        className="px-10 py-4 rounded-2xl text-[10px] font-black uppercase tracking-[0.2em] bg-emerald-600 hover:bg-emerald-700 text-white shadow-xl shadow-emerald-500/20 transition-all flex items-center gap-3 active:scale-95"
                     >
                        <Play size={14} fill="white" />
                        Run Endpoint Sentry
                     </button>
                  </div>
               </div>
            </div>
         </div>
      )
   }

   // --- RENDER VALIDATION MODE ---
   if (currentMode === 'validation') {
      return (
         <div className="w-full h-full flex flex-col p-8 bg-slate-50 text-left">
            <div className="flex-1 bg-white border border-slate-200 rounded-[2rem] p-8 shadow-sm overflow-hidden flex flex-col gap-4">
               <h3 className="text-xs font-black uppercase tracking-wider text-slate-400 flex items-center gap-2">
                  <Database size={14} className="text-blue-600" />
                  Response Payload JSON Inspection
               </h3>
               <div className="flex-1 overflow-auto bg-slate-50 border border-slate-100 rounded-2xl p-6">
                  <pre className="text-xs font-mono leading-relaxed text-slate-700 select-all">
                     {resultData ? JSON.stringify(resultData.response_body, null, 2) : '// Run the sentry execution first to inspect response data.'}
                  </pre>
               </div>
            </div>
         </div>
      )
   }

   // --- RENDER EXECUTION MODE ---
   return (
      <div className="flex-1 flex bg-white overflow-hidden text-left">
         <div className="flex-1 flex flex-col min-w-0 bg-white">
            {isRunning ? (
               <div className="flex-1 opacity-95">
                  <Terminal logs={logs} minHeight="100%" />
               </div>
            ) : isComplete && resultData ? (
               <div className="flex-1 overflow-y-auto animate-in fade-in slide-in-from-bottom-2 duration-500">
                  {/* KPI Strip */}
                  <div className="grid grid-cols-3 divide-x divide-slate-100 border-b border-slate-100">
                     <div className="px-8 py-5">
                        <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Response Time</p>
                        <p className="text-2xl font-bold text-blue-600">{resultData.latency_ms}<span className="text-sm text-slate-400 font-normal"> ms</span></p>
                     </div>
                     <div className="px-8 py-5">
                        <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Status Code</p>
                        <p className="text-2xl font-bold text-slate-800">{resultData.status_code}</p>
                     </div>
                     <div className="px-8 py-5">
                        <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Outcome</p>
                        <p className={`text-2xl font-bold ${resultData.passed ? 'text-emerald-600' : 'text-rose-500'}`}>
                           {resultData.passed ? 'PASSED' : 'FAILED'}
                        </p>
                     </div>
                  </div>

                  {/* Assertion logs */}
                  <div className="px-8 py-6">
                     <div className="border border-slate-100 rounded-xl overflow-hidden mb-6">
                        <div className="px-5 py-3.5 bg-slate-50/80 border-b border-slate-100 flex items-center justify-between">
                           <h3 className="text-xs font-bold text-slate-600">Verification Assertion Logs</h3>
                           <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded text-[10px] font-black border ${resultData.passed ? 'bg-emerald-50 text-emerald-600 border-emerald-100' : 'bg-rose-50 text-rose-600 border-rose-100'}`}>
                              {resultData.passed ? 'SUCCEEDED' : 'ASSERTION_FAILED'}
                           </span>
                        </div>
                        <div className="p-5 space-y-2">
                           {resultData.validation_logs.map((log, idx) => (
                              <div key={idx} className="flex items-center gap-3 text-xs font-bold text-slate-700">
                                 {resultData.passed ? <CheckCircle size={14} className="text-emerald-500" /> : <AlertTriangle size={14} className="text-rose-500" />}
                                 {log}
                              </div>
                           ))}
                        </div>
                     </div>

                     {/* HTTP headers */}
                     <div className="border border-slate-100 rounded-xl overflow-hidden">
                        <div className="px-5 py-3.5 bg-slate-50/80 border-b border-slate-100">
                           <h3 className="text-xs font-bold text-slate-600">Response Headers</h3>
                        </div>
                        <div className="p-5 overflow-auto max-h-60 bg-slate-50/50">
                           <table className="w-full text-left border-collapse">
                              <thead>
                                 <tr className="border-b border-slate-200">
                                    <th className="py-2 text-[10px] uppercase tracking-wider text-slate-400 font-bold">Header Field</th>
                                    <th className="py-2 text-[10px] uppercase tracking-wider text-slate-400 font-bold pl-4">Value</th>
                                 </tr>
                              </thead>
                              <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                                 {Object.entries(resultData.headers).map(([key, val]) => (
                                    <tr key={key}>
                                       <td className="py-2 text-slate-600 font-black">{key}</td>
                                       <td className="py-2 text-slate-500 pl-4 break-all">{String(val)}</td>
                                    </tr>
                                 ))}
                              </tbody>
                           </table>
                        </div>
                     </div>
                  </div>
               </div>
            ) : (
               <div className="flex-1 flex flex-col items-center justify-center text-center p-16">
                  <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center mb-6">
                     <PlayCircle size={28} className="text-slate-300" />
                  </div>
                  <h3 className="text-sm font-bold text-slate-700 mb-2">Ready to Run API Sentry</h3>
                  <p className="text-xs text-slate-400 max-w-xs leading-relaxed mb-6">Select a request method and parameters in the <span className="font-semibold text-slate-500">Query Mode</span>, then click <span className="font-semibold text-slate-500">Run</span> to execute validation.</p>
                  <button onClick={handleRunTest} className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold transition-all active:scale-95">
                     <Zap size={13} /> Run
                  </button>
               </div>
            )}
         </div>
      </div>
   )
}
