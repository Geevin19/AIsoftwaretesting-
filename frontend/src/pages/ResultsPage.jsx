import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { StatusBadge, CategoryBadge } from '../components/StatusBadge';
import { FixReview } from '../components/FixReview';
import { 
  Play, 
  BarChart3, 
  Sparkles, 
  AlertCircle, 
  CheckCircle2, 
  Clock, 
  Loader2,
  RotateCcw,
  FileCode
} from 'lucide-react';

export const ResultsPage = () => {
  const navigate = useNavigate();
  const {
    testResults,
    metrics,
    handleRunTests,
    handleAnalyzeBug,
    analyzingTestId,
    errorMessage,
    successMessage,
    clearMessages,
  } = useApp();

  if (!testResults || testResults.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[460px] text-center p-8 bg-white border border-slate-200 rounded-xl shadow-xs">
        <div className="w-14 h-14 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center mb-3">
          <Play className="w-7 h-7 text-emerald-600" />
        </div>
        <h2 className="text-lg font-bold text-slate-900">No Test Results Available</h2>
        <p className="text-xs text-slate-500 max-w-sm mt-1">
          Tests have not been executed yet. Head over to Step 2 to view and execute the test suite.
        </p>
        <button
          onClick={() => navigate('/tests')}
          className="mt-4 px-4 py-2 rounded text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 transition-colors shadow-xs"
        >
          <span>Go to Step 2: Test Suite</span>
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold text-indigo-600 uppercase tracking-wider">
            <span>Step 3 of 5</span>
            <span>•</span>
            <span>Subprocess Execution Results</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight mt-0.5">
            Test Run Execution Summary
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Tests executed in isolated subprocesses with 5-second timeouts. Click &quot;Explain Bug&quot; on any failure to generate an AI root-cause diagnosis.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleRunTests()}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded text-slate-700 bg-white hover:bg-slate-50 transition-colors border border-slate-300 shadow-xs"
          >
            <RotateCcw className="w-3.5 h-3.5 text-slate-500" />
            <span>Re-Run Suite</span>
          </button>

          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 transition-all shadow-xs"
          >
            <BarChart3 className="w-3.5 h-3.5" />
            <span>View Visual Analytics</span>
          </button>
        </div>
      </div>

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

      {/* Metrics Banner */}
      {metrics && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
          <div className="bg-white border border-slate-200 p-3 rounded-lg shadow-xs">
            <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider block">Total Executed</span>
            <span className="text-lg font-bold font-mono text-slate-900">{metrics.total}</span>
          </div>
          <div className="bg-emerald-50/50 border border-emerald-200 p-3 rounded-lg shadow-xs">
            <span className="text-[10px] text-emerald-700 font-semibold uppercase tracking-wider block">Passed</span>
            <span className="text-lg font-bold font-mono text-emerald-700">{metrics.passed}</span>
          </div>
          <div className="bg-rose-50/50 border border-rose-200 p-3 rounded-lg shadow-xs">
            <span className="text-[10px] text-rose-700 font-semibold uppercase tracking-wider block">Failed</span>
            <span className="text-lg font-bold font-mono text-rose-700">{metrics.failed}</span>
          </div>
          <div className="bg-amber-50/50 border border-amber-200 p-3 rounded-lg shadow-xs">
            <span className="text-[10px] text-amber-800 font-semibold uppercase tracking-wider block">Errors</span>
            <span className="text-lg font-bold font-mono text-amber-800">{metrics.error}</span>
          </div>
          <div className="bg-indigo-50/50 border border-indigo-200 p-3 rounded-lg shadow-xs">
            <span className="text-[10px] text-indigo-700 font-semibold uppercase tracking-wider block">Pass Rate</span>
            <span className="text-lg font-bold font-mono text-indigo-900">{metrics.pass_percent}%</span>
          </div>
          <div className="bg-white border border-slate-200 p-3 rounded-lg shadow-xs">
            <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider block">Execution Time</span>
            <span className="text-lg font-bold font-mono text-slate-800">{metrics.total_time_ms} ms</span>
          </div>
        </div>
      )}

      {/* Results Detailed Table */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
        <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <h3 className="text-xs sm:text-sm font-semibold text-slate-900">
            Subprocess Test Execution Results
          </h3>
          <span className="text-[11px] text-slate-500 font-mono">
            Subprocess timeout: 5.00s per test
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-100/70 text-slate-600 border-b border-slate-200 uppercase text-[10px] tracking-wider">
              <tr>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3 font-sans">Test Name</th>
                <th className="py-2.5 px-3">Category</th>
                <th className="py-2.5 px-3">File</th>
                <th className="py-2.5 px-3">Input</th>
                <th className="py-2.5 px-3">Expected</th>
                <th className="py-2.5 px-3">Actual Result</th>
                <th className="py-2.5 px-3">Time</th>
                <th className="py-2.5 px-3 text-right">AI Bug Assistant</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {testResults.map((result) => {
                const isFailing = result.status === 'FAIL' || result.status === 'ERROR';
                const isAnalyzing = analyzingTestId === result.id;

                return (
                  <tr
                    key={result.id}
                    className={`hover:bg-slate-50 transition-colors ${
                      isFailing ? 'bg-rose-50/20' : ''
                    }`}
                  >
                    <td className="py-2.5 px-3 whitespace-nowrap">
                      <StatusBadge status={result.status} />
                    </td>
                    <td className="py-2.5 px-3 font-sans">
                      <div className="font-medium text-slate-900">{result.name}</div>
                      {result.error_message && (
                        <div className="text-[11px] text-rose-700 mt-0.5 line-clamp-1 font-mono">
                          {result.error_message}
                        </div>
                      )}
                    </td>
                    <td className="py-2.5 px-3 whitespace-nowrap">
                      <CategoryBadge category={result.category} />
                    </td>
                    <td className="py-2.5 px-3 text-slate-600 truncate max-w-[110px]" title={result.file}>
                      {result.file}
                    </td>
                    <td className="py-2.5 px-3">
                      {result.class_name && result.constructor_args && result.constructor_args.length > 0 && (
                        <div className="text-[10px] text-slate-500 mb-1 font-sans flex items-center gap-1">
                          <span className="text-slate-400 font-medium">init({result.class_name}):</span>
                          <span className="bg-slate-100 px-1.5 py-0.2 rounded font-mono text-slate-700 border border-slate-200">
                            {JSON.stringify(result.constructor_args)}
                          </span>
                        </div>
                      )}
                      <div className="flex items-center gap-1">
                        {result.class_name && (
                          <span className="text-[10px] text-slate-400 font-sans font-medium">args:</span>
                        )}
                        <span className="bg-slate-100 px-2 py-0.5 rounded text-slate-800 border border-slate-200 inline-block font-mono">
                          {JSON.stringify(result.input)}
                        </span>
                      </div>
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="bg-emerald-50 px-2 py-0.5 rounded text-emerald-800 border border-emerald-200 inline-block font-mono font-medium">
                        {typeof result.expected === 'string'
                          ? `"${result.expected}"`
                          : JSON.stringify(result.expected)}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`px-2 py-0.5 rounded border inline-block font-mono font-medium ${
                          isFailing
                            ? 'text-rose-700 bg-rose-50 border-rose-200'
                            : 'text-emerald-700 bg-emerald-50 border-emerald-200'
                        }`}
                      >
                        {String(result.actual)}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-500 whitespace-nowrap">
                      <span className="inline-flex items-center gap-1 text-[11px]">
                        <Clock className="w-3 h-3 text-slate-400" />
                        {result.execution_time_ms} ms
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-right whitespace-nowrap">
                      {isFailing ? (
                        <button
                          onClick={() => handleAnalyzeBug(result)}
                          disabled={isAnalyzing}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs transition-all disabled:opacity-50"
                        >
                          {isAnalyzing ? (
                            <>
                              <Loader2 className="w-3 h-3 animate-spin" />
                              <span>Analyzing...</span>
                            </>
                          ) : (
                            <>
                              <Sparkles className="w-3 h-3 text-indigo-200" />
                              <span>Explain Bug</span>
                            </>
                          )}
                        </button>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-xs text-emerald-700 font-medium">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Passed</span>
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Fix Review Modal */}
      <FixReview />
    </div>
  );
};
