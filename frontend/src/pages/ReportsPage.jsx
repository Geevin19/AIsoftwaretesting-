import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { StatusBadge, CategoryBadge } from '../components/StatusBadge';
import { 
  Download, 
  ChevronDown, 
  ChevronRight, 
  Filter, 
  FileSpreadsheet, 
  ArrowLeft, 
  AlertCircle,
  Sparkles,
  FileArchive,
  FileCode,
  FileText,
  FileCheck2,
  Settings2,
  Layers,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Loader2,
  Check
} from 'lucide-react';

const REPORT_SECTIONS = [
  { num: '1', title: 'Introduction', desc: 'Document Purpose, Scope, System Overview, Reference Documents' },
  { num: '2', title: 'Executive Summary', desc: 'Testing Overview, Final Recommendation & Acceptance Verdict' },
  { num: '3', title: 'Test Environment & Configuration', desc: 'OS, Python runtime, test harness, execution parameters' },
  { num: '4', title: 'Test Methodology & Scope', desc: 'Strategy, Level/Categories, AST Inclusions & Exclusions' },
  { num: '5', title: 'Execution Summary & Metrics', desc: 'High-Level Metrics, Category Breakdown, Embedded Visualizations' },
  { num: '6', title: 'Detailed Test Results', desc: 'Full Test Execution Register with inputs, expected, and actuals' },
  { num: '7', title: 'Defect Log & Classification', desc: 'Identified Defects, Severity (High/Med/Low), Priority (P1-P3)' },
  { num: '8', title: 'AI Defect Analysis & Root Causes', desc: 'Root cause investigations and proposed automated code fixes' },
  { num: '9', title: 'Requirements & Code Traceability', desc: 'Function-to-Test mapping matrix and coverage confirmation' },
  { num: '10', title: 'Regression Analysis & Comparison', desc: 'Multi-run performance and delta variance tracking' },
  { num: '11', title: 'Quality Assessment & Acceptance', desc: 'Threshold evaluation, risk analysis, release readiness' },
  { num: '12', title: 'Recommendations & Lessons', desc: 'Strategic remediations, QA process improvements' },
  { num: '13', title: 'Sign-off & Approvals', desc: 'Formal approval roles, signatures, and authorization blocks' },
  { num: 'App A', title: 'Appendix A: Reproducibility', desc: 'Test environment hashes, CLI execution reproduction steps' },
  { num: 'App B', title: 'Appendix B: Raw Execution Log', desc: 'Subprocess trace log sample for audit compliance' },
];

