import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { 
  Folder, 
  FolderOpen, 
  FileCode, 
  Plus, 
  Trash2, 
  ChevronRight, 
  ChevronDown, 
  AlertCircle,
  FilePlus,
  CheckSquare,
  Square
} from 'lucide-react';

export const FileTree = () => {
  const {
    files,
    activeFile,
    setActiveFile,
    toggleFileIncluded,
    addFile,
    removeFile,
  } = useApp();

  const [expandedFolders, setExpandedFolders] = useState({});
  const [isCreatingFile, setIsCreatingFile] = useState(false);
  const [newFileName, setNewFileName] = useState('');

  // Calculate total size
  const totalSizeBytes = files.reduce((acc, f) => acc + new Blob([f.content]).size, 0);
  const totalSizeFormatted = (totalSizeBytes / 1024).toFixed(1) + ' KB';

  // Build tree data structure from flat paths (e.g. 'utils/math/ops.py')
  const buildTree = () => {
    const root = { name: '', isDir: true, children: {}, files: [] };

    files.forEach((fileObj) => {
      const parts = fileObj.path.split('/');
      let curr = root;

      for (let i = 0; i < parts.length - 1; i++) {
        const folderName = parts[i];
        if (!curr.children[folderName]) {
          curr.children[folderName] = {
            name: folderName,
            isDir: true,
            pathPrefix: parts.slice(0, i + 1).join('/'),
            children: {},
            files: [],
          };
        }
        curr = curr.children[folderName];
      }

      curr.files.push(fileObj);
    });

    return root;
  };

  const toggleFolder = (folderPath) => {
    setExpandedFolders((prev) => ({
      ...prev,
      [folderPath]: prev[folderPath] === undefined ? false : !prev[folderPath],
    }));
  };

  const handleCreateSubmit = (e) => {
    e.preventDefault();
    if (!newFileName.trim()) return;
    let name = newFileName.trim();
    if (!name.endsWith('.py')) {
      name += '.py';
    }
    addFile(name, '# Source file\n');
    setNewFileName('');
    setIsCreatingFile(false);
  };

  const tree = buildTree();

  // Recursive directory renderer
  const renderDirectory = (dirNode, currentPath = '') => {
    return (
      <div key={currentPath || 'root'} className="space-y-0.5">
        {/* Subdirectories */}
        {Object.values(dirNode.children).map((folder) => {
          const folderPath = currentPath ? `${currentPath}/${folder.name}` : folder.name;
          const isExpanded = expandedFolders[folderPath] !== false; // default expanded

          return (
            <div key={folderPath} className="space-y-0.5">
              <div
                onClick={() => toggleFolder(folderPath)}
                className="flex items-center gap-1.5 px-2 py-1 rounded text-xs text-slate-700 hover:bg-slate-100 cursor-pointer select-none transition-colors"
              >
                {isExpanded ? (
                  <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                ) : (
                  <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                )}
                {isExpanded ? (
                  <FolderOpen className="w-3.5 h-3.5 text-slate-500" />
                ) : (
                  <Folder className="w-3.5 h-3.5 text-slate-500" />
                )}
                <span className="font-mono text-[11px] font-medium truncate">{folder.name}</span>
              </div>

              {isExpanded && (
                <div className="pl-3.5 border-l border-slate-200 ml-2.5 space-y-0.5">
                  {renderDirectory(folder, folderPath)}
                </div>
              )}
            </div>
          );
        })}

        {/* Files inside this directory */}
        {dirNode.files.map((f) => {
          const isActive = activeFile === f.path;
          const fileName = f.path.split('/').pop();

          return (
            <div
              key={f.path}
              className={`group flex items-center justify-between px-2 py-1 rounded text-xs transition-colors cursor-pointer select-none ${
                isActive
                  ? 'bg-slate-200 text-slate-900 font-semibold'
                  : 'text-slate-700 hover:bg-slate-100'
              }`}
            >
              <div
                onClick={() => setActiveFile(f.path)}
                className="flex items-center gap-1.5 flex-1 min-w-0"
              >
                {/* Include in analysis checkbox */}
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleFileIncluded(f.path);
                  }}
                  title={f.included ? 'Included in test analysis' : 'Excluded from test analysis'}
                  className="text-slate-400 hover:text-slate-700"
                >
                  {f.included ? (
                    <CheckSquare className="w-3 h-3 text-indigo-600" />
                  ) : (
                    <Square className="w-3 h-3 text-slate-400" />
                  )}
                </button>

                <FileCode className="w-3.5 h-3.5 text-slate-500 shrink-0" />

                <span
                  className={`font-mono text-[11px] truncate ${
                    !f.included ? 'line-through text-slate-400' : ''
                  }`}
                >
                  {fileName}
                </span>

                {/* Syntax Error Indicator */}
                {f.syntax_error && (
                  <span
                    title={`Syntax Error: ${f.syntax_error}`}
                    className="flex items-center text-rose-600"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-rose-600"></span>
                  </span>
                )}
              </div>

              {/* Actions */}
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                {files.length > 1 && (
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFile(f.path);
                    }}
                    title="Remove file"
                    className="p-0.5 rounded text-slate-400 hover:text-rose-600 hover:bg-slate-200"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="w-[240px] shrink-0 bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs flex flex-col h-full select-none">
      {/* File Tree Header */}
      <div className="flex items-center justify-between px-3 py-2.5 bg-slate-50 border-b border-slate-200">
        <div>
          <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider block">
            Explorer
          </span>
          <span className="text-[10px] text-slate-500 font-mono">
            {files.length} file{files.length !== 1 ? 's' : ''} • {totalSizeFormatted}
          </span>
        </div>

        <button
          type="button"
          onClick={() => setIsCreatingFile(true)}
          title="New file"
          className="p-1 rounded text-slate-500 hover:text-slate-800 hover:bg-slate-200 transition-colors"
        >
          <FilePlus className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* New file input form */}
      {isCreatingFile && (
        <form onSubmit={handleCreateSubmit} className="p-2 border-b border-slate-200 bg-slate-50">
          <input
            type="text"
            autoFocus
            value={newFileName}
            onChange={(e) => setNewFileName(e.target.value)}
            onBlur={() => {
              if (!newFileName.trim()) setIsCreatingFile(false);
            }}
            placeholder="filename.py or dir/file.py"
            className="w-full bg-white border border-slate-300 rounded px-2 py-1 text-xs text-slate-800 font-mono focus:outline-none focus:border-indigo-600"
          />
        </form>
      )}

      {/* Tree Content */}
      <div className="flex-1 p-2 overflow-y-auto space-y-0.5">
        {files.length === 0 ? (
          <div className="text-[11px] text-slate-400 text-center py-6 font-mono">
            No files in project
          </div>
        ) : (
          renderDirectory(tree)
        )}
      </div>

      {/* Tree Legend Footer */}
      <div className="px-3 py-2 bg-slate-50 border-t border-slate-200 text-[10px] text-slate-500 font-mono flex items-center justify-between">
        <span className="flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-rose-600"></span>
          <span>Syntax Error</span>
        </span>
        <span>Checkbox: include in test analysis</span>
      </div>
    </div>
  );
};
