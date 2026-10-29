import React from 'react';
import Editor from '@monaco-editor/react';
import { useApp } from '../context/AppContext';
import { Code, BookOpen, FileCode, Plus, Trash2, AlertCircle } from 'lucide-react';

export const CodeEditor = () => {
  const {
    files,
    activeFile,
    currentFileObj,
    updateFileContent,
    language,
    setLanguage,
    samplesList,
    selectedSample,
    handleLoadSample,
    removeFile,
    addFile,
  } = useApp();

  if (!files || files.length === 0 || !currentFileObj) {
    return (
      <div className="flex flex-col items-center justify-center h-full min-h-[460px] bg-white border border-slate-200 rounded-xl p-8 text-center shadow-xs">
        <FileCode className="w-10 h-10 text-slate-400 mb-3" />
        <h3 className="text-sm font-semibold text-slate-800">No files in project</h3>
        <p className="text-xs text-slate-500 max-w-sm mt-1">
          Paste code, upload files, or upload a project folder to start analyzing.
        </p>
        <button
          onClick={() => addFile('main.py', '# Main Python script\n\ndef main():\n    pass\n')}
          className="mt-4 px-3 py-1.5 text-xs font-medium rounded border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 shadow-xs"
        >
          Create main.py
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
      {/* Top Controls Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-2.5 px-4 py-2.5 bg-slate-50 border-b border-slate-200">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs text-slate-700 font-medium">
            <Code className="w-3.5 h-3.5 text-indigo-600" />
            <span>Target Language:</span>
          </div>

          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="bg-white text-slate-800 text-xs rounded px-2 py-1 border border-slate-300 focus:outline-none focus:border-indigo-600 font-mono shadow-xs"
          >
            <option value="python">Python 3.10+ (Supported)</option>
            <option value="java" disabled>Java (Coming Soon)</option>
            <option value="javascript" disabled>JavaScript (Coming Soon)</option>
          </select>
        </div>

        {/* Load Sample Dropdown */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 text-xs text-slate-700 font-medium">
            <BookOpen className="w-3.5 h-3.5 text-emerald-600" />
            <span>Load Sample:</span>
          </div>

          <select
            value={selectedSample}
            onChange={(e) => handleLoadSample(e.target.value)}
            className="bg-white text-slate-800 text-xs rounded px-2 py-1 border border-slate-300 focus:outline-none focus:border-emerald-600 font-mono shadow-xs"
          >
            {samplesList.length > 0 ? (
              samplesList.map((sample) => (
                <option key={sample.id} value={sample.id}>
                  {sample.title}
                </option>
              ))
            ) : (
              <>
                <option value="calculator">Calculator with Edge-Case Bug</option>
                <option value="login_validator">Login Credential Validator</option>
              </>
            )}
          </select>
        </div>
      </div>

      {/* File Breadcrumb / Tab Bar */}
      <div className="flex items-center justify-between px-4 py-1.5 bg-slate-100/70 border-b border-slate-200 text-xs">
        <div className="flex items-center gap-2 font-mono">
          <FileCode className="w-3.5 h-3.5 text-slate-500" />
          <span className="text-slate-800 font-semibold">{currentFileObj.path}</span>
          {!currentFileObj.included && (
            <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-100 text-amber-800 border border-amber-200">
              Excluded from analysis
            </span>
          )}
          {currentFileObj.syntax_error && (
            <span className="text-[10px] px-1.5 py-0.2 rounded bg-rose-100 text-rose-800 border border-rose-200 flex items-center gap-1">
              <AlertCircle className="w-3 h-3 text-rose-600" />
              <span>{currentFileObj.syntax_error}</span>
            </span>
          )}
        </div>

        <div className="flex items-center gap-1.5">
          {files.length > 1 && (
            <button
              onClick={() => removeFile(currentFileObj.path)}
              className="text-slate-400 hover:text-rose-600 p-1 rounded hover:bg-slate-200 transition-colors"
              title="Delete active file"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Monaco Editor Container */}
      <div className="flex-1 min-h-[440px] relative border-b border-slate-200">
        <Editor
          height="100%"
          language={language === 'python' ? 'python' : 'javascript'}
          theme="vs"
          value={currentFileObj.content}
          onChange={(newVal) => updateFileContent(currentFileObj.path, newVal || '')}
          options={{
            fontSize: 13,
            fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 4,
            lineNumbers: 'on',
            lineDecorationsWidth: 8,
            cursorBlinking: 'smooth',
            wordWrap: 'on',
            padding: { top: 12, bottom: 12 },
          }}
        />
      </div>

      {/* Editor Footer / Info Bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-slate-50 text-[11px] text-slate-500 font-mono">
        <div className="flex items-center gap-3">
          <span>UTF-8</span>
          <span>Spaces: 4</span>
          <span>{currentFileObj.content.split('\n').length} lines</span>
          <span>{(new Blob([currentFileObj.content]).size / 1024).toFixed(1)} KB</span>
        </div>
        <div className="flex items-center gap-2 text-indigo-700 font-medium">
          <span>Auto-saved in memory session</span>
        </div>
      </div>
    </div>
  );
};
