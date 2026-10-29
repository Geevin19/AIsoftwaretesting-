/**
 * API Client Service
 * Centralized Axios client for communicating with the FastAPI backend.
 */
import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || (
  typeof window !== 'undefined' && window.location.hostname ? '' : 'http://localhost:8000'
);

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 60000, // 60s timeout for multi-file LLM analysis
});

// Response interceptor for consistent error extraction
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    let errorMsg = 'An unexpected error occurred. Please check your backend connection.';
    if (error.response && error.response.data) {
      if (typeof error.response.data.detail === 'string') {
        errorMsg = error.response.data.detail;
      } else if (Array.isArray(error.response.data.detail)) {
        errorMsg = error.response.data.detail.map((d) => d.msg || JSON.stringify(d)).join(', ');
      }
    } else if (error.message) {
      errorMsg = error.message;
    }
    return Promise.reject(new Error(errorMsg));
  }
);

/**
 * Fetch available sample programs
 */
export const getSamples = async () => {
  const res = await apiClient.get('/api/samples');
  return res.data;
};

/**
 * Fetch a specific sample code by name
 */
export const getSample = async (name) => {
  const res = await apiClient.get(`/api/samples/${name}`);
  return res.data;
};

/**
 * Upload files, directories, or .zip archive
 */
export const uploadProjectFiles = async (formData) => {
  const res = await apiClient.post('/api/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return res.data;
};

/**
 * Stage 1: Static AST Code Analysis (No AI)
 */
export const analyzeCode = async (files) => {
  const res = await apiClient.post('/api/analyze-code', { files });
  return res.data;
};

/**
 * Stage 2: Generate unit tests from project files and selected functions
 */
export const generateTests = async (files, selectedFunctions = null, perFunction = 6, language = 'python') => {
  const normalizedSelected = Array.isArray(selectedFunctions)
    ? selectedFunctions.map((item) => (typeof item === 'object' && item !== null ? (item.id || item.function_name || item.name) : item))
    : selectedFunctions;

  const res = await apiClient.post('/api/generate-tests', {
    files,
    selected_functions: normalizedSelected,
    per_function: perFunction,
    language,
  });
  return res.data;
};

/**
 * Generate additional tests for a specific function / category
 */
export const generateMoreTests = async (files, functionId = null, category = null, count = 3, existingTests = []) => {
  const res = await apiClient.post('/api/generate-more', {
    files,
    function_id: functionId,
    category,
    count,
    existing_tests: existingTests,
  });
  return res.data;
};

/**
 * Run test cases against project files in isolated subprocesses
 */
export const runTests = async (files, tests) => {
  const res = await apiClient.post('/api/run-tests', { files, tests });
  return res.data;
};

/**
 * Analyze a failing test with AI and get explanation + code fix for target file
 */
export const analyzeBug = async (files, test, actual, status) => {
  const res = await apiClient.post('/api/analyze', { files, test, actual, status });
  return res.data;
};

/**
 * Export full project and pytest suite as downloadable .zip
 */
export const exportPytestSuite = async (files, tests) => {
  const response = await apiClient.post('/api/export/pytest', { files, tests }, {
    responseType: 'blob',
  });
  const blob = new Blob([response.data], { type: 'application/zip' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', 'pytest_project_suite.zip');
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};



/**
 * Request CSV report and trigger browser download
 */
export const downloadReportCsv = async (results) => {
  const response = await apiClient.post('/api/report/csv', results, {
    responseType: 'blob',
  });
  const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', 'ai_software_testing_report.csv');
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

/**
 * Request AI narrative synthesis for IEEE 829 report
 */
export const getReportNarrative = async (payload) => {
  const res = await apiClient.post('/api/report/narrative', payload);
  return res.data;
};

/**
 * Generate and download formal IEEE 829 PDF test report
 */
export const downloadReportPdf = async (payload) => {
  const response = await apiClient.post('/api/report/pdf', payload, {
    responseType: 'blob',
  });
  const blob = new Blob([response.data], { type: 'application/pdf' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  const filename = `${(payload.metadata?.project_name || 'Software').replace(/\s+/g, '_')}_Test_Report.pdf`;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

/**
 * Generate and download formal IEEE 829 Word (.docx) test report
 */
export const downloadReportDocx = async (payload) => {
  const response = await apiClient.post('/api/report/docx', payload, {
    responseType: 'blob',
  });
  const blob = new Blob([response.data], {
    type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  const filename = `${(payload.metadata?.project_name || 'Software').replace(/\s+/g, '_')}_Test_Report.docx`;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};