export const ReportsPage = () => {
  const navigate = useNavigate();
  const { 
    testResults, 
    activeAnalysis, 
    handleExportPytest, 
    handleExportReport,
    files, 
    tests,
    runHistory,
    reportMetadata,
    setReportMetadata,
    isLoading,
    loadingMessage,
    metrics
  } = useApp();

  const [statusFilter, setStatusFilter] = useState('ALL');
  const [fileFilter, setFileFilter] = useState('ALL');
  const [expandedRows, setExpandedRows] = useState({});
  const [isDownloadDropdownOpen, setIsDownloadDropdownOpen] = useState(false);
  const [isMetadataModalOpen, setIsMetadataModalOpen] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState('pdf');
  const [showPreviewStructure, setShowPreviewStructure] = useState(false);

  // Editable metadata state for modal
  const [modalMetadata, setModalMetadata] = useState(reportMetadata || {
    project_name: 'AI-Assisted Software Testing Assistant',
    report_title: 'Software Test Report (IEEE 829 / ISO 29119)',
    document_id: `TR-${new Date().toISOString().slice(0, 10).replace(/-/g, '')}-001`,
    version: '1.0.0',
    organization: 'Department of Computer Science & Engineering',
    prepared_by: 'QA Lead Engineer',
    reviewed_by: 'Software Quality Assurance Committee',
    test_environment: 'Windows 11 / Python 3.9 / Pytest Subprocess Runner',
    test_date: new Date().toISOString().slice(0, 10),
    pass_threshold: 90.0,
  });

  const hasResults = testResults && testResults.length > 0;

  const toggleRow = (id) => {
    setExpandedRows((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const handleOpenModal = (format) => {
    setSelectedFormat(format);
    setIsDownloadDropdownOpen(false);
    // Refresh modal form with current context metadata or defaults
    setModalMetadata({
      project_name: reportMetadata?.project_name || 'AI-Assisted Software Testing Assistant',
      report_title: reportMetadata?.report_title || 'Software Test Report (IEEE 829 / ISO 29119)',
      document_id: reportMetadata?.document_id || `TR-${new Date().toISOString().slice(0, 10).replace(/-/g, '')}-001`,
      version: reportMetadata?.version || '1.0.0',
      organization: reportMetadata?.organization || 'Department of Computer Science & Engineering',
      prepared_by: reportMetadata?.prepared_by || 'QA Lead Engineer',
      reviewed_by: reportMetadata?.reviewed_by || 'Software Quality Assurance Committee',
      test_environment: reportMetadata?.test_environment || 'Windows 11 / Python 3.9 / Pytest Subprocess Runner',
      test_date: reportMetadata?.test_date || new Date().toISOString().slice(0, 10),
      pass_threshold: reportMetadata?.pass_threshold !== undefined ? reportMetadata.pass_threshold : 90.0,
    });
    setIsMetadataModalOpen(true);
  };

  const handleConfirmDownload = async (e) => {
    e.preventDefault();
    setIsMetadataModalOpen(false);
    setReportMetadata(modalMetadata);
    await handleExportReport(selectedFormat, modalMetadata);
  };

  const handleCsvClick = async () => {
    setIsDownloadDropdownOpen(false);
    await handleExportReport('csv');
  };

  // Distinct file list for file filter
  const distinctFiles = hasResults ? Array.from(new Set(testResults.map((r) => r.file || 'main.py'))) : [];

  const filteredResults = hasResults ? testResults.filter((item) => {
    const matchStatus = statusFilter === 'ALL' || (item.status || '').toUpperCase() === statusFilter;
    const matchFile = fileFilter === 'ALL' || (item.file || 'main.py') === fileFilter;
    return matchStatus && matchFile;
  }) : [];

  // Group failures by file for failure summary
  const failuresByFile = hasResults ? testResults.reduce((acc, r) => {
    if (r.status === 'FAIL' || r.status === 'ERROR') {
      const f = r.file || 'main.py';
      acc[f] = (acc[f] || 0) + 1;
    }
    return acc;
  }, {}) : {};

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold text-indigo-600 uppercase tracking-wider">
            <span>Step 5 of 5</span>
            <span>•</span>
            <span>IEEE 829 QA Documentation & Export</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight mt-0.5">
            Software Test Report & Pytest Suite
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Generate formal IEEE 829 / ISO 29119 documentation in PDF and Word (.docx), inspect execution records, or export a pytest suite.
          </p>
        </div>

        {/* Export Actions Bar */}
        <div className="flex items-center gap-2">
          {/* Pytest Suite Export */}
          <button
            onClick={handleExportPytest}
            disabled={!hasResults || isLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-300 shadow-xs transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Download full project and pytest test suite as a .zip"
          >
            <FileArchive className="w-3.5 h-3.5 text-indigo-600" />
            <span>Export Pytest (.zip)</span>
          </button>

          {/* Prominent Split Button for Report Downloads */}
          <div className="relative inline-flex rounded-md shadow-xs">
            <button
              onClick={() => handleOpenModal('pdf')}
              disabled={!hasResults || isLoading}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-l text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 border-r border-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Download Report</span>
            </button>
            <button
              type="button"
              onClick={() => setIsDownloadDropdownOpen((prev) => !prev)}
              disabled={!hasResults || isLoading}
              className="px-2 py-1.5 rounded-r text-xs text-white bg-indigo-600 hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Select report format"
            >
              <ChevronDown className="w-3.5 h-3.5" />
            </button>

            {/* Dropdown Menu */}
            {isDownloadDropdownOpen && (
              <div 
                className="absolute right-0 top-full mt-1.5 w-56 rounded-md bg-white border border-slate-200 shadow-lg z-30 py-1 text-xs"
                onMouseLeave={() => setIsDownloadDropdownOpen(false)}
              >
                <button
                  onClick={() => handleOpenModal('pdf')}
                  className="w-full text-left px-3 py-2 text-slate-700 hover:bg-slate-50 flex items-center justify-between"
                >
                  <span className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-rose-600" />
                    <span>PDF Report (.pdf)</span>
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">IEEE 829</span>
                </button>
                <button
                  onClick={() => handleOpenModal('docx')}
                  className="w-full text-left px-3 py-2 text-slate-700 hover:bg-slate-50 flex items-center justify-between border-t border-slate-100"
                >
                  <span className="flex items-center gap-2">
                    <FileCheck2 className="w-4 h-4 text-blue-600" />
                    <span>Word Document (.docx)</span>
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">ISO 29119</span>
                </button>
                <button
                  onClick={handleCsvClick}
                  className="w-full text-left px-3 py-2 text-slate-700 hover:bg-slate-50 flex items-center justify-between border-t border-slate-100"
                >
                  <span className="flex items-center gap-2">
                    <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
                    <span>CSV Records (.csv)</span>
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">Raw data</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Progress / Loading Indicator */}
      {isLoading && (
        <div className="flex items-center gap-3 p-3 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-900 text-xs">
          <Loader2 className="w-4 h-4 animate-spin text-indigo-600 shrink-0" />
          <div className="space-y-0.5">
            <span className="font-semibold block">Generating Formal IEEE 829 Test Report...</span>
            <span className="text-slate-600 text-[11px]">{loadingMessage || 'Synthesizing narrative, rendering charts, and compiling document.'}</span>
          </div>
        </div>
      )}

      {/* Disabled / Empty State when No Test Results */}
      {!hasResults && (
        <div className="flex flex-col items-center justify-center min-h-[380px] text-center p-8 bg-white border border-slate-200 rounded-xl shadow-xs">
          <div className="w-14 h-14 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-center mb-3 text-slate-400">
            <FileText className="w-7 h-7" />
          </div>
          <h2 className="text-base font-bold text-slate-800">Run tests to generate a report</h2>
          <p className="text-xs text-slate-500 max-w-md mt-1 leading-relaxed">
            Execute the generated test cases against your codebase to calculate quality metrics, detect defects, and compile the formal IEEE 829 / ISO 29119 Software Test Report.
          </p>
          <button
            onClick={() => navigate('/tests')}
            className="mt-4 inline-flex items-center gap-1.5 px-4 py-2 rounded text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 transition-colors shadow-xs"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Go to Tests & Run</span>
          </button>
        </div>
      )}

      {/* When Results Exist: Structure Preview & Execution Results */}
      {hasResults && (
        <>
          {/* Structure Preview Card */}
          <div className="bg-white border border-slate-200 rounded-lg p-3 shadow-xs">
            <div className="flex items-center justify-between">
              <button
                onClick={() => setShowPreviewStructure((prev) => !prev)}
                className="flex items-center gap-2 text-xs font-semibold text-slate-800 hover:text-indigo-600 transition-colors"
              >
                <Layers className="w-3.5 h-3.5 text-indigo-600" />
                <span>Preview Report Structure (13 Standard IEEE 829 / ISO 29119 Sections + Appendices)</span>
                {showPreviewStructure ? (
                  <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                ) : (
                  <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                )}
              </button>

              <div className="flex items-center gap-2 text-[11px]">
                <button
                  onClick={() => handleOpenModal('pdf')}
                  className="text-indigo-600 hover:text-indigo-800 font-medium inline-flex items-center gap-1"
                >
                  <Settings2 className="w-3 h-3" />
                  <span>Configure Details</span>
                </button>
              </div>
            </div>

            {showPreviewStructure && (
              <div className="mt-3 pt-3 border-t border-slate-100 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                {REPORT_SECTIONS.map((sec) => {
                  const isSec10 = sec.num === '10';
                  const runsCount = runHistory?.length || 1;
                  const isMultiRun = runsCount >= 2;

                  return (
                    <div
                      key={sec.num}
                      className="p-2 rounded bg-slate-50 border border-slate-200 text-xs flex flex-col justify-between"
                    >
                      <div>
                        <div className="flex items-center justify-between mb-0.5">
                          <span className="font-mono font-bold text-indigo-700 text-[11px]">
                            {sec.num.startsWith('App') ? sec.num : `${sec.num}.`} {sec.title}
                          </span>
                          {isSec10 && (
                            <span className={`text-[10px] px-1.5 py-0.2 rounded font-medium border ${
                              isMultiRun 
                                ? 'bg-emerald-50 text-emerald-700 border-emerald-200' 
                                : 'bg-slate-100 text-slate-600 border-slate-200'
                            }`}>
                              {isMultiRun ? `Active (${runsCount} runs)` : 'Baseline only (1 run)'}
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-slate-500 line-clamp-2 leading-relaxed">
                          {sec.desc}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Failure Breakdown by File Banner */}
          {Object.keys(failuresByFile).length > 0 && (
            <div className="p-3 bg-rose-50/70 border border-rose-200 rounded-lg text-xs space-y-1">
              <span className="font-semibold text-rose-900 block">
                Failures Grouped by File:
              </span>
              <div className="flex flex-wrap gap-2">
                {Object.entries(failuresByFile).map(([fName, count]) => (
                  <span
                    key={fName}
                    onClick={() => setFileFilter(fName)}
                    className="cursor-pointer inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-white text-rose-800 border border-rose-200 font-mono text-[11px] hover:border-rose-400"
                  >
                    <FileCode className="w-3 h-3 text-rose-600" />
                    <span>{fName}: {count} failure{count !== 1 ? 's' : ''}</span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Filter Toolbar */}
          <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-white border border-slate-200 rounded-lg shadow-xs">
            <div className="flex flex-wrap items-center gap-3">
              {/* Status Filter */}
              <div className="flex items-center gap-1.5">
                <Filter className="w-3.5 h-3.5 text-slate-500" />
                <span className="text-xs text-slate-700 font-medium">Status:</span>
                <div className="flex items-center gap-1">
                  {['ALL', 'PASS', 'FAIL', 'ERROR'].map((st) => (
                    <button
                      key={st}
                      onClick={() => setStatusFilter(st)}
                      className={`px-2 py-0.5 rounded text-xs font-mono font-medium transition-colors ${
                        statusFilter === st
                          ? 'bg-indigo-600 text-white shadow-xs'
                          : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                      }`}
                    >
                      {st}
                    </button>
                  ))}
                </div>
              </div>

              {/* File Filter */}
              {distinctFiles.length > 1 && (
                <div className="flex items-center gap-1.5">
                  <span className="text-xs text-slate-700 font-medium">File:</span>
                  <select
                    value={fileFilter}
                    onChange={(e) => setFileFilter(e.target.value)}
                    className="bg-white border border-slate-300 rounded px-2 py-0.5 text-xs text-slate-800 font-mono"
                  >
                    <option value="ALL">All Files</option>
                    {distinctFiles.map((df) => (
                      <option key={df} value={df}>
                        {df}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>

            <div className="text-[11px] text-slate-500 font-mono">
              Showing <span className="text-indigo-700 font-bold">{filteredResults.length}</span> of {testResults.length} test records
            </div>
          </div>

          {/* Expandable Test Results Table */}
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-100/70 text-slate-600 border-b border-slate-200 uppercase text-[10px] tracking-wider">
                  <tr>
                    <th className="py-2.5 px-3 w-8"></th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3 font-sans">Test Name</th>
                    <th className="py-2.5 px-3">Category</th>
                    <th className="py-2.5 px-3">File</th>
                    <th className="py-2.5 px-3">Function</th>
                    <th className="py-2.5 px-3">Expected</th>
                    <th className="py-2.5 px-3">Actual</th>
                    <th className="py-2.5 px-3 text-right">Time</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {filteredResults.map((item) => {
                    const isExpanded = !!expandedRows[item.id];
                    const isFailing = item.status === 'FAIL' || item.status === 'ERROR';

                    return (
                      <React.Fragment key={item.id}>
                        <tr
                          onClick={() => toggleRow(item.id)}
                          className={`hover:bg-slate-50 cursor-pointer transition-colors ${
                            isExpanded ? 'bg-slate-50/70' : ''
                          }`}
                        >
                          <td className="py-2.5 px-3 text-slate-400">
                            {isExpanded ? (
                              <ChevronDown className="w-3.5 h-3.5 text-indigo-600" />
                            ) : (
                              <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                            )}
                          </td>
                          <td className="py-2.5 px-3 whitespace-nowrap">
                            <StatusBadge status={item.status} />
                          </td>
                          <td className="py-2.5 px-3 font-sans">
                            <div className="font-medium text-slate-900">{item.name}</div>
                          </td>
                          <td className="py-2.5 px-3 whitespace-nowrap">
                            <CategoryBadge category={item.category} />
                          </td>
                          <td className="py-2.5 px-3 text-slate-600 truncate max-w-[110px]" title={item.file}>
                            {item.file}
                          </td>
                          <td className="py-2.5 px-3 text-indigo-700 font-semibold">
                            {item.function_name}()
                          </td>
                          <td className="py-2.5 px-3">
                            <span className="text-emerald-700 font-medium">
                              {typeof item.expected === 'string'
                                ? `"${item.expected}"`
                                : JSON.stringify(item.expected)}
                            </span>
                          </td>
                          <td className="py-2.5 px-3">
                            <span className={isFailing ? 'text-rose-700 font-semibold' : 'text-slate-700'}>
                              {String(item.actual)}
                            </span>
                          </td>
                          <td className="py-2.5 px-3 text-right text-slate-500 whitespace-nowrap">
                            {item.execution_time_ms} ms
                          </td>
                        </tr>

                        {/* Expandable Row with Details */}
                        {isExpanded && (
                          <tr className="bg-slate-50/70 border-l-2 border-l-indigo-600">
                            <td colSpan={9} className="p-3">
                              <div className="space-y-2 font-sans text-xs">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                                  <div className="bg-white p-3 rounded border border-slate-200 shadow-xs">
                                    <span className="text-slate-500 font-semibold uppercase text-[10px] tracking-wider block mb-1">
                                      Test Purpose & Verification Goal:
                                    </span>
                                    <p className="text-slate-800 leading-relaxed font-mono text-[11px]">
                                      {item.purpose || 'Automated verification check.'}
                                    </p>
                                  </div>

                                  <div className="bg-white p-3 rounded border border-slate-200 shadow-xs">
                                    <span className="text-slate-500 font-semibold uppercase text-[10px] tracking-wider block mb-1">
                                      Module Import & Arguments:
                                    </span>
                                    <p className="text-indigo-700 font-mono text-[11px]">
                                      from {item.module} import {item.function_name}; call with {JSON.stringify(item.input)}
                                    </p>
                                  </div>
                                </div>

                                {item.error_message && (
                                  <div className="bg-rose-50 p-2.5 rounded border border-rose-200">
                                    <span className="text-rose-800 font-semibold uppercase text-[10px] tracking-wider block mb-0.5">
                                      Execution Error Message:
                                    </span>
                                    <p className="text-rose-700 font-mono text-[11px]">
                                      {item.error_message}
                                    </p>
                                  </div>
                                )}

                                {activeAnalysis && activeAnalysis.testId === item.id && (
                                  <div className="bg-indigo-50 p-2.5 rounded border border-indigo-200">
                                    <span className="text-indigo-900 font-semibold uppercase text-[10px] tracking-wider flex items-center gap-1 mb-0.5">
                                      <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                                      Saved AI Bug Diagnosis for {item.file}:
                                    </span>
                                    <p className="text-slate-700 text-[11px] leading-relaxed whitespace-pre-line">
                                      {activeAnalysis.explanation}
                                    </p>
                                  </div>
                                )}
                              </div>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* Report Metadata Modal */}
      {isMetadataModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4 overflow-y-auto">
          <div className="bg-white border border-slate-200 rounded-xl shadow-xl w-full max-w-xl my-8 overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <div>
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <FileText className="w-4 h-4 text-indigo-600" />
                  <span>Configure Software Test Report Details</span>
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  IEEE 829 / ISO 29119 document control headers and verification criteria.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setIsMetadataModalOpen(false)}
                className="text-slate-400 hover:text-slate-700 text-lg leading-none"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleConfirmDownload} className="p-5 space-y-3.5 text-xs">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Project Name</label>
                  <input
                    type="text"
                    required
                    value={modalMetadata.project_name}
                    onChange={(e) => setModalMetadata({ ...modalMetadata, project_name: e.target.value })}
                    className="w-full px-2.5 py-1.5 border border-slate-300 rounded text-slate-800 focus:outline-indigo-500"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Report Title</label>
                  <input
                    type="text"
                    required
                    value={modalMetadata.report_title}
                    onChange={(e) => setModalMetadata({ ...modalMetadata, report_title: e.target.value })}
                    className="w-full px-2.5 py-1.5 border border-slate-300 rounded text-slate-800 focus:outline-indigo-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Document ID</label>
                  <input
                    type="text"
                    required
                    value={modalMetadata.document_id}
                    onChange={(e) => setModalMetadata({ ...modalMetadata, document_id: e.target.value })}
                    className="w-full px-2.5 py-1.5 border border-slate-300 rounded text-slate-800 font-mono text-[11px] focus:outline-indigo-500"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Version</label>
                  <input
                    type="text"
                    required
                    value={modalMetadata.version}
                    onChange={(e) => setModalMetadata({ ...modalMetadata, version: e.target.value })}
                    className="w-full px-2.5 py-1.5 border border-slate-300 rounded text-slate-800 focus:outline-indigo-500"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Pass Threshold (%)</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    step="1"
                    required
                    value={modalMetadata.pass_threshold}
                    onChange={(e) => setModalMetadata({ ...modalMetadata, pass_threshold: parseFloat(e.target.value) || 0 })}
                    className="w-full px-2.5 py-1.5 border border-slate-300 rounded text-slate-800 focus:outline-indigo-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Organization / College</label>
                  <input
                    type="text"
                    required
                    value={modalMetadata.organization}
                    onChange={(e) => setModalMetadata({ ...modalMetadata, organization: e.target.value })}
                    className="w-full px-2.5 py-1.5 border border-slate-300 rounded text-slate-800 focus:outline-indigo-500"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Test Date</label>
                  <input
                    type="date"
                    required
                    value={modalMetadata.test_date}
                    onChange={(e) => setModalMetadata({ ...modalMetadata, test_date: e.target.value })}
                    className="w-full px-2.5 py-1.5 border border-slate-300 rounded text-slate-800 focus:outline-indigo-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Prepared By (Lead QA)</label>
                  <input
                    type="text"
                    required
                    value={modalMetadata.prepared_by}
                    onChange={(e) => setModalMetadata({ ...modalMetadata, prepared_by: e.target.value })}
                    className="w-full px-2.5 py-1.5 border border-slate-300 rounded text-slate-800 focus:outline-indigo-500"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Reviewed By (Approver)</label>
                  <input
                    type="text"
                    required
                    value={modalMetadata.reviewed_by}
                    onChange={(e) => setModalMetadata({ ...modalMetadata, reviewed_by: e.target.value })}
                    className="w-full px-2.5 py-1.5 border border-slate-300 rounded text-slate-800 focus:outline-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Test Environment</label>
                <input
                  type="text"
                  required
                  value={modalMetadata.test_environment}
                  onChange={(e) => setModalMetadata({ ...modalMetadata, test_environment: e.target.value })}
                  className="w-full px-2.5 py-1.5 border border-slate-300 rounded text-slate-800 focus:outline-indigo-500"
                />
              </div>

              <div className="pt-3 border-t border-slate-200 flex items-center justify-between">
                <div className="text-[11px] text-slate-500">
                  Target Format: <span className="font-bold uppercase text-indigo-700">{selectedFormat}</span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setIsMetadataModalOpen(false)}
                    className="px-3 py-1.5 rounded border border-slate-300 text-slate-700 hover:bg-slate-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-1.5 rounded text-white bg-indigo-600 hover:bg-indigo-700 font-semibold transition-colors flex items-center gap-1.5 shadow-xs"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Generate & Download</span>
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
