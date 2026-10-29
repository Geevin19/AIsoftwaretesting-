import React from 'react';
import { NavLink } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { 
  Code2, 
  FlaskConical, 
  CheckCircle2, 
  BarChart3, 
  FileText, 
  Sparkles 
} from 'lucide-react';

export const Navbar = () => {
  const { tests, metrics } = useApp();

  const navItems = [
    { name: '1. Code Editor', path: '/', icon: Code2 },
    { 
      name: '2. Test Suite', 
      path: '/tests', 
      icon: FlaskConical,
      badge: tests.length > 0 ? tests.length : null,
      badgeColor: 'bg-indigo-100 text-indigo-700 border border-indigo-200'
    },
    { 
      name: '3. Results', 
      path: '/results', 
      icon: CheckCircle2,
      badge: metrics ? `${metrics.passed}/${metrics.total}` : null,
      badgeColor: metrics && metrics.failed > 0 ? 'bg-rose-100 text-rose-700' : 'bg-emerald-100 text-emerald-700'
    },
    { name: '4. Dashboard', path: '/dashboard', icon: BarChart3 },
    { name: '5. Reports', path: '/reports', icon: FileText },
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200 bg-white/95 backdrop-blur-md shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Title */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-500 flex items-center justify-center shadow-md shadow-indigo-500/20">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-slate-900 tracking-tight text-base sm:text-lg">
                  AI Test Assistant
                </span>
                <span className="hidden md:inline-flex px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded-md bg-indigo-50 text-indigo-600 border border-indigo-200">
                  Micro Project
                </span>
              </div>
              <p className="text-[11px] text-slate-500 hidden sm:block">
                AI-Assisted Automated QA & Subprocess Runner
              </p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="flex items-center space-x-1 sm:space-x-1.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs sm:text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-indigo-50 text-indigo-700 font-semibold border border-indigo-200 shadow-xs'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                    }`
                  }
                >
                  <Icon className="w-4 h-4" />
                  <span className="hidden lg:inline">{item.name}</span>
                  {item.badge && (
                    <span className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono font-semibold ${item.badgeColor}`}>
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              );
            })}
          </nav>

          {/* Backend Status indicator */}
          <div className="hidden xl:flex items-center gap-2 text-xs text-slate-600 bg-slate-100 px-3 py-1.5 rounded-full border border-slate-200">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="font-medium">Stateless Python API</span>
          </div>
        </div>
      </div>
    </header>
  );
};
