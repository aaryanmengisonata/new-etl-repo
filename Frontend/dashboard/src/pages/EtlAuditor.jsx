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

export default function EtlAuditor() {
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
  // STEP 1: CONNECTIONS STATE
  // ----------------------------------------------------
  const [sourceType, setSourceType] = useState('database');
  const [sourceConfig, setSourceConfig] = useState({
    connection_name: 'Source_Database',
    db_type: 'sqlite',
    host: 'localhost',
    port: '5432',
    db_name: 'test_audit_src.db',
    username: '',
    password: ''
  });

  const [targetType, setTargetType] = useState('database');
  const [targetConfig, setTargetConfig] = useState({
    connection_name: 'Target_Database',
    db_type: 'sqlite',
    host: 'localhost',
    port: '5432',
    db_name: 'test_audit_tgt.db',
    username: '',
    password: ''
  });

  const [testingSource, setTestingSource] = useState(false);
  const [sourceConnStatus, setSourceConnStatus] = useState(null); // { success: bool, message, metadata, latency_ms }

  const [testingTarget, setTestingTarget] = useState(false);
  const [targetConnStatus, setTargetConnStatus] = useState(null);

  // ----------------------------------------------------
  // STEP 2: PIPELINE DETAILS STATE
  // ----------------------------------------------------
  const [pipelineName, setPipelineName] = useState('Medallion Reconciliation Pipeline');
  const [environment, setEnvironment] = useState('DEV');
  const [pipelineType, setPipelineType] = useState('BronzeToSilver');
  const [sourceQuery, setSourceQuery] = useState('SELECT * FROM products');
  const [targetQuery, setTargetQuery] = useState('SELECT * FROM products_silver');
  const [keyColumnsInput, setKeyColumnsInput] = useState('id');

  // ----------------------------------------------------
  // STEP 3 & 4: VALIDATION CHECKS STATE
  // ----------------------------------------------------
  const [analyzingSchema, setAnalyzingSchema] = useState(false);
  const [analysisLogs, setAnalysisLogs] = useState([]);
  const [sourceColumns, setSourceColumns] = useState([]);
  const [targetColumns, setTargetColumns] = useState([]);
  const [validationsList, setValidationsList] = useState([]); // List of ValidationDescriptor

  // Custom Validation Builder Form
  const [showBuilder, setShowBuilder] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [customVal, setCustomVal] = useState({
    id: '',
    name: '',
    type: 'null_check',
    severity: 'medium',
    enabled: true,
    column_name: '',
    aggregate_column: '',
    aggregate_function: 'SUM',
    source_sql: '',
    target_sql: '',
    description: ''
  });

  // ----------------------------------------------------
  // STEP 5: EXECUTION STATE
  // ----------------------------------------------------
  const [rowLimit, setRowLimit] = useState(10000);
  const [chunkSize, setChunkSize] = useState(2000);
  const [queryTimeout, setQueryTimeout] = useState(30);
  const [executing, setExecuting] = useState(false);
  const [executingProgress, setExecutingProgress] = useState(0);
  const [executionLogs, setExecutionLogs] = useState([]);
  const [completedAuditId, setCompletedAuditId] = useState(null);

  // ----------------------------------------------------
  // STEP 6: RESULTS STATE
  // ----------------------------------------------------
  const [auditResult, setAuditResult] = useState(null); // ExecutePipelineResponse
  const [exportDropdownOpen, setExportDropdownOpen] = useState(false);
  const [expandedResultId, setExpandedResultId] = useState(null);

  // Dynamic log streamer for slick presentation
  const logStreamTimer = useRef(null);

  // Clean up timers on unmount
  useEffect(() => {
    return () => clearInterval(logStreamTimer.current);
  }, []);

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
                <Sparkles size={20} className="text-blue-600" />
              </div>
              <h2 className="text-xl font-black text-slate-800 mb-4 tracking-tight">ETL Pipeline Auditor</h2>
              <p className="text-sm font-medium text-slate-500 leading-relaxed max-w-xl">
                Professional-grade Medallion architecture validation. Audit ETL data transformation rules, schema layouts, and record counts across Bronze, Silver, and Gold delta layers.
              </p>
            </div>

            {/* Quick Stats / Info */}
            <div className="p-8 rounded-[2rem] bg-slate-900 text-white shadow-xl shadow-slate-900/10 flex flex-col justify-between relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-slate-800 rounded-full blur-3xl" />
              <div className="relative z-10">
                <Layers className="text-slate-400 mb-6" size={24} />
                <h3 className="text-sm font-black mb-2 tracking-wide">Medallion Validation</h3>
                <p className="text-[10px] font-medium text-slate-400 leading-relaxed">
                  Verify transformations across Bronze → Silver → Gold layer reconciliations automatically.
                </p>
              </div>
              <div className="relative z-10 mt-8">
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500 mb-1">Architecture</p>
                <p className="text-sm font-bold text-slate-300">Reconciliation Layer</p>
              </div>
            </div>
          </div>

          {/* Getting Started Guide */}
          <div className="flex flex-col items-center justify-center p-12 text-center rounded-[2rem] border border-dashed border-slate-300/60 bg-white/50">
            <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4">
              <ChevronRight className="text-slate-400 rotate-90" size={20} />
            </div>
            <h3 className="text-lg font-black text-slate-800 mb-2 tracking-tight">Ready to audit your pipeline?</h3>
            <p className="text-xs font-bold text-slate-400 max-w-sm mx-auto leading-relaxed mb-6">
              Configure connections and query scopes in <span className="text-blue-600">Query Mode</span>, define check assertions in <span className="text-blue-600">Validation Mode</span>, or execute pipelines.
            </p>
            <div className="flex items-center gap-4">
              <button
                onClick={() => {
                  setNavParams({ defaultTab: 'pipeline', returnPage: 'etl_auditor', returnMode: 'intro' })
                  setActivePage('configuration')
                }}
                className="px-8 py-3 rounded-xl border border-slate-200 text-slate-600 bg-white text-[10px] font-black uppercase tracking-widest hover:bg-slate-50 transition-colors shadow-sm"
              >
                Configure Pipeline
              </button>
              <button
                onClick={() => setFeatureState('query')}
                className="px-8 py-3 rounded-xl bg-blue-600 text-white text-[10px] font-black uppercase tracking-widest hover:bg-blue-700 transition-colors shadow-lg shadow-blue-500/20 active:scale-95"
              >
                Launch Pipeline Auditor
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ----------------------------------------------------
  // API SERVICE CALLS
  // ----------------------------------------------------
  const handleTestConnection = async (isSource) => {
    const type = isSource ? sourceType : targetType;
    const config = isSource ? sourceConfig : targetConfig;
    const setTesting = isSource ? setTestingSource : setTestingTarget;
    const setStatus = isSource ? setSourceConnStatus : setTargetConnStatus;

    setTesting(true);
    setStatus(null);

    try {
      if (type === 'api' && !config.base_url) {
        throw new Error("Base URL is required for API validation");
      }
      if (type === 'database' && !config.db_name) {
        throw new Error("Database name is required");
      }

      const res = await api.testPipelineConnection({ type, config });
      if (res.status === 'success') {
        setStatus({
          success: true,
          message: res.message,
          metadata: res.metadata,
          latency_ms: res.latency_ms
        });
        showAlert("Connected Successfully", res.message, "success");
      } else {
        throw new Error(res.message || "Failed to establish connection");
      }
    } catch (err) {
      setStatus({
        success: false,
        message: err.message
      });
      showAlert("Connection Error", err.message, "error");
    } finally {
      setTesting(false);
    }
  };

  const handleAnalyzePipeline = async () => {
    setAnalyzingSchema(true);
    setAnalysisLogs(["[SYSTEM] Initializing schema validator...", "[PROCESS] Contacting source and target systems..."]);
    setSourceColumns([]);
    setTargetColumns([]);

    const keyCols = keyColumnsInput.split(',').map(s => s.trim()).filter(Boolean);

    try {
      const res = await api.analyzePipeline({
        source_type: sourceType,
        source_config: sourceConfig,
        target_type: targetType,
        target_config: targetConfig,
        source_query: sourceQuery,
        target_query: targetQuery,
        key_columns: keyCols,
        pipeline_name: pipelineName,
        environment,
        pipeline_type: pipelineType
      });

      if (res.status === 'success') {
        setAnalysisLogs(res.analysis_logs || []);
        setSourceColumns(res.source_columns || []);
        setTargetColumns(res.target_columns || []);
        
        // Merge suggestions or set validations list
        setValidationsList(res.suggestions || []);
        showAlert("Analysis Complete", `Successfully generated ${res.suggestions?.length || 0} checks.`, "success");
        // Automatically proceed to Step 4 after analysis
        setTimeout(() => {
          setCurrentStep(4);
        }, 1200);
      }
    } catch (err) {
      setAnalysisLogs(prev => [...prev, `[ERROR] Schema mapping failed: ${err.message}`]);
      showAlert("Analysis Failed", err.message, "error");

      // Load static defaults to ensure UI does not block
      const fallbackList = [
        { id: "RC_001", name: "Row Count Validation", type: "row_count", description: "Verify row count equality", severity: "critical", enabled: true },
        { id: "SV_001", name: "Schema Structure Check", type: "schema_validation", description: "Validate column compatibilities", severity: "high", enabled: true }
      ];
      if (keyCols.length > 0) {
        fallbackList.push({ id: "EM_001", name: `Exact Match on ${keyCols.join(', ')}`, type: "exact_match", description: "Row cell values check", severity: "critical", enabled: true });
        fallbackList.push({ id: "MR_001", name: "Missing Records Detection", type: "missing_records", description: "Identify orphaned key rows", severity: "critical", enabled: true });
      }
      setValidationsList(fallbackList);
    } finally {
      setAnalyzingSchema(false);
    }
  };

  const handleExecuteAudit = async () => {
    const keyCols = keyColumnsInput.split(',').map(s => s.trim()).filter(Boolean);
    const enabledValidations = validationsList.filter(v => v.enabled);

    if (enabledValidations.length === 0) {
      showAlert("No Checks Enabled", "Please enable or configure at least one check to execute.", "info");
      return;
    }

    setExecuting(true);
    setExecutingProgress(10);
    setCompletedAuditId(null);
    setAuditResult(null);

    // Initial log messages
    const initialLogs = [
      `[SYSTEM] Connecting to Source (${sourceType}) and Target (${targetType})...`,
      `[PROCESS] Validating SQL syntax safety...`,
      `[INFO] Reconciliation pipeline: ${pipelineName} [${pipelineType} | ${environment}]`,
      `[INFO] Key columns aligned: ${JSON.stringify(keyCols)}`,
      `[INFO] Selected Validations: ${enabledValidations.map(v => v.name).join(', ')}`
    ];
    setExecutionLogs(initialLogs);

    try {
      const payload = {
        pipeline_name: pipelineName,
        environment,
        pipeline_type: pipelineType,
        source_type: sourceType,
        source_config: sourceConfig,
        target_type: targetType,
        target_config: targetConfig,
        source_query: sourceQuery,
        target_query: targetQuery,
        key_columns: keyCols,
        validations: enabledValidations,
        row_limit: rowLimit,
        chunk_size: chunkSize,
        query_timeout: queryTimeout,
        execution_timeout: 300
      };

      setExecutingProgress(40);
      const res = await api.executePipelineAudit(payload);

      setExecutingProgress(85);
      
      // Stream logs nicely to give it a high-tech console feeling
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
          setAuditResult(res);
          setCompletedAuditId(res.audit_id);
          showAlert("Audit Completed", `Pipeline Auditor reconciled ${res.summary?.passed_checks}/${res.summary?.total_checks} checks.`, res.status === 'success' ? 'success' : 'error');
          // Navigate to step 6
          setCurrentStep(6);
        }
      }, 100);

    } catch (err) {
      clearInterval(logStreamTimer.current);
      setExecutingProgress(100);
      setExecuting(false);
      setExecutionLogs(prev => [
        ...prev,
        `[FATAL] Pipeline audit orchestrator crashed.`,
        `[ERROR] Execution message: ${err.message}`
      ]);
      showAlert("Audit Failed", err.message, "error");
    }
  };

  const handleExport = async (format) => {
    if (!completedAuditId) return;
    try {
      const res = await api.exportPipelineAuditReport(completedAuditId, format);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `pipeline_reconciliation_report_${completedAuditId}.${format === 'excel' ? 'xlsx' : format}`;
      a.click();
      window.URL.revokeObjectURL(url);
      setExportDropdownOpen(false);
    } catch (err) {
      showAlert("Export Failed", err.message, "error");
    }
  };

  const handleAddCustomValidation = () => {
    // Generate simple unique ID
    const nextId = customVal.id || `CUST_${Date.now().toString().slice(-4)}`;
    
    const newCheck = {
      id: nextId,
      name: customVal.name || `Custom ${customVal.type} Check`,
      type: customVal.type,
      severity: customVal.severity,
      enabled: customVal.enabled,
      description: customVal.description || 'User-defined assertion logic',
      column_name: ['null_check', 'duplicate_check'].includes(customVal.type) ? customVal.column_name : null,
      aggregate_column: customVal.type === 'aggregate' ? customVal.aggregate_column : null,
      aggregate_function: customVal.type === 'aggregate' ? customVal.aggregate_function : null,
      source_sql: customVal.source_sql || null,
      target_sql: customVal.target_sql || null
    };

    if (editingId) {
      setValidationsList(prev => prev.map(v => v.id === editingId ? newCheck : v));
      showAlert("Check Updated", `Successfully updated check "${newCheck.name}".`, "success");
    } else {
      setValidationsList(prev => [...prev, newCheck]);
      showAlert("Check Added", `Successfully registered custom check "${newCheck.name}".`, "success");
    }

    // Reset Builder Form
    setCustomVal({
      id: '',
      name: '',
      type: 'null_check',
      severity: 'medium',
      enabled: true,
      column_name: '',
      aggregate_column: '',
      aggregate_function: 'SUM',
      source_sql: '',
      target_sql: '',
      description: ''
    });
    setEditingId(null);
    setShowBuilder(false);
  };

  const handleEditValidation = (check) => {
    setCustomVal({
      id: check.id,
      name: check.name,
      type: check.type,
      severity: check.severity,
      enabled: check.enabled,
      column_name: check.column_name || '',
      aggregate_column: check.aggregate_column || '',
      aggregate_function: check.aggregate_function || 'SUM',
      source_sql: check.source_sql || '',
      target_sql: check.target_sql || '',
      description: check.description || ''
    });
    setEditingId(check.id);
    setShowBuilder(true);
  };

  const handleDeleteValidation = (id) => {
    setValidationsList(prev => prev.filter(v => v.id !== id));
    showAlert("Check Removed", "Validation check deleted successfully.", "info");
  };

  const toggleCheckEnabled = (id) => {
    setValidationsList(prev => prev.map(v => v.id === id ? { ...v, enabled: !v.enabled } : v));
  };

  const handleResetWizard = () => {
    setFeatureState('query');
    setCurrentStep(1);
    setSourceConnStatus(null);
    setTargetConnStatus(null);
    setValidationsList([]);
    setAuditResult(null);
    setCompletedAuditId(null);
    setExecutionLogs([]);
    setExecutingProgress(0);
  };



  // ----------------------------------------------------
  // WIZARD STEPS RENDERS
  // ----------------------------------------------------

  return (
    <div className="w-full h-full overflow-y-auto flex flex-col p-8 lg:p-12 animate-in fade-in duration-700 bg-slate-50/30 text-left">
      <div className="max-w-7xl mx-auto w-full pt-4">

        <Card className="shadow-slate-200/30 mb-8 border-slate-200">
          
          {/* Step 1: CONNECTIONS CONFIG */}
          {currentStep === 1 && (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <CardHeader 
                title="Step 1: Source & Target Connection Management" 
                subtitle="Specify configurations for databases or APIs. Test both pipelines before proceeding."
              />
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                
                {/* SOURCE CARD */}
                <div className="p-8 rounded-[2rem] border border-slate-100 bg-slate-50/40 relative overflow-hidden flex flex-col justify-between">
                  <div className="space-y-6">
                    <div className="flex items-center justify-between pb-4 border-b border-slate-150">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center">
                          <Database size={18} className="text-blue-600" />
                        </div>
                        <div>
                          <h4 className="text-xs font-black uppercase tracking-wider text-slate-800">Source Configuration</h4>
                          <p className="text-[9px] font-bold text-slate-400 uppercase tracking-wide">Data ingestion layer</p>
                        </div>
                      </div>
                      <select 
                        value={sourceType} 
                        onChange={(e) => setSourceType(e.target.value)} 
                        className="border border-slate-200 rounded-lg px-2.5 py-1.5 text-[10px] font-black uppercase tracking-wider text-slate-700 bg-white outline-none cursor-pointer"
                      >
                        <option value="database">DATABASE</option>
                        <option value="api">API SERVICE</option>
                      </select>
                    </div>

                    {sourceType === 'database' ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="flex flex-col gap-1 md:col-span-2">
                          <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Connection Name</label>
                          <input type="text" value={sourceConfig.connection_name} onChange={(e) => setSourceConfig({ ...sourceConfig, connection_name: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Database Type</label>
                          <select value={sourceConfig.db_type} onChange={(e) => setSourceConfig({ ...sourceConfig, db_type: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold cursor-pointer">
                            <option value="sqlite">SQLite</option>
                            <option value="postgresql">PostgreSQL</option>
                            <option value="mysql">MySQL</option>
                            <option value="mssql">MS SQL Server</option>
                          </select>
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Database Name / Path</label>
                          <input type="text" value={sourceConfig.db_name} onChange={(e) => setSourceConfig({ ...sourceConfig, db_name: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                        </div>
                        {sourceConfig.db_type !== 'sqlite' && (
                          <>
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Host</label>
                              <input type="text" value={sourceConfig.host} onChange={(e) => setSourceConfig({ ...sourceConfig, host: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Port</label>
                              <input type="text" value={sourceConfig.port} onChange={(e) => setSourceConfig({ ...sourceConfig, port: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Username</label>
                              <input type="text" value={sourceConfig.username} onChange={(e) => setSourceConfig({ ...sourceConfig, username: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Password</label>
                              <input type="password" value={sourceConfig.password} onChange={(e) => setSourceConfig({ ...sourceConfig, password: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                            </div>
                          </>
                        )}
                      </div>
                    ) : (
                      <div className="space-y-4">
                        <div className="flex flex-col gap-1">
                          <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Base URL</label>
                          <input type="text" value={sourceConfig.base_url} placeholder="https://api.github.com" onChange={(e) => setSourceConfig({ ...sourceConfig, base_url: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">HTTP Method</label>
                            <select value={sourceConfig.method} onChange={(e) => setSourceConfig({ ...sourceConfig, method: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold cursor-pointer">
                              <option value="GET">GET</option>
                              <option value="POST">POST</option>
                            </select>
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Auth Type</label>
                            <select value={sourceConfig.auth_type} onChange={(e) => setSourceConfig({ ...sourceConfig, auth_type: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold cursor-pointer">
                              <option value="none">NONE</option>
                              <option value="bearer">BEARER TOKEN</option>
                              <option value="api_key">API KEY</option>
                            </select>
                          </div>
                        </div>
                        {sourceConfig.auth_type !== 'none' && (
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Token / API Key</label>
                            <input type="password" value={sourceConfig.token} onChange={(e) => setSourceConfig({ ...sourceConfig, token: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="mt-8 pt-4 border-t border-slate-100 flex flex-col gap-3">
                    <Button 
                      onClick={() => handleTestConnection(true)} 
                      isLoading={testingSource} 
                      icon={RefreshCw}
                      variant="ghost" 
                      className="w-full"
                    >
                      Test Source Connection
                    </Button>
                    
                    {sourceConnStatus && (
                      <div className={`p-4 rounded-xl border text-[10px] font-bold leading-relaxed flex items-start gap-2.5 ${
                        sourceConnStatus.success 
                          ? 'bg-emerald-50/50 text-emerald-700 border-emerald-100' 
                          : 'bg-rose-50/50 text-rose-700 border-rose-100'
                      }`}>
                        {sourceConnStatus.success ? (
                          <>
                            <CheckCircle size={14} className="text-emerald-500 shrink-0 mt-0.5" />
                            <div>
                              <p className="font-black uppercase tracking-wider">SUCCESS ({sourceConnStatus.latency_ms}ms)</p>
                              <p className="opacity-80 mt-0.5">{sourceConnStatus.message}</p>
                              {sourceConnStatus.metadata?.tables && (
                                <p className="mt-1 font-mono text-[9px] text-emerald-600 uppercase tracking-tight">
                                  Found: {sourceConnStatus.metadata.tables.join(', ')}
                                </p>
                              )}
                            </div>
                          </>
                        ) : (
                          <>
                            <AlertTriangle size={14} className="text-rose-500 shrink-0 mt-0.5" />
                            <div>
                              <p className="font-black uppercase tracking-wider">CONNECTION FAILED</p>
                              <p className="opacity-80 mt-0.5">{sourceConnStatus.message}</p>
                            </div>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {/* TARGET CARD */}
                <div className="p-8 rounded-[2rem] border border-slate-100 bg-slate-50/40 relative overflow-hidden flex flex-col justify-between">
                  <div className="space-y-6">
                    <div className="flex items-center justify-between pb-4 border-b border-slate-150">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center">
                          <Database size={18} className="text-indigo-600" />
                        </div>
                        <div>
                          <h4 className="text-xs font-black uppercase tracking-wider text-slate-800">Target Configuration</h4>
                          <p className="text-[9px] font-bold text-slate-400 uppercase tracking-wide">Data reconciliation layer</p>
                        </div>
                      </div>
                      <select 
                        value={targetType} 
                        onChange={(e) => setTargetType(e.target.value)} 
                        className="border border-slate-200 rounded-lg px-2.5 py-1.5 text-[10px] font-black uppercase tracking-wider text-slate-700 bg-white outline-none cursor-pointer"
                      >
                        <option value="database">DATABASE</option>
                        <option value="api">API SERVICE</option>
                      </select>
                    </div>

                    {targetType === 'database' ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="flex flex-col gap-1 md:col-span-2">
                          <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Connection Name</label>
                          <input type="text" value={targetConfig.connection_name} onChange={(e) => setTargetConfig({ ...targetConfig, connection_name: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Database Type</label>
                          <select value={targetConfig.db_type} onChange={(e) => setTargetConfig({ ...targetConfig, db_type: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold cursor-pointer">
                            <option value="sqlite">SQLite</option>
                            <option value="postgresql">PostgreSQL</option>
                            <option value="mysql">MySQL</option>
                            <option value="mssql">MS SQL Server</option>
                          </select>
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Database Name / Path</label>
                          <input type="text" value={targetConfig.db_name} onChange={(e) => setTargetConfig({ ...targetConfig, db_name: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                        </div>
                        {targetConfig.db_type !== 'sqlite' && (
                          <>
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Host</label>
                              <input type="text" value={targetConfig.host} onChange={(e) => setTargetConfig({ ...targetConfig, host: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Port</label>
                              <input type="text" value={targetConfig.port} onChange={(e) => setTargetConfig({ ...targetConfig, port: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Username</label>
                              <input type="text" value={targetConfig.username} onChange={(e) => setTargetConfig({ ...targetConfig, username: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Password</label>
                              <input type="password" value={targetConfig.password} onChange={(e) => setTargetConfig({ ...targetConfig, password: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                            </div>
                          </>
                        )}
                      </div>
                    ) : (
                      <div className="space-y-4">
                        <div className="flex flex-col gap-1">
                          <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Base URL</label>
                          <input type="text" value={targetConfig.base_url} placeholder="https://api.github.com" onChange={(e) => setTargetConfig({ ...targetConfig, base_url: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">HTTP Method</label>
                            <select value={targetConfig.method} onChange={(e) => setTargetConfig({ ...targetConfig, method: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold cursor-pointer">
                              <option value="GET">GET</option>
                              <option value="POST">POST</option>
                            </select>
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Auth Type</label>
                            <select value={targetConfig.auth_type} onChange={(e) => setTargetConfig({ ...targetConfig, auth_type: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold cursor-pointer">
                              <option value="none">NONE</option>
                              <option value="bearer">BEARER TOKEN</option>
                              <option value="api_key">API KEY</option>
                            </select>
                          </div>
                        </div>
                        {targetConfig.auth_type !== 'none' && (
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Token / API Key</label>
                            <input type="password" value={targetConfig.token} onChange={(e) => setTargetConfig({ ...targetConfig, token: e.target.value })} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold" />
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="mt-8 pt-4 border-t border-slate-100 flex flex-col gap-3">
                    <Button 
                      onClick={() => handleTestConnection(false)} 
                      isLoading={testingTarget} 
                      icon={RefreshCw}
                      variant="ghost" 
                      className="w-full"
                    >
                      Test Target Connection
                    </Button>
                    
                    {targetConnStatus && (
                      <div className={`p-4 rounded-xl border text-[10px] font-bold leading-relaxed flex items-start gap-2.5 ${
                        targetConnStatus.success 
                          ? 'bg-emerald-50/50 text-emerald-700 border-emerald-100' 
                          : 'bg-rose-50/50 text-rose-700 border-rose-100'
                      }`}>
                        {targetConnStatus.success ? (
                          <>
                            <CheckCircle size={14} className="text-emerald-500 shrink-0 mt-0.5" />
                            <div>
                              <p className="font-black uppercase tracking-wider">SUCCESS ({targetConnStatus.latency_ms}ms)</p>
                              <p className="opacity-80 mt-0.5">{targetConnStatus.message}</p>
                              {targetConnStatus.metadata?.tables && (
                                <p className="mt-1 font-mono text-[9px] text-emerald-600 uppercase tracking-tight">
                                  Found: {targetConnStatus.metadata.tables.join(', ')}
                                </p>
                              )}
                            </div>
                          </>
                        ) : (
                          <>
                            <AlertTriangle size={14} className="text-rose-500 shrink-0 mt-0.5" />
                            <div>
                              <p className="font-black uppercase tracking-wider">CONNECTION FAILED</p>
                              <p className="opacity-80 mt-0.5">{targetConnStatus.message}</p>
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
                  Next: Pipeline Details
                </Button>
              </div>
            </div>
          )}

          {/* Step 2: PIPELINE DETAILS */}
          {currentStep === 2 && (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <CardHeader 
                title="Step 2: Pipeline Definitions & Audit Scope" 
                subtitle="Name your run context, target environment, and matching primary key identifiers."
              />

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Pipeline Name</label>
                  <input type="text" value={pipelineName} onChange={(e) => setPipelineName(e.target.value)} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 font-bold outline-none" />
                </div>
                
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Environment</label>
                  <select value={environment} onChange={(e) => setEnvironment(e.target.value)} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 font-bold outline-none cursor-pointer">
                    <option value="DEV">DEV</option>
                    <option value="QA">QA</option>
                    <option value="UAT">UAT</option>
                    <option value="PROD">PROD</option>
                  </select>
                </div>

                <div className="flex flex-col gap-1">
                  <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Pipeline Layer / Type</label>
                  <select value={pipelineType} onChange={(e) => setPipelineType(e.target.value)} className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 font-bold outline-none cursor-pointer">
                    <option value="BronzeToSilver">Bronze → Silver</option>
                    <option value="SilverToGold">Silver → Gold</option>
                    <option value="Custom">Custom Mapping</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[9px] font-black uppercase tracking-wider text-slate-400 flex items-center justify-between">
                    <span>Source Query / Endpoint</span>
                    <span className="text-[8px] opacity-60">strictly read-only (SELECT / WITH)</span>
                  </label>
                  <textarea 
                    value={sourceQuery} 
                    onChange={(e) => setSourceQuery(e.target.value)}
                    className="border border-slate-200 rounded-2xl px-5 py-4 font-mono text-xs text-slate-700 h-48 outline-none resize-none focus:ring-1 focus:ring-blue-500/20"
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-[9px] font-black uppercase tracking-wider text-slate-400 flex items-center justify-between">
                    <span>Target Query / Endpoint</span>
                    <span className="text-[8px] opacity-60">strictly read-only (SELECT / WITH)</span>
                  </label>
                  <textarea 
                    value={targetQuery} 
                    onChange={(e) => setTargetQuery(e.target.value)}
                    className="border border-slate-200 rounded-2xl px-5 py-4 font-mono text-xs text-slate-700 h-48 outline-none resize-none focus:ring-1 focus:ring-blue-500/20"
                  />
                </div>
              </div>

              <div className="flex flex-col gap-1 mt-4 max-w-md">
                <label className="text-[9px] font-black uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <span>Matching Keys (Composite columns)</span>
                  <HelpCircle size={12} className="text-slate-350" title="Comma-separated columns representing composite joins. Ex: id, category_id" />
                </label>
                <input 
                  type="text" 
                  value={keyColumnsInput} 
                  placeholder="id, store_id" 
                  onChange={(e) => setKeyColumnsInput(e.target.value)} 
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
                  Next: AI Suggestions
                </Button>
              </div>
            </div>
          )}

          {/* Step 3: AI SCHEMA ANALYSIS SUGGESTIONS */}
          {currentStep === 3 && (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <CardHeader 
                title="Step 3: AI Suggestions & Schema Profiling" 
                subtitle="Execute dynamic mapping to analyze columns, data types, and compile automated assertion recommendations."
              />

              {!analyzingSchema && analysisLogs.length === 0 ? (
                <div className="flex flex-col items-center justify-center p-16 text-center border border-dashed border-slate-200 rounded-[2.5rem] bg-slate-50/20">
                  <div className="w-16 h-16 rounded-full bg-blue-50 flex items-center justify-center mb-6">
                    <Sparkles size={24} className="text-blue-600 animate-pulse" />
                  </div>
                  <h4 className="text-sm font-black text-slate-800 mb-2">Ready to profile pipeline layers</h4>
                  <p className="text-xs text-slate-400 max-w-sm mx-auto leading-relaxed mb-6">
                    Click analyze to establish dynamic sessions, pull schema layouts, and discover target column models.
                  </p>
                  <Button onClick={handleAnalyzePipeline} icon={Sparkles}>
                    Analyze Pipeline Schema
                  </Button>
                </div>
              ) : (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                  {/* Schema Analysis Progress and Console Logs */}
                  <div className="lg:col-span-2 space-y-4">
                    <h4 className="text-[10px] font-black uppercase tracking-wider text-slate-400 flex items-center gap-2">
                      <TerminalIcon size={14} />
                      AI Analyzer Trace Stream
                    </h4>
                    
                    <div className="bg-slate-950 text-slate-350 p-6 rounded-2xl font-mono text-[10px] h-64 overflow-y-auto space-y-1 border border-slate-900 shadow-inner">
                      {analysisLogs.map((log, idx) => (
                        <div key={idx} className={log.includes('[ERROR]') ? 'text-rose-400' : log.includes('[SYSTEM]') ? 'text-indigo-400' : 'text-slate-300'}>
                          {log}
                        </div>
                      ))}
                      {analyzingSchema && (
                        <div className="flex items-center gap-2 text-blue-400 mt-2 font-black">
                          <RefreshCw size={10} className="animate-spin" /> Profile analyzing layers...
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Schema Mapping Column structures */}
                  <div className="space-y-4">
                    <h4 className="text-[10px] font-black uppercase tracking-wider text-slate-400 flex items-center gap-2">
                      <Layers size={14} />
                      Discovered Datasets
                    </h4>
                    
                    <div className="border border-slate-200 rounded-2xl p-6 space-y-6 h-64 overflow-y-auto bg-white shadow-sm">
                      <div>
                        <p className="text-[9px] font-black uppercase tracking-widest text-slate-400 mb-2">Source Columns ({sourceColumns.length})</p>
                        <div className="flex flex-wrap gap-1.5">
                          {sourceColumns.length > 0 ? sourceColumns.map((col, i) => (
                            <span key={i} className="px-2 py-1 rounded-lg bg-blue-50 text-blue-700 text-[9px] font-bold font-mono">
                              {col.name} <span className="opacity-40">({col.type})</span>
                            </span>
                          )) : <span className="text-[10px] text-slate-400 font-bold">Awaiting profiling...</span>}
                        </div>
                      </div>

                      <div className="border-t border-slate-100 pt-4">
                        <p className="text-[9px] font-black uppercase tracking-widest text-slate-400 mb-2">Target Columns ({targetColumns.length})</p>
                        <div className="flex flex-wrap gap-1.5">
                          {targetColumns.length > 0 ? targetColumns.map((col, i) => (
                            <span key={i} className="px-2 py-1 rounded-lg bg-indigo-50 text-indigo-700 text-[9px] font-bold font-mono">
                              {col.name} <span className="opacity-40">({col.type})</span>
                            </span>
                          )) : <span className="text-[10px] text-slate-400 font-bold">Awaiting profiling...</span>}
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
                  disabled={analyzingSchema}
                >
                  Back
                </Button>
                
                <div className="flex items-center gap-3">
                  {analysisLogs.length > 0 && !analyzingSchema && (
                    <Button 
                      onClick={handleAnalyzePipeline} 
                      variant="ghost" 
                      icon={RefreshCw}
                    >
                      Re-Analyze
                    </Button>
                  )}
                  <Button 
                    onClick={() => setCurrentStep(4)} 
                    icon={ArrowRight}
                    className="px-10"
                    disabled={analyzingSchema}
                  >
                    Next: Custom Builder
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Step 4: CUSTOM VALIDATIONS BUILDER */}
          {currentStep === 4 && (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <CardHeader 
                title="Step 4: Custom Assertion Specification Builder" 
                subtitle="Select validation modules, tune parameters, or build custom SQL statements for target layers."
                action={
                  <Button 
                    onClick={() => {
                      setEditingId(null);
                      setShowBuilder(!showBuilder);
                    }} 
                    variant="ghost"
                    icon={showBuilder ? X : PlusCircle}
                  >
                    {showBuilder ? "Close Form" : "Create Custom Check"}
                  </Button>
                }
              />

              {/* Validation Builder Modal-Like Form Panel */}
              {showBuilder && (
                <div className="p-8 rounded-[2rem] border border-slate-200/80 bg-slate-50/50 shadow-xl space-y-6 relative overflow-hidden animate-in zoom-in-95 duration-200">
                  <div className="absolute top-0 right-0 w-24 h-24 bg-blue-50 rounded-full blur-2xl -z-10" />
                  
                  <h4 className="text-xs font-black uppercase tracking-wider text-slate-800 border-b border-slate-100 pb-2">
                    {editingId ? `Edit Validation Check (${editingId})` : "Define New Data Reconciliation Check"}
                  </h4>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="flex flex-col gap-1">
                      <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Check Name</label>
                      <input 
                        type="text" 
                        value={customVal.name} 
                        placeholder="Row Count Validation Check"
                        onChange={(e) => setCustomVal({ ...customVal, name: e.target.value })} 
                        className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 font-bold bg-white outline-none" 
                      />
                    </div>

                    <div className="flex flex-col gap-1">
                      <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Check Type</label>
                      <select 
                        value={customVal.type} 
                        onChange={(e) => setCustomVal({ ...customVal, type: e.target.value })} 
                        className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 font-bold bg-white outline-none cursor-pointer"
                      >
                        <option value="row_count">Row Count Validation</option>
                        <option value="exact_match">Exact Match Validation</option>
                        <option value="null_check">Null Check Validation</option>
                        <option value="duplicate_check">Duplicate Check Validation</option>
                        <option value="schema_validation">Schema Validation</option>
                        <option value="aggregate">Aggregate Check Validation</option>
                        <option value="missing_records">Missing Records Validation</option>
                      </select>
                    </div>

                    <div className="flex flex-col gap-1">
                      <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Severity Level</label>
                      <select 
                        value={customVal.severity} 
                        onChange={(e) => setCustomVal({ ...customVal, severity: e.target.value })} 
                        className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 font-bold bg-white outline-none cursor-pointer"
                      >
                        <option value="critical">Critical</option>
                        <option value="high">High</option>
                        <option value="medium">Medium</option>
                        <option value="low">Low</option>
                      </select>
                    </div>
                  </div>

                  {/* Type Specific Fields */}
                  {['null_check', 'duplicate_check'].includes(customVal.type) && (
                    <div className="flex flex-col gap-1 max-w-sm">
                      <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Target Column Name</label>
                      <input 
                        type="text" 
                        value={customVal.column_name} 
                        placeholder="category"
                        onChange={(e) => setCustomVal({ ...customVal, column_name: e.target.value })} 
                        className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-mono" 
                      />
                    </div>
                  )}

                  {customVal.type === 'aggregate' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-xl">
                      <div className="flex flex-col gap-1">
                        <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Aggregate Function</label>
                        <select 
                          value={customVal.aggregate_function} 
                          onChange={(e) => setCustomVal({ ...customVal, aggregate_function: e.target.value })} 
                          className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-bold cursor-pointer"
                        >
                          <option value="SUM">SUM</option>
                          <option value="COUNT">COUNT</option>
                          <option value="AVG">AVG</option>
                          <option value="MIN">MIN</option>
                          <option value="MAX">MAX</option>
                        </select>
                      </div>
                      <div className="flex flex-col gap-1">
                        <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Aggregate Column</label>
                        <input 
                          type="text" 
                          value={customVal.aggregate_column} 
                          placeholder="price"
                          onChange={(e) => setCustomVal({ ...customVal, aggregate_column: e.target.value })} 
                          className="border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 bg-white outline-none font-mono" 
                        />
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="flex flex-col gap-1">
                      <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Source Specific Override SQL (Optional)</label>
                      <textarea 
                        value={customVal.source_sql} 
                        placeholder="SELECT SUM(price) FROM products WHERE id > 10"
                        onChange={(e) => setCustomVal({ ...customVal, source_sql: e.target.value })} 
                        className="border border-slate-200 rounded-xl px-4 py-3 font-mono text-xs text-slate-700 h-24 outline-none resize-none bg-white" 
                      />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Target Specific Override SQL (Optional)</label>
                      <textarea 
                        value={customVal.target_sql} 
                        placeholder="SELECT SUM(price) FROM products_silver WHERE id > 10"
                        onChange={(e) => setCustomVal({ ...customVal, target_sql: e.target.value })} 
                        className="border border-slate-200 rounded-xl px-4 py-3 font-mono text-xs text-slate-700 h-24 outline-none resize-none bg-white" 
                      />
                    </div>
                  </div>

                  <div className="flex flex-col gap-1">
                    <label className="text-[9px] font-black uppercase tracking-wider text-slate-400">Check Description</label>
                    <textarea 
                      value={customVal.description} 
                      placeholder="Ensure prices match on target silver layers."
                      onChange={(e) => setCustomVal({ ...customVal, description: e.target.value })} 
                      className="border border-slate-200 rounded-xl px-4 py-3 text-xs text-slate-700 h-20 outline-none resize-none bg-white" 
                    />
                  </div>

                  <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
                    <Button 
                      onClick={() => setShowBuilder(false)} 
                      variant="secondary"
                    >
                      Cancel
                    </Button>
                    <Button 
                      onClick={handleAddCustomValidation} 
                      variant="primary"
                    >
                      {editingId ? "Save Changes" : "Register Check"}
                    </Button>
                  </div>
                </div>
              )}

              {/* Checks Checklist Table */}
              <div className="border border-slate-250/60 rounded-3xl overflow-hidden shadow-sm bg-white">
                <div className="px-6 py-4 bg-slate-55/80 border-b border-slate-200 flex justify-between items-center">
                  <h4 className="text-xs font-black uppercase tracking-wider text-slate-500">Pipeline Reconciliation Checks Checklist</h4>
                  <span className="text-[10px] text-slate-400 font-bold">
                    {validationsList.length} check(s) registered ({validationsList.filter(v => v.enabled).length} enabled)
                  </span>
                </div>
                
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-b border-slate-200 bg-slate-50/30">
                      <th className="px-6 py-3 text-[10px] font-black uppercase tracking-wider text-slate-400 w-12 text-center">Enable</th>
                      <th className="px-6 py-3 text-[10px] font-black uppercase tracking-wider text-slate-400">Check Details</th>
                      <th className="px-6 py-3 text-[10px] font-black uppercase tracking-wider text-slate-400 w-32">Type</th>
                      <th className="px-6 py-3 text-[10px] font-black uppercase tracking-wider text-slate-400 w-24">Severity</th>
                      <th className="px-6 py-3 text-[10px] font-black uppercase tracking-wider text-slate-400 w-24 text-center">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {validationsList.length > 0 ? (
                      validationsList.map((check) => (
                        <tr key={check.id} className="hover:bg-slate-50/20 transition-colors">
                          <td className="px-6 py-4 text-center">
                            <button 
                              onClick={() => toggleCheckEnabled(check.id)} 
                              className={`p-1.5 rounded-lg border transition-all ${
                                check.enabled 
                                  ? 'bg-blue-600 border-blue-600 text-white shadow-sm' 
                                  : 'bg-white border-slate-200 text-slate-300 hover:border-slate-300'
                              }`}
                            >
                              {check.enabled ? <CheckSquare size={14} /> : <Square size={14} />}
                            </button>
                          </td>
                          <td className="px-6 py-4">
                            <div className="font-bold text-xs text-slate-800 flex items-center gap-1.5">
                              <span>{check.name}</span>
                              <span className="text-[9px] opacity-40 font-mono">({check.id})</span>
                            </div>
                            <p className="text-[10px] text-slate-400 leading-normal mt-1">{check.description}</p>
                            {(check.column_name || check.aggregate_column) && (
                              <div className="flex items-center gap-2 mt-2">
                                {check.column_name && (
                                  <span className="px-2 py-0.5 rounded bg-slate-50 border border-slate-100 text-[8px] font-mono font-bold text-slate-500">
                                    Col: {check.column_name}
                                  </span>
                                )}
                                {check.aggregate_column && (
                                  <span className="px-2 py-0.5 rounded bg-slate-50 border border-slate-100 text-[8px] font-mono font-bold text-slate-500 font-black">
                                    Agg: {check.aggregate_function}({check.aggregate_column})
                                  </span>
                                )}
                              </div>
                            )}
                          </td>
                          <td className="px-6 py-4">
                            <span className="px-2.5 py-1.5 rounded-lg bg-slate-100 text-slate-600 text-[9px] font-black uppercase tracking-wider border border-slate-200/50">
                              {check.type.replace('_', ' ')}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-wider border ${
                              check.severity === 'critical' ? 'bg-red-50 text-red-600 border-red-100' :
                              check.severity === 'high' ? 'bg-orange-50 text-orange-600 border-orange-100' :
                              check.severity === 'medium' ? 'bg-blue-50 text-blue-600 border-blue-100' :
                              'bg-slate-50 text-slate-500 border-slate-100'
                            }`}>
                              {check.severity}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-center">
                            <div className="flex items-center justify-center gap-1.5">
                              <button 
                                onClick={() => handleEditValidation(check)} 
                                className="p-2 rounded-lg border border-slate-200 bg-white text-slate-500 hover:text-blue-600 hover:border-blue-100 hover:bg-blue-50/20 transition-all shadow-sm"
                                title="Edit Check"
                              >
                                <Edit3 size={12} />
                              </button>
                              <button 
                                onClick={() => handleDeleteValidation(check.id)} 
                                className="p-2 rounded-lg border border-slate-200 bg-white text-slate-500 hover:text-red-650 hover:border-red-100 hover:bg-red-50/20 transition-all shadow-sm"
                                title="Delete Check"
                              >
                                <Trash2 size={12} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={5} className="px-6 py-12 text-center text-xs font-bold text-slate-400 bg-slate-50/10">
                          No validation checks defined. Use the suggestions panel or create custom ones using the builder!
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
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
                  Next: Execution Parameters
                </Button>
              </div>
            </div>
          )}

          {/* Step 5: EXECUTION SCREEN */}
          {currentStep === 5 && (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <CardHeader 
                title="Step 5: Reconciliation Execution Console" 
                subtitle="Calibrate limits and trigger the backend strategy orchestration. Stream console logs in real-time."
              />

              {!executing && executionLogs.length === 0 ? (
                <div className="space-y-8">
                  {/* Calibrate Limits */}
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
                    <h4 className="text-xs font-black text-slate-800 mb-1.5 uppercase">Reconciliation Audit Suite Ready</h4>
                    <p className="text-[10px] text-slate-450 max-w-xs mx-auto leading-relaxed mb-6">
                      Will execute {validationsList.filter(v => v.enabled).length} enabled verification check(s).
                    </p>
                    <Button onClick={handleExecuteAudit} icon={Play} className="px-12 py-4 bg-emerald-600 hover:bg-emerald-700 shadow-emerald-500/10">
                      Run Reconciliation Engine
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Execution Progress Bar */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-[9px] font-black uppercase tracking-wider">
                      <span className="text-slate-400">Execution Status</span>
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

                  {/* Execution done notification panel */}
                  {!executing && auditResult && (
                    <div className="p-6 rounded-2xl border border-emerald-100 bg-emerald-50/40 flex items-center justify-between animate-in fade-in slide-in-from-bottom-2 duration-300">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-600">
                          <CheckCircle size={20} />
                        </div>
                        <div>
                          <p className="text-xs font-black text-slate-800 uppercase tracking-tight">Audit Session Finalized</p>
                          <p className="text-[10px] text-slate-450 font-bold uppercase tracking-wider mt-0.5">
                            Accuracy rating is {auditResult.summary?.accuracy}%. Proceed to view full telemetry dashboard.
                          </p>
                        </div>
                      </div>
                      <Button onClick={() => setCurrentStep(6)} icon={ArrowRight}>
                        View Results Dashboard
                      </Button>
                    </div>
                  )}
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

          {/* Step 6: RESULTS DASHBOARD */}
          {currentStep === 6 && auditResult && (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <CardHeader 
                title="Step 6: Pipeline Reconciliation Telemetry" 
                subtitle={`Reconciliation telemetry for Run #${completedAuditId} | ${pipelineName}`}
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
                        <button onClick={() => handleExport('csv')} className="w-full text-left px-4 py-3 hover:bg-slate-50 text-[10px] font-black uppercase tracking-wider text-slate-650 hover:text-slate-900 border-b border-slate-100 flex items-center gap-2">
                          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> CSV Format (.csv)
                        </button>
                        <button onClick={() => handleExport('json')} className="w-full text-left px-4 py-3 hover:bg-slate-50 text-[10px] font-black uppercase tracking-wider text-slate-650 hover:text-slate-900 border-b border-slate-100 flex items-center gap-2">
                          <span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> JSON Format (.json)
                        </button>
                        <button onClick={() => handleExport('excel')} className="w-full text-left px-4 py-3 hover:bg-slate-50 text-[10px] font-black uppercase tracking-wider text-slate-650 hover:text-slate-900 flex items-center gap-2">
                          <span className="w-2.5 h-2.5 rounded-full bg-blue-500" /> Excel Spreadsheet (.xlsx)
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
                  
                  <p className="text-[9px] font-black uppercase tracking-widest text-slate-400 mb-4">Quality Index</p>
                  
                  <div className="relative w-32 h-32 flex items-center justify-center mb-2">
                    {/* SVG Progress Circle */}
                    <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                      <circle cx="50" cy="50" r="40" fill="transparent" stroke="#f1f5f9" strokeWidth="8" />
                      <circle 
                        cx="50" cy="50" r="40" fill="transparent" 
                        stroke={parseFloat(auditResult.summary?.accuracy) >= 90 ? '#10b981' : parseFloat(auditResult.summary?.accuracy) >= 70 ? '#3b82f6' : '#ef4444'} 
                        strokeWidth="8" 
                        strokeDasharray={2 * Math.PI * 40}
                        strokeDashoffset={(2 * Math.PI * 40) * (1 - parseFloat(auditResult.summary?.accuracy || 0) / 100)}
                        strokeLinecap="round"
                        className="transition-all duration-1000 ease-out"
                      />
                    </svg>
                    <div className="absolute flex flex-col items-center justify-center">
                      <span className="text-2xl font-black text-slate-800 tracking-tight">{auditResult.summary?.accuracy}%</span>
                      <span className="text-[8px] font-bold text-slate-400 uppercase tracking-widest">Matched</span>
                    </div>
                  </div>
                  
                  <span className={`text-[8px] font-black uppercase tracking-wider px-2 py-0.5 rounded border ${
                    parseFloat(auditResult.summary?.accuracy) >= 90 ? 'bg-emerald-50 text-emerald-600 border-emerald-100' :
                    parseFloat(auditResult.summary?.accuracy) >= 70 ? 'bg-blue-50 text-blue-600 border-blue-100' :
                    'bg-red-50 text-red-600 border-red-100'
                  }`}>
                    {parseFloat(auditResult.summary?.accuracy) >= 90 ? 'COMPLIANT' : parseFloat(auditResult.summary?.accuracy) >= 70 ? 'WARNING' : 'DISCREPANCY'}
                  </span>
                </div>

                <div className="p-5 rounded-2xl bg-slate-50 border border-slate-100 flex flex-col justify-between shadow-sm">
                  <div>
                    <p className="text-[9px] font-black uppercase tracking-widest text-slate-400">Total Validations</p>
                    <p className="text-2.5xl font-black text-slate-800 mt-2">{auditResult.summary?.total_checks}</p>
                  </div>
                  <div className="pt-2 border-t border-slate-100/50 flex items-center justify-between text-[9px] text-slate-400 font-bold uppercase">
                    <span>Active Checks</span>
                    <span className="text-slate-650">{auditResult.results?.length}</span>
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-slate-50 border border-slate-100 flex flex-col justify-between shadow-sm">
                  <div>
                    <p className="text-[9px] font-black uppercase tracking-widest text-slate-400">Assertions Reconciled</p>
                    <p className="text-2.5xl font-black text-emerald-600 mt-2">{auditResult.summary?.passed_checks}</p>
                  </div>
                  <div className="pt-2 border-t border-slate-100/50 flex items-center justify-between text-[9px] text-emerald-500 font-bold uppercase">
                    <span>Passed Rate</span>
                    <span>{((auditResult.summary?.passed_checks / auditResult.summary?.total_checks) * 100 || 0).toFixed(0)}%</span>
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-slate-50 border border-slate-100 flex flex-col justify-between shadow-sm">
                  <div>
                    <p className="text-[9px] font-black uppercase tracking-widest text-slate-400">Telemetry Latency</p>
                    <p className="text-2.5xl font-black text-slate-800 mt-2">
                      {(auditResult.summary?.duration_ms / 1000).toFixed(2)}s
                    </p>
                  </div>
                  <div className="pt-2 border-t border-slate-100/50 flex items-center justify-between text-[9px] text-slate-400 font-bold uppercase">
                    <span>Duration MS</span>
                    <span className="text-slate-650">{auditResult.summary?.duration_ms} ms</span>
                  </div>
                </div>

              </div>

              {/* Detailed Check Spectrum Results Table */}
              <div className="border border-slate-200 rounded-3xl overflow-hidden bg-white shadow-sm flex flex-col">
                <div className="px-6 py-4 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
                  <h4 className="text-xs font-black uppercase tracking-wider text-slate-500">Assertion Telemetry Results Spectrum</h4>
                  <span className="text-[10px] text-slate-400 font-bold">{auditResult.summary?.failed_checks} failed check(s)</span>
                </div>
                
                <div className="divide-y divide-slate-100">
                  {auditResult.results?.map((res, index) => {
                    const isExpanded = expandedResultId === res.id;
                    const isPass = res.status === 'passed';
                    const isError = res.status === 'error';
                    
                    return (
                      <div key={res.id} className="p-6 hover:bg-slate-50/10 transition-colors flex flex-col gap-4">
                        <div className="flex justify-between items-start gap-4">
                          <div className="flex items-start gap-3">
                            <div className="mt-1">
                              {isPass ? (
                                <CheckCircle size={16} className="text-emerald-500" />
                              ) : isError ? (
                                <AlertTriangle size={16} className="text-amber-500" />
                              ) : (
                                <AlertTriangle size={16} className="text-rose-500" />
                              )}
                            </div>
                            <div>
                              <div className="font-black text-xs text-slate-800 uppercase tracking-tight flex items-center gap-2">
                                <span>{res.name}</span>
                                <span className="text-[9px] font-mono opacity-40">({res.id})</span>
                              </div>
                              <p className="text-[9px] text-slate-450 font-bold uppercase tracking-wider mt-1">
                                Check Type: {res.type.replace('_', ' ')} | Severity: {res.severity}
                              </p>
                            </div>
                          </div>
                          
                          <div className="flex items-center gap-3 shrink-0">
                            <span className={`text-[9px] font-black uppercase tracking-widest px-2.5 py-1 rounded-md border ${
                              isPass 
                                ? 'bg-emerald-50 text-emerald-600 border-emerald-100' 
                                : isError 
                                  ? 'bg-amber-50 text-amber-600 border-amber-100' 
                                  : 'bg-rose-50 text-rose-600 border-rose-100'
                            }`}>
                              {res.status.toUpperCase()}
                            </span>
                            
                            {res.mismatch_details && (
                              <button 
                                onClick={() => setExpandedResultId(isExpanded ? null : res.id)} 
                                className="p-2 border border-slate-200 rounded-lg bg-white text-slate-500 hover:text-slate-800 shadow-sm transition-all"
                              >
                                <ChevronDown className={`transform transition-transform ${isExpanded ? 'rotate-180' : ''}`} size={12} />
                              </button>
                            )}
                          </div>
                        </div>

                        {/* Mismatch Detail Table (collapsible) */}
                        {isExpanded && res.mismatch_details && (
                          <div className="border border-slate-150 rounded-xl overflow-hidden bg-slate-50/50 mt-2 animate-in slide-in-from-top-1 duration-200">
                            <div className="px-4 py-2.5 bg-slate-100 border-b border-slate-150 flex items-center justify-between text-[9px] font-bold text-slate-500 uppercase tracking-wider">
                              <span>Mismatch Details (showing top {res.mismatch_details.length} rows)</span>
                              <span>Total failed: {res.records_failed}</span>
                            </div>
                            <div className="p-4 overflow-x-auto">
                              <pre className="font-mono text-[9px] text-slate-650 bg-white p-3 rounded-lg border border-slate-200/60 overflow-y-auto max-h-56">
                                {JSON.stringify(res.mismatch_details, null, 2)}
                              </pre>
                            </div>
                          </div>
                        )}

                        {res.error_message && (
                          <div className="text-[10px] font-semibold text-rose-600 p-3 bg-rose-50 border border-rose-100 rounded-xl flex items-center gap-2 mt-1">
                            <AlertTriangle size={12} className="shrink-0" />
                            <span>Error: {res.error_message}</span>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* AI INSIGHTS BLOCK */}
              {auditResult.ai_insights && (
                <div className="border border-indigo-100 rounded-3xl bg-indigo-50/15 overflow-hidden shadow-sm flex flex-col">
                  <div className="px-6 py-4 bg-indigo-50/30 border-b border-indigo-100/50 flex items-center gap-2">
                    <Sparkles size={16} className="text-indigo-600" />
                    <h4 className="text-xs font-black uppercase tracking-wider text-indigo-900">AI Engine Diagnoses & Action Recommendations</h4>
                  </div>
                  
                  <div className="p-6 space-y-6">
                    <div className="text-xs text-slate-700 leading-relaxed font-bold bg-white p-4 rounded-xl border border-indigo-50/80">
                      {auditResult.ai_insights.summary}
                    </div>
                    
                    {auditResult.ai_insights.failures && auditResult.ai_insights.failures.length > 0 && (
                      <div className="space-y-4">
                        {auditResult.ai_insights.failures.map((fail, i) => (
                          <div key={i} className="p-5 rounded-2xl bg-white border border-slate-150 space-y-2.5 shadow-sm">
                            <div className="flex items-center gap-2 text-xs font-black text-rose-700 uppercase">
                              <AlertTriangle size={14} />
                              <span>{fail.name} Mismatch Diagnosis</span>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-[11px] leading-relaxed pt-2 border-t border-slate-50">
                              <div className="space-y-1">
                                <p className="font-black text-slate-400 uppercase tracking-widest text-[8px]">Primary Cause</p>
                                <p className="text-slate-700 font-semibold">{fail.cause}</p>
                              </div>
                              <div className="space-y-1">
                                <p className="font-black text-slate-400 uppercase tracking-widest text-[8px] text-emerald-600">Action Fix Recommendation</p>
                                <p className="text-emerald-700 font-semibold">{fail.recommendation}</p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Mask Variables Accordion */}
              <div className="border border-slate-200 rounded-3xl overflow-hidden bg-white shadow-sm flex flex-col">
                <div className="px-6 py-4 bg-slate-50/50 border-b border-slate-100 flex items-center justify-between">
                  <h4 className="text-xs font-black uppercase tracking-wider text-slate-500">Security Audit Context Variables (Masked)</h4>
                </div>
                <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6 text-[10px]">
                  <div className="space-y-1">
                    <p className="font-black text-slate-400 uppercase tracking-widest text-[8px]">Source Config context</p>
                    <pre className="p-3.5 bg-slate-50 border border-slate-100 rounded-xl font-mono text-slate-500 overflow-x-auto">
                      {JSON.stringify(api.getDbConfig ? { connection: sourceType, credentials: "••••••••" } : {}, null, 2)}
                    </pre>
                  </div>
                  <div className="space-y-1">
                    <p className="font-black text-slate-400 uppercase tracking-widest text-[8px]">Target Config context</p>
                    <pre className="p-3.5 bg-slate-50 border border-slate-100 rounded-xl font-mono text-slate-500 overflow-x-auto">
                      {JSON.stringify(api.getDbConfig ? { connection: targetType, credentials: "••••••••" } : {}, null, 2)}
                    </pre>
                  </div>
                </div>
              </div>

              <div className="pt-6 border-t border-slate-100 flex items-center justify-end">
                <Button 
                  onClick={handleResetWizard} 
                  icon={RefreshCw}
                  variant="primary"
                  className="px-10"
                >
                  Configure New Audit Run
                </Button>
              </div>
            </div>
          )}

        </Card>
      </div>
    </div>
  );
}
