/**
 * AppContext: Global Session State Management
 * Holds project source files, active file selection, AST static analysis metadata,
 * generated tests, subprocess results, and AI fix proposals.
 * No database required — all session data is held in client memory state.
 */
import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  getSamples,
  getSample,
  analyzeCode,
  generateTests,
  generateMoreTests,
  runTests,
  analyzeBug,
  exportPytestSuite,
  getReportNarrative,
  downloadReportPdf,
  downloadReportDocx,
  downloadReportCsv,
} from '../api/client';

const AppContext = createContext(null);

const DEFAULT_PYTHON_CODE = `"""
Sample Module: Calculator
Contains basic arithmetic operations with deliberate edge-case bugs.
Used to demonstrate AI-assisted testing and bug detection in software engineering.
"""

def calculate(operation: str, a: float, b: float) -> float:
    """
    Performs arithmetic calculation based on operation name.
    
    Supported operations:
        - 'add': returns a + b
        - 'subtract': returns a - b
        - 'multiply': returns a * b
        - 'divide': returns a / b (should raise ZeroDivisionError when b == 0)
    
    DELIBERATE BUGS:
    1. Division by zero: Returns 0.0 instead of raising ZeroDivisionError.
    2. Invalid operation string does not raise ValueError properly when empty.
    """
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Arguments a and b must be numeric")

    op = str(operation).strip().lower()
    
    if op == "add":
        return float(a + b)
    elif op == "subtract":
        return float(a - b)
    elif op == "multiply":
        return float(a * b)
    elif op == "divide":
        # DELIBERATE BUG: Returns 0.0 instead of raising ZeroDivisionError when b == 0
        if b == 0:
            return 0.0
        return float(a / b)
    else:
        raise ValueError(f"Unsupported operation: {operation}")
`;

