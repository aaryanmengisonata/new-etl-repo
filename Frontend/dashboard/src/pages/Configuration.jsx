import React, { useState, useEffect } from 'react'
import {
  Loader2, CheckCircle, CloudUpload, ChevronLeft, ChevronDown
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

export default function Configuration({ navParams, setActivePage, setFeatureState }) {
  const [config, setConfig] = useState({ ...defaultConfig, FABRIC_CONFIGS: cloneConfigs() })
  const [loading, setLoading] = useState(true)
  const [saved, setSaved] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    api.getConfig()
      .then(data => {
        setConfig(syncSelectedValues({
          ...defaultConfig,
          ...data,
          FABRIC_CONFIGS: mergeConfigs(data.FABRIC_CONFIGS),
        }))
        setLoading(false)
      })
      .catch(err => {
        console.error("Failed to load config:", err)
        setLoading(false)
      })
  }, [navParams])

  const handleSave = async () => {
    try {
      setSaving(true)
      const response = await api.saveConfig(config)
      setConfig(prev => syncSelectedValues({
        ...prev,
        ...(response?.config || {}),
        FABRIC_CONFIGS: mergeConfigs(response?.config?.FABRIC_CONFIGS),
      }))
      setSaved(true)
      setTimeout(() => {
        setSaved(false)
        setActivePage('fabric_audit')
      }, 1500)
    } catch (err) {
      console.error("Failed to save config:", err)
      alert("Failed to save configuration.")
    } finally {
      setSaving(false)
    }
  }

  const mapImportedConfig = (imported) => {
    const nextConfigs = cloneConfigs()
    const envKeyMap = {
      dev: 'DEV',
      qa: 'QAT',
      prod: 'PROD',
    }

    for (const env of ['dev', 'qa', 'prod']) {
      for (const layer of ['bronze', 'silver', 'gold']) {
        const prefix = layer.toUpperCase()
        const envPrefix = envKeyMap[env]
        nextConfigs[env][layer] = {
          lakehouse:
            imported[`${envPrefix}_${prefix}_LAKEHOUSE_NAME`] ||
            imported[`${prefix}_LAKEHOUSE_NAME`] ||
            '',
          endpoint:
            imported[`${envPrefix}_${prefix}_SQL_ENDPOINT`] ||
            imported[`${prefix}_SQL_ENDPOINT`] ||
            '',
        }
      }
    }

    const environment = imported.ENVIRONMENT?.toUpperCase()
    const activeLayer = imported.ACTIVE_FABRIC_LAYER?.toLowerCase() || imported.FABRIC_LAYER?.toLowerCase() || 'bronze'
    const selectedEnv =
      environment === 'DEV' ? 'dev' :
      environment === 'QAT' || environment === 'QA' || environment === 'TEST' ? 'qa' :
      environment === 'PROD' ? 'prod' :
      'dev'

    return syncSelectedValues({
      FABRIC_LAYER: activeLayer,
      FABRIC_ENV: selectedEnv,
      FABRIC_LAKEHOUSE: '',
      FABRIC_ENDPOINT: '',
      FABRIC_CONFIGS: nextConfigs,
    })
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
      } catch (err) { alert("Invalid file") }
    }
    reader.readAsText(file)
  }

  const handleLayerChange = (value) => {
    setConfig(prev => syncSelectedValues({
      ...prev,
      FABRIC_LAYER: value,
    }))
  }

  const handleEnvChange = (value) => {
    setConfig(prev => syncSelectedValues({
      ...prev,
      FABRIC_ENV: value,
    }))
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

  return (
    <div className="max-w-4xl mx-auto animate-in fade-in slide-in-from-top-4 duration-700 space-y-8">
      <div className="flex items-start justify-between">
        <div className="flex flex-col gap-2">
          <h1 className="text-3xl font-black tracking-tight text-slate-900">
            Master Configuration
          </h1>
          <p className="text-[10px] font-bold uppercase tracking-[0.3em] opacity-30">
            Fabric Reconciliation Protocol
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
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
              <div className="space-y-3">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] opacity-30 ml-1">Layer</label>
                <div className="relative group">
                  <select
                    value={config.FABRIC_LAYER || 'bronze'}
                    onChange={(e) => handleLayerChange(e.target.value)}
                    className="w-full appearance-none bg-slate-50 border border-slate-200 rounded-2xl px-6 py-4 text-[11px] font-black uppercase tracking-widest outline-none focus:border-blue-500/50 transition-all cursor-pointer hover:bg-white"
                  >
                    <option value="bronze">Bronze</option>
                    <option value="silver">Silver</option>
                    <option value="gold">Gold</option>
                  </select>
                  <ChevronDown className="absolute right-6 top-1/2 -translate-y-1/2 opacity-30 group-hover:opacity-100 transition-opacity pointer-events-none" size={16} />
                </div>
              </div>

              <div className="space-y-3">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] opacity-30 ml-1">Env</label>
                <div className="relative group">
                  <select
                    value={config.FABRIC_ENV || 'dev'}
                    onChange={(e) => handleEnvChange(e.target.value)}
                    className="w-full appearance-none bg-slate-50 border border-slate-200 rounded-2xl px-6 py-4 text-[11px] font-black uppercase tracking-widest outline-none focus:border-blue-500/50 transition-all cursor-pointer hover:bg-white"
                  >
                    <option value="dev">Development</option>
                    <option value="qa">Quality Assurance</option>
                    <option value="prod">Production</option>
                  </select>
                  <ChevronDown className="absolute right-6 top-1/2 -translate-y-1/2 opacity-30 group-hover:opacity-100 transition-opacity pointer-events-none" size={16} />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-[140px_1fr] items-center gap-6">
              <label className="text-[11px] font-black uppercase tracking-[0.2em] opacity-30">Lakehouse</label>
              <input
                type="text"
                placeholder="Ex: LH_Sales_Data_Lake"
                value={config.FABRIC_LAKEHOUSE || ''}
                onChange={(e) => updateSelectedField('lakehouse', e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-5 py-3 text-xs font-mono outline-none focus:border-blue-500/50 transition-all hover:bg-white"
              />
            </div>

            <div className="grid grid-cols-[140px_1fr] items-center gap-6">
              <label className="text-[11px] font-black uppercase tracking-[0.2em] opacity-30">End Point</label>
              <input
                type="text"
                placeholder="Ex: tcp:fabric-sql.database.windows.net,1433"
                value={config.FABRIC_ENDPOINT || ''}
                onChange={(e) => updateSelectedField('endpoint', e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-5 py-3 text-xs font-mono outline-none focus:border-blue-500/50 transition-all hover:bg-white"
              />
            </div>

            <div className="flex items-center justify-between pt-4">
              <div>
                <input type="file" id="import" className="hidden" onChange={handleImport} />
                <button
                  onClick={() => document.getElementById('import').click()}
                  className="flex items-center gap-2 text-[9px] font-black uppercase tracking-widest transition-colors text-slate-400 hover:text-blue-600"
                >
                  <CloudUpload size={14} /> Auto-Fill
                </button>
              </div>
              <button
                onClick={handleSave}
                disabled={saving}
                className={`px-12 py-4 rounded-xl text-[10px] font-black uppercase tracking-[0.2em] text-white transition-all duration-300 transform active:scale-95 shadow-xl ${saving ? 'bg-slate-700' :
                  saved ? 'bg-emerald-600 shadow-emerald-500/20' :
                    'bg-blue-600 hover:bg-blue-700 shadow-blue-500/20'
                  }`}
              >
                {saving ? <span className="flex items-center gap-2"><Loader2 size={12} className="animate-spin" /> Saving...</span>
                  : saved ? <span className="flex items-center gap-2"><CheckCircle size={12} /> Saved</span>
                    : 'Save'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
