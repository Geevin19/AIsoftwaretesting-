import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { 
  FileCode, 
  Code2, 
  Layers, 
  AlertTriangle, 
  CheckSquare, 
  Square, 
  Sparkles, 
  ArrowRight,
  ShieldAlert,
  Flame,
  CornerDownRight
} from 'lucide-react';

export const AnalysisPanel = () => {
  const navigate = useNavigate();
  const {
    codeAnalysis,
    selectedFunctionIds,
    toggleFunctionSelection,
    selectAllFunctions,
    handleGenerateTests,
    handleAnalyzeCode,
    isCodeDirty,
    isLoading,
  } = useApp();

  if (!codeAnalysis) {
    return (
      <div className="bg-white border border-slate-200 rounded-lg p-5 text-center shadow-xs">
        <div className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-slate-100 border border-slate-200 mb-2">
          <Code2 className="w-5 h-5 text-slate-600" />
        </div>
        <h3 className="text-sm font-semibold text-slate-800">AST Code Analysis Required</h3>
        <p className="text-xs text-slate-500 max-w-md mx-auto mt-1 mb-3">
          Run the static AST analyzer to discover public functions, class methods, cyclomatic branches, and parameter types from your code.
        </p>
        <button
          onClick={() => handleAnalyzeCode()}
          disabled={isLoading}
          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-md text-xs font-medium text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 transition-colors shadow-xs"
        >
          <Code2 className="w-3.5 h-3.5 text-indigo-600" />
          <span>Run AST Static Analysis</span>
        </button>
      </div>
    );
  }

  const { functions = [], syntax_errors = [], summary = {} } = codeAnalysis;
  const allSelected = functions.length > 0 && selectedFunctionIds.length === functions.length;
  const selectedCount = selectedFunctionIds.length;

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4 space-y-4 shadow-xs">
      {/* Code Changed Notification */}
      {isCodeDirty && (
        <div className="flex items-center justify-between p-2.5 rounded border border-amber-200 bg-amber-50 text-amber-900 text-xs">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
            <span>Code was modified since the last analysis. Re-run analysis to refresh detected functions.</span>
          </div>
          <button
            onClick={() => handleAnalyzeCode()}
            className="px-2.5 py-1 rounded bg-amber-600 text-white font-medium hover:bg-amber-700 transition-colors text-[11px]"
          >
            Re-Analyze Now
          </button>
        </div>
      )}

      {/* Summary Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        <div className="bg-slate-50 border border-slate-200 rounded p-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wide">Files</span>
            <FileCode className="w-3.5 h-3.5 text-slate-400" />
          </div>
          <div className="text-lg font-mono font-bold text-slate-800 mt-1">
            {summary.total_files || 0}
          </div>
        </div>

        <div className="bg-slate-50 border border-slate-200 rounded p-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wide">Functions</span>
            <Code2 className="w-3.5 h-3.5 text-slate-400" />
          </div>
          <div className="text-lg font-mono font-bold text-indigo-700 mt-1">
            {summary.total_functions || 0}
          </div>
        </div>

        <div className="bg-slate-50 border border-slate-200 rounded p-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wide">Classes</span>
            <Layers className="w-3.5 h-3.5 text-slate-400" />
          </div>
          <div className="text-lg font-mono font-bold text-slate-800 mt-1">
            {summary.total_classes || 0}
          </div>
        </div>

        <div className="bg-slate-50 border border-slate-200 rounded p-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wide">Risky Calls</span>
            <ShieldAlert className="w-3.5 h-3.5 text-amber-500" />
          </div>
          <div className="text-lg font-mono font-bold text-amber-700 mt-1">
            {summary.risky_functions || 0}
          </div>
        </div>
      </div>

      {/* Syntax Errors Section */}
      {syntax_errors.length > 0 && (
        <div className="border border-rose-200 bg-rose-50 rounded p-3 text-xs space-y-1.5">
          <div className="flex items-center gap-1.5 font-semibold text-rose-800">
            <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
            <span>Syntax Errors Found ({syntax_errors.length}) - Excluded from test generation:</span>
          </div>
          <ul className="list-disc list-inside space-y-1 text-rose-700 font-mono text-[11px]">
            {syntax_errors.map((err, idx) => (
              <li key={idx}>
                <span className="font-semibold text-rose-900">{err.file}:{err.line}</span> — {err.message}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Functions Table */}
      <div className="border border-slate-200 rounded overflow-hidden">
        {/* Table Toolbar */}
        <div className="flex flex-wrap items-center justify-between gap-2 px-3 py-2 bg-slate-50 border-b border-slate-200 text-xs">
          <div className="flex items-center gap-3">
            <button
              onClick={() => selectAllFunctions(!allSelected)}
              className="flex items-center gap-1.5 font-medium text-slate-700 hover:text-slate-900"
            >
              {allSelected ? (
                <CheckSquare className="w-3.5 h-3.5 text-indigo-600" />
              ) : (
                <Square className="w-3.5 h-3.5 text-slate-400" />
              )}
              <span>{allSelected ? 'Deselect All' : 'Select All'}</span>
            </button>
            <span className="text-slate-400">|</span>
            <span className="text-slate-600 font-mono">
              {selectedCount} of {functions.length} function{functions.length !== 1 ? 's' : ''} selected
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => handleAnalyzeCode()}
              disabled={isLoading}
              className="px-2.5 py-1 rounded bg-white hover:bg-slate-100 text-slate-700 border border-slate-300 font-medium text-[11px] transition-colors"
            >
              Re-Analyze
            </button>
            <button
              onClick={() => handleGenerateTests(navigate)}
              disabled={selectedCount === 0 || isLoading}
              className="flex items-center gap-1.5 px-3 py-1 rounded bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-[11px] transition-colors shadow-xs disabled:opacity-50"
            >
              <Sparkles className="w-3 h-3 text-indigo-200" />
              <span>Generate Tests ({selectedCount})</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>

        {/* Function rows */}
        {functions.length === 0 ? (
          <div className="p-4 text-center text-xs text-slate-500">
            No public functions or methods found in the included files.
          </div>
        ) : (
          <div className="overflow-x-auto max-h-72 divide-y divide-slate-100">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-100/70 text-slate-600 text-[10px] uppercase font-sans border-b border-slate-200">
                <tr>
                  <th className="py-1.5 px-2.5 w-8 text-center">Sel</th>
                  <th className="py-1.5 px-2.5">Target Function / Method</th>
                  <th className="py-1.5 px-2.5">File</th>
                  <th className="py-1.5 px-2.5">Parameters</th>
                  <th className="py-1.5 px-2.5 text-center">Branches</th>
                  <th className="py-1.5 px-2.5">Flags</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {functions.map((fn) => {
                  const isSelected = selectedFunctionIds.includes(fn.id);
                  const isMethod = !!fn.class_name;
                  const displayName = isMethod ? `${fn.class_name}.${fn.name}` : fn.name;

                  return (
                    <tr
                      key={fn.id}
                      onClick={() => toggleFunctionSelection(fn.id)}
                      className={`cursor-pointer transition-colors ${
                        isSelected ? 'bg-indigo-50/30 hover:bg-indigo-50/50' : 'hover:bg-slate-50'
                      }`}
                    >
                      <td className="py-1.5 px-2.5 text-center" onClick={(e) => e.stopPropagation()}>
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleFunctionSelection(fn.id)}
                          className="rounded border-slate-300 text-indigo-600 focus:ring-0 cursor-pointer"
                        />
                      </td>

                      <td className="py-1.5 px-2.5 font-medium text-slate-900">
                        <div className="flex items-center gap-1.5">
                          {isMethod ? (
                            <CornerDownRight className="w-3 h-3 text-slate-400 shrink-0" />
                          ) : (
                            <Code2 className="w-3 h-3 text-indigo-600 shrink-0" />
                          )}
                          <span className="font-semibold text-slate-900">{displayName}</span>
                          {fn.return_type && (
                            <span className="text-[10px] text-slate-400">
                              -&gt; {fn.return_type}
                            </span>
                          )}
                        </div>
                        {fn.docstring && (
                          <div className="text-[10px] text-slate-500 font-sans line-clamp-1 mt-0.5">
                            {fn.docstring}
                          </div>
                        )}
                      </td>

                      <td className="py-1.5 px-2.5 text-slate-600 text-[11px] truncate max-w-[120px]" title={fn.file}>
                        {fn.file}
                      </td>

                      <td className="py-1.5 px-2.5 text-[11px] text-slate-700">
                        {fn.parameters.length === 0 ? (
                          <span className="text-slate-400 text-[10px]">(no params)</span>
                        ) : (
                          <span>
                            ({fn.parameters.map((p) => `${p.name}${p.type_hint ? `: ${p.type_hint}` : ''}`).join(', ')})
                          </span>
                        )}
                      </td>

                      <td className="py-1.5 px-2.5 text-center">
                        <span className="inline-block px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">
                          {fn.branch_count || 1}
                        </span>
                      </td>

                      <td className="py-1.5 px-2.5 whitespace-nowrap">
                        <div className="flex items-center gap-1">
                          {fn.is_async && (
                            <span className="px-1.5 py-0.2 rounded text-[9px] font-sans font-medium bg-purple-50 text-purple-700 border border-purple-200">
                              async
                            </span>
                          )}
                          {fn.raises && fn.raises.length > 0 && (
                            <span
                              className="px-1.5 py-0.2 rounded text-[9px] font-sans font-medium bg-amber-50 text-amber-800 border border-amber-200"
                              title={`Raises: ${fn.raises.join(', ')}`}
                            >
                              raises {fn.raises.length}
                            </span>
                          )}
                          {fn.risky_calls && fn.risky_calls.length > 0 && (
                            <span
                              className="px-1.5 py-0.2 rounded text-[9px] font-sans font-medium bg-rose-50 text-rose-700 border border-rose-200"
                              title={`Risky calls: ${fn.risky_calls.join(', ')}`}
                            >
                              risky: {fn.risky_calls[0]}
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
