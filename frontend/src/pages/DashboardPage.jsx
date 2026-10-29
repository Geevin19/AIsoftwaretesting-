import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { MetricCard } from '../components/MetricCard';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import {
  CheckCircle2,
  XCircle,
  Clock,
  Percent,
  Layers,
  ArrowLeft,
  ArrowRight,
  TrendingUp,
  Activity,
  FileText
} from 'lucide-react';

export const DashboardPage = () => {
  const navigate = useNavigate();
  const { metrics, testResults } = useApp();

  if (!metrics || !testResults || testResults.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[460px] text-center p-8 bg-white border border-slate-200 rounded-2xl shadow-sm">
        <div className="w-16 h-16 rounded-2xl bg-indigo-50 border border-indigo-200 flex items-center justify-center mb-4">
          <Activity className="w-8 h-8 text-indigo-600" />
        </div>
        <h2 className="text-xl font-bold text-slate-900">No Analytics Data Available</h2>
        <p className="text-sm text-slate-500 max-w-md mt-2">
          Execute tests first in Step 2 or 3 to populate this QA dashboard with real-time charts and reliability metrics.
        </p>
        <button
          onClick={() => navigate('/tests')}
          className="mt-6 flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 transition-colors shadow-md shadow-indigo-600/20"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Go to Tests Page</span>
        </button>
      </div>
    );
  }

  // 1. Data for Pie Chart (Pass vs Fail vs Error)
  const pieData = [
    { name: 'Passed', value: metrics.passed, color: '#10b981' },
    { name: 'Failed', value: metrics.failed, color: '#f43f5e' },
    { name: 'Error', value: metrics.error, color: '#f59e0b' },
  ].filter((item) => item.value > 0);

  // 2. Data for Category Breakdown Bar Chart
  const categories = ['normal', 'boundary', 'invalid'];
  const barData = categories.map((cat) => {
    const testsInCat = testResults.filter((r) => (r.category || '').toLowerCase() === cat);
    const passed = testsInCat.filter((r) => r.status === 'PASS').length;
    const failed = testsInCat.filter((r) => r.status === 'FAIL' || r.status === 'ERROR').length;
    const label = cat === 'normal' ? 'Normal Cases' : cat === 'boundary' ? 'Boundary Cases' : 'Invalid Inputs';
    return {
      category: label,
      Passed: passed,
      Failed: failed,
      Total: testsInCat.length,
    };
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold text-indigo-600 uppercase tracking-wider">
            <span>Step 4 of 5</span>
            <span>•</span>
            <span>Quality Analytics & Metrics</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight mt-1">
            Software Testing Dashboard
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Real-time visual breakdown of test execution health, boundary defect density, and response times.
          </p>
        </div>

        <button
          onClick={() => navigate('/reports')}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 transition-all shadow-md shadow-indigo-600/20"
        >
          <FileText className="w-4 h-4" />
          <span>View Exportable Reports</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard
          title="Total Tests"
          value={metrics.total}
          subtitle="Suite size"
          icon={Layers}
          color="blue"
        />
        <MetricCard
          title="Passed Tests"
          value={metrics.passed}
          subtitle="Compliant assertions"
          icon={CheckCircle2}
          color="emerald"
        />
        <MetricCard
          title="Failed / Bugs"
          value={metrics.failed + metrics.error}
          subtitle="Detected defects"
          icon={XCircle}
          color="rose"
        />
        <MetricCard
          title="Pass Percentage"
          value={`${metrics.pass_percent}%`}
          subtitle="Test suite reliability"
          icon={Percent}
          color={metrics.pass_percent > 80 ? 'emerald' : 'amber'}
        />
        <MetricCard
          title="Execution Time"
          value={`${metrics.total_time_ms} ms`}
          subtitle="Subprocess total duration"
          icon={Clock}
          color="indigo"
        />
      </div>

      {/* Visual Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pass vs Fail Distribution (Pie Chart) */}
        <div className="bg-white border border-slate-200 p-5 rounded-2xl shadow-sm flex flex-col">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-emerald-600" />
                Pass vs Fail Distribution
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">Ratio of successful to failing unit tests</p>
            </div>
            <span className="text-xs font-mono font-semibold text-indigo-700 bg-indigo-50 px-2.5 py-1 rounded-md border border-indigo-200">
              {metrics.pass_percent}% Success
            </span>
          </div>

          <div className="h-64 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={5}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    borderColor: '#cbd5e1',
                    borderRadius: '8px',
                    color: '#0f172a',
                    fontSize: '12px',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                  }}
                />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  wrapperStyle={{ fontSize: '12px', color: '#475569' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Results by Category (Bar Chart) */}
        <div className="bg-white border border-slate-200 p-5 rounded-2xl shadow-sm flex flex-col">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-600" />
                Test Results by Category
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Comparison across Normal, Boundary, and Invalid Input sets
              </p>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={barData}
                margin={{ top: 20, right: 30, left: -10, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis
                  dataKey="category"
                  stroke="#64748b"
                  fontSize={11}
                  tickLine={false}
                />
                <YAxis
                  stroke="#64748b"
                  fontSize={11}
                  allowDecimals={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    borderColor: '#cbd5e1',
                    borderRadius: '8px',
                    color: '#0f172a',
                    fontSize: '12px',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                  }}
                />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  wrapperStyle={{ fontSize: '12px', color: '#475569' }}
                />
                <Bar dataKey="Passed" fill="#10b981" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Failed" fill="#f43f5e" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Engineering Insights Card */}
      <div className="p-5 rounded-2xl bg-indigo-50/70 border border-indigo-200 shadow-xs">
        <h4 className="text-sm font-semibold text-indigo-950 flex items-center gap-2 mb-2">
          <Activity className="w-4 h-4 text-indigo-600" />
          Software Engineering Micro Project Assessment
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-slate-700 mt-3">
          <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-xs">
            <span className="font-semibold text-slate-900 block mb-1">Subprocess Isolation</span>
            <p className="text-slate-500 text-[11px] leading-relaxed">
              Every unit test was spawned in a dedicated Python interpreter process with a strict 5-second timeout, ensuring zero cross-test interference or infinite loop crashes.
            </p>
          </div>
          <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-xs">
            <span className="font-semibold text-slate-900 block mb-1">Boundary Defect Density</span>
            <p className="text-slate-500 text-[11px] leading-relaxed">
              Boundary edge-cases (e.g. division by zero, min string lengths) successfully exposed intentional bugs that traditional random testing often overlooks.
            </p>
          </div>
          <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-xs">
            <span className="font-semibold text-slate-900 block mb-1">Gemini AI Debug Assistance</span>
            <p className="text-slate-500 text-[11px] leading-relaxed">
              When tests fail, the AI model generates an educational explanation and a ready-to-merge source fix directly applicable through React Context.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
