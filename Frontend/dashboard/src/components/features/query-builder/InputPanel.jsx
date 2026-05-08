import React from 'react';
import { MessageSquare, Zap, Loader2 } from 'lucide-react';

export default function InputPanel({ prompt, setPrompt, onGenerate, isLoading }) {
  return (
    <div className="flex flex-col h-full rounded-2xl border border-slate-200 bg-white shadow-lg overflow-hidden transition-all duration-300">
      <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-100 flex items-center justify-center">
            <MessageSquare size={18} className="text-purple-600" />
          </div>
          <span className="text-sm text-slate-500 uppercase tracking-wide font-semibold">Requirement Prompt</span>
        </div>
      </div>
      
      <div className="flex-1 p-6 flex flex-col gap-6">
        <div className="flex-1 relative group">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="What logic would you like to build? (e.g., 'Reconcile Bronze and Silver layers')"
            className="w-full h-full p-4 rounded-xl border border-slate-200 focus:border-indigo-500 outline-none transition-all duration-200 resize-none text-base text-slate-800 placeholder:text-slate-400"
          />
          <div className="absolute top-4 right-4 pointer-events-none opacity-0 group-focus-within:opacity-100 transition-opacity">
            <div className="w-2 h-2 rounded-full bg-purple-500 animate-pulse" />
          </div>
        </div>

        <button
          onClick={onGenerate}
          disabled={isLoading || !prompt.trim()}
          className="w-full py-4 px-6 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-medium shadow-md hover:shadow-lg transition-all duration-200 flex items-center justify-center gap-3 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <>
              <Loader2 className="animate-spin" size={18} />
              <span>Generating query...</span>
            </>
          ) : (
            <>
              <Zap size={18} className={prompt.trim() ? "fill-white" : ""} />
              <span>Generate / Fix Query</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
