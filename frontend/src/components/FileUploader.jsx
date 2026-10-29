import React, { useState, useRef } from 'react';
import { useApp } from '../context/AppContext';
import { uploadProjectFiles } from '../api/client';
import { UploadCloud, FolderUp, FileArchive, FileCode, AlertCircle, X, Info } from 'lucide-react';

export const FileUploader = () => {
  const { handleUploadSuccess, uploadSkipped, setUploadSkipped, uploadInfo } = useApp();

  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [inlineError, setInlineError] = useState(null);

  const fileInputRef = useRef(null);
  const folderInputRef = useRef(null);
  const zipInputRef = useRef(null);

  const sendFilesToBackend = async (fileList) => {
    if (!fileList || fileList.length === 0) {
      setInlineError('No files selected.');
      return;
    }

    setInlineError(null);
    setUploading(true);

    try {
      const formData = new FormData();
      let hasSupportedCandidate = false;

      for (let i = 0; i < fileList.length; i++) {
        const file = fileList[i];
        const relativePath = file.webkitRelativePath || file.name;
        const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();

        if (ext === '.py' || ext === '.zip') {
          hasSupportedCandidate = true;
        }

        formData.append('files', file, relativePath);
      }

      if (!hasSupportedCandidate) {
        setInlineError('No supported Python (.py) or .zip project files found in the selection.');
        setUploading(false);
        return;
      }

      const response = await uploadProjectFiles(formData);
      handleUploadSuccess(response.files, response.skipped);

      if (response.files.length === 0 && response.skipped.length > 0) {
        setInlineError('All submitted files were skipped according to validation rules.');
      }
    } catch (err) {
      setInlineError(err.message || 'File upload failed. Please verify file sizes and connectivity.');
    } finally {
      setUploading(false);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const items = e.dataTransfer.items;
    if (items && items.length > 0) {
      // Traverse directory entries if supported
      const filesToUpload = [];

      const traverseEntry = async (entry, path = '') => {
        if (entry.isFile) {
          const file = await new Promise((resolve) => entry.file(resolve));
          // Attach relative path
          Object.defineProperty(file, 'webkitRelativePath', {
            value: path ? `${path}/${file.name}` : file.name,
            writable: false,
          });
          filesToUpload.push(file);
        } else if (entry.isDirectory) {
          const dirReader = entry.createReader();
          const entries = await new Promise((resolve) => dirReader.readEntries(resolve));
          for (const child of entries) {
            await traverseEntry(child, path ? `${path}/${entry.name}` : entry.name);
          }
        }
      };

      const entryPromises = [];
      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        if (item.webkitGetAsEntry) {
          const entry = item.webkitGetAsEntry();
          if (entry) {
            entryPromises.push(traverseEntry(entry));
          }
        }
      }

      if (entryPromises.length > 0) {
        await Promise.all(entryPromises);
        if (filesToUpload.length > 0) {
          await sendFilesToBackend(filesToUpload);
          return;
        }
      }
    }

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      await sendFilesToBackend(e.dataTransfer.files);
    }
  };

  return (
    <div className="space-y-3">
      {/* Plain Dashed Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border border-dashed rounded-lg p-3 text-center transition-colors bg-white ${
          isDragging
            ? 'border-indigo-600 bg-indigo-50/50'
            : 'border-slate-300 hover:border-slate-400'
        }`}
      >
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2.5 text-left">
            <div className="p-2 rounded bg-slate-100 text-slate-600 border border-slate-200">
              <UploadCloud className="w-4 h-4 text-slate-700" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-800">
                Drop project files, folders, or .zip archive here
              </p>
              <p className="text-[11px] text-slate-500 font-mono">
                Only .py files • Max 25 files • 200 KB per file • 1 MB project total
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-1.5 w-full sm:w-auto">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="flex-1 sm:flex-none inline-flex items-center justify-center gap-1.5 px-2.5 py-1.5 text-xs font-medium rounded border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 shadow-xs transition-colors disabled:opacity-50"
            >
              <FileCode className="w-3.5 h-3.5 text-slate-600" />
              <span>Upload files</span>
            </button>

            <button
              type="button"
              onClick={() => folderInputRef.current?.click()}
              disabled={uploading}
              className="flex-1 sm:flex-none inline-flex items-center justify-center gap-1.5 px-2.5 py-1.5 text-xs font-medium rounded border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 shadow-xs transition-colors disabled:opacity-50"
            >
              <FolderUp className="w-3.5 h-3.5 text-slate-600" />
              <span>Upload folder</span>
            </button>

            <button
              type="button"
              onClick={() => zipInputRef.current?.click()}
              disabled={uploading}
              className="flex-1 sm:flex-none inline-flex items-center justify-center gap-1.5 px-2.5 py-1.5 text-xs font-medium rounded border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 shadow-xs transition-colors disabled:opacity-50"
            >
              <FileArchive className="w-3.5 h-3.5 text-slate-600" />
              <span>Upload .zip</span>
            </button>
          </div>
        </div>

        {uploading && (
          <div className="mt-2 text-xs text-indigo-700 font-medium animate-pulse">
            Validating files and checking Python AST syntax...
          </div>
        )}
      </div>

      {/* Hidden File Inputs */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".py,.zip"
        onChange={(e) => sendFilesToBackend(e.target.files)}
        className="hidden"
      />

      <input
        ref={folderInputRef}
        type="file"
        webkitdirectory=""
        directory=""
        multiple
        onChange={(e) => sendFilesToBackend(e.target.files)}
        className="hidden"
      />

      <input
        ref={zipInputRef}
        type="file"
        accept=".zip"
        onChange={(e) => sendFilesToBackend(e.target.files)}
        className="hidden"
      />

      {/* Inline Feedback / Errors (No Alerts) */}
      {inlineError && (
        <div className="flex items-start justify-between gap-2 p-2.5 rounded border border-rose-200 bg-rose-50 text-rose-800 text-xs">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-3.5 h-3.5 shrink-0 text-rose-600" />
            <span>{inlineError}</span>
          </div>
          <button
            onClick={() => setInlineError(null)}
            className="text-rose-600 hover:text-rose-900 font-bold"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Upload info / skipped file notices */}
      {uploadInfo && (
        <div className="flex items-start justify-between gap-2 p-2.5 rounded border border-slate-200 bg-slate-100 text-slate-700 text-xs">
          <div className="flex items-center gap-2">
            <Info className="w-3.5 h-3.5 shrink-0 text-slate-600" />
            <span>{uploadInfo}</span>
          </div>
        </div>
      )}

      {uploadSkipped && uploadSkipped.length > 0 && (
        <div className="p-2.5 rounded border border-amber-200 bg-amber-50 text-amber-900 text-xs space-y-1">
          <div className="flex items-center justify-between font-semibold">
            <span>Skipped files ({uploadSkipped.length}):</span>
            <button
              onClick={() => setUploadSkipped([])}
              className="text-amber-800 hover:text-amber-950"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="max-h-24 overflow-y-auto space-y-0.5 font-mono text-[11px]">
            {uploadSkipped.map((item, idx) => (
              <div key={idx} className="truncate">
                • <span className="font-semibold">{item.path}</span>: {item.reason}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
