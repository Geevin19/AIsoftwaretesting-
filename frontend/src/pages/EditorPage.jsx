import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { CodeEditor } from '../components/CodeEditor';
import { FileTree } from '../components/FileTree';
import { FileUploader } from '../components/FileUploader';
import { AnalysisPanel } from '../components/AnalysisPanel';
import { Sparkles, ArrowRight, AlertCircle, CheckCircle2, Code2 } from 'lucide-react';

export const EditorPage = () => {
  const navigate = useNavigate();
  const {
    handleGenerateTests,
    handleAnalyzeCode,
    codeAnalysis,
    selectedFunctionIds,
    errorMessage,
    successMessage,
    clearMessages,
    files,
    isLoading,
  } = useApp();

  const includedCount = files.filter((f) => f.included && !f.syntax_error).length;
  const selectedCount = selectedFunctionIds.length;

  return (
    <div className="space-y-4">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold text-indigo-600 uppercase tracking-wider">
            <span>Step 1 of 5</span>
            <span>•</span>
            <span>Project Explorer & Code Inspector</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight mt-0.5">
            Source Code & Function Analysis
          </h1>
          <p className="text-xs text-slate-500 mt-0.5 max-w-2xl">
            Upload files, folders, or .zip projects. AST static analysis extracts signatures, classes, and branch conditions to ground AI test generation in your actual code.
          </p>
        </div>

        {/* Primary Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleAnalyzeCode()}
            disabled={includedCount === 0 || isLoading}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-300 shadow-xs transition-all disabled:opacity-50"
          >
            <Code2 className="w-3.5 h-3.5 text-indigo-600" />
            <span>Analyze Code</span>
          </button>

          <button
            onClick={() => handleGenerateTests(navigate)}
            disabled={includedCount === 0 || isLoading}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 shadow-sm transition-all disabled:opacity-50"
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-200" />
            <span>
              Generate Tests {selectedCount > 0 ? `(${selectedCount} fns)` : `(${includedCount} files)`}
            </span>
            <ArrowRight className="w-3.5 h-3.5" />
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

      {/* File & Folder Uploader Zone */}
      <FileUploader />

      {/* Main Workspace: FileTree Sidebar + Monaco Editor */}
      <div className="flex flex-col lg:flex-row gap-3 h-[480px]">
        {/* Left Explorer Sidebar (240px) */}
        <FileTree />

        {/* Right Monaco Code Editor Area */}
        <div className="flex-1 min-w-0 h-full">
          <CodeEditor />
        </div>
      </div>

      {/* Static AST Code Analysis & Function Selection Panel */}
      <AnalysisPanel />
    </div>
  );
};
