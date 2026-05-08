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
import Welcome from './pages/Welcome'
import { X } from 'lucide-react'

import Footer from './components/shared/Footer'

export default function App() {
  const { 
    activePage, setActivePage, 
    navParams, setNavParams, 
    featureState, setFeatureState,
    isSettingsOpen, setIsSettingsOpen
  } = useAppContext()

  const pages = {
    dashboard: <Dashboard setActivePage={setActivePage} />,
    test_cases: <TestCases />,
    run: <RunTests />,
    reports: <Reports />,
    fabric_audit: <FabricAudit setActivePage={setActivePage} setNavParams={setNavParams} />,
    configuration: <Configuration navParams={navParams} setActivePage={setActivePage} />,
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
        
        <main className={`flex-1 flex flex-col min-h-0 bg-white pb-10 ${(activePage === 'fabric_audit' && featureState === 'execution') ? 'overflow-hidden' : 'overflow-y-auto'}`}>
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
      </div>
    </div>
  )
}
