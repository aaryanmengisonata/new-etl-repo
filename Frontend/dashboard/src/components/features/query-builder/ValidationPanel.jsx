import React, { useState } from 'react';
import { ShieldCheck, Plus, Sparkles, Send, CheckCircle2, ChevronDown, ListChecks, Zap } from 'lucide-react';

const INITIAL_VALIDATIONS = [
  { id: 'v1', name: 'Null Ratio Check', desc: 'Ensures target column has highly similar null ratios as the source table, preventing data loss during ELT.', type: 'Data Quality' },
  { id: 'v2', name: 'Format Matching', desc: 'Validates that column data types and string formats match the expected regex standard.', type: 'Schema Validate' },
  { id: 'v3', name: 'Volume Diff', desc: 'Compares the volume of row changes against an expected threshold between Delta layers.', type: 'Reconciliation' },
  { id: 'v4', name: 'Referential Integrity', desc: 'Checks foreign keys across Bronze -> Silver layer joins to ensure no orphaned records exist.', type: 'Integrity Check' }
];

export default function ValidationPanel() {
  const [validations, setValidations] = useState(INITIAL_VALIDATIONS);
  const [activeValidationId, setActiveValidationId] = useState(INITIAL_VALIDATIONS[0].id);
  const [prompt, setPrompt] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [isEditingName, setIsEditingName] = useState(false);

  const activeValidation = validations.find(v => v.id === activeValidationId) || validations[0];

  const handleCreateNew = () => {
    const newId = `v${Date.now()}`;
    const newValidation = {
      id: newId,
      name: 'New Functionality',
      desc: 'No description generated yet. Use the prompt box to define the functionality rules and AI will generate the validation logic.',
      type: 'Custom API'
    };
    setValidations(prev => [...prev, newValidation]);
    setActiveValidationId(newId);
    setIsEditingName(true);
  };

  const handleRun = () => {
    if (!prompt.trim()) return;
    
    setIsRunning(true);
    // Simulate AI LLM delay
    setTimeout(() => {
      setValidations(prev => prev.map(v => {
        if (v.id === activeValidationId) {
          // If it's a completely new functionality, update title too based on prompt smartly
          const isNew = v.name === 'New Functionality';
          return {
            ...v,
            desc: `[Updated via Prompt]: ${prompt}\n\n${!isNew ? v.desc : ''}`
          };
        }
        return v;
      }));
      setPrompt('');
      setIsRunning(false);
    }, 1200);
  };

  return (
    <div className="w-full h-full flex flex-col bg-slate-50/50 animate-in fade-in duration-500">
      <div className="flex-1 flex gap-6 p-6 overflow-hidden">
        
        {/* Left Panel: Prompt Input Box & Operations */}
        <div className="w-[45%] h-full flex flex-col bg-white rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.06)] border border-slate-200/60 overflow-hidden relative z-10 flex-shrink-0">
          <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-3 bg-white shrink-0">
             <div className="w-7 h-7 rounded-lg bg-blue-50 border border-blue-100 flex items-center justify-center shadow-sm">
                 <Sparkles size={14} className="text-blue-600" />
             </div>
             <h2 className="text-[13px] font-black text-slate-800 tracking-tight flex-1">
                Validation Prompt
             </h2>
          </div>
          
          <div className="p-6 flex-1 flex flex-col gap-5 overflow-y-auto [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
             
             <div className="flex flex-col gap-4">
                {/* Dropdown & Editable Name Cell */}
                <div className="flex items-center gap-3">
                   <div className="flex-1 relative group">
                      <label className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-1.5 block ml-1">{isEditingName ? 'Name Functionality' : 'Select Functionality'}</label>
                      {isEditingName ? (
                         <input
                            autoFocus
                            type="text"
                            value={activeValidation.name}
                            onChange={(e) => setValidations(prev => prev.map(v => v.id === activeValidationId ? { ...v, name: e.target.value } : v))}
                            onKeyDown={(e) => e.key === 'Enter' && setIsEditingName(false)}
                            className="w-full bg-white text-[13px] font-bold text-blue-600 border border-blue-300 rounded-xl px-4 py-2.5 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all shadow-md"
                            placeholder="Type name and press Enter..."
                         />
                      ) : (
                         <>
                            <select
                               value={activeValidationId}
                               onChange={(e) => setActiveValidationId(e.target.value)}
                               className="w-full appearance-none bg-white text-[13px] font-semibold text-slate-700 border border-slate-200 rounded-xl px-4 py-2.5 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all cursor-pointer shadow-sm hover:border-slate-300"
                            >
                               {validations.map(v => (
                                  <option key={v.id} value={v.id}>{v.name}</option>
                               ))}
                            </select>
                            <ChevronDown className="absolute right-4 top-[32px] text-slate-400 pointer-events-none group-hover:text-slate-600 transition-colors" size={14} />
                         </>
                      )}
                   </div>
                   <div className="mt-5 shrink-0">
                      {isEditingName ? (
                         <button 
                            onClick={() => setIsEditingName(false)}
                            className="px-4 py-2.5 rounded-xl bg-emerald-50 hover:bg-emerald-100 text-emerald-600 text-[12px] font-bold transition-all flex items-center gap-1.5 border border-emerald-200 shadow-sm"
                         >
                            <CheckCircle2 size={14} /> Save
                         </button>
                      ) : (
                         <button 
                            onClick={handleCreateNew}
                            className="px-4 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-[12px] font-bold transition-all flex items-center gap-1.5 border border-slate-200 shadow-sm"
                         >
                            <Plus size={14} className="text-blue-600" /> New
                         </button>
                      )}
                   </div>
                </div>

             </div>

             {/* Prompt Box */}
             <div className="flex-1 flex flex-col">
                <label className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-1.5 ml-1">AI Prompt Input</label>
                <div className="flex-1 relative rounded-xl border border-slate-200 bg-slate-50/50 shadow-inner overflow-hidden focus-within:border-blue-500 focus-within:ring-4 focus-within:ring-blue-500/10 transition-all flex flex-col">
                   <textarea 
                     value={prompt}
                     onChange={(e) => setPrompt(e.target.value)}
                     className="w-full flex-1 bg-transparent px-4 py-4 text-[13px] leading-relaxed text-slate-700 outline-none resize-none placeholder:text-slate-400"
                     placeholder="Type your validation changes or new logic here. Example: 'Modify this functionality to check for blank strings instead of just nulls...'"
                   />
                </div>
             </div>

             {/* Run Button */}
             <div className="shrink-0 pt-2">
                <button 
                  onClick={handleRun}
                  disabled={isRunning || !prompt.trim()}
                  className={`w-full py-3 rounded-xl text-[13px] font-bold shadow-lg transition-all active:scale-[0.98] flex items-center justify-center gap-2 ${
                     isRunning || !prompt.trim() 
                     ? 'bg-slate-200 text-slate-400 shadow-none cursor-not-allowed border border-slate-200'
                     : 'bg-blue-600 hover:bg-blue-700 text-white shadow-blue-500/20'
                  }`}
                >
                   {isRunning ? <><Zap className="animate-pulse" size={14} /> Generating Changes...</> : <><Send size={14} /> Run Transformation</>}
                </button>
             </div>
          </div>
        </div>

        {/* Right Panel: Framework Validation Info */}
        <div className="w-[55%] h-full flex flex-col bg-white rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.06)] border border-slate-200/60 relative overflow-hidden flex-shrink-0">
          
          <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between shrink-0 bg-slate-50/50">
             <div className="flex items-center gap-3">
                <div className="flex gap-1.5">
                   <div className="w-3 h-3 rounded-full bg-rose-400/80 shadow-[0_0_8px_rgba(244,63,94,0.2)]" />
                   <div className="w-3 h-3 rounded-full bg-amber-400/80 shadow-[0_0_8px_rgba(245,158,11,0.2)]" />
                   <div className="w-3 h-3 rounded-full bg-emerald-400/80 shadow-[0_0_8px_rgba(16,185,129,0.2)]" />
                </div>
                <h2 className="text-[13px] font-bold text-slate-700 ml-3 tracking-wide">Validation Output</h2>
             </div>
             <ShieldCheck size={16} className="text-blue-500/80" />
          </div>

          <div className="p-6 flex-1 flex flex-col gap-6 overflow-hidden z-10">
            {/* Synchronized Dropdown */}
            <div className="shrink-0 relative">
               <label className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-2.5 ml-1 flex items-center gap-2">
                  <ListChecks size={12} className="text-blue-500" />
                  Active Functionality Context
               </label>
               <div className="relative group">
                  <select
                     value={activeValidationId}
                     onChange={(e) => setActiveValidationId(e.target.value)}
                     className="w-full appearance-none bg-white text-[13px] font-bold text-slate-800 border border-slate-200 rounded-xl px-4 py-3 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all cursor-pointer shadow-sm hover:border-slate-300"
                  >
                     {validations.map(v => (
                        <option key={v.id} value={v.id}>{v.name}</option>
                     ))}
                  </select>
                  <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none group-hover:text-slate-600 transition-colors" size={14} />
               </div>
            </div>

            {/* Validation Info Box */}
            <div className="bg-slate-50 border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col">
               <div className="space-y-6">
                  <div>
                     <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400 block mb-2 border-b border-slate-200 pb-2">Functionality Behavior & Description</span>
                     <p className="text-[13px] leading-relaxed text-slate-700 whitespace-pre-wrap">{activeValidation.desc}</p>
                  </div>
               </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
