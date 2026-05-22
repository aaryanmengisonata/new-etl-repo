import React, { useState, useEffect, useRef } from 'react'
import {
  Plus, Edit2, Trash2, Search, Filter, Play, Save, X,
  Database, Upload, Download, FileText, Eye, CheckCircle,
  AlertTriangle, Loader2, List, FileSpreadsheet, RefreshCw, ChevronRight, Layers, Shield, Monitor
} from 'lucide-react'
import { api } from '../services/api'
import { useAppContext } from '../store/AppContext'

export default function TestCases() {
  const { selectedDataset, showAlert } = useAppContext()
  const [testCases, setTestCases] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isPreviewOpen, setIsPreviewOpen] = useState(false)
  const [selectedPreview, setSelectedPreview] = useState(null)
  const [editingId, setEditingId] = useState(null)
  const fileInputRef = useRef(null)

  const [formData, setFormData] = useState({
    functionality: '',
    test_id: '',
    sql_id: '',
    expected_condition: 'EQUAL',
    enabled: 'TRUE',
    description: ''
  })

  const fetchTestCases = async () => {
    try {
      const data = await api.getTestCases(selectedDataset)
      setTestCases(data)
    } catch (err) {
      console.error("Failed to fetch test cases:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    setLoading(true)
    fetchTestCases()
  }, [selectedDataset])

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const openModal = (testCase = null) => {
    if (testCase) {
      setEditingId(testCase.test_id)
      setFormData(testCase)
    } else {
      setEditingId(null)
      setFormData({
        functionality: 'general',
        test_id: `TC_${Math.floor(Math.random() * 1000)}`,
        sql_id: '1',
        expected_condition: 'EQUAL',
        enabled: 'TRUE',
        description: ''
      })
    }
    setIsModalOpen(true)
  }

  const handleSave = async (e) => {
    e.preventDefault()
    try {
      if (editingId) {
        await api.updateTestCase(selectedDataset, editingId, formData)
      } else {
        await api.createTestCase(selectedDataset, formData)
      }
      fetchTestCases()
      setIsModalOpen(false)
    } catch (err) {
      console.error("Failed to save:", err)
      showAlert("Save Failed", "Failed to save test case. Please review the inputs and try again.", "error")
    }
  }

  const handleDelete = async (test_id) => {
    showAlert(
      "Delete Test Case",
      `Are you sure you want to delete test case ${test_id}? This action cannot be undone.`,
      "confirm",
      async () => {
        try {
          await api.deleteTestCase(selectedDataset, test_id)
          fetchTestCases()
          showAlert("Deleted", `Test case ${test_id} has been deleted.`, "success")
        } catch (err) {
          console.error("Failed to delete:", err)
          showAlert("Delete Failed", "Failed to delete test case.", "error")
        }
      }
    )
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    const formDataUpload = new FormData()
    formDataUpload.append('file', file)

    try {
      setLoading(true)
      const res = await fetch('http://localhost:8000/api/test-cases/upload', {
        method: 'POST',
        body: formDataUpload
      })
      if (res.ok) {
        showAlert("Success", "Bulk test cases uploaded successfully!", "success")
        fetchTestCases()
      }
    } catch (err) {
      console.error("Upload failed", err)
    } finally {
      setLoading(false)
    }
  }

  const downloadTemplate = () => { window.location.href = 'http://localhost:8000/api/test-cases/template' }
  const downloadCurrentCSV = () => { window.location.href = 'http://localhost:8000/api/test-cases/download' }

  const filteredTests = testCases.filter(t =>
    t.test_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    t.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    t.functionality?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (loading) return (
    <div className="flex flex-col items-center justify-center p-20 gap-4 text-slate-400">
      <Loader2 className="animate-spin text-blue-600" size={32} />
      <p className="text-[10px] font-black uppercase tracking-[0.3em]">Parsing CSV Repository...</p>
    </div>
  )

  return (
    <div className="space-y-6 max-w-7xl animate-in fade-in slide-in-from-top-4 duration-500 text-left">
      {/* Top Banner */}
      <div className="p-8 border border-slate-200 rounded-[2.5rem] relative overflow-hidden bg-white shadow-xl shadow-slate-200/50">
        <div className="relative z-10 space-y-4">
          <div className="flex items-center gap-2 text-blue-600 font-black text-[9px] uppercase tracking-[0.3em]">
            <FileSpreadsheet size={14} /> Repository Active
          </div>
          <div className="space-y-1">
            <h1 className="text-2xl font-black uppercase tracking-tight text-slate-900">Test Cases</h1>
            <p className="text-xs font-bold text-slate-400 max-w-xl">
              Manage Data validation mappings, source-to-target reconciliation logic, and metadata quality rules within a unified framework.
            </p>
          </div>
        </div>
        <div className="absolute right-0 top-0 w-64 h-full flex items-center justify-center opacity-[0.03] pointer-events-none">
          <Monitor size={120} className="rotate-12 text-slate-900" />
        </div>
      </div>

      {/* Action Bar */}
      <div className="flex flex-wrap items-center justify-between gap-6 p-6 border border-slate-200 rounded-3xl bg-white shadow-lg">
        <div className="flex items-center gap-4 flex-1">
          <div className="relative group flex-1 max-w-md">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300 group-focus-within:text-blue-600 transition-colors" size={16} />
            <input
              type="text"
              placeholder="Search by ID, functionality, or description..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-12 pr-4 py-3 text-xs font-bold uppercase tracking-wider rounded-xl border border-slate-100 bg-slate-50 focus:bg-white focus:outline-none focus:ring-1 focus:ring-blue-500/20 w-full transition-all"
            />
          </div>
        </div>

        <div className="flex items-center gap-3">
          <input type="file" ref={fileInputRef} onChange={handleFileUpload} accept=".csv" className="hidden" />
          <button onClick={() => fileInputRef.current.click()} className="flex items-center gap-2 px-5 py-3 rounded-xl text-[10px] font-black uppercase tracking-widest text-slate-500 hover:text-blue-600 border border-slate-100 hover:bg-slate-50 transition-all">
            <Upload size={14} /> Bulk Port
          </button>
          <button onClick={downloadTemplate} className="flex items-center gap-2 px-5 py-3 rounded-xl text-[10px] font-black uppercase tracking-widest text-slate-500 hover:text-blue-600 border border-slate-100 hover:bg-slate-50 transition-all">
            <FileText size={14} /> Template
          </button>
          <div className="w-px h-6 bg-slate-100 mx-1" />
          <button
            onClick={() => openModal()}
            className="flex items-center gap-3 bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-xl text-[10px] font-black uppercase tracking-[0.2em] transition-all shadow-xl shadow-blue-500/20"
          >
            <Plus size={14} /> Add New Definition
          </button>
        </div>
      </div>

      {/* Repository Table */}
      <div className="border border-slate-200 rounded-[2rem] shadow-2xl overflow-hidden bg-white">
        <table className="w-full text-left order-collapse">
          <thead>
            <tr className="text-[10px] uppercase tracking-[0.2em] font-black text-slate-400 bg-slate-50/50 border-b border-slate-100">
              <th className="px-8 py-5">State</th>
              <th className="px-8 py-5">Object ID</th>
              <th className="px-8 py-5">Classification</th>
              <th className="px-8 py-5">Descriptor</th>
              <th className="px-8 py-5">Logic</th>
              <th className="px-8 py-5 text-right">Operations</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {filteredTests.map((t) => (
              <tr key={t.test_id} className="group hover:bg-slate-50/50 transition-colors">
                <td className="px-8 py-5">
                  <div className={`w-2 h-2 rounded-full ${t.enabled.toUpperCase() === 'TRUE' ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.3)]' : 'bg-slate-200'}`} />
                </td>
                <td className="px-8 py-5 font-mono text-[11px] font-black text-blue-600">{t.test_id}</td>
                <td className="px-8 py-5">
                  <span className="text-[9px] font-black px-2.5 py-1 rounded-lg bg-slate-100 text-slate-600 uppercase tracking-widest">
                    {t.functionality}
                  </span>
                </td>
                <td className="px-8 py-5 text-xs font-bold text-slate-500 truncate max-w-xs">{t.description}</td>
                <td className="px-8 py-5">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded-md border border-indigo-100 bg-indigo-50 text-[10px] font-black text-indigo-600 uppercase tracking-tighter">{t.expected_condition}</span>
                    <span className="text-[10px] font-bold text-slate-300">#{t.sql_id}</span>
                  </div>
                </td>
                <td className="px-8 py-5 text-right">
                  <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onClick={() => { setSelectedPreview(t); setIsPreviewOpen(true); }} className="p-2 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-900 transition-all"><Eye size={15} /></button>
                    <button onClick={() => openModal(t)} className="p-2 rounded-lg hover:bg-blue-50 text-slate-400 hover:text-blue-600 transition-all"><Edit2 size={15} /></button>
                    <button onClick={() => handleDelete(t.test_id)} className="p-2 rounded-lg hover:bg-rose-50 text-slate-400 hover:text-rose-600 transition-all"><Trash2 size={15} /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modal - Add / Edit */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-md z-50 flex items-center justify-center p-4 animate-in fade-in duration-300">
          <div className="bg-white rounded-[2.5rem] w-full max-w-lg shadow-[0_0_100px_rgba(0,0,0,0.1)] overflow-hidden border border-white">
            <div className="flex items-center justify-between px-10 py-8 border-b border-slate-50 bg-slate-50/50">
              <h3 className="text-xs font-black uppercase tracking-[0.3em] flex items-center gap-3 text-slate-900">
                <Database size={16} className="text-blue-600" />
                {editingId ? 'Modify Definition' : 'Define New Protocol'}
              </h3>
              <button onClick={() => setIsModalOpen(false)} className="p-2 rounded-full hover:bg-slate-200 text-slate-400 transition-colors"><X size={20} /></button>
            </div>

            <form onSubmit={handleSave} className="p-10 space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-1">Object ID</label>
                  <input required name="test_id" value={formData.test_id} onChange={handleInputChange} className="w-full border border-slate-100 bg-slate-50 rounded-2xl px-5 py-4 text-xs font-black text-slate-900 focus:bg-white focus:ring-1 focus:ring-blue-500/20 outline-none transition-all" readOnly={!!editingId} />
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-1">Classification</label>
                  <input required name="functionality" value={formData.functionality} onChange={handleInputChange} className="w-full border border-slate-100 bg-slate-50 rounded-2xl px-5 py-4 text-xs font-black text-slate-900 focus:bg-white focus:ring-1 focus:ring-blue-500/20 outline-none transition-all" />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-1">Descriptor</label>
                <textarea required name="description" value={formData.description} onChange={handleInputChange} className="w-full border border-slate-100 bg-slate-50 rounded-2xl px-5 py-4 text-xs font-black text-slate-900 h-24 resize-none focus:bg-white focus:ring-1 focus:ring-blue-500/20 outline-none transition-all" />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2 col-span-1">
                  <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-1">Logic ID</label>
                  <input required name="sql_id" type="number" value={formData.sql_id} onChange={handleInputChange} className="w-full border border-slate-100 bg-slate-50 rounded-2xl px-5 py-4 text-xs font-black text-slate-900 focus:bg-white focus:ring-1 focus:ring-blue-500/20 outline-none transition-all" />
                </div>
                <div className="space-y-2 col-span-2">
                  <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-1">Expected Clause</label>
                  <select name="expected_condition" value={formData.expected_condition} onChange={handleInputChange} className="w-full border border-slate-100 bg-slate-50 rounded-2xl px-5 py-4 text-[10px] font-black uppercase tracking-widest text-slate-900 focus:bg-white focus:ring-1 focus:ring-blue-500/20 outline-none transition-all cursor-pointer">
                    <option value="EQUAL">EQUAL asserting</option>
                    <option value="NOT_EQUAL">NOT_EQUAL asserting</option>
                    <option value="GREATER_THAN">GREATER_THAN asserting</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-4 pt-6">
                <button type="button" onClick={() => setIsModalOpen(false)} className="px-8 py-4 text-[10px] font-black uppercase tracking-widest text-slate-400 hover:text-slate-900 transition-colors">Discard</button>
                <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white px-10 py-4 rounded-[1.5rem] text-[10px] font-black uppercase tracking-[0.2em] transition-all shadow-xl shadow-blue-500/20">Commit Definition</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Preview Side Sheet */}
      {isPreviewOpen && selectedPreview && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-md animate-in fade-in duration-500" onClick={() => setIsPreviewOpen(false)} />
          <div className="relative w-full max-w-lg bg-white shadow-2xl overflow-y-auto animate-in slide-in-from-right duration-500 flex flex-col border-l border-slate-100">
            <div className="px-10 py-8 border-b border-slate-50 flex items-center justify-between sticky top-0 bg-white/90 backdrop-blur-md z-10">
              <div>
                <p className="text-[9px] font-black text-blue-600 uppercase tracking-[0.3em] mb-2">Metadata Spectrum</p>
                <h3 className="text-xl font-black uppercase tracking-tight text-slate-900">{selectedPreview.test_id}</h3>
              </div>
              <button onClick={() => setIsPreviewOpen(false)} className="p-3 rounded-full hover:bg-slate-100 text-slate-400 transition-colors"><X size={20} /></button>
            </div>

            <div className="p-10 space-y-12">
              <div className="space-y-6">
                <div className="flex items-center gap-3 text-slate-900">
                  <div className="w-8 h-8 rounded-xl bg-slate-100 flex items-center justify-center text-slate-500"><Layers size={16} /></div>
                  <h4 className="text-xs font-black uppercase tracking-widest">Architectural Mapping</h4>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <SummaryItem label="Identifier" val={selectedPreview.test_id} />
                  <SummaryItem label="Functional Unit" val={selectedPreview.functionality} />
                  <SummaryItem label="Validation Clause" val={selectedPreview.expected_condition} />
                  <SummaryItem label="Reference ID" val={`SQL_GATEWAY_${selectedPreview.sql_id}`} />
                </div>
              </div>

              <div className="space-y-6">
                <div className="flex items-center gap-3 text-slate-900">
                  <div className="w-8 h-8 rounded-xl bg-slate-100 flex items-center justify-center text-slate-500"><FileText size={16} /></div>
                  <h4 className="text-xs font-black uppercase tracking-widest">Narrative Descriptor</h4>
                </div>
                <div className="p-8 rounded-3xl bg-slate-50 border border-slate-100 relative">
                  <p className="text-xs leading-relaxed italic font-bold text-slate-700 relative z-10">
                    "{selectedPreview.description}"
                  </p>
                  <div className="absolute top-4 right-6 text-slate-200 select-none"><Shield size={40} /></div>
                </div>
              </div>

              <div className="p-8 rounded-[2rem] bg-indigo-600 text-white shadow-2xl shadow-indigo-500/20 flex flex-col gap-4">
                <div className="flex items-center gap-4">
                  <ShieldCheck size={24} className="opacity-50" />
                  <h5 className="text-xs font-black uppercase tracking-widest">Integrity Assurance</h5>
                </div>
                <p className="text-[11px] font-bold leading-relaxed opacity-80 uppercase tracking-tight">
                  This definition is correctly mapped to the master transformation layer. Deployment will trigger a targeted audit of all associated relational table objects.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function ShieldCheck({ size, className }) {
  return <Shield size={size} className={className} />
}

function SummaryItem({ label, val }) {
  return (
    <div className="p-5 rounded-2xl bg-slate-50 border border-slate-100 shadow-sm flex flex-col gap-1">
      <span className="text-[8px] font-black uppercase tracking-[0.2em] text-slate-400">{label}</span>
      <span className="text-xs font-black uppercase tracking-tight text-slate-900 truncate">{val}</span>
    </div>
  )
}
