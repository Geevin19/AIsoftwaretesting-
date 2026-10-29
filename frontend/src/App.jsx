import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AppProvider, useApp } from './context/AppContext';
import { Navbar } from './components/Navbar';
import { Loader } from './components/Loader';
import { EditorPage } from './pages/EditorPage';
import { TestsPage } from './pages/TestsPage';
import { ResultsPage } from './pages/ResultsPage';
import { DashboardPage } from './pages/DashboardPage';
import { ReportsPage } from './pages/ReportsPage';
import { Terminal } from 'lucide-react';

const AppContent = () => {
  const { isLoading, loadingMessage } = useApp();

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-800 selection:bg-indigo-500 selection:text-white">
      {/* Global Light Navbar */}
      <Navbar />

      {/* Global Loading Spinner Overlay */}
      {isLoading && <Loader message={loadingMessage} />}

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Routes>
          <Route path="/" element={<EditorPage />} />
          <Route path="/tests" element={<TestsPage />} />
          <Route path="/results" element={<ResultsPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>

      {/* Light Theme Footer */}
      <footer className="border-t border-slate-200 bg-white py-5 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2 font-medium text-slate-700">
            <Terminal className="w-4 h-4 text-indigo-600" />
            <span>AI-Assisted Software Testing Assistant • College Micro Project</span>
          </div>

          <div className="flex items-center gap-3 text-[11px] text-slate-500 font-mono">
            <span>FastAPI (Port 8000)</span>
            <span>•</span>
            <span>Vite React (Port 5173)</span>
            <span>•</span>
            <span>Gemini Official SDK</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default function App() {
  return (
    <AppProvider>
      <Router>
        <AppContent />
      </Router>
    </AppProvider>
  );
}
