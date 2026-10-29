import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { TestTable } from '../components/TestTable';
import { 
  Play, 
  ArrowLeft, 
  ArrowRight, 
  AlertCircle, 
  CheckCircle2, 
  FlaskConical,
  RefreshCw,
  AlertTriangle,
  Info
} from 'lucide-react';

export const TestsPage = () => {
  const navigate = useNavigate();
  const {
    tests,
    handleRunTests,
    handleGenerateTests,
    isCodeDirty,
    rejectedTests = [],
    skippedFunctions = [],
    errorMessage,
    successMessage,
    clearMessages,
    isLoading,
  } = useApp();

  // Empty state if user opened page directly before generating tests
  if (!tests || tests.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[460px] text-center p-8 bg-white border border-slate-200 rounded-lg shadow-xs">
        <div className="w-12 h-12 rounded-lg bg-indigo-50 border border-indigo-200 flex items-center justify-center mb-3">
          <FlaskConical className="w-6 h-6 text-indigo-600" />
        </div>
        <h2 className="text-lg font-bold text-slate-900">No Unit Tests Generated Yet</h2>
        <p className="text-xs text-slate-500 max-w-md mt-1">
          Your test suite is currently empty. Please visit the Code Inspector in Step 1 to analyze code and generate unit tests.
        </p>
        <button
          onClick={() => navigate('/')}
          className="mt-5 flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 transition-colors shadow-xs"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Go to Step 1: Code Inspector</span>
        </button>
      </div>
    );
  }

  const normalCount = tests.filter((t) => t.category === 'normal').length;
  const boundaryCount = tests.filter((t) => t.category === 'boundary').length;
  const invalidCount = tests.filter((t) => t.category === 'invalid').length;
  const aiCount = tests.filter((t) => t.is_ai !== false).length;
  const manualCount = tests.filter((t) => t.is_ai === false).length;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold text-indigo-600 uppercase tracking-wider">
            <span>Step 2 of 5</span>
            <span>•</span>
            <span>Automated Test Suite</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight mt-0.5">
            Unit Test Cases
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Tests generated from AST code signatures and branch conditions. Review, modify, or add assertions before running.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md text-slate-700 bg-white hover:bg-slate-50 transition-colors border border-slate-300 shadow-xs"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Edit Code</span>
          </button>

          <button
            onClick={() => handleRunTests(navigate)}
            disabled={isLoading || tests.length === 0}
            className="flex items-center gap-2 px-4 py-1.5 rounded-md text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 shadow-xs transition-all disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 fill-white text-white" />
            <span>Execute All {tests.length} Tests</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Code Changed Since Generation Banner */}
      {isCodeDirty && (
        <div className="flex items-center justify-between p-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 text-xs shadow-xs">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
            <div>
              <span className="font-semibold">Code changed since tests were generated.</span>
              <span className="text-amber-800 ml-1">
                Your source files have been modified. Existing tests may no longer match updated signatures or logic.
              </span>
            </div>
          </div>
          <button
            onClick={() => handleGenerateTests(null)}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-amber-600 hover:bg-amber-700 text-white font-medium text-[11px] transition-colors shrink-0 shadow-xs"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Re-analyze and Regenerate</span>
          </button>
        </div>
      )}

      {/* Skipped Functions Notice Banner */}
      {skippedFunctions.length > 0 && (
        <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-slate-700 text-xs">
          <div className="flex items-center gap-1.5 font-semibold text-slate-800 mb-1">
            <Info className="w-3.5 h-3.5 text-slate-500" />
            <span>Skipped Functions ({skippedFunctions.length}):</span>
          </div>
          <ul className="list-disc list-inside space-y-0.5 text-slate-600 text-[11px] font-mono">
            {skippedFunctions.map((item, idx) => (
              <li key={idx}>
                <span className="font-semibold text-slate-800">{item.function}</span>: {item.reason}
              </li>
            ))}
          </ul>
        </div>
      )}



      {/* Notifications */}
      {errorMessage && (
        <div className="flex items-center justify-between p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-3.5 h-3.5 shrink-0 text-rose-600" />
            <span>{errorMessage}</span>
          </div>
          <button onClick={clearMessages} className="text-rose-600 hover:text-rose-900 font-bold">
            ×
          </button>
        </div>
      )}

      {successMessage && (
        <div className="flex items-center justify-between p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-emerald-600" />
            <span>{successMessage}</span>
          </div>
          <button onClick={clearMessages} className="text-emerald-600 hover:text-emerald-900 font-bold">
            ×
          </button>
        </div>
      )}

      {/* Category Breakdown Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        <div className="bg-white border border-slate-200 p-3 rounded-lg shadow-xs">
          <div className="text-[11px] font-medium text-slate-500 uppercase tracking-wide">Normal Cases</div>
          <div className="flex items-baseline justify-between mt-1">
            <span className="text-lg font-mono font-bold text-slate-800">{normalCount}</span>
            <span className="text-[11px] text-slate-400">Happy path</span>
          </div>
        </div>

        <div className="bg-white border border-slate-200 p-3 rounded-lg shadow-xs">
          <div className="text-[11px] font-medium text-purple-700 uppercase tracking-wide">Boundary Cases</div>
          <div className="flex items-baseline justify-between mt-1">
            <span className="text-lg font-mono font-bold text-purple-800">{boundaryCount}</span>
            <span className="text-[11px] text-purple-600">Limits & edges</span>
          </div>
        </div>

        <div className="bg-white border border-slate-200 p-3 rounded-lg shadow-xs">
          <div className="text-[11px] font-medium text-amber-800 uppercase tracking-wide">Invalid Inputs</div>
          <div className="flex items-baseline justify-between mt-1">
            <span className="text-lg font-mono font-bold text-amber-800">{invalidCount}</span>
            <span className="text-[11px] text-amber-600">Type / Error checks</span>
          </div>
        </div>

        <div className="bg-white border border-slate-200 p-3 rounded-lg shadow-xs">
          <div className="text-[11px] font-medium text-indigo-700 uppercase tracking-wide">Test Composition</div>
          <div className="flex items-baseline justify-between mt-1">
            <span className="text-lg font-mono font-bold text-indigo-800">
              {aiCount} <span className="text-xs font-normal text-slate-400">AI</span> / {manualCount} <span className="text-xs font-normal text-slate-400">Manual</span>
            </span>
          </div>
        </div>
      </div>

      {/* Interactive Grouped Test Table */}
      <TestTable />
    </div>
  );
};
