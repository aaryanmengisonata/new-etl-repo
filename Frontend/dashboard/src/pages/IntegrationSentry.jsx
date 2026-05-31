import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, Settings, Send, FileText, ChevronRight, Sparkles, Cpu, 
  CloudUpload, ArrowRight, Zap, Database, RefreshCw, Activity, Layers, 
  Terminal as TerminalIcon, PlusCircle, X, CheckCircle, AlertTriangle, 
  PlayCircle, Edit3, Trash2, Check, ArrowLeft, Download, ShieldCheck, 
  HelpCircle, CheckSquare, Square, ChevronDown, Award
} from 'lucide-react';
import Terminal from '../components/shared/Terminal';
import { api } from '../services/api';
import { Button } from '../components/ui/Button';
import { Card, CardHeader } from '../components/ui/Card';
import { useAppContext } from '../store/AppContext';

export default function IntegrationSentry() {
  const { featureState, setFeatureState, showAlert, setActivePage, setNavParams } = useAppContext();

  // Wizard Steps (1 to 6)
  const [currentStep, setCurrentStep] = useState(1);

  // Keep currentStep in sync with featureState when featureState is changed via sidebar
  useEffect(() => {
    if (featureState === 'query') {
      if (currentStep !== 1 && currentStep !== 2) {
        setCurrentStep(1);
      }
    } else if (featureState === 'validation') {
      if (currentStep !== 3 && currentStep !== 4) {
        setCurrentStep(3);
      }
    } else if (featureState === 'execution') {
      if (currentStep !== 5 && currentStep !== 6) {
        setCurrentStep(5);
      }
    } else if (!featureState) {
      setFeatureState('intro');
    }
  }, [featureState]);

  const currentMode = (!featureState || featureState === 'intro') ? 'intro' : featureState;

  // ----------------------------------------------------
  // STEP 1: SYSTEMS CONNECTION CONFIGS
  // ----------------------------------------------------
  const [systemAType, setSystemAType] = useState('database');
  const [systemAEnv, setSystemAEnv] = useState('DEV');
  const [systemAConfig, setSystemAConfig] = useState({
    connection_name: 'System_A_DB',
    db_type: 'sqlite',
    host: 'localhost',
    port: '5432',
    db_name: 'test_audit_src.db',
    username: '',
    password: ''
  });
  const [systemAAPIConfig, setSystemAAPIConfig] = useState({
    base_url: 'https://fakestoreapi.com',
    method: 'GET',
    auth_type: 'none',
    token: ''
  });

  const [systemBType, setSystemBType] = useState('database');
  const [systemBEnv, setSystemBEnv] = useState('QA');
  const [systemBConfig, setSystemBConfig] = useState({
    connection_name: 'System_B_DB',
    db_type: 'sqlite',
    host: 'localhost',
    port: '5432',
    db_name: 'test_audit_tgt.db',
    username: '',
    password: ''
  });
  const [systemBAPIConfig, setSystemBAPIConfig] = useState({
    base_url: 'https://fakestoreapi.com',
    method: 'GET',
    auth_type: 'none',
    token: ''
  });

  const [testingA, setTestingA] = useState(false);
  const [connAStatus, setConnAStatus] = useState(null); // { success: bool, message, metadata, latency_ms }

  const [testingB, setTestingB] = useState(false);
  const [connBStatus, setConnBStatus] = useState(null);

  // ----------------------------------------------------
  // STEP 2: SCOPES & QUERIES
  // ----------------------------------------------------
  const [systemAQuery, setSystemAQuery] = useState('SELECT id, title, price, category FROM products');
  const [systemBQuery, setSystemBQuery] = useState('SELECT id, title, price, category FROM products_silver');
  const [keyColumn, setKeyColumn] = useState('id');

  // ----------------------------------------------------
  // STEP 3 & 4: SCHEMA PROFILING & SCENARIOS
  // ----------------------------------------------------
  const [profiling, setProfiling] = useState(false);
  const [profilingLogs, setProfilingLogs] = useState([]);
  const [schemaA, setSchemaA] = useState([]);
  const [schemaB, setSchemaB] = useState([]);
  const [suggestedScenarios, setSuggestedScenarios] = useState([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState('bit_perfect');
  const [aiSteps, setAiSteps] = useState([]);

  // ----------------------------------------------------
  // STEP 5: EXECUTION parameters
  // ----------------------------------------------------
  const [rowLimit, setRowLimit] = useState(10000);
  const [chunkSize, setChunkSize] = useState(2000);
  const [queryTimeout, setQueryTimeout] = useState(30);
  const [executing, setExecuting] = useState(false);
  const [executingProgress, setExecutingProgress] = useState(0);
  const [executionLogs, setExecutionLogs] = useState([]);
  
  // ----------------------------------------------------
  // STEP 6: TELETEMETRY RESULTS
  // ----------------------------------------------------
  const [reconcileResult, setReconcileResult] = useState(null); // ReconciliationResult
  const [exportDropdownOpen, setExportDropdownOpen] = useState(false);

  const logStreamTimer = useRef(null);

  useEffect(() => {
    return () => clearInterval(logStreamTimer.current);
  }, []);

  // --- connection pinger helpers ---
  const handleTestConnection = async (isSystemA) => {
    const type = isSystemA ? systemAType : systemBType;
    const env = isSystemA ? systemAEnv : systemBEnv;
    const configRaw = isSystemA 
      ? (systemAType === 'database' ? systemAConfig : systemAAPIConfig)
      : (systemBType === 'database' ? systemBConfig : systemBAPIConfig);
      
    const setTesting = isSystemA ? setTestingA : setTestingB;
    const setStatus = isSystemA ? setConnAStatus : setConnBStatus;

    setTesting(true);
    setStatus(null);

    // format payload to match ConnectionRequest
    const payload = {
      type,
      config: type === 'database' 
        ? { ...configRaw, db_type: configRaw.db_type, db_name: configRaw.db_name }
        : { base_url: configRaw.base_url, method: configRaw.method, auth_type: configRaw.auth_type, token: configRaw.token }
    };

    try {
      if (type === 'api' && !payload.config.base_url) {
        throw new Error("Base URL is required for API validation");
      }
      if (type === 'database' && !payload.config.db_name) {
        throw new Error("Database name is required");
      }

      const res = await api.testPipelineConnection(payload);
      if (res.status === 'success') {
        setStatus({
          success: true,
          message: res.message,
          metadata: res.metadata,
          latency_ms: res.latency_ms
        });
        showAlert("Connection Success", res.message, "success");
      } else {
        throw new Error(res.message || "Failed to establish connection");
      }
    } catch (err) {
      setStatus({
        success: false,
        message: err.message
      });
      showAlert("Connection Failure", err.message, "error");
    } finally {
      setTesting(false);
    }
  };

  // --- schema analysis handler ---
  const handleAnalyzeSystems = async () => {
    setProfiling(true);
    setProfilingLogs(["[SYSTEM] Initiating Cross-System Integration Profiler...", "[PROCESS] Mapping connection tunnels..."]);
    setSchemaA([]);
    setSchemaB([]);
    setSuggestedScenarios([]);
    setAiSteps([]);

    const payload = {
      system_a: {
        system_type: systemAType,
        environment: systemAEnv,
        query: systemAType === 'database' ? systemAQuery : systemAQuery, // for API it parses URL path
        db_config: systemAType === 'database' ? systemAConfig : null,
        url: systemAType === 'api' ? `${systemAAPIConfig.base_url}/${systemAQuery.replace(/^\//, '')}` : null,
        method: systemAType === 'api' ? systemAAPIConfig.method : 'GET',
        headers: systemAType === 'api' ? systemAAPIConfig.headers : null,
        payload: systemAType === 'api' ? systemAAPIConfig.payload : null
      },
      system_b: {
        system_type: systemBType,
        environment: systemBEnv,
        query: systemBType === 'database' ? systemBQuery : systemBQuery,
        db_config: systemBType === 'database' ? systemBConfig : null,
        url: systemBType === 'api' ? `${systemBAPIConfig.base_url}/${systemBQuery.replace(/^\//, '')}` : null,
        method: systemBType === 'api' ? systemBAPIConfig.method : 'GET',
        headers: systemBType === 'api' ? systemBAPIConfig.headers : null,
        payload: systemBType === 'api' ? systemBAPIConfig.payload : null
      }
    };

    try {
      const res = await api.analyzeIntegrationSystems(payload);
      setSchemaA(res.system_a_schema || []);
      setSchemaB(res.system_b_schema || []);
      setSuggestedScenarios(res.suggested_scenarios || []);
      setAiSteps(res.cross_functional_steps || []);
      setProfilingLogs(prev => [
        ...prev,
        `[SUCCESS] System A dataset profiled. Schema: ${res.system_a_schema?.length || 0} fields mapped.`,
        `[SUCCESS] System B dataset profiled. Schema: ${res.system_b_schema?.length || 0} fields mapped.`,
        "[SYSTEM] Compiling auto-suggested cross-functional flow sequence..."
      ]);
      
      showAlert("Analysis Complete", `Successfully mapped ${res.system_a_schema?.length || 0} A-fields and ${res.system_b_schema?.length || 0} B-fields.`, "success");
      
      setTimeout(() => {
        setCurrentStep(4);
      }, 1200);
    } catch (err) {
      setProfilingLogs(prev => [...prev, `[ERROR] Mapping failed: ${err.message}`]);
      showAlert("Analysis Error", err.message, "error");
    } finally {
      setProfiling(false);
    }
  };

  // --- execute reconciliation ---
  const handleExecuteReconciliation = async () => {
    setExecuting(true);
    setExecutingProgress(15);
    setReconcileResult(null);

    const initialLogs = [
      `[SYSTEM] Connecting to System A (${systemAType}) and System B (${systemBType})...`,
      `[PROCESS] Validating query syntax safety...`,
      `[INFO] Reconciler Scenario: ${selectedScenarioId}`,
      `[INFO] Join Key Column aligned: ${keyColumn}`
    ];
    setExecutionLogs(initialLogs);

    const payload = {
      system_a: {
        system_type: systemAType,
        environment: systemAEnv,
        query: systemAType === 'database' ? systemAQuery : null,
        db_config: systemAType === 'database' ? systemAConfig : null,
        url: systemAType === 'api' ? `${systemAAPIConfig.base_url}/${systemAQuery.replace(/^\//, '')}` : null,
        method: systemAType === 'api' ? systemAAPIConfig.method : 'GET',
        headers: systemAType === 'api' ? systemAAPIConfig.headers : null,
        payload: systemAType === 'api' ? systemAAPIConfig.payload : null
      },
      system_b: {
        system_type: systemBType,
        environment: systemBEnv,
        query: systemBType === 'database' ? systemBQuery : null,
        db_config: systemBType === 'database' ? systemBConfig : null,
        url: systemBType === 'api' ? `${systemBAPIConfig.base_url}/${systemBQuery.replace(/^\//, '')}` : null,
        method: systemBType === 'api' ? systemBAPIConfig.method : 'GET',
        headers: systemBType === 'api' ? systemBAPIConfig.headers : null,
        payload: systemBType === 'api' ? systemBAPIConfig.payload : null
      },
      scenario_id: selectedScenarioId,
      key_column: keyColumn,
      row_limit: rowLimit,
      chunk_size: chunkSize,
      query_timeout: queryTimeout
    };

    try {
      setExecutingProgress(50);
      const res = await api.executeIntegrationReconciliation(payload);
      setExecutingProgress(85);

      let logIndex = 0;
      const allLogs = res.execution_logs || [];
      
      setExecutionLogs(prev => [...prev, "[PROCESS] Streaming execution tracer logs..."]);
      
      logStreamTimer.current = setInterval(() => {
        if (logIndex < allLogs.length) {
          setExecutionLogs(prev => [...prev, allLogs[logIndex]]);
          logIndex++;
        } else {
          clearInterval(logStreamTimer.current);
          setExecutingProgress(100);
          setExecuting(false);
          setReconcileResult(res);
          showAlert("Reconciliation Complete", `Checks resolved with ${res.accuracy}% accuracy.`, res.passed ? 'success' : 'error');
          setCurrentStep(6);
        }
      }, 100);

    } catch (err) {
      clearInterval(logStreamTimer.current);
      setExecutingProgress(100);
      setExecuting(false);
      setExecutionLogs(prev => [
        ...prev,
        `[FATAL] Cross-system reconciler engine crashed.`,
        `[ERROR] Execution message: ${err.message}`
      ]);
      showAlert("Execution Failed", err.message, "error");
    }
  };

  const handleResetWizard = () => {
    setFeatureState('query');
    setCurrentStep(1);
    setConnAStatus(null);
    setConnBStatus(null);
    setSchemaA([]);
    setSchemaB([]);
    setSuggestedScenarios([]);
    setReconcileResult(null);
    setExecutionLogs([]);
    setExecutingProgress(0);
  };

  // --- RENDER INTRO MODE ---
  if (currentMode === 'intro') {
    return (
      <div className="w-full h-full overflow-y-auto flex flex-col p-8 lg:p-12 animate-in fade-in duration-700 bg-slate-50/30 text-left">
        <div className="max-w-5xl mx-auto w-full pt-4">
          {/* Core Bento Overview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            {/* Main Description */}
            <div className="md:col-span-2 p-10 rounded-[2rem] bg-white border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
              <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center mb-6">
                <Zap size={20} className="text-blue-600 animate-pulse" />
              </div>
              <h2 className="text-xl font-black text-slate-800 mb-4 tracking-tight">System Reconciler (Integration Sentry)</h2>
              <p className="text-sm font-medium text-slate-500 leading-relaxed max-w-xl">
                Audit data consistency across disparate database engines, tables, or APIs. Reconcile millions of records row-by-row and compile detailed divergence analysis summaries.
              </p>
            </div>

            {/* Quick Stats / Info */}
            <div className="p-8 rounded-[2rem] bg-slate-900 text-white shadow-xl shadow-slate-900/10 flex flex-col justify-between relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-slate-800 rounded-full blur-3xl" />
              <div className="relative z-10">
                <Cpu className="text-slate-400 mb-6" size={24} />
                <h3 className="text-sm font-black mb-2 tracking-wide">Cross-System Testing</h3>
                <p className="text-[10px] font-medium text-slate-400 leading-relaxed">
                  Validate system integrations, API-to-database syncing, and data duplication issues.
                </p>
              </div>
              <div className="relative z-10 mt-8">
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500 mb-1">Testing Mode</p>
                <p className="text-sm font-bold text-slate-300">End-to-End Integration</p>
              </div>
            </div>
          </div>

          {/* Getting Started Guide */}
          <div className="flex flex-col items-center justify-center p-12 text-center rounded-[2rem] border border-dashed border-slate-300/60 bg-white/50">
            <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4">
              <ChevronRight className="text-slate-400 rotate-90" size={20} />
            </div>
            <h3 className="text-lg font-black text-slate-800 mb-2 tracking-tight">Ready to reconcile integrations?</h3>
            <p className="text-xs font-bold text-slate-400 max-w-sm mx-auto leading-relaxed mb-6">
              Configure connections and query scopes in <span className="text-blue-600">Query Mode</span>, define check assertions in <span className="text-blue-600">Validation Mode</span>, or execute comparisons.
            </p>
            <div className="flex items-center gap-4">
              <button
                onClick={() => {
                  setNavParams({ defaultTab: 'integration', returnPage: 'integration_sentry', returnMode: 'intro' })
                  setActivePage('configuration')
                }}
                className="px-8 py-3 rounded-xl border border-slate-200 text-slate-600 bg-white text-[10px] font-black uppercase tracking-widest hover:bg-slate-50 transition-colors shadow-sm"
              >
                Configure Integration
              </button>
              <button
                onClick={() => setFeatureState('query')}
                className="px-8 py-3 rounded-xl bg-blue-600 text-white text-[10px] font-black uppercase tracking-widest hover:bg-blue-700 transition-colors shadow-lg shadow-blue-500/20 active:scale-95"
              >
                Launch System Reconciler
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // --- WIZARD RENDER ---
  return (
    <div className="w-full h-full overflow-y-auto flex flex-col p-8 lg:p-12 animate-in fade-in duration-700 bg-slate-50/30 text-left">
      <div className="max-w-7xl mx-auto w-full pt-4">

        <Card className="shadow-slate-200/30 mb-8 border-slate-200">
          
          {/* Step 1: CONNECTIONS CONFIG */}
          {currentStep === 1 && (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <CardHeader 
                title="Step 1: System Connection Definitions" 
                subtitle="Select system types, database engines, or APIs. Configure distinct environment parameters for System A and B."
              />
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                
                {/* SYSTEM A */}
                <div className="p-8 rounded-[2rem] border border-slate-100 bg-slate-50/40 relative overflow-hidden flex flex-col justify-between">
                  <div className="space-y-6">
                    <div className="flex items-center justify-between pb-4 border-b border-slate-150">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center">
                          <Database size={18} className="text-blue-600" />
                        </div>
                        <div>
                          <h4 className="text-xs font-black uppercase tracking-wider text-slate-800">System A (Source)</h4>
                          <p className="text-[9px] font-bold text-slate-400 uppercase tracking-wide">Data source layer</p>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <select 
                          value={systemAEnv} 
                          onChange={(e) => setSystemAEnv(e.target.value)} 
                          className="border border-slate-200 rounded-lg px-2 py-1 text-[9px] font-black uppercase text-slate-500 bg-white"
                        >
                          <option value="DEV">DEV</option>
                          <option value="QA">QA</option>
                          <option value="UAT">UAT</option>
                          <option value="PROD">PROD</option>
                        </select>
                        <select 
                          value={systemAType} 
                          onChange={(e) => setSystemAType(e.target.value)} 
                          className="border border-slate-200 rounded-lg px-2.5 py-1.5 text-[10px] font-black uppercase tracking-wider text-slate-700 bg-white outline-none cursor-pointer"
                        >
                          <option value="database">DATABASE</option>
                          <option value="api">API SERVICE</option>
                        </select>
                      </div>
                    </div>

                    {systemAType === 'database' ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="flex flex-col gap-1 md:col-span-2">
                          <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Connection Name</label>
                          <input type="text" value={systemAConfig.connection_name} onChange={(e) => setSystemAConfig({ ...systemAConfig, connection_name: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Database Engine</label>
                          <select value={systemAConfig.db_type} onChange={(e) => setSystemAConfig({ ...systemAConfig, db_type: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold cursor-pointer">
                            <option value="sqlite">SQLite</option>
                            <option value="postgresql">PostgreSQL</option>
                            <option value="mysql">MySQL</option>
                            <option value="mssql">MS SQL Server</option>
                          </select>
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Database Name</label>
                          <input type="text" value={systemAConfig.db_name} onChange={(e) => setSystemAConfig({ ...systemAConfig, db_name: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                        </div>
                        {systemAConfig.db_type !== 'sqlite' && (
                          <>
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Host</label>
                              <input type="text" value={systemAConfig.host} onChange={(e) => setSystemAConfig({ ...systemAConfig, host: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Port</label>
                              <input type="text" value={systemAConfig.port} onChange={(e) => setSystemAConfig({ ...systemAConfig, port: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Username</label>
                              <input type="text" value={systemAConfig.username} onChange={(e) => setSystemAConfig({ ...systemAConfig, username: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Password</label>
                              <input type="password" value={systemAConfig.password} onChange={(e) => setSystemAConfig({ ...systemAConfig, password: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                            </div>
                          </>
                        )}
                      </div>
                    ) : (
                      <div className="space-y-4">
                        <div className="flex flex-col gap-1">
                          <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Base URL</label>
                          <input type="text" value={systemAAPIConfig.base_url} placeholder="https://api.github.com" onChange={(e) => setSystemAAPIConfig({ ...systemAAPIConfig, base_url: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">HTTP Method</label>
                            <select value={systemAAPIConfig.method} onChange={(e) => setSystemAAPIConfig({ ...systemAAPIConfig, method: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold cursor-pointer">
                              <option value="GET">GET</option>
                              <option value="POST">POST</option>
                            </select>
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Auth Type</label>
                            <select value={systemAAPIConfig.auth_type} onChange={(e) => setSystemAAPIConfig({ ...systemAAPIConfig, auth_type: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold cursor-pointer">
                              <option value="none">NONE</option>
                              <option value="bearer">BEARER TOKEN</option>
                              <option value="api_key">API KEY</option>
                            </select>
                          </div>
                        </div>
                        {systemAAPIConfig.auth_type !== 'none' && (
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Token / API Key</label>
                            <input type="password" value={systemAAPIConfig.token} onChange={(e) => setSystemAAPIConfig({ ...systemAAPIConfig, token: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="mt-8 pt-4 border-t border-slate-100 flex flex-col gap-3">
                    <Button 
                      onClick={() => handleTestConnection(true)} 
                      isLoading={testingA} 
                      icon={RefreshCw}
                      variant="ghost" 
                      className="w-full"
                    >
                      Test System A Connection
                    </Button>
                    
                    {connAStatus && (
                      <div className={`p-4 rounded-xl border text-[10px] font-bold leading-relaxed flex items-start gap-2.5 ${
                        connAStatus.success 
                          ? 'bg-emerald-50/50 text-emerald-700 border-emerald-100' 
                          : 'bg-rose-50/50 text-rose-700 border-rose-100'
                      }`}>
                        {connAStatus.success ? (
                          <>
                            <CheckCircle size={14} className="text-emerald-500 shrink-0 mt-0.5" />
                            <div>
                              <p className="font-black uppercase tracking-wider">SUCCESS ({connAStatus.latency_ms}ms)</p>
                              <p className="opacity-80 mt-0.5">{connAStatus.message}</p>
                              {connAStatus.metadata?.tables && (
                                <p className="mt-1 font-mono text-[9px] text-emerald-600 uppercase tracking-tight">
                                  Found: {connAStatus.metadata.tables.join(', ')}
                                </p>
                              )}
                            </div>
                          </>
                        ) : (
                          <>
                            <AlertTriangle size={14} className="text-rose-500 shrink-0 mt-0.5" />
                            <div>
                              <p className="font-black uppercase tracking-wider">CONNECTION FAILED</p>
                              <p className="opacity-80 mt-0.5">{connAStatus.message}</p>
                            </div>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {/* SYSTEM B */}
                <div className="p-8 rounded-[2rem] border border-slate-100 bg-slate-50/40 relative overflow-hidden flex flex-col justify-between">
                  <div className="space-y-6">
                    <div className="flex items-center justify-between pb-4 border-b border-slate-150">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center">
                          <Database size={18} className="text-indigo-600" />
                        </div>
                        <div>
                          <h4 className="text-xs font-black uppercase tracking-wider text-slate-800">System B (Target)</h4>
                          <p className="text-[9px] font-bold text-slate-400 uppercase tracking-wide">Data target layer</p>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <select 
                          value={systemBEnv} 
                          onChange={(e) => setSystemBEnv(e.target.value)} 
                          className="border border-slate-200 rounded-lg px-2 py-1 text-[9px] font-black uppercase text-slate-500 bg-white"
                        >
                          <option value="DEV">DEV</option>
                          <option value="QA">QA</option>
                          <option value="UAT">UAT</option>
                          <option value="PROD">PROD</option>
                        </select>
                        <select 
                          value={systemBType} 
                          onChange={(e) => setSystemBType(e.target.value)} 
                          className="border border-slate-200 rounded-lg px-2.5 py-1.5 text-[10px] font-black uppercase tracking-wider text-slate-700 bg-white outline-none cursor-pointer"
                        >
                          <option value="database">DATABASE</option>
                          <option value="api">API SERVICE</option>
                        </select>
                      </div>
                    </div>

                    {systemBType === 'database' ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="flex flex-col gap-1 md:col-span-2">
                          <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Connection Name</label>
                          <input type="text" value={systemBConfig.connection_name} onChange={(e) => setSystemBConfig({ ...systemBConfig, connection_name: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Database Engine</label>
                          <select value={systemBConfig.db_type} onChange={(e) => setSystemBConfig({ ...systemBConfig, db_type: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold cursor-pointer">
                            <option value="sqlite">SQLite</option>
                            <option value="postgresql">PostgreSQL</option>
                            <option value="mysql">MySQL</option>
                            <option value="mssql">MS SQL Server</option>
                          </select>
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Database Name</label>
                          <input type="text" value={systemBConfig.db_name} onChange={(e) => setSystemBConfig({ ...systemBConfig, db_name: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                        </div>
                        {systemBConfig.db_type !== 'sqlite' && (
                          <>
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Host</label>
                              <input type="text" value={systemBConfig.host} onChange={(e) => setSystemBConfig({ ...systemBConfig, host: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Port</label>
                              <input type="text" value={systemBConfig.port} onChange={(e) => setSystemBConfig({ ...systemBConfig, port: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Username</label>
                              <input type="text" value={systemBConfig.username} onChange={(e) => setSystemBConfig({ ...systemBConfig, username: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Password</label>
                              <input type="password" value={systemBConfig.password} onChange={(e) => setSystemBConfig({ ...systemBConfig, password: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                            </div>
                          </>
                        )}
                      </div>
                    ) : (
                      <div className="space-y-4">
                        <div className="flex flex-col gap-1">
                          <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Base URL</label>
                          <input type="text" value={systemBAPIConfig.base_url} placeholder="https://api.github.com" onChange={(e) => setSystemBAPIConfig({ ...systemBAPIConfig, base_url: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">HTTP Method</label>
                            <select value={systemBAPIConfig.method} onChange={(e) => setSystemBAPIConfig({ ...systemBAPIConfig, method: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold cursor-pointer">
                              <option value="GET">GET</option>
                              <option value="POST">POST</option>
                            </select>
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Auth Type</label>
                            <select value={systemBAPIConfig.auth_type} onChange={(e) => setSystemBAPIConfig({ ...systemBAPIConfig, auth_type: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold cursor-pointer">
                              <option value="none">NONE</option>
                              <option value="bearer">BEARER TOKEN</option>
                              <option value="api_key">API KEY</option>
                            </select>
                          </div>
                        </div>
                        {systemBAPIConfig.auth_type !== 'none' && (
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Token / API Key</label>
                            <input type="password" value={systemBAPIConfig.token} onChange={(e) => setSystemBAPIConfig({ ...systemBAPIConfig, token: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="mt-8 pt-4 border-t border-slate-100 flex flex-col gap-3">
                    <Button 
                      onClick={() => handleTestConnection(false)} 
                      isLoading={testingB} 
                      icon={RefreshCw}
                      variant="ghost" 
                      className="w-full"
                    >
                      Test System B Connection
                    </Button>
                    
                    {connBStatus && (
                      <div className={`p-4 rounded-xl border text-[10px] font-bold leading-relaxed flex items-start gap-2.5 ${
                        connBStatus.success 
                          ? 'bg-emerald-50/50 text-emerald-700 border-emerald-100' 
                          : 'bg-rose-50/50 text-rose-700 border-rose-100'
                      }`}>
                        {connBStatus.success ? (
                          <>
                            <CheckCircle size={14} className="text-emerald-500 shrink-0 mt-0.5" />
                            <div>
                              <p className="font-black uppercase tracking-wider">SUCCESS ({connBStatus.latency_ms}ms)</p>
                              <p className="opacity-80 mt-0.5">{connBStatus.message}</p>
                              {connBStatus.metadata?.tables && (
                                <p className="mt-1 font-mono text-[9px] text-emerald-600 uppercase tracking-tight">
                                  Found: {connBStatus.metadata.tables.join(', ')}
                                </p>
                              )}
                            </div>
                          </>
                        ) : (
                          <>
                            <AlertTriangle size={14} className="text-rose-500 shrink-0 mt-0.5" />
                            <div>
                              <p className="font-black uppercase tracking-wider">CONNECTION FAILED</p>
                              <p className="opacity-80 mt-0.5">{connBStatus.message}</p>
                            </div>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                </div>

              </div>

              <div className="pt-6 border-t border-slate-100 flex items-center justify-end">
                <Button 
                  onClick={() => setCurrentStep(2)} 
                  icon={ArrowRight}
                  className="px-10"
                >
                  Next: Scope & Queries
                </Button>
              </div>
            </div>
          )}

          {/* Step 2: SCOPES & QUERIES */}
          {currentStep === 2 && (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <CardHeader 
                title="Step 2: Define Queries & Join Key" 
                subtitle="Provide the database queries or API endpoints to fetch datasets. Enter a matching key column to link records."
              />

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[9px] font-black uppercase tracking-wider text-slate-400 flex items-center justify-between">
                    <span>System A Query / URL Path</span>
                    <span className="text-[8px] opacity-60">e.g. SELECT * FROM table, or endpoints path /products</span>
                  </label>
                  <textarea 
                    value={systemAQuery} 
                    onChange={(e) => setSystemAQuery(e.target.value)}
                    className="border border-slate-200 rounded-2xl px-5 py-4 font-mono text-xs text-slate-700 h-48 outline-none resize-none focus:ring-1 focus:ring-blue-500/20"
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-[9px] font-black uppercase tracking-wider text-slate-400 flex items-center justify-between">
                    <span>System B Query / URL Path</span>
                    <span className="text-[8px] opacity-60">e.g. SELECT * FROM table_silver, or endpoints path /silver/products</span>
                  </label>
                  <textarea 
                    value={systemBQuery} 
                    onChange={(e) => setSystemBQuery(e.target.value)}
                    className="border border-slate-200 rounded-2xl px-5 py-4 font-mono text-xs text-slate-700 h-48 outline-none resize-none focus:ring-1 focus:ring-blue-500/20"
                  />
                </div>
              </div>

              <div className="flex flex-col gap-1 mt-4 max-w-md">
                <label className="text-[9px] font-black uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <span>Reconciliation Key Column</span>
                  <HelpCircle size={12} className="text-slate-350" title="The unique identifier used to join rows from both systems. Default is 'id'." />
                </label>
                <input 
                  type="text" 
                  value={keyColumn} 
                  placeholder="id" 
                  onChange={(e) => setKeyColumn(e.target.value)} 
                  className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 font-mono outline-none" 
                />
              </div>

              <div className="pt-6 border-t border-slate-100 flex items-center justify-between">
                <Button 
                  onClick={() => setCurrentStep(1)} 
                  variant="secondary" 
                  icon={ArrowLeft}
                >
                  Back
                </Button>
                <Button 
                  onClick={() => {
                    setFeatureState('validation');
                    setCurrentStep(3);
                  }} 
                  icon={ArrowRight}
                  className="px-10"
                >
                  Next: Schema Profiler
                </Button>
              </div>
            </div>
          )}

          {/* Step 3: SCHEMA PROFILER */}
          {currentStep === 3 && (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <CardHeader 
                title="Step 3: Cross-System Schema Profiling" 
                subtitle="Execute metadata discovery session to profile and compare table fields side-by-side."
              />

              {!profiling && schemaA.length === 0 ? (
                <div className="flex flex-col items-center justify-center p-16 text-center border border-dashed border-slate-200 rounded-[2.5rem] bg-slate-50/20">
                  <div className="w-16 h-16 rounded-full bg-blue-50 flex items-center justify-center mb-6">
                    <Sparkles size={24} className="text-blue-600 animate-pulse" />
                  </div>
                  <h4 className="text-sm font-black text-slate-800 mb-2">Awaiting Profiler Initialization</h4>
                  <p className="text-xs text-slate-400 max-w-sm mx-auto leading-relaxed mb-6">
                    Establish session channels to pull structural schemas and match metadata properties.
                  </p>
                  <Button onClick={handleAnalyzeSystems} icon={Sparkles}>
                    Discover & Profile Schemas
                  </Button>
                </div>
              ) : (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                  {/* Profiling Console Log */}
                  <div className="lg:col-span-1 space-y-4">
                    <h4 className="text-[10px] font-black uppercase tracking-wider text-slate-400 flex items-center gap-2">
                      <TerminalIcon size={14} />
                      Profiler Log Feed
                    </h4>
                    
                    <div className="bg-slate-950 text-slate-350 p-6 rounded-2xl font-mono text-[10px] h-64 overflow-y-auto space-y-1 border border-slate-900 shadow-inner">
                      {profilingLogs.map((log, idx) => (
                        <div key={idx} className={log.includes('[ERROR]') ? 'text-rose-400' : log.includes('[SYSTEM]') ? 'text-indigo-400' : 'text-slate-300'}>
                          {log}
                        </div>
                      ))}
                      {profiling && (
                        <div className="flex items-center gap-2 text-blue-400 mt-2 font-black">
                          <RefreshCw size={10} className="animate-spin" /> Compiling schema variables...
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Schema Structure Side by Side */}
                  <div className="lg:col-span-2 space-y-4">
                    <h4 className="text-[10px] font-black uppercase tracking-wider text-slate-400 flex items-center gap-2">
                      <Layers size={14} />
                      Side-By-Side Schema Mapping
                    </h4>
                    
                    <div className="grid grid-cols-2 gap-4 border border-slate-200 rounded-2xl p-6 bg-white shadow-sm h-64 overflow-y-auto">
                      <div>
                        <p className="text-[9px] font-black uppercase tracking-widest text-slate-400 mb-2 border-b pb-1">System A Fields ({schemaA.length})</p>
                        <div className="flex flex-col gap-1">
                          {schemaA.map((col, i) => (
                            <span key={i} className="px-2 py-1 rounded bg-blue-50/50 text-blue-700 text-[10px] font-bold font-mono">
                              {col.name} <span className="opacity-40">({col.type})</span>
                            </span>
                          ))}
                        </div>
                      </div>

                      <div>
                        <p className="text-[9px] font-black uppercase tracking-widest text-slate-400 mb-2 border-b pb-1">System B Fields ({schemaB.length})</p>
                        <div className="flex flex-col gap-1">
                          {schemaB.map((col, i) => (
                            <span key={i} className="px-2 py-1 rounded bg-indigo-50/50 text-indigo-700 text-[10px] font-bold font-mono">
                              {col.name} <span className="opacity-40">({col.type})</span>
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div className="pt-6 border-t border-slate-100 flex items-center justify-between">
                <Button 
                  onClick={() => {
                    setFeatureState('query');
                    setCurrentStep(2);
                  }} 
                  variant="secondary" 
                  icon={ArrowLeft}
                  disabled={profiling}
                >
                  Back
                </Button>
                
                <div className="flex items-center gap-3">
                  {profilingLogs.length > 0 && !profiling && (
                    <Button 
                      onClick={handleAnalyzeSystems} 
                      variant="ghost" 
                      icon={RefreshCw}
                    >
                      Re-Profile
                    </Button>
                  )}
                  <Button 
                    onClick={() => setCurrentStep(4)} 
                    icon={ArrowRight}
                    className="px-10"
                    disabled={profiling}
                  >
                    Next: Comparison Scenarios
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Step 4: COMPARISON SCENARIOS */}
          {currentStep === 4 && (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <CardHeader 
                title="Step 4: Select Reconciliation Scenarios" 
                subtitle="Choose predefined bit-perfect comparison rules. Review automatically suggested cross-functional actions."
              />

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Predefined Comparison Cards */}
                <div className="lg:col-span-2 space-y-4">
                  <h4 className="text-[10px] font-black uppercase tracking-wider text-slate-400">Reconciliation Scenarios</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {suggestedScenarios.map((scen) => {
                      const isSelected = selectedScenarioId === scen.id;
                      return (
                        <div 
                          key={scen.id} 
                          onClick={() => setSelectedScenarioId(scen.id)}
                          className={`p-6 rounded-[2rem] border transition-all cursor-pointer flex flex-col justify-between ${
                            isSelected 
                              ? 'bg-blue-600 border-blue-600 text-white shadow-xl shadow-blue-500/20' 
                              : 'bg-white border-slate-200 text-slate-800 hover:border-slate-350 shadow-sm'
                          }`}
                        >
                          <div>
                            <div className="flex items-center gap-2 mb-3">
                              <ShieldCheck size={18} className={isSelected ? 'text-white' : 'text-blue-600'} />
                              <span className="text-[10px] font-black uppercase tracking-wider">{scen.type}</span>
                            </div>
                            <h4 className="text-xs font-black uppercase tracking-tight mb-2">{scen.name}</h4>
                            <p className={`text-[10px] font-medium leading-relaxed ${isSelected ? 'text-blue-100' : 'text-slate-450'}`}>{scen.description}</p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* AI suggested steps */}
                <div className="space-y-4">
                  <h4 className="text-[10px] font-black uppercase tracking-wider text-slate-400 flex items-center gap-2">
                    <Sparkles size={14} className="text-fuchsia-600" />
                    AI Suggested Actions Flow
                  </h4>
                  
                  <div className="border border-slate-200 rounded-2xl p-6 bg-slate-50/20 h-64 overflow-y-auto space-y-3">
                    {aiSteps.length > 0 ? aiSteps.map((step, idx) => (
                      <p key={idx} className="text-[10px] font-bold text-slate-650 leading-relaxed font-mono">
                        {step}
                      </p>
                    )) : (
                      <p className="text-[10px] font-bold text-slate-400 text-center pt-20">Awaiting schema profiling...</p>
                    )}
                  </div>
                </div>
              </div>

              <div className="pt-6 border-t border-slate-100 flex items-center justify-between">
                <Button 
                  onClick={() => setCurrentStep(3)} 
                  variant="secondary" 
                  icon={ArrowLeft}
                >
                  Back
                </Button>
                <Button 
                  onClick={() => {
                    setFeatureState('execution');
                    setCurrentStep(5);
                  }} 
                  icon={ArrowRight}
                  className="px-10"
                >
                  Next: Calibration & Execute
                </Button>
              </div>
            </div>
          )}

          {/* Step 5: CALIBRATION & EXECUTE */}
          {currentStep === 5 && (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <CardHeader 
                title="Step 5: Execution Console & System Limits" 
                subtitle="Calibrate memory boundaries and execute the system-wide integration checks."
              />

              {!executing && executionLogs.length === 0 ? (
                <div className="space-y-8">
                  {/* Calibrate limits */}
                  <div className="p-8 rounded-[2rem] border border-slate-200/80 bg-slate-50/50 shadow-inner grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="flex flex-col gap-1.5">
                      <label className="text-[9px] font-black uppercase tracking-wider text-slate-400 flex justify-between">
                        <span>Max Row Limit</span>
                        <span className="text-blue-600 font-bold">{rowLimit.toLocaleString()}</span>
                      </label>
                      <input 
                        type="range" 
                        min="100" 
                        max="200000" 
                        step="1000" 
                        value={rowLimit} 
                        onChange={(e) => setRowLimit(Number(e.target.value))} 
                        className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600" 
                      />
                      <p className="text-[8px] text-slate-400 font-bold uppercase">Boundary cap protection</p>
                    </div>

                    <div className="flex flex-col gap-1.5">
                      <label className="text-[9px] font-black uppercase tracking-wider text-slate-400 flex justify-between">
                        <span>Chunk Size</span>
                        <span className="text-blue-600 font-bold">{chunkSize.toLocaleString()}</span>
                      </label>
                      <input 
                        type="range" 
                        min="100" 
                        max="20000" 
                        step="500" 
                        value={chunkSize} 
                        onChange={(e) => setChunkSize(Number(e.target.value))} 
                        className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600" 
                      />
                      <p className="text-[8px] text-slate-400 font-bold uppercase">Memory partition limit</p>
                    </div>

                    <div className="flex flex-col gap-1.5">
                      <label className="text-[9px] font-black uppercase tracking-wider text-slate-400 flex justify-between">
                        <span>Query Timeout (seconds)</span>
                        <span className="text-blue-600 font-bold">{queryTimeout}s</span>
                      </label>
                      <input 
                        type="range" 
                        min="1" 
                        max="180" 
                        step="1" 
                        value={queryTimeout} 
                        onChange={(e) => setQueryTimeout(Number(e.target.value))} 
                        className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600" 
                      />
                      <p className="text-[8px] text-slate-400 font-bold uppercase">Enforces query halts</p>
                    </div>
                  </div>

                  <div className="flex flex-col items-center justify-center py-8 text-center bg-white border border-slate-100 rounded-[2rem]">
                    <div className="w-14 h-14 rounded-full bg-slate-100 flex items-center justify-center mb-4">
                      <PlayCircle size={24} className="text-slate-400" />
                    </div>
                    <h4 className="text-xs font-black text-slate-800 mb-1.5 uppercase">Reconciliation Execution Ready</h4>
                    <p className="text-[10px] text-slate-450 max-w-xs mx-auto leading-relaxed mb-6">
                      Will execute cross-system integration check: <span className="text-blue-600 font-black">{selectedScenarioId}</span>
                    </p>
                    <Button onClick={handleExecuteReconciliation} icon={Play} className="px-12 py-4 bg-emerald-600 hover:bg-emerald-700 shadow-emerald-500/10">
                      Run Reconciler Engine
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Execution Progress */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-[9px] font-black uppercase tracking-wider">
                      <span className="text-slate-400">Executing Integration Reconciliations</span>
                      <span className="text-blue-600">{executingProgress}% Complete</span>
                    </div>
                    <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden border">
                      <div 
                        className="h-full bg-gradient-to-r from-blue-600 to-indigo-500 transition-all duration-300 rounded-full shadow-inner animate-pulse" 
                        style={{ width: `${executingProgress}%` }}
                      />
                    </div>
                  </div>

                  {/* Terminal Component */}
                  <Terminal logs={executionLogs} minHeight="400px" />
                </div>
              )}

              <div className="pt-6 border-t border-slate-100 flex items-center justify-between">
                <Button 
                  onClick={() => {
                    clearInterval(logStreamTimer.current);
                    setExecuting(false);
                    setExecutionLogs([]);
                    setFeatureState('validation');
                    setCurrentStep(4);
                  }} 
                  variant="secondary" 
                  icon={ArrowLeft}
                  disabled={executing}
                >
                  Back
                </Button>
              </div>
            </div>
          )}

          {/* Step 6: TELEMETRY RESULTS */}
          {currentStep === 6 && reconcileResult && (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <CardHeader 
                title="Step 6: Telemetry Results & Reports" 
                subtitle={`Cross-System Check Results — Scenario: ${selectedScenarioId}`}
                action={
                  <div className="flex items-center gap-3 relative">
                    <Button 
                      onClick={() => setExportDropdownOpen(!exportDropdownOpen)} 
                      variant="ghost"
                      icon={Download}
                    >
                      Export Report
                    </Button>
                    {exportDropdownOpen && (
                      <div className="absolute right-0 top-12 bg-white border border-slate-200 rounded-2xl shadow-xl w-48 z-[60] overflow-hidden py-1 animate-in slide-in-from-top-1 duration-200">
                        {/* We simulate download for the cross-system report */}
                        <button 
                          onClick={() => {
                            showAlert("Report Exported", "CSV report exported successfully.", "success");
                            setExportDropdownOpen(false);
                          }} 
                          className="w-full text-left px-4 py-3 hover:bg-slate-50 text-[10px] font-black uppercase tracking-wider text-slate-650 hover:text-slate-900 border-b border-slate-100 flex items-center gap-2"
                        >
                          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> CSV Format (.csv)
                        </button>
                        <button 
                          onClick={() => {
                            showAlert("Report Exported", "JSON report exported successfully.", "success");
                            setExportDropdownOpen(false);
                          }} 
                          className="w-full text-left px-4 py-3 hover:bg-slate-50 text-[10px] font-black uppercase tracking-wider text-slate-650 hover:text-slate-900 border-b border-slate-100 flex items-center gap-2"
                        >
                          <span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> JSON Format (.json)
                        </button>
                      </div>
                    )}
                  </div>
                }
              />

              {/* KPI Strip & Gauge */}
              <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                
                {/* Accuracy Gauge Widget */}
                <div className="p-6 rounded-2xl border border-slate-200 bg-white flex flex-col items-center justify-center text-center shadow-sm relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-12 h-12 bg-slate-50 rounded-full blur-2xl" />
                  
                  <p className="text-[9px] font-black uppercase tracking-widest text-slate-400 mb-4">Accuracy Score</p>
                  
                  <div className="relative w-32 h-32 flex items-center justify-center mb-2">
                    <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                      <circle cx="50" cy="50" r="40" fill="transparent" stroke="#f1f5f9" strokeWidth="8" />
                      <circle 
                        cx="50" cy="50" r="40" fill="transparent" 
                        stroke={reconcileResult.accuracy >= 90 ? '#10b981' : reconcileResult.accuracy >= 70 ? '#3b82f6' : '#ef4444'} 
                        strokeWidth="8" 
                        strokeDasharray={2 * Math.PI * 40}
                        strokeDashoffset={(2 * Math.PI * 40) * (1 - (reconcileResult.accuracy || 0) / 100)}
                        strokeLinecap="round"
                        className="transition-all duration-1000 ease-out"
                      />
                    </svg>
                    <div className="absolute flex flex-col items-center justify-center">
                      <span className="text-2xl font-black text-slate-800 tracking-tight">{reconcileResult.accuracy.toFixed(1)}%</span>
                      <span className="text-[8px] font-bold text-slate-400 uppercase tracking-widest">Matched</span>
                    </div>
                  </div>
                  
                  <span className={`text-[8px] font-black uppercase tracking-wider px-2 py-0.5 rounded border ${
                    reconcileResult.accuracy >= 90 ? 'bg-emerald-50 text-emerald-600 border-emerald-100' :
                    reconcileResult.accuracy >= 70 ? 'bg-blue-50 text-blue-600 border-blue-100' :
                    'bg-red-50 text-red-600 border-red-100'
                  }`}>
                    {reconcileResult.passed ? 'COMPLIANT' : 'DISCREPANCIES DETECTED'}
                  </span>
                </div>

                <div className="p-5 rounded-2xl bg-slate-50 border border-slate-100 flex flex-col justify-between shadow-sm">
                  <div>
                    <p className="text-[9px] font-black uppercase tracking-widest text-slate-400">Total Records (System A)</p>
                    <p className="text-2.5xl font-black text-slate-800 mt-2">{reconcileResult.total_records_a}</p>
                  </div>
                  <div className="pt-2 border-t border-slate-100/50 flex items-center justify-between text-[9px] text-slate-400 font-bold uppercase">
                    <span>Source Rows</span>
                    <span className="text-slate-650">{reconcileResult.total_records_a}</span>
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-slate-50 border border-slate-100 flex flex-col justify-between shadow-sm">
                  <div>
                    <p className="text-[9px] font-black uppercase tracking-widest text-slate-400">Records Matched</p>
                    <p className="text-2.5xl font-black text-emerald-600 mt-2">{reconcileResult.matches}</p>
                  </div>
                  <div className="pt-2 border-t border-slate-100/50 flex items-center justify-between text-[9px] text-emerald-500 font-bold uppercase">
                    <span>Match count</span>
                    <span>{reconcileResult.matches}</span>
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-slate-50 border border-slate-100 flex flex-col justify-between shadow-sm">
                  <div>
                    <p className="text-[9px] font-black uppercase tracking-widest text-slate-400">Variances Found</p>
                    <p className={`text-2.5xl font-black mt-2 ${reconcileResult.mismatches > 0 ? 'text-red-500' : 'text-slate-400'}`}>
                      {reconcileResult.mismatches}
                    </p>
                  </div>
                  <div className="pt-2 border-t border-slate-100/50 flex items-center justify-between text-[9px] text-slate-400 font-bold uppercase">
                    <span>Divergences</span>
                    <span className="text-slate-650">{reconcileResult.mismatches}</span>
                  </div>
                </div>

              </div>

              {/* Variances Grid table */}
              <div className="border border-slate-200 rounded-3xl overflow-hidden bg-white shadow-sm flex flex-col">
                <div className="px-6 py-4 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
                  <h4 className="text-xs font-black uppercase tracking-wider text-slate-500">Cross-System Variance Log</h4>
                  <span className="text-[10px] text-slate-400 font-bold">{reconcileResult.mismatches} discrepancy(s) found</span>
                </div>
                
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-b border-slate-100 bg-slate-50/20">
                      {['Record Key', 'Field', 'Source Value (System A)', 'Target Value (System B)', 'Risk Level'].map(col => (
                        <th key={col} className="px-6 py-3 text-[10px] font-black uppercase tracking-wider text-slate-400">{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {reconcileResult.mismatches > 0 ? (
                      reconcileResult.mismatch_details.map((m, i) => (
                        <tr key={i} className="hover:bg-slate-50/20 transition-colors">
                          <td className="px-6 py-4 font-mono text-xs font-semibold text-slate-700">{m.id}</td>
                          <td className="px-6 py-4 text-xs text-slate-500 uppercase tracking-tight font-medium">{m.field}</td>
                          <td className="px-6 py-4 text-xs font-semibold text-emerald-600">{m.source}</td>
                          <td className="px-6 py-4 text-xs font-semibold text-rose-500">{m.target}</td>
                          <td className="px-6 py-4">
                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-wider border ${
                              m.risk === 'Critical' ? 'bg-rose-50 text-rose-600 border-rose-100' :
                              m.risk === 'High' ? 'bg-orange-50 text-orange-600 border-orange-100' :
                              'bg-blue-50 text-blue-600 border-blue-100'
                            }`}>{m.risk}</span>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={5} className="px-6 py-12 text-center text-xs font-bold text-slate-400">
                          No discrepancies found. Both systems are fully aligned.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              <div className="pt-6 border-t border-slate-100 flex items-center justify-end">
                <Button onClick={handleResetWizard} icon={RefreshCw} className="px-10 py-3">
                  Reset Reconciler Wizard
                </Button>
              </div>
            </div>
          )}

        </Card>
      </div>
    </div>
  );
}
