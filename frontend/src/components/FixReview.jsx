import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { Check, X, Sparkles, Copy, CheckCheck, AlertTriangle, FileCode } from 'lucide-react';

export const FixReview = () => {
  const { activeAnalysis, acceptFix, rejectFix } = useApp();
  const [copied, setCopied] = useState(false);

  if (!activeAnalysis) return null;

  const handleCopy = () => {
    if (activeAnalysis.suggestedFix) {
      navigator.clipboard.writeText(activeAnalysis.suggestedFix);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-white border border-slate-200 rounded-2xl max-w-3xl w-full shadow-2xl overflow-hidden my-8">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-slate-50 border-b border-slate-200">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-50 border border-indigo-200 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-indigo-600" />
            </div>
            <div>
              <h3 className="text-sm sm:text-base font-semibold text-slate-900 flex items-center gap-2">
                AI Bug Diagnosis & Proposed Fix
              </h3>
              <div className="flex items-center gap-2 text-xs text-slate-500 mt-0.5">
                <span>Failing Test:</span>
                <span className="text-slate-800 font-mono font-medium">{activeAnalysis.testName}</span>
                <span>•</span>
                <span className="flex items-center gap-1 font-mono text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
                  <FileCode className="w-3 h-3" />
                  {activeAnalysis.file || 'main.py'}
                </span>
              </div>
            </div>
          </div>
          <button
            onClick={rejectFix}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-4 max-h-[75vh] overflow-y-auto">
          {/* Discrepancy Overview */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs bg-slate-50 p-3 rounded-lg border border-slate-200 font-mono">
            <div>
              <span className="text-slate-500 block mb-1 font-sans font-medium">Expected Result:</span>
              <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 inline-block font-semibold">
                {typeof activeAnalysis.expected === 'string'
                  ? activeAnalysis.expected
                  : JSON.stringify(activeAnalysis.expected)}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block mb-1 font-sans font-medium">Actual Result:</span>
              <span className="text-rose-700 bg-rose-50 px-2 py-0.5 rounded border border-rose-200 inline-block font-semibold">
                {String(activeAnalysis.actual)}
              </span>
            </div>
          </div>

          {/* Root Cause Explanation */}
          <div>
            <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
              Root Cause Analysis
            </h4>
            <div className="bg-slate-50 p-3.5 rounded-lg border border-slate-200 text-xs text-slate-700 leading-relaxed whitespace-pre-line font-sans">
              {activeAnalysis.explanation}
            </div>
          </div>

          {/* Suggested Fix Code Block */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                Suggested Fixed Code for <span className="font-mono text-indigo-700 lowercase">{activeAnalysis.file}</span>
              </h4>
              <button
                onClick={handleCopy}
                className="flex items-center gap-1 text-[11px] text-slate-600 hover:text-slate-900 transition-colors font-medium"
              >
                {copied ? (
                  <>
                    <CheckCheck className="w-3.5 h-3.5 text-emerald-600" />
                    <span className="text-emerald-600">Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Copy Code</span>
                  </>
                )}
              </button>
            </div>

            <div className="relative rounded-lg border border-slate-200 bg-slate-900 text-slate-100 overflow-hidden font-mono text-xs shadow-inner">
              <div className="px-3 py-1.5 bg-slate-800 border-b border-slate-700 text-[11px] text-slate-300 flex items-center justify-between">
                <span>Proposed Solution Patch</span>
                <span>{activeAnalysis.file}</span>
              </div>
              <pre className="p-4 text-emerald-300 overflow-x-auto max-h-64 text-xs font-mono leading-relaxed">
                {activeAnalysis.suggestedFix}
              </pre>
            </div>
          </div>
        </div>

        {/* Modal Actions */}
        <div className="flex items-center justify-between px-6 py-3.5 bg-slate-50 border-t border-slate-200">
          <p className="text-xs text-slate-500">
            Applying fix updates <span className="font-mono font-medium text-slate-700">{activeAnalysis.file}</span> in memory so you can re-run tests.
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={rejectFix}
              className="px-3.5 py-1.5 text-xs font-medium rounded border border-slate-300 bg-white hover:bg-slate-100 text-slate-700 shadow-xs"
            >
              Reject / Close
            </button>
            <button
              onClick={() => acceptFix(activeAnalysis.suggestedFix, activeAnalysis.file)}
              className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-semibold rounded bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs transition-all"
            >
              <Check className="w-3.5 h-3.5" />
              <span>Apply Fix to {activeAnalysis.file}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
