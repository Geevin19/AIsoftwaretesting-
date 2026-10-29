import React from 'react';
import { Loader2, Sparkles, Cpu } from 'lucide-react';

export const Loader = ({ message = 'Processing...' }) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4">
      <div className="bg-white border border-slate-200 rounded-2xl p-6 max-w-md w-full shadow-2xl flex flex-col items-center text-center">
        <div className="relative mb-4">
          <div className="w-16 h-16 rounded-2xl bg-indigo-50 border border-indigo-200 flex items-center justify-center animate-pulse">
            <Cpu className="w-8 h-8 text-indigo-600" />
          </div>
          <Loader2 className="w-6 h-6 text-indigo-600 absolute -bottom-1 -right-1 animate-spin" />
        </div>

        <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2 mb-2">
          <Sparkles className="w-4 h-4 text-indigo-600" />
          AI Software Testing Engine
        </h3>

        <p className="text-xs text-slate-700 leading-relaxed font-mono bg-slate-50 p-3 rounded-lg border border-slate-200 w-full">
          {message}
        </p>

        <div className="mt-4 flex items-center gap-2 text-xs text-slate-500">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
          Subprocess Sandbox & Gemini LLM Active
        </div>
      </div>
    </div>
  );
};
