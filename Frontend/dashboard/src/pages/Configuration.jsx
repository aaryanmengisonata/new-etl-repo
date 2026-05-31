import React, { useState, useEffect } from 'react'
import { useAppContext } from '../store/AppContext'
import {
  Loader2, CheckCircle, CloudUpload, ChevronLeft, ChevronDown,
  Database, Layers, Zap, FlaskConical, FileText, Settings, Activity
} from 'lucide-react'
import { api } from '../services/api'

const defaultConfigs = {
  dev: {
    bronze: { lakehouse: '', endpoint: '' },
    silver: { lakehouse: '', endpoint: '' },
    gold: { lakehouse: '', endpoint: '' },
  },
  qa: {
    bronze: { lakehouse: '', endpoint: '' },
    silver: { lakehouse: '', endpoint: '' },
    gold: { lakehouse: '', endpoint: '' },
  },
  prod: {
    bronze: { lakehouse: '', endpoint: '' },
    silver: { lakehouse: '', endpoint: '' },
    gold: { lakehouse: '', endpoint: '' },
  },
}

const defaultConfig = {
  FABRIC_LAYER: 'bronze',
  FABRIC_ENV: 'dev',
  FABRIC_LAKEHOUSE: '',
  FABRIC_ENDPOINT: '',
  FABRIC_CONFIGS: defaultConfigs,
}

const cloneConfigs = () => JSON.parse(JSON.stringify(defaultConfigs))

const getSelectedValues = (state) => {
  const envConfig = state.FABRIC_CONFIGS?.[state.FABRIC_ENV] || {}
  const layerConfig = envConfig[state.FABRIC_LAYER] || {}
  return {
    lakehouse: layerConfig.lakehouse || '',
    endpoint: layerConfig.endpoint || '',
  }
}

const syncSelectedValues = (state) => {
  const selected = getSelectedValues(state)
  return {
    ...state,
    FABRIC_LAKEHOUSE: selected.lakehouse,
    FABRIC_ENDPOINT: selected.endpoint,
  }
}

const mergeConfigs = (incoming = {}) => {
  const merged = cloneConfigs()
  for (const env of ['dev', 'qa', 'prod']) {
    for (const layer of ['bronze', 'silver', 'gold']) {
      merged[env][layer] = {
        ...merged[env][layer],
        ...(incoming?.[env]?.[layer] || {}),
      }
    }
  }
  return merged
}

// ── Tab Definitions ──────────────────────────────────────────────
const TABS = [
  { id: 'fabric',      label: 'Fabric',         icon: Layers },
  { id: 'database',    label: 'Database',        icon: Database },
  { id: 'api_sentry',  label: 'API Sentry',      icon: Zap },
  { id: 'pipeline',    label: 'Pipeline',        icon: Activity },
  { id: 'integration', label: 'Integration',     icon: Settings },
  { id: 'testing',     label: 'Testing',         icon: FlaskConical },
  { id: 'reporting',   label: 'Reporting',       icon: FileText },
]

