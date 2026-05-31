import React from 'react'
import { useAppContext } from './store/AppContext'
import Sidebar from './components/Sidebar'
import Header from './components/Header'
import Dashboard from './pages/Dashboard'
import RunTests from './pages/RunTests'
import Reports from './pages/Reports'
import Configuration from './pages/Configuration'
import Logs from './pages/Logs'
import TestCases from './pages/TestCases'
import FabricAudit from './pages/FabricAudit'
import ApiSentry from './pages/ApiSentry'
import DbAuditor from './pages/DbAuditor'
import EtlAuditor from './pages/EtlAuditor'
import IntegrationSentry from './pages/IntegrationSentry'
import Welcome from './pages/Welcome'
import { X, AlertCircle, CheckCircle as CheckCircleIcon, Sparkles } from 'lucide-react'

import Footer from './components/shared/Footer'

export default function App() {
  const { 
    activePage, setActivePage, 
    navParams, setNavParams, 
    featureState, setFeatureState,
    isSettingsOpen, setIsSettingsOpen,
    customAlert, setCustomAlert,
    setActiveModule
  } = useAppContext()

  console.log("App render: activePage =", activePage, "navParams =", navParams)

  React.useEffect(() => {
    if (['db_auditor', 'fabric_audit', 'etl_auditor', 'api_sentry', 'integration_sentry'].includes(activePage)) {
      setActiveModule(activePage);
    }
  }, [activePage, setActiveModule]);


  const pages = {
    dashboard: <Dashboard setActivePage={setActivePage} />,
    test_cases: <TestCases />,
    run: <RunTests />,
    reports: <Reports />,
    fabric_audit: <FabricAudit setActivePage={setActivePage} setNavParams={setNavParams} />,
    api_sentry: <ApiSentry />,
    db_auditor: <DbAuditor />,
    etl_auditor: <EtlAuditor />,
    integration_sentry: <IntegrationSentry />,
    configuration: <Configuration navParams={navParams} setActivePage={setActivePage} setFeatureState={setFeatureState} />,
    logs: <Logs />,
    welcome: <Welcome />,
  }

  const currentPage = pages[activePage] || pages.dashboard

  return (
    <div className="flex h-screen overflow-hidden bg-white text-slate-800">
      {!['dashboard', 'welcome'].includes(activePage) && (
        <Sidebar activePage={activePage} setActivePage={setActivePage} featureState={featureState} setFeatureState={setFeatureState} />
      )}
      <div className="flex flex-col flex-1 overflow-hidden relative">
        {!['dashboard', 'welcome'].includes(activePage) && <Header activePage={activePage} />}
        
        <main className={`flex-1 flex flex-col min-h-0 bg-white pb-10 ${(['fabric_audit', 'api_sentry', 'db_auditor', 'integration_sentry', 'etl_auditor'].includes(activePage) && featureState === 'execution') ? 'overflow-hidden' : 'overflow-y-auto'}`}>
          {React.cloneElement(currentPage, { featureState, setFeatureState })}
        </main>
        
        {!['dashboard'].includes(activePage) && <Footer />}

        {/* Global Settings Modal */}
        {isSettingsOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-in fade-in duration-300">
            <div className="bg-white w-full max-w-4xl max-h-[90vh] rounded-[2.5rem] shadow-2xl overflow-hidden flex flex-col animate-in zoom-in-95 duration-300">
              <div className="p-6 border-b flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-black text-slate-900">Settings</h2>
                  <p className="text-xs text-slate-400">Global System Configuration</p>
                </div>
                <button 
                  onClick={() => setIsSettingsOpen(false)}
                  className="p-2 rounded-xl hover:bg-slate-100 transition-colors"
                >
                  <X size={20} className="text-slate-400" />
                </button>
              </div>
              <div className="flex-1 overflow-y-auto p-6">
                <Configuration navParams={{}} setActivePage={() => setIsSettingsOpen(false)} />
              </div>
            </div>
          </div>
        )}
        {/* Custom Alert / Confirmation Modal */}
        {customAlert && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-in fade-in duration-100">
            <div className="relative bg-white border border-slate-100 w-full max-w-md rounded-3xl shadow-2xl flex flex-col p-6 overflow-hidden animate-in zoom-in-95 duration-100 animate-out fade-out zoom-out-95">
              {/* Subtle Background Pattern */}
              <div className="absolute top-0 right-0 w-36 h-36 bg-blue-50/50 rounded-full blur-3xl -z-10" />
              
              <div className="flex items-start gap-4">
                <div className={`w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 ${
                  customAlert.type === 'success' ? 'bg-emerald-50 text-emerald-600' :
                  customAlert.type === 'error' ? 'bg-rose-50 text-rose-600' :
                  customAlert.type === 'confirm' ? 'bg-amber-50 text-amber-600' :
                  'bg-blue-50 text-blue-600'
                }`}>
                  {customAlert.type === 'success' && <CheckCircleIcon size={22} />}
                  {customAlert.type === 'error' && <AlertCircle size={22} />}
                  {customAlert.type === 'confirm' && <AlertCircle size={22} />}
                  {customAlert.type === 'info' && <Sparkles size={22} />}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-base font-black text-slate-800 tracking-tight mb-2">
                    {customAlert.title}
                  </h3>
                  <p className="text-sm font-medium text-slate-500 leading-relaxed whitespace-pre-line">
                    {customAlert.message}
                  </p>
                </div>
              </div>

              <div className="mt-8 flex items-center justify-end gap-3">
                {customAlert.type === 'confirm' ? (
                  <>
                    <button 
                      onClick={() => setCustomAlert(null)}
                      className="px-4 py-2 rounded-xl text-xs font-black uppercase tracking-wider text-slate-500 hover:bg-slate-50 transition-colors"
                    >
                      Cancel
                    </button>
                    <button 
                      onClick={() => {
                        if (customAlert.onConfirm) customAlert.onConfirm();
                        setCustomAlert(null);
                      }}
                      className="px-6 py-3 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-[10px] font-black uppercase tracking-widest transition-all active:scale-95 shadow-md shadow-slate-900/10"
                    >
                      Confirm
                    </button>
                  </>
                ) : (
                  <button 
                    onClick={() => setCustomAlert(null)}
                    className={`px-6 py-3 rounded-xl text-[10px] font-black uppercase tracking-widest text-white transition-all active:scale-95 shadow-lg ${
                      customAlert.type === 'success' ? 'bg-emerald-600 hover:bg-emerald-700 shadow-emerald-500/10' :
                      customAlert.type === 'error' ? 'bg-rose-600 hover:bg-rose-700 shadow-rose-500/10' :
                      'bg-blue-600 hover:bg-blue-700 shadow-blue-500/10'
                    }`}
                  >
                    Dismiss
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
