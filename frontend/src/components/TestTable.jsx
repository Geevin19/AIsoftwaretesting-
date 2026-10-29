import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { CategoryBadge } from './StatusBadge';
import { 
  Trash2, 
  Edit2, 
  Check, 
  X, 
  PlusCircle, 
  Sparkles, 
  FileCode, 
  Code2, 
  Info,
  CheckCircle2,
  Cpu,
  UserCheck
} from 'lucide-react';

export const TestTable = () => {
  const {
    tests,
    updateTest,
    deleteTest,
    addTest,
    files,
    codeAnalysis,
    coverageNotes,
    handleGenerateMore,
    isLoading,
  } = useApp();

  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({});

  // Add Test Modal state
  const [showAddModal, setShowAddModal] = useState(false);
  const [newTest, setNewTest] = useState({
    name: '',
    category: 'normal',
    file: files[0]?.path || 'main.py',
    module: 'main',
    class_name: '',
    function_name: '',
    input: '',
    expected: '',
    purpose: '',
  });

  // Generate More Modal state
  const [showMoreModal, setShowMoreModal] = useState(false);
  const [moreForm, setMoreForm] = useState({
    function_id: '',
    category: 'all',
    count: 3,
  });

  const availableFunctions = codeAnalysis?.functions || [];

  // Group tests by file then function
  const grouped = tests.reduce((acc, test) => {
    const fileKey = test.file || 'main.py';
    const fnKey = test.class_name ? `${test.class_name}.${test.function_name}` : test.function_name;
    const groupKey = `${fileKey}::${fnKey}`;

    if (!acc[groupKey]) {
      acc[groupKey] = {
        file: fileKey,
        module: test.module || fileKey.replace(/\.py$/, '').replace(/\//g, '.'),
        class_name: test.class_name || null,
        function_name: test.function_name,
        displayName: fnKey,
        tests: [],
      };
    }
    acc[groupKey].tests.push(test);
    return acc;
  }, {});

  const groupKeys = Object.keys(grouped);

  const startEdit = (test) => {
    setEditingId(test.id);
    setEditForm({
      name: test.name,
      category: test.category,
      file: test.file || 'main.py',
      module: test.module || 'main',
      class_name: test.class_name || '',
      function_name: test.function_name,
      input: JSON.stringify(test.input),
      expected: typeof test.expected === 'string' ? test.expected : JSON.stringify(test.expected),
      purpose: test.purpose || '',
    });
  };

  const saveEdit = (id) => {
    let parsedInput = [];
    let parsedExpected = editForm.expected;

    try {
      parsedInput = JSON.parse(editForm.input);
    } catch {
      parsedInput = editForm.input.split(',').map((s) => {
        const trimmed = s.trim();
        const num = Number(trimmed);
        return isNaN(num) ? trimmed : num;
      });
    }

    try {
      parsedExpected = JSON.parse(editForm.expected);
    } catch {
      parsedExpected = editForm.expected;
    }

    updateTest(id, {
      name: editForm.name,
      category: editForm.category,
      file: editForm.file,
      module: editForm.module,
      class_name: editForm.class_name || null,
      function_name: editForm.function_name,
      input: parsedInput,
      expected: parsedExpected,
      purpose: editForm.purpose,
    });

    setEditingId(null);
  };

  const openAddModal = (defaultFn = null) => {
    if (defaultFn) {
      setNewTest({
        name: `Verify ${defaultFn.displayName} behavior`,
        category: 'normal',
        file: defaultFn.file,
        module: defaultFn.module,
        class_name: defaultFn.class_name || '',
        function_name: defaultFn.function_name,
        input: '[]',
        expected: '',
        purpose: `Manual test for ${defaultFn.displayName}`,
      });
    } else if (availableFunctions.length > 0) {
      const firstFn = availableFunctions[0];
      setNewTest({
        name: `Verify ${firstFn.name} behavior`,
        category: 'normal',
        file: firstFn.file,
        module: firstFn.module,
        class_name: firstFn.class_name || '',
        function_name: firstFn.name,
        input: '[]',
        expected: '',
        purpose: `Manual test for ${firstFn.name}`,
      });
    } else {
      setNewTest({
        name: 'Custom Unit Test',
        category: 'normal',
        file: files[0]?.path || 'main.py',
        module: 'main',
        class_name: '',
        function_name: 'calculate',
        input: '[]',
        expected: '',
        purpose: '',
      });
    }
    setShowAddModal(true);
  };

  const handleSelectFnInAddModal = (fnId) => {
    const fn = availableFunctions.find((f) => f.id === fnId);
    if (!fn) return;
    setNewTest((prev) => ({
      ...prev,
      file: fn.file,
      module: fn.module,
      class_name: fn.class_name || '',
      function_name: fn.name,
      name: `Verify ${fn.class_name ? fn.class_name + '.' : ''}${fn.name} behavior`,
      purpose: `Manual test for ${fn.name}`,
    }));
  };

  const handleCreateTest = (e) => {
    e.preventDefault();
    let parsedInput = [];
    let parsedExpected = newTest.expected;

    try {
      parsedInput = JSON.parse(newTest.input);
    } catch {
      parsedInput = newTest.input.split(',').map((s) => {
        const trimmed = s.trim();
        const num = Number(trimmed);
        return isNaN(num) ? trimmed : num;
      });
    }

    try {
      parsedExpected = JSON.parse(newTest.expected);
    } catch {
      parsedExpected = newTest.expected;
    }

    const created = {
      id: `tc_manual_${Date.now()}`,
      name: newTest.name || 'Manual Unit Test',
      category: newTest.category,
      file: newTest.file,
      module: newTest.module,
      class_name: newTest.class_name || null,
      function_name: newTest.function_name,
      input: parsedInput,
      expected: parsedExpected,
      purpose: newTest.purpose || 'User-defined custom unit test',
      is_ai: false,
    };

    addTest(created);
    setShowAddModal(false);
  };

  const openGenerateMoreModal = (defaultFnId = '') => {
    setMoreForm({
      function_id: defaultFnId || (availableFunctions[0]?.id || ''),
      category: 'all',
      count: 3,
    });
    setShowMoreModal(true);
  };

  const submitGenerateMore = async (e) => {
    e.preventDefault();
    const cat = moreForm.category === 'all' ? null : moreForm.category;
    await handleGenerateMore(moreForm.function_id || null, cat, Number(moreForm.count) || 3);
    setShowMoreModal(false);
  };

  return (
    <div className="space-y-4">
      {/* Table Global Controls Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-white border border-slate-200 rounded-lg shadow-xs">
        <div>
          <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
            Unit Test Suite
            <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-slate-100 text-slate-700 border border-slate-200">
              {tests.length} Total
            </span>
          </h3>
          <p className="text-[11px] text-slate-500 mt-0.5">
            Test cases grounded in your code's AST signatures. Grouped by target module and function.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => openGenerateMoreModal()}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium bg-white hover:bg-slate-50 text-indigo-700 border border-indigo-200 shadow-xs transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
            <span>Generate More</span>
          </button>

          <button
            onClick={() => openAddModal()}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 shadow-xs transition-colors"
          >
            <PlusCircle className="w-3.5 h-3.5 text-slate-600" />
            <span>Add Manual Test</span>
          </button>
        </div>
      </div>

      {/* Grouped Function Tables */}
      {groupKeys.length === 0 ? (
        <div className="p-8 text-center bg-white border border-slate-200 rounded-lg text-slate-500 text-xs">
          No test cases available.
        </div>
      ) : (
        groupKeys.map((groupKey) => {
          const group = grouped[groupKey];
          // Determine coverage note
          const groupNote =
            coverageNotes[groupKey] ||
            coverageNotes[`${group.file}::${group.displayName}`] ||
            coverageNotes[group.function_name] ||
            group.tests.find((t) => t.coverage_note)?.coverage_note ||
            null;

          // Find AST function match if available
          const astMatch = availableFunctions.find(
            (f) =>
              f.file === group.file &&
              (f.class_name ? `${f.class_name}.${f.name}` : f.name) === group.displayName
          );

          return (
            <div
              key={groupKey}
              className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-xs"
            >
              {/* Group Header */}
              <div className="px-3.5 py-2.5 bg-slate-50 border-b border-slate-200 flex flex-wrap items-center justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-mono text-slate-500">
                      Generated from:
                    </span>
                    <span className="font-mono text-xs font-semibold text-slate-900 bg-white px-2 py-0.5 rounded border border-slate-200">
                      {group.file} / {group.displayName}()
                    </span>
                    <span className="text-[11px] text-slate-500 font-mono">
                      ({group.tests.length} tests)
                    </span>
                  </div>

                  {/* Coverage Note */}
                  {groupNote && (
                    <div className="mt-1 flex items-center gap-1.5 text-[11px] text-slate-600">
                      <Info className="w-3.5 h-3.5 text-indigo-500 shrink-0" />
                      <span>{groupNote}</span>
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => openGenerateMoreModal(astMatch?.id || '')}
                    className="flex items-center gap-1 px-2 py-1 rounded text-[11px] font-medium text-indigo-700 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 transition-colors"
                  >
                    <Sparkles className="w-3 h-3 text-indigo-600" />
                    <span>Generate More</span>
                  </button>

                  <button
                    onClick={() => openAddModal(group)}
                    className="flex items-center gap-1 px-2 py-1 rounded text-[11px] font-medium text-slate-700 bg-white hover:bg-slate-50 border border-slate-300 transition-colors"
                  >
                    <PlusCircle className="w-3 h-3 text-slate-500" />
                    <span>Add Test</span>
                  </button>
                </div>
              </div>

              {/* Tests in this group */}
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-slate-100/60 text-slate-500 uppercase text-[10px] tracking-wider border-b border-slate-200">
                    <tr>
                      <th className="py-2 px-3 w-8">#</th>
                      <th className="py-2 px-3 w-20">Source</th>
                      <th className="py-2 px-3 font-sans">Test Name & Purpose</th>
                      <th className="py-2 px-3">Category</th>
                      <th className="py-2 px-3">Input Arguments</th>
                      <th className="py-2 px-3">Expected Result</th>
                      <th className="py-2 px-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {group.tests.map((test, idx) => {
                      const isEditing = editingId === test.id;
                      const isAi = test.is_ai !== false;

                      if (isEditing) {
                        return (
                          <tr key={test.id} className="bg-indigo-50/40 border-l-2 border-l-indigo-600">
                            <td className="py-2 px-3 text-slate-400">{idx + 1}</td>
                            <td className="py-2 px-3">
                              <span className="text-[10px] font-sans px-1.5 py-0.5 rounded bg-slate-200 text-slate-700">
                                Editing
                              </span>
                            </td>
                            <td className="py-2 px-3 font-sans">
                              <input
                                type="text"
                                value={editForm.name}
                                onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                                className="w-full bg-white border border-slate-300 rounded px-2 py-1 text-slate-900 text-xs mb-1"
                                placeholder="Test Name"
                              />
                              <input
                                type="text"
                                value={editForm.purpose}
                                onChange={(e) => setEditForm({ ...editForm, purpose: e.target.value })}
                                className="w-full bg-white border border-slate-300 rounded px-2 py-1 text-slate-600 text-[11px]"
                                placeholder="Purpose"
                              />
                            </td>
                            <td className="py-2 px-3">
                              <select
                                value={editForm.category}
                                onChange={(e) => setEditForm({ ...editForm, category: e.target.value })}
                                className="bg-white border border-slate-300 rounded px-2 py-1 text-xs text-slate-800"
                              >
                                <option value="normal">Normal</option>
                                <option value="boundary">Boundary</option>
                                <option value="invalid">Invalid</option>
                              </select>
                            </td>
                            <td className="py-2 px-3">
                              <input
                                type="text"
                                value={editForm.input}
                                onChange={(e) => setEditForm({ ...editForm, input: e.target.value })}
                                className="bg-white border border-slate-300 rounded px-2 py-1 text-slate-800 text-xs w-36"
                              />
                            </td>
                            <td className="py-2 px-3">
                              <input
                                type="text"
                                value={editForm.expected}
                                onChange={(e) => setEditForm({ ...editForm, expected: e.target.value })}
                                className="bg-white border border-slate-300 rounded px-2 py-1 text-slate-800 text-xs w-28"
                              />
                            </td>
                            <td className="py-2 px-3 text-right">
                              <div className="flex items-center justify-end gap-1">
                                <button
                                  onClick={() => saveEdit(test.id)}
                                  className="p-1 rounded bg-emerald-100 text-emerald-700 hover:bg-emerald-200"
                                  title="Save changes"
                                >
                                  <Check className="w-3.5 h-3.5" />
                                </button>
                                <button
                                  onClick={() => setEditingId(null)}
                                  className="p-1 rounded bg-slate-200 text-slate-600 hover:bg-slate-300"
                                  title="Cancel"
                                >
                                  <X className="w-3.5 h-3.5" />
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      }

                      return (
                        <tr key={test.id} className="hover:bg-slate-50 transition-colors">
                          <td className="py-2.5 px-3 text-slate-400">{idx + 1}</td>

                          {/* AI / Manual Badge */}
                          <td className="py-2.5 px-3 whitespace-nowrap">
                            {isAi ? (
                              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-sans font-medium bg-indigo-50 text-indigo-700 border border-indigo-200">
                                <Cpu className="w-2.5 h-2.5" />
                                AI
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-sans font-medium bg-slate-100 text-slate-700 border border-slate-200">
                                <UserCheck className="w-2.5 h-2.5" />
                                Manual
                              </span>
                            )}
                          </td>

                          {/* Test Name & Purpose */}
                          <td className="py-2.5 px-3 font-sans">
                            <div className="font-medium text-slate-900">{test.name}</div>
                            {test.purpose && (
                              <div className="text-[11px] text-slate-500 mt-0.5 line-clamp-1">
                                {test.purpose}
                              </div>
                            )}
                          </td>

                          {/* Category Badge */}
                          <td className="py-2.5 px-3 whitespace-nowrap">
                            <CategoryBadge category={test.category} />
                          </td>

                          {/* Inputs */}
                          <td className="py-2.5 px-3">
                            {test.class_name && test.constructor_args && test.constructor_args.length > 0 && (
                              <div className="text-[10px] text-slate-500 mb-1 font-sans flex items-center gap-1">
                                <span className="text-slate-400 font-medium">init({test.class_name}):</span>
                                <span className="bg-slate-100 px-1.5 py-0.2 rounded font-mono text-slate-700 border border-slate-200">
                                  {JSON.stringify(test.constructor_args)}
                                </span>
                              </div>
                            )}
                            <div className="flex items-center gap-1">
                              {test.class_name && (
                                <span className="text-[10px] text-slate-400 font-sans font-medium">args:</span>
                              )}
                              <span className="bg-slate-100 px-2 py-0.5 rounded text-slate-800 border border-slate-200 inline-block font-mono text-[11px]">
                                {JSON.stringify(test.input)}
                              </span>
                            </div>
                          </td>

                          {/* Expected Result */}
                          <td className="py-2.5 px-3">
                            <span className="bg-amber-50 px-2 py-0.5 rounded text-amber-800 border border-amber-200 inline-block font-semibold font-mono text-[11px]">
                              {typeof test.expected === 'string'
                                ? `"${test.expected}"`
                                : JSON.stringify(test.expected)}
                            </span>
                          </td>

                          {/* Actions */}
                          <td className="py-2.5 px-3 text-right">
                            <div className="flex items-center justify-end gap-1">
                              <button
                                onClick={() => startEdit(test)}
                                className="p-1 rounded text-slate-400 hover:text-indigo-600 hover:bg-slate-100 transition-colors"
                                title="Edit test"
                              >
                                <Edit2 className="w-3.5 h-3.5" />
                              </button>
                              <button
                                onClick={() => deleteTest(test.id)}
                                className="p-1 rounded text-slate-400 hover:text-rose-600 hover:bg-slate-100 transition-colors"
                                title="Delete test"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          );
        })
      )}

      {/* Add Custom Test Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="bg-white border border-slate-200 rounded-lg p-5 max-w-lg w-full shadow-lg">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200">
              <h4 className="text-sm font-semibold text-slate-900 flex items-center gap-1.5">
                <PlusCircle className="w-4 h-4 text-indigo-600" />
                Add Manual Unit Test
              </h4>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateTest} className="mt-3.5 space-y-3 text-xs">
              {/* Function dropdown from AST */}
              {availableFunctions.length > 0 && (
                <div>
                  <label className="block font-semibold text-slate-700 mb-0.5">
                    Target Function (from AST Code Analysis)
                  </label>
                  <select
                    onChange={(e) => handleSelectFnInAddModal(e.target.value)}
                    className="w-full bg-white border border-slate-300 rounded px-2.5 py-1.5 text-slate-800 font-mono"
                    defaultValue=""
                  >
                    <option value="" disabled>-- Select detected function --</option>
                    {availableFunctions.map((fn) => (
                      <option key={fn.id} value={fn.id}>
                        {fn.file} -&gt; {fn.class_name ? `${fn.class_name}.` : ''}{fn.name}({fn.parameters.map((p) => p.name).join(', ')})
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label className="block font-semibold text-slate-700 mb-0.5">Test Name</label>
                <input
                  type="text"
                  required
                  value={newTest.name}
                  onChange={(e) => setNewTest({ ...newTest, name: e.target.value })}
                  placeholder="e.g. Verify calculate handles zero divisor correctly"
                  className="w-full bg-white border border-slate-300 rounded px-2.5 py-1.5 text-slate-800"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block font-semibold text-slate-700 mb-0.5">Category</label>
                  <select
                    value={newTest.category}
                    onChange={(e) => setNewTest({ ...newTest, category: e.target.value })}
                    className="w-full bg-white border border-slate-300 rounded px-2 py-1.5 text-slate-800"
                  >
                    <option value="normal">Normal</option>
                    <option value="boundary">Boundary</option>
                    <option value="invalid">Invalid</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-0.5">Function Name</label>
                  <input
                    type="text"
                    required
                    value={newTest.function_name}
                    onChange={(e) => setNewTest({ ...newTest, function_name: e.target.value })}
                    placeholder="calculate"
                    className="w-full bg-white border border-slate-300 rounded px-2 py-1.5 text-slate-800 font-mono"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block font-semibold text-slate-700 mb-0.5">File Path</label>
                  <input
                    type="text"
                    required
                    value={newTest.file}
                    onChange={(e) => setNewTest({ ...newTest, file: e.target.value })}
                    className="w-full bg-white border border-slate-300 rounded px-2 py-1.5 text-slate-800 font-mono text-[11px]"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-0.5">Class Name (optional)</label>
                  <input
                    type="text"
                    value={newTest.class_name}
                    onChange={(e) => setNewTest({ ...newTest, class_name: e.target.value })}
                    placeholder="e.g. BankAccount"
                    className="w-full bg-white border border-slate-300 rounded px-2 py-1.5 text-slate-800 font-mono text-[11px]"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-0.5">
                  Input Arguments (JSON array, e.g. ["add", 10, 5])
                </label>
                <input
                  type="text"
                  required
                  value={newTest.input}
                  onChange={(e) => setNewTest({ ...newTest, input: e.target.value })}
                  placeholder='["add", 10, 5]'
                  className="w-full bg-white border border-slate-300 rounded px-2.5 py-1.5 text-slate-800 font-mono"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-0.5">
                  Expected Result (Literal Value or Exception Name)
                </label>
                <input
                  type="text"
                  required
                  value={newTest.expected}
                  onChange={(e) => setNewTest({ ...newTest, expected: e.target.value })}
                  placeholder='15.0 or "ZeroDivisionError"'
                  className="w-full bg-white border border-slate-300 rounded px-2.5 py-1.5 text-slate-800 font-mono"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-0.5">Purpose</label>
                <input
                  type="text"
                  value={newTest.purpose}
                  onChange={(e) => setNewTest({ ...newTest, purpose: e.target.value })}
                  placeholder="e.g. Validates correct addition of two positive numbers"
                  className="w-full bg-white border border-slate-300 rounded px-2.5 py-1.5 text-slate-800"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3 py-1.5 rounded text-xs bg-slate-100 text-slate-700 hover:bg-slate-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded text-xs font-semibold bg-indigo-600 text-white hover:bg-indigo-700"
                >
                  Add Test
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Generate More Modal */}
      {showMoreModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="bg-white border border-slate-200 rounded-lg p-5 max-w-md w-full shadow-lg">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200">
              <h4 className="text-sm font-semibold text-slate-900 flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-indigo-600" />
                Generate Additional Unit Tests
              </h4>
              <button
                onClick={() => setShowMoreModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={submitGenerateMore} className="mt-3.5 space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-0.5">Target Function</label>
                <select
                  value={moreForm.function_id}
                  onChange={(e) => setMoreForm({ ...moreForm, function_id: e.target.value })}
                  className="w-full bg-white border border-slate-300 rounded px-2.5 py-1.5 text-slate-800 font-mono"
                >
                  <option value="">All Detected Functions</option>
                  {availableFunctions.map((fn) => (
                    <option key={fn.id} value={fn.id}>
                      {fn.file} -&gt; {fn.class_name ? `${fn.class_name}.` : ''}{fn.name}()
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-0.5">Test Category</label>
                <select
                  value={moreForm.category}
                  onChange={(e) => setMoreForm({ ...moreForm, category: e.target.value })}
                  className="w-full bg-white border border-slate-300 rounded px-2.5 py-1.5 text-slate-800"
                >
                  <option value="all">Balanced (Normal, Boundary, Invalid)</option>
                  <option value="normal">Normal (Standard Happy Paths)</option>
                  <option value="boundary">Boundary (Limits, Zeroes, Off-by-one)</option>
                  <option value="invalid">Invalid (Type errors, Exceptions)</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-0.5">Number of Tests</label>
                <select
                  value={moreForm.count}
                  onChange={(e) => setMoreForm({ ...moreForm, count: Number(e.target.value) })}
                  className="w-full bg-white border border-slate-300 rounded px-2.5 py-1.5 text-slate-800"
                >
                  <option value={1}>1 test</option>
                  <option value={2}>2 tests</option>
                  <option value={3}>3 tests</option>
                  <option value={4}>4 tests</option>
                  <option value={5}>5 tests</option>
                </select>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setShowMoreModal(false)}
                  className="px-3 py-1.5 rounded text-xs bg-slate-100 text-slate-700 hover:bg-slate-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="flex items-center gap-1.5 px-4 py-1.5 rounded text-xs font-semibold bg-indigo-600 text-white hover:bg-indigo-700 shadow-xs"
                >
                  <Sparkles className="w-3.5 h-3.5 text-indigo-200" />
                  <span>Generate Tests</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