export default function Configuration({ navParams, setActivePage, setFeatureState }) {
  const { showAlert, activeModule } = useAppContext()
  console.log("Configuration render: navParams =", navParams, "activeModule =", activeModule)

  // ── Active Tab ──────────────────────────────────────────────
  const resolveDefaultTab = () => {
    if (navParams?.defaultTab) return navParams.defaultTab
    if (activeModule === 'db_auditor') return 'database'
    if (activeModule === 'api_sentry') return 'api_sentry'
    if (activeModule === 'etl_auditor') return 'pipeline'
    if (activeModule === 'integration_sentry') return 'integration'
    return 'fabric'
  }
  const [activeTab, setActiveTab] = useState(resolveDefaultTab)

  // ── Fabric Config State ──────────────────────────────────────
  const [config, setConfig] = useState({ ...defaultConfig, FABRIC_CONFIGS: cloneConfigs() })

  // ── Database Config State ────────────────────────────────────
  const [dbConfig, setDbConfig] = useState({
    engine: 'sqlite', host: 'localhost', port: '5432',
    db_name: 'etl_test.db', username: '', password: ''
  })

  // ── Pipeline Config State ────────────────────────────────────
  const [pipelineConfig, setPipelineConfig] = useState({
    default_row_limit: 10000, default_chunk_size: 2000,
    default_query_timeout: 30, default_source_db: 'test_audit_src_test.db',
    default_target_db: 'test_audit_tgt_test.db'
  })

  // ── API Sentry Config State ──────────────────────────────────
  const [apiConfig, setApiConfig] = useState({
    base_url: 'https://fakestoreapi.com', timeout: 30, ssl_verify: false
  })

  // ── Integration Config State ─────────────────────────────────
  const [integrationConfig, setIntegrationConfig] = useState({
    source_db: 'test_audit_src_test.db', target_db: 'test_audit_tgt_test.db',
    key_column: 'id', reconciliation_type: 'data_diff'
  })

  // ── Testing Config State ─────────────────────────────────────
  const [testingConfig, setTestingConfig] = useState({
    csv_file: 'test_cases.csv', sql_dir: 'sql', report_dir: 'reports',
    enable_parallel: false, max_workers: 4
  })

  // ── Reporting Config State ───────────────────────────────────
  const [reportingConfig, setReportingConfig] = useState({
    allure_results: 'reports/allure-results', xml_results: 'reports/xml-results',
    generate_xml: true, generate_html: true
  })

  const [loading, setLoading] = useState(true)
  const [saved, setSaved] = useState(false)
  const [saving, setSaving] = useState(false)

  // ── Load ALL configs on mount ────────────────────────────────
  useEffect(() => {
    const safeGet = (fn, fallback) => fn().catch(err => { console.warn("Config load fallback:", err); return fallback })

    Promise.all([
      safeGet(api.getConfig.bind(api), defaultConfig),
      safeGet(api.getDbConfig.bind(api), dbConfig),
      safeGet(api.getPipelineConfig.bind(api), pipelineConfig),
      safeGet(api.getApiSentryConfig.bind(api), apiConfig),
      safeGet(api.getIntegrationConfig.bind(api), integrationConfig),
      safeGet(api.getTestingConfig.bind(api), testingConfig),
      safeGet(api.getReportingConfig.bind(api), reportingConfig),
    ]).then(([fabricData, dbData, pipeData, apiData, intData, testData, repData]) => {
      setConfig(syncSelectedValues({
        ...defaultConfig, ...fabricData,
        FABRIC_CONFIGS: mergeConfigs(fabricData.FABRIC_CONFIGS),
      }))
      setDbConfig(dbData)
      setPipelineConfig(pipeData)
      setApiConfig(apiData)
      setIntegrationConfig(intData)
      setTestingConfig(testData)
      setReportingConfig(repData)
      setLoading(false)
    }).catch(err => {
      console.error("Failed to load configs:", err)
      setLoading(false)
    })
  }, [navParams])

  // ── Save Handlers ────────────────────────────────────────────
  const handleSaveFabric = async () => {
    try {
      setSaving(true)
      const response = await api.saveConfig(config)
      setConfig(prev => syncSelectedValues({
        ...prev, ...(response?.config || {}),
        FABRIC_CONFIGS: mergeConfigs(response?.config?.FABRIC_CONFIGS),
      }))
      setSaved(true)
      setTimeout(() => {
        setSaved(false)
        setActivePage('fabric_audit')
      }, 1500)
    } catch (err) {
      console.error("Failed to save config:", err)
      showAlert("Configuration Error", "Failed to save configuration. Please check if backend is running.", "error")
    } finally { setSaving(false) }
  }

  const handleSaveDb = async () => {
    try {
      setSaving(true)
      const response = await api.saveDbConfig(dbConfig)
      setDbConfig(response.config || dbConfig)
      setSaved(true)
      setTimeout(() => {
        setSaved(false)
        if (navParams?.returnPage) setActivePage(navParams.returnPage)
        else setActivePage('db_auditor')
      }, 1500)
    } catch (err) {
      console.error("Failed to save DB config:", err)
      showAlert("Configuration Error", "Failed to save database configuration.", "error")
    } finally { setSaving(false) }
  }

  const createGenericSaveHandler = (saveFn, setStateFn, returnPage) => async (currentData) => {
    try {
      setSaving(true)
      const response = await saveFn(currentData)
      if (response.config) setStateFn(response.config)
      setSaved(true)
      setTimeout(() => {
        setSaved(false)
        if (navParams?.returnPage) {
          if (navParams.returnMode && setFeatureState) setFeatureState(navParams.returnMode)
          setActivePage(navParams.returnPage)
        } else {
          setActivePage(returnPage)
        }
      }, 1500)
    } catch (err) {
      console.error("Failed to save config:", err)
      showAlert("Configuration Error", "Failed to save configuration.", "error")
    } finally { setSaving(false) }
  }

  const handleSavePipeline = createGenericSaveHandler(api.savePipelineConfig.bind(api), setPipelineConfig, 'etl_auditor')
  const handleSaveApi = createGenericSaveHandler(api.saveApiSentryConfig.bind(api), setApiConfig, 'api_sentry')
  const handleSaveIntegration = createGenericSaveHandler(api.saveIntegrationConfig.bind(api), setIntegrationConfig, 'integration_sentry')
  const handleSaveTesting = createGenericSaveHandler(api.saveTestingConfig.bind(api), setTestingConfig, 'run')
  const handleSaveReporting = createGenericSaveHandler(api.saveReportingConfig.bind(api), setReportingConfig, 'reports')

  // ── Fabric helpers ───────────────────────────────────────────
  const mapImportedConfig = (imported) => {
    const nextConfigs = cloneConfigs()
    const envKeyMap = { dev: 'DEV', qa: 'QAT', prod: 'PROD' }
    for (const env of ['dev', 'qa', 'prod']) {
      for (const layer of ['bronze', 'silver', 'gold']) {
        const prefix = layer.toUpperCase()
        const envPrefix = envKeyMap[env]
        nextConfigs[env][layer] = {
          lakehouse: imported[`${envPrefix}_${prefix}_LAKEHOUSE_NAME`] || imported[`${prefix}_LAKEHOUSE_NAME`] || '',
          endpoint: imported[`${envPrefix}_${prefix}_SQL_ENDPOINT`] || imported[`${prefix}_SQL_ENDPOINT`] || '',
        }
      }
    }
    const environment = imported.ENVIRONMENT?.toUpperCase()
    const activeLayer = imported.ACTIVE_FABRIC_LAYER?.toLowerCase() || imported.FABRIC_LAYER?.toLowerCase() || 'bronze'
    const selectedEnv =
      environment === 'DEV' ? 'dev' :
      environment === 'QAT' || environment === 'QA' || environment === 'TEST' ? 'qa' :
      environment === 'PROD' ? 'prod' : 'dev'
    return syncSelectedValues({ FABRIC_LAYER: activeLayer, FABRIC_ENV: selectedEnv, FABRIC_LAKEHOUSE: '', FABRIC_ENDPOINT: '', FABRIC_CONFIGS: nextConfigs })
  }

  const handleImport = (e) => {
    const file = e.target.files[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (event) => {
      try {
        const content = event.target.result
        const imported = file.name.endsWith('.json')
          ? JSON.parse(content)
          : Object.fromEntries(
            content.split('\n').map(l => l.split('=')).filter(p => p.length === 2).map(([k, v]) => [k.trim().toUpperCase(), v.trim()])
          )
        setConfig(mapImportedConfig(imported))
      } catch (err) { showAlert("Import Failed", "The uploaded properties file is invalid or corrupted.", "error") }
    }
    reader.readAsText(file)
  }

  const handleLayerChange = (value) => {
    setConfig(prev => syncSelectedValues({ ...prev, FABRIC_LAYER: value }))
  }

  const handleEnvChange = (value) => {
    setConfig(prev => syncSelectedValues({ ...prev, FABRIC_ENV: value }))
  }

  const updateSelectedField = (field, value) => {
    setConfig(prev => ({
      ...prev,
      FABRIC_LAKEHOUSE: field === 'lakehouse' ? value : prev.FABRIC_LAKEHOUSE,
      FABRIC_ENDPOINT: field === 'endpoint' ? value : prev.FABRIC_ENDPOINT,
      FABRIC_CONFIGS: {
        ...prev.FABRIC_CONFIGS,
        [prev.FABRIC_ENV]: {
          ...prev.FABRIC_CONFIGS[prev.FABRIC_ENV],
          [prev.FABRIC_LAYER]: {
            ...prev.FABRIC_CONFIGS[prev.FABRIC_ENV][prev.FABRIC_LAYER],
            [field]: value,
          },
        },
      },
    }))
  }

  if (loading) return <div className="p-20 text-center uppercase tracking-widest animate-pulse">Loading Props...</div>

  // ── Reusable Components ──────────────────────────────────────
  const SaveButton = ({ onClick, label = 'Save' }) => (
    <button
      onClick={onClick}
      disabled={saving}
      className={`px-12 py-4 rounded-xl text-[10px] font-black uppercase tracking-[0.2em] text-white transition-all duration-300 transform active:scale-95 shadow-xl ${saving ? 'bg-slate-700' :
        saved ? 'bg-emerald-600 shadow-emerald-500/20' :
          'bg-blue-600 hover:bg-blue-700 shadow-blue-500/20'
        }`}
    >
      {saving ? <span className="flex items-center gap-2"><Loader2 size={12} className="animate-spin" /> Saving...</span>
        : saved ? <span className="flex items-center gap-2"><CheckCircle size={12} /> Saved</span>
          : label}
    </button>
  )

  const FieldInput = ({ label, value, onChange, placeholder, type = 'text', mono = false }) => (
    <div className="space-y-3">
      <label className="text-[10px] font-black uppercase tracking-[0.2em] opacity-30 ml-1">{label}</label>
      <input
        type={type}
        placeholder={placeholder}
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        className={`w-full bg-slate-50 border border-slate-200 rounded-2xl px-6 py-4 text-xs ${mono ? 'font-mono' : ''} outline-none focus:border-blue-500/50 transition-all hover:bg-white`}
      />
    </div>
  )

  const FieldSelect = ({ label, value, onChange, options }) => (
    <div className="space-y-3">
      <label className="text-[10px] font-black uppercase tracking-[0.2em] opacity-30 ml-1">{label}</label>
      <div className="relative group">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full appearance-none bg-slate-50 border border-slate-200 rounded-2xl px-6 py-4 text-[11px] font-black uppercase tracking-widest outline-none focus:border-blue-500/50 transition-all cursor-pointer hover:bg-white"
        >
          {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <ChevronDown className="absolute right-6 top-1/2 -translate-y-1/2 opacity-30 group-hover:opacity-100 transition-opacity pointer-events-none" size={16} />
      </div>
    </div>
  )

  const FieldToggle = ({ label, value, onChange }) => (
    <div className="flex items-center justify-between py-4 px-1">
      <label className="text-[10px] font-black uppercase tracking-[0.2em] opacity-50">{label}</label>
      <button
        onClick={() => onChange(!value)}
        className={`relative w-11 h-6 rounded-full transition-colors duration-200 ${value ? 'bg-blue-600' : 'bg-slate-200'}`}
      >
        <span className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow-md transition-transform duration-200 ${value ? 'translate-x-5' : ''}`} />
      </button>
    </div>
  )

  // ── Determine title ──────────────────────────────────────────
  const currentTabMeta = TABS.find(t => t.id === activeTab)
  const title = `${currentTabMeta?.label || 'Master'} Configuration`
  const subtitle = activeTab === 'fabric' ? 'Fabric Reconciliation Protocol' :
                   activeTab === 'database' ? 'SQL Connection Settings' :
                   activeTab === 'api_sentry' ? 'REST Endpoint Configuration' :
                   activeTab === 'pipeline' ? 'Pipeline Auditor Settings' :
                   activeTab === 'integration' ? 'Cross-System Reconciliation' :
                   activeTab === 'testing' ? 'Test Execution Engine' :
                   activeTab === 'reporting' ? 'Report Generation Settings' : ''

  return (
    <div className="max-w-4xl mx-auto animate-in fade-in slide-in-from-top-4 duration-700 space-y-8">
      <div className="flex items-start justify-between">
        <div className="flex flex-col gap-2">
          <h1 className="text-3xl font-black tracking-tight text-slate-900">
            {title}
          </h1>
          <p className="text-[10px] font-bold uppercase tracking-[0.3em] opacity-30">
            {subtitle}
          </p>
        </div>
        <button
          onClick={() => {
            if (navParams?.returnPage) {
              if (navParams.returnMode && setFeatureState) setFeatureState(navParams.returnMode)
              setActivePage(navParams.returnPage)
            } else {
              setActivePage('dashboard')
            }
          }}
          className="p-3 rounded-full transition-all duration-300 bg-slate-100 hover:bg-slate-200 text-slate-500 flex items-center gap-2 pr-5"
          title="Back"
        >
          <ChevronLeft size={20} />
          <span className="text-[10px] font-black uppercase tracking-widest">Back</span>
        </button>
      </div>



      <div className="border rounded-[2.5rem] shadow-2xl overflow-hidden transition-all duration-500 bg-white border-slate-200 shadow-slate-200/50 text-slate-800">
        <div className="p-10">

          {/* ════════════════════════════════════════════════════
              FABRIC TAB
              ════════════════════════════════════════════════════ */}
          {activeTab === 'fabric' && (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                <FieldSelect label="Layer" value={config.FABRIC_LAYER || 'bronze'} onChange={handleLayerChange}
                  options={[{ value: 'bronze', label: 'Bronze' }, { value: 'silver', label: 'Silver' }, { value: 'gold', label: 'Gold' }]} />
                <FieldSelect label="Env" value={config.FABRIC_ENV || 'dev'} onChange={handleEnvChange}
                  options={[{ value: 'dev', label: 'Development' }, { value: 'qa', label: 'Quality Assurance' }, { value: 'prod', label: 'Production' }]} />
              </div>

              <div className="grid grid-cols-[140px_1fr] items-center gap-6">
                <label className="text-[11px] font-black uppercase tracking-[0.2em] opacity-30">Lakehouse</label>
                <input type="text" placeholder="Ex: LH_Sales_Data_Lake" value={config.FABRIC_LAKEHOUSE || ''} onChange={(e) => updateSelectedField('lakehouse', e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-5 py-3 text-xs font-mono outline-none focus:border-blue-500/50 transition-all hover:bg-white" />
              </div>
              <div className="grid grid-cols-[140px_1fr] items-center gap-6">
                <label className="text-[11px] font-black uppercase tracking-[0.2em] opacity-30">End Point</label>
                <input type="text" placeholder="Ex: tcp:fabric-sql.database.windows.net,1433" value={config.FABRIC_ENDPOINT || ''} onChange={(e) => updateSelectedField('endpoint', e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-5 py-3 text-xs font-mono outline-none focus:border-blue-500/50 transition-all hover:bg-white" />
              </div>

              <div className="flex items-center justify-between pt-4">
                <div>
                  <input type="file" id="import" className="hidden" onChange={handleImport} />
                  <button onClick={() => document.getElementById('import').click()}
                    className="flex items-center gap-2 text-[9px] font-black uppercase tracking-widest transition-colors text-slate-400 hover:text-blue-600">
                    <CloudUpload size={14} /> Auto-Fill
                  </button>
                </div>
                <SaveButton onClick={handleSaveFabric} />
              </div>
            </div>
          )}

          {/* ════════════════════════════════════════════════════
              DATABASE TAB
              ════════════════════════════════════════════════════ */}
          {activeTab === 'database' && (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                <FieldSelect label="Database Engine" value={dbConfig.engine || 'sqlite'} onChange={(v) => setDbConfig(prev => ({ ...prev, engine: v }))}
                  options={[{ value: 'sqlite', label: 'SQLite' }, { value: 'postgresql', label: 'PostgreSQL' }, { value: 'mysql', label: 'MySQL' }, { value: 'mssql', label: 'SQL Server' }]} />
                <FieldInput label="Database Name / Path" value={dbConfig.db_name} onChange={(v) => setDbConfig(prev => ({ ...prev, db_name: v }))} placeholder="Ex: etl_test.db" mono />
              </div>

              {dbConfig.engine !== 'sqlite' && (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-10 animate-in fade-in duration-300">
                    <FieldInput label="Host / Server" value={dbConfig.host} onChange={(v) => setDbConfig(prev => ({ ...prev, host: v }))} placeholder="Ex: localhost" mono />
                    <FieldInput label="Port" value={dbConfig.port} onChange={(v) => setDbConfig(prev => ({ ...prev, port: v }))} placeholder="Ex: 5432" mono />
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-10 animate-in fade-in duration-300">
                    <FieldInput label="Username" value={dbConfig.username} onChange={(v) => setDbConfig(prev => ({ ...prev, username: v }))} placeholder="Ex: postgres" mono />
                    <FieldInput label="Password" value={dbConfig.password} onChange={(v) => setDbConfig(prev => ({ ...prev, password: v }))} placeholder="••••••••" type="password" mono />
                  </div>
                </>
              )}

              <div className="flex items-center justify-end pt-4">
                <SaveButton onClick={handleSaveDb} label="Save Database Config" />
              </div>
            </div>
          )}

          {/* ════════════════════════════════════════════════════
              API SENTRY TAB
              ════════════════════════════════════════════════════ */}
          {activeTab === 'api_sentry' && (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                <div className="md:col-span-2">
                  <FieldInput label="Base URL" value={apiConfig.base_url} onChange={(v) => setApiConfig(prev => ({ ...prev, base_url: v }))} placeholder="https://fakestoreapi.com" mono />
                </div>
                <FieldInput label="Timeout (seconds)" value={apiConfig.timeout} onChange={(v) => setApiConfig(prev => ({ ...prev, timeout: parseInt(v) || 30 }))} placeholder="30" />
                <FieldToggle label="SSL Verify" value={apiConfig.ssl_verify} onChange={(v) => setApiConfig(prev => ({ ...prev, ssl_verify: v }))} />
              </div>
              <div className="flex items-center justify-end pt-4">
                <SaveButton onClick={() => handleSaveApi(apiConfig)} label="Save API Config" />
              </div>
            </div>
          )}

          {/* ════════════════════════════════════════════════════
              PIPELINE TAB
              ════════════════════════════════════════════════════ */}
          {activeTab === 'pipeline' && (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
                <FieldInput label="Row Limit" value={pipelineConfig.default_row_limit} onChange={(v) => setPipelineConfig(prev => ({ ...prev, default_row_limit: parseInt(v) || 10000 }))} placeholder="10000" />
                <FieldInput label="Chunk Size" value={pipelineConfig.default_chunk_size} onChange={(v) => setPipelineConfig(prev => ({ ...prev, default_chunk_size: parseInt(v) || 2000 }))} placeholder="2000" />
                <FieldInput label="Query Timeout (s)" value={pipelineConfig.default_query_timeout} onChange={(v) => setPipelineConfig(prev => ({ ...prev, default_query_timeout: parseInt(v) || 30 }))} placeholder="30" />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                <FieldInput label="Default Source DB" value={pipelineConfig.default_source_db} onChange={(v) => setPipelineConfig(prev => ({ ...prev, default_source_db: v }))} placeholder="test_audit_src_test.db" mono />
                <FieldInput label="Default Target DB" value={pipelineConfig.default_target_db} onChange={(v) => setPipelineConfig(prev => ({ ...prev, default_target_db: v }))} placeholder="test_audit_tgt_test.db" mono />
              </div>
              <div className="flex items-center justify-end pt-4">
                <SaveButton onClick={() => handleSavePipeline(pipelineConfig)} label="Save Pipeline Config" />
              </div>
            </div>
          )}

          {/* ════════════════════════════════════════════════════
              INTEGRATION TAB
              ════════════════════════════════════════════════════ */}
          {activeTab === 'integration' && (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                <FieldInput label="Source Database" value={integrationConfig.source_db} onChange={(v) => setIntegrationConfig(prev => ({ ...prev, source_db: v }))} placeholder="test_audit_src_test.db" mono />
                <FieldInput label="Target Database" value={integrationConfig.target_db} onChange={(v) => setIntegrationConfig(prev => ({ ...prev, target_db: v }))} placeholder="test_audit_tgt_test.db" mono />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                <FieldInput label="Key Column" value={integrationConfig.key_column} onChange={(v) => setIntegrationConfig(prev => ({ ...prev, key_column: v }))} placeholder="id" mono />
                <FieldSelect label="Reconciliation Type" value={integrationConfig.reconciliation_type} onChange={(v) => setIntegrationConfig(prev => ({ ...prev, reconciliation_type: v }))}
                  options={[{ value: 'data_diff', label: 'Data Diff' }, { value: 'schema_compare', label: 'Schema Compare' }, { value: 'full_reconciliation', label: 'Full Reconciliation' }]} />
              </div>
              <div className="flex items-center justify-end pt-4">
                <SaveButton onClick={() => handleSaveIntegration(integrationConfig)} label="Save Integration Config" />
              </div>
            </div>
          )}

          {/* ════════════════════════════════════════════════════
              TESTING TAB
              ════════════════════════════════════════════════════ */}
          {activeTab === 'testing' && (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
                <FieldInput label="CSV File" value={testingConfig.csv_file} onChange={(v) => setTestingConfig(prev => ({ ...prev, csv_file: v }))} placeholder="test_cases.csv" mono />
                <FieldInput label="SQL Directory" value={testingConfig.sql_dir} onChange={(v) => setTestingConfig(prev => ({ ...prev, sql_dir: v }))} placeholder="sql" mono />
                <FieldInput label="Report Directory" value={testingConfig.report_dir} onChange={(v) => setTestingConfig(prev => ({ ...prev, report_dir: v }))} placeholder="reports" mono />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                <FieldToggle label="Enable Parallel Execution" value={testingConfig.enable_parallel} onChange={(v) => setTestingConfig(prev => ({ ...prev, enable_parallel: v }))} />
                <FieldInput label="Max Workers" value={testingConfig.max_workers} onChange={(v) => setTestingConfig(prev => ({ ...prev, max_workers: parseInt(v) || 4 }))} placeholder="4" />
              </div>
              <div className="flex items-center justify-end pt-4">
                <SaveButton onClick={() => handleSaveTesting(testingConfig)} label="Save Testing Config" />
              </div>
            </div>
          )}

          {/* ════════════════════════════════════════════════════
              REPORTING TAB
              ════════════════════════════════════════════════════ */}
          {activeTab === 'reporting' && (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                <FieldInput label="Allure Results Path" value={reportingConfig.allure_results} onChange={(v) => setReportingConfig(prev => ({ ...prev, allure_results: v }))} placeholder="reports/allure-results" mono />
                <FieldInput label="XML Results Path" value={reportingConfig.xml_results} onChange={(v) => setReportingConfig(prev => ({ ...prev, xml_results: v }))} placeholder="reports/xml-results" mono />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                <FieldToggle label="Generate XML Reports" value={reportingConfig.generate_xml} onChange={(v) => setReportingConfig(prev => ({ ...prev, generate_xml: v }))} />
                <FieldToggle label="Generate HTML Reports" value={reportingConfig.generate_html} onChange={(v) => setReportingConfig(prev => ({ ...prev, generate_html: v }))} />
              </div>
              <div className="flex items-center justify-end pt-4">
                <SaveButton onClick={() => handleSaveReporting(reportingConfig)} label="Save Reporting Config" />
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  )
}