export const AppProvider = ({ children }) => {
  // Multi-file state: [{ path: "main.py", content: "...", included: true, syntax_error: null }]
  const [files, setFiles] = useState([
    {
      path: 'main.py',
      content: DEFAULT_PYTHON_CODE,
      included: true,
      syntax_error: null,
    },
  ]);
  const [activeFile, setActiveFile] = useState('main.py');
  const [language, setLanguage] = useState('python');

  // Sample catalog state
  const [samplesList, setSamplesList] = useState([]);
  const [selectedSample, setSelectedSample] = useState('calculator');

  // Upload notifications / skipped list
  const [uploadSkipped, setUploadSkipped] = useState([]);
  const [uploadInfo, setUploadInfo] = useState(null);

  // Stage 1 Static AST Analysis state
  const [codeAnalysis, setCodeAnalysis] = useState(null);
  const [selectedFunctionIds, setSelectedFunctionIds] = useState([]);
  const [isCodeDirty, setIsCodeDirty] = useState(false);

  // Stage 2 Grounded AI Generation state & Diagnostics
  const [tests, setTests] = useState([]);
  const [rejectedTests, setRejectedTests] = useState([]);
  const [skippedFunctions, setSkippedFunctions] = useState([]);
  const [coverageNotes, setCoverageNotes] = useState({});

  // Execution results & statistics
  const [testResults, setTestResults] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [runHistory, setRunHistory] = useState([]);

  // Fix suggestions captured from AI bug analyses
  const [fixSuggestions, setFixSuggestions] = useState([]);

  // Report metadata for formal IEEE 829 / ISO 29119 reports
  const [reportMetadata, setReportMetadata] = useState({
    project_name: 'AI Software Testing Assistant',
    report_title: 'Software Test Summary Report',
    document_id: `TR-${new Date().toISOString().slice(0, 10).replace(/-/g, '')}-001`,
    version: '1.0',
    organization: 'Department of Computer Science & Engineering',
    prepared_by: 'QA Automation Lead',
    reviewed_by: 'Principal Software Architect',
    test_environment: 'Windows 11 / Python 3.9 / FastAPI / AST Subprocess Runner',
    test_date: new Date().toISOString().slice(0, 10),
    pass_threshold: 90,
  });

  // Bug analysis state for FixReview component
  const [activeAnalysis, setActiveAnalysis] = useState(null);
  const [analyzingTestId, setAnalyzingTestId] = useState(null);

  // UI Loading and Notification state
  const [isLoading, setIsLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // Fetch sample catalog on startup
  useEffect(() => {
    const fetchSamplesList = async () => {
      try {
        const samples = await getSamples();
        setSamplesList(samples);
      } catch (err) {
        console.warn('Backend samples list not immediately reachable:', err.message);
      }
    };
    fetchSamplesList();
  }, []);

  // Helper getter for active file object
  const currentFileObj = files.find((f) => f.path === activeFile) || files[0] || null;

  /**
   * Update active file content (used by Monaco editor when user types or pastes)
   */
  const updateFileContent = (path, newContent) => {
    setIsCodeDirty(true);
    setFiles((prev) =>
      prev.map((f) => (f.path === path ? { ...f, content: newContent, syntax_error: null } : f))
    );
  };

  /**
   * Toggle file inclusion checkbox in FileTree
   */
  const toggleFileIncluded = (path) => {
    setIsCodeDirty(true);
    setFiles((prev) =>
      prev.map((f) => (f.path === path ? { ...f, included: !f.included } : f))
    );
  };

  /**
   * Add a new file to the project
   */
  const addFile = (newPath, initialContent = '# New Python module\n') => {
    const cleanPath = newPath.replace(/\\/g, '/').trim().replace(/^\//, '');
    if (!cleanPath) return;

    if (files.some((f) => f.path === cleanPath)) {
      setErrorMessage(`File '${cleanPath}' already exists.`);
      return;
    }

    const newObj = {
      path: cleanPath,
      content: initialContent,
      included: true,
      syntax_error: null,
    };

    setIsCodeDirty(true);
    setFiles((prev) => [...prev, newObj]);
    setActiveFile(cleanPath);
    setSuccessMessage(`Created file '${cleanPath}'.`);
  };

  /**
   * Remove a file from the project
   */
  const removeFile = (path) => {
    setIsCodeDirty(true);
    setFiles((prev) => {
      const remaining = prev.filter((f) => f.path !== path);
      if (activeFile === path) {
        setActiveFile(remaining[0]?.path || '');
      }
      return remaining;
    });
  };

  /**
   * Handle files returned from /api/upload
   */
  const handleUploadSuccess = (uploadedFiles, skipped) => {
    if (uploadedFiles && uploadedFiles.length > 0) {
      setFiles(uploadedFiles);
      setActiveFile(uploadedFiles[0].path);
      setTests([]);
      setTestResults([]);
      setMetrics(null);
      setActiveAnalysis(null);
      setCodeAnalysis(null);
      setSelectedFunctionIds([]);
      setIsCodeDirty(true);
    }
    setUploadSkipped(skipped || []);
    if (skipped && skipped.length > 0) {
      setUploadInfo(`Uploaded ${uploadedFiles.length} files. ${skipped.length} files were skipped according to policy.`);
    } else {
      setUploadInfo(`Successfully uploaded and parsed ${uploadedFiles.length} source files.`);
    }
  };

  /**
   * Load code from a selected sample into the editor as a single file
   */
  const handleLoadSample = async (sampleId) => {
    try {
      setIsLoading(true);
      setLoadingMessage(`Loading sample '${sampleId}'...`);
      setSelectedSample(sampleId);
      const data = await getSample(sampleId);
      if (data && data.code) {
        const sampleFileName = `${sampleId}.py`;
        setFiles([
          {
            path: sampleFileName,
            content: data.code,
            included: true,
            syntax_error: null,
          },
        ]);
        setActiveFile(sampleFileName);
        setTests([]);
        setTestResults([]);
        setMetrics(null);
        setActiveAnalysis(null);
        setCodeAnalysis(null);
        setSelectedFunctionIds([]);
        setIsCodeDirty(true);
        setUploadSkipped([]);
        setUploadInfo(null);
        setSuccessMessage(`Loaded sample '${data.title}'. Click 'Analyze Code' to inspect functions.`);
      }
    } catch (err) {
      setErrorMessage(`Failed to load sample: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Stage 1: Static AST Code Analysis
   * Parses included files with Python ast, detects public functions, classes,
   * risky operations, and syntax errors.
   */
  const handleAnalyzeCode = async () => {
    const includedFiles = files.filter((f) => f.included);
    if (!includedFiles || includedFiles.length === 0) {
      setErrorMessage('No included files found to analyze. Please check at least one file.');
      return null;
    }

    try {
      setIsLoading(true);
      setLoadingMessage('Parsing source code structure using Python AST analyzer...');
      setErrorMessage(null);

      const res = await analyzeCode(includedFiles);
      setCodeAnalysis(res);

      // Reflect syntax errors back onto file state if any
      if (res.syntax_errors && res.syntax_errors.length > 0) {
        const errMap = new Map();
        res.syntax_errors.forEach((err) => {
          errMap.set(err.file, err.message);
        });
        setFiles((prev) =>
          prev.map((f) => ({
            ...f,
            syntax_error: errMap.get(f.path) || null,
          }))
        );
      } else {
        setFiles((prev) => prev.map((f) => ({ ...f, syntax_error: null })));
      }

      // Default: select all detected functions
      const allIds = (res.functions || []).map((fn) => fn.id);
      setSelectedFunctionIds(allIds);

      setIsCodeDirty(false);
      setSuccessMessage(
        `AST Analysis complete: Detected ${res.summary?.total_functions || 0} function(s) across ${res.summary?.total_files || 0} file(s).`
      );
      return res;
    } catch (err) {
      setErrorMessage(`Static Analysis Failed: ${err.message}`);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Toggle function selection in AnalysisPanel
   */
  const toggleFunctionSelection = (functionId) => {
    setSelectedFunctionIds((prev) =>
      prev.includes(functionId)
        ? prev.filter((id) => id !== functionId)
        : [...prev, functionId]
    );
  };

  /**
   * Select or deselect all detected functions
   */
  const selectAllFunctions = (select = true) => {
    if (!codeAnalysis?.functions) return;
    if (select) {
      setSelectedFunctionIds(codeAnalysis.functions.map((fn) => fn.id));
    } else {
      setSelectedFunctionIds([]);
    }
  };

  /**
   * Stage 2: Grounded AI Test Generation
   * Synthesizes unit tests for selected functions based on AST signature grounding.
   */
  const handleGenerateTests = async (onSuccessNavigate, perFunction = 6) => {
    const includedFiles = files.filter((f) => f.included && !f.syntax_error);
    if (!includedFiles || includedFiles.length === 0) {
      setErrorMessage('No valid included Python files available for test generation.');
      return;
    }

    // If static analysis hasn't run yet or code changed, run AST analysis first
    let currentAnalysis = codeAnalysis;
    let functionsToTarget = null;

    if (!currentAnalysis || isCodeDirty) {
      currentAnalysis = await handleAnalyzeCode();
      if (!currentAnalysis) return;
      functionsToTarget = currentAnalysis.functions;
    } else {
      // Filter selected functions
      if (selectedFunctionIds.length > 0 && currentAnalysis.functions) {
        functionsToTarget = currentAnalysis.functions.filter((fn) =>
          selectedFunctionIds.includes(fn.id)
        );
      } else {
        functionsToTarget = currentAnalysis.functions;
      }
    }

    if (!functionsToTarget || functionsToTarget.length === 0) {
      setErrorMessage('No functions selected for test generation. Please select at least one function in the Analysis Panel.');
      return;
    }

    try {
      setIsLoading(true);
      setLoadingMessage(
        `Gemini AI is generating grounded unit tests for ${functionsToTarget.length} selected function(s)...`
      );
      setErrorMessage(null);

      const selectedIdsToSend = (functionsToTarget || []).map((f) => f.id || f.function_name || f.name);

      const response = await generateTests(
        includedFiles,
        selectedIdsToSend,
        perFunction,
        language
      );

      if (response && response.tests) {
        // Tag tests with is_ai: true if not explicitly set
        const taggedTests = response.tests.map((t) => ({
          ...t,
          is_ai: t.is_ai !== undefined ? t.is_ai : true,
        }));

        const notesMap = {};
        if (Array.isArray(response.coverage_notes)) {
          response.coverage_notes.forEach((item) => {
            if (item.function_id) notesMap[item.function_id] = item.note;
            if (item.function_name) notesMap[item.function_name] = item.note;
            if (item.file && item.function_name) {
              notesMap[`${item.file}::${item.function_name}`] = item.note;
            }
          });
        } else if (response.coverage_notes && typeof response.coverage_notes === 'object') {
          Object.assign(notesMap, response.coverage_notes);
        }

        setTests(taggedTests);
        setRejectedTests(response.rejected || []);
        setSkippedFunctions(response.skipped_functions || []);
        setCoverageNotes(notesMap);
        setTestResults([]);
        setMetrics(null);
        setActiveAnalysis(null);
        setIsCodeDirty(false);

        const count = taggedTests.length;
        const rejectedCount = (response.rejected || []).length;
        let msg = `Successfully generated ${count} grounded unit test(s)!`;
        if (rejectedCount > 0) {
          msg += ` (${rejectedCount} malformed/duplicate tests were filtered by AST validator).`;
        }
        setSuccessMessage(msg);

        if (onSuccessNavigate) {
          onSuccessNavigate('/tests');
        }
      }
    } catch (err) {
      setErrorMessage(`Test Generation Error: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Generate additional tests for a specific function/category
   */
  const handleGenerateMore = async (functionId, category = null, count = 3) => {
    const includedFiles = files.filter((f) => f.included && !f.syntax_error);
    if (!includedFiles || includedFiles.length === 0) {
      setErrorMessage('No valid included files available.');
      return;
    }

    try {
      setIsLoading(true);
      setLoadingMessage(`Generating ${count} more ${category || 'targeted'} tests...`);
      setErrorMessage(null);

      const response = await generateMoreTests(
        includedFiles,
        functionId,
        category,
        count,
        tests
      );

      if (response && response.tests && response.tests.length > 0) {
        const newTests = response.tests.map((t) => ({
          ...t,
          is_ai: true,
        }));
        setTests((prev) => [...prev, ...newTests]);
        if (response.coverage_notes) {
          setCoverageNotes((prev) => ({ ...prev, ...response.coverage_notes }));
        }
        setSuccessMessage(`Added ${newTests.length} new unit test(s) to the suite.`);
      } else {
        setErrorMessage('No additional valid tests could be synthesized for the requested target.');
      }
    } catch (err) {
      setErrorMessage(`Generate More Failed: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Execute the current test suite against all project files
   */
  const handleRunTests = async (onSuccessNavigate) => {
    if (!tests || tests.length === 0) {
      setErrorMessage('No test cases to run. Please generate or add tests first.');
      return;
    }

    try {
      setIsLoading(true);
      setLoadingMessage(`Executing ${tests.length} tests in isolated Python subprocesses with 5-second timeouts...`);
      setErrorMessage(null);

      const response = await runTests(files, tests);
      if (response && response.results) {
        setTestResults(response.results);
        setMetrics(response.metrics);
        setRunHistory((prev) => [
          ...prev,
          {
            id: Date.now(),
            timestamp: new Date().toISOString(),
            metrics: response.metrics,
            results: response.results,
          },
        ]);
        setSuccessMessage(`Execution completed: ${response.metrics.passed}/${response.metrics.total} passed (${response.metrics.pass_percent}%).`);
        if (onSuccessNavigate) {
          onSuccessNavigate('/results');
        }
      }
    } catch (err) {
      setErrorMessage(`Test Run Error: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Request AI Bug Explanation and Code Fix for a failing test
   */
  const handleAnalyzeBug = async (resultItem) => {
    const matchingTest = tests.find((t) => t.id === resultItem.id) || {
      name: resultItem.name,
      file: resultItem.file || activeFile,
      module: resultItem.module || 'main',
      function_name: resultItem.function_name,
      input: resultItem.input,
      expected: resultItem.expected,
      purpose: resultItem.purpose || '',
    };

    try {
      setAnalyzingTestId(resultItem.id);
      setIsLoading(true);
      setLoadingMessage(`Gemini AI is analyzing failure for '${resultItem.name}' in '${matchingTest.file}'...`);
      setErrorMessage(null);

      const analysis = await analyzeBug(
        files,
        matchingTest,
        resultItem.actual,
        resultItem.status
      );

      setActiveAnalysis({
        testId: resultItem.id,
        testName: resultItem.name,
        test: matchingTest,
        file: analysis.file || matchingTest.file,
        actual: resultItem.actual,
        expected: resultItem.expected,
        status: resultItem.status,
        explanation: analysis.explanation,
        suggestedFix: analysis.suggested_fix,
      });

      setFixSuggestions((prev) => {
        const filtered = prev.filter((s) => s.testId !== resultItem.id);
        return [
          ...filtered,
          {
            testId: resultItem.id,
            function_name: matchingTest.function_name,
            file: analysis.file || matchingTest.file,
            explanation: analysis.explanation,
            suggested_fix: analysis.suggested_fix,
          },
        ];
      });
    } catch (err) {
      setErrorMessage(`AI Bug Analysis Error: ${err.message}`);
    } finally {
      setIsLoading(false);
      setAnalyzingTestId(null);
    }
  };

  /**
   * Accept AI proposed fix: Replaces code of the target file in Context
   */
  const acceptFix = (suggestedFixCode, targetFilePath) => {
    const path = targetFilePath || activeAnalysis?.file || activeFile;
    if (suggestedFixCode && path) {
      setIsCodeDirty(true);
      updateFileContent(path, suggestedFixCode);
      setActiveFile(path);
      setActiveAnalysis(null);
      setSuccessMessage(`AI fix applied to '${path}'! Re-analyze code and re-run tests to verify the fix.`);
    }
  };

  /**
   * Reject proposed fix
   */
  const rejectFix = () => {
    setActiveAnalysis(null);
  };

  /**
   * Edit an individual test case
   */
  const updateTest = (testId, updatedFields) => {
    setTests((prev) =>
      prev.map((t) => (t.id === testId ? { ...t, ...updatedFields } : t))
    );
  };

  /**
   * Delete a test case
   */
  const deleteTest = (testId) => {
    setTests((prev) => prev.filter((t) => t.id !== testId));
  };

  /**
   * Add a custom manual test case
   */
  const addTest = (newTest) => {
    setTests((prev) => [
      ...prev,
      {
        ...newTest,
        is_ai: false,
      },
    ]);
  };

  /**
   * Export pytest project suite as zip
   */
  const handleExportPytest = async () => {
    try {
      setIsLoading(true);
      setLoadingMessage('Packaging project and pytest suite into .zip archive...');
      await exportPytestSuite(files, tests);
    } catch (err) {
      setErrorMessage(`Export failed: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Export formal IEEE 829 Software Test Report (PDF, Word, or CSV)
   */
  const handleExportReport = async (format = 'pdf', customMetadata = null) => {
    if (!testResults || testResults.length === 0) {
      setErrorMessage('Cannot generate report without test execution results. Please execute tests first.');
      return;
    }

    const meta = customMetadata || reportMetadata;

    // CSV direct stream download
    if (format === 'csv') {
      try {
        setIsLoading(true);
        setLoadingMessage('Exporting raw test execution results as CSV...');
        await downloadReportCsv(testResults);
        setSuccessMessage('Successfully exported CSV test report.');
      } catch (err) {
        setErrorMessage(`CSV Export failed: ${err.message}`);
      } finally {
        setIsLoading(false);
      }
      return;
    }

    try {
      setIsLoading(true);
      setLoadingMessage('Synthesizing AI prose narrative and compiling formal software test report...');
      setErrorMessage(null);

      // Build regression comparison payload if 2 or more runs exist
      let comparison = null;
      if (runHistory && runHistory.length >= 2) {
        const prevRun = runHistory[runHistory.length - 2];
        comparison = {
          has_previous_run: true,
          previous_metrics: prevRun.metrics,
          previous_results: prevRun.results,
        };
      }

      // Prepare defects summary for the narrative generator
      const failedDefectsSummary = (testResults || [])
        .filter((r) => r.status === 'FAIL' || r.status === 'ERROR')
        .map((r, idx) => ({
          defect_id: `DEF-${String(idx + 1).padStart(3, '0')}`,
          title: r.name,
          function: r.function_name,
          file: r.file,
          input: JSON.stringify(r.input),
          expected: JSON.stringify(r.expected),
          actual: String(r.actual),
          severity:
            r.status === 'ERROR' || r.category === 'normal'
              ? 'High'
              : r.category === 'boundary'
              ? 'Medium'
              : 'Low',
        }));

      const highSeverityCount = failedDefectsSummary.filter((d) => d.severity === 'High').length;

      // 1. Fetch single-call AI narrative
      let narrative = null;
      try {
        narrative = await getReportNarrative({
          metadata: meta,
          metrics,
          results: testResults,
          functions_count: codeAnalysis?.functions?.length || 0,
          files_count: files.length,
          high_severity_count: highSeverityCount,
          failed_tests_summary: failedDefectsSummary,
        });
      } catch (narrErr) {
        console.warn('AI narrative synthesis note (using deterministic template):', narrErr.message);
      }

      // 2. Build full generation payload
      const payload = {
        metadata: meta,
        files: files.filter((f) => f.included && !f.syntax_error),
        results: testResults,
        metrics,
        analysis: codeAnalysis,
        suggestions: fixSuggestions,
        comparison,
        narrative,
      };

      // 3. Download target document format
      if (format === 'docx') {
        setLoadingMessage('Compiling IEEE 829 Word (.docx) document with dynamic Table of Contents...');
        await downloadReportDocx(payload);
        setSuccessMessage('Successfully generated and downloaded formal IEEE 829 Word (.docx) test report.');
      } else {
        setLoadingMessage('Compiling IEEE 829 PDF document with running headers, footers, and charts...');
        await downloadReportPdf(payload);
        setSuccessMessage('Successfully generated and downloaded formal IEEE 829 PDF test report.');
      }
    } catch (err) {
      setErrorMessage(`Report Generation Failed: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const clearMessages = () => {
    setErrorMessage(null);
    setSuccessMessage(null);
    setUploadInfo(null);
  };

  return (
    <AppContext.Provider
      value={{
        files,
        setFiles,
        activeFile,
        setActiveFile,
        currentFileObj,
        updateFileContent,
        toggleFileIncluded,
        addFile,
        removeFile,
        handleUploadSuccess,
        uploadSkipped,
        setUploadSkipped,
        uploadInfo,
        language,
        setLanguage,
        samplesList,
        selectedSample,
        handleLoadSample,
        codeAnalysis,
        selectedFunctionIds,
        isCodeDirty,
        handleAnalyzeCode,
        toggleFunctionSelection,
        selectAllFunctions,
        tests,
        setTests,
        rejectedTests,
        skippedFunctions,
        coverageNotes,
        updateTest,
        deleteTest,
        addTest,
        handleGenerateTests,
        handleGenerateMore,
        testResults,
        metrics,
        runHistory,
        reportMetadata,
        setReportMetadata,
        fixSuggestions,
        handleRunTests,
        handleAnalyzeBug,
        analyzingTestId,
        activeAnalysis,
        acceptFix,
        rejectFix,
        handleExportPytest,
        handleExportReport,
        isLoading,
        loadingMessage,
        errorMessage,
        successMessage,
        clearMessages,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
