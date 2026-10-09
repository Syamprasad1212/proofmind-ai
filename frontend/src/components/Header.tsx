import React from 'react';
import { ShieldCheck, Sparkles, Database } from 'lucide-react';
import type { HealthResponse } from '../types';

interface HeaderProps {
  health: HealthResponse | null;
  loadingHealth: boolean;
}

export const Header: React.FC<HeaderProps> = ({ health, loadingHealth }) => {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-700 to-sky-500 flex items-center justify-center text-white shadow-md shadow-indigo-100 ring-2 ring-indigo-50">
            <ShieldCheck className="w-6 h-6 stroke-[2.2]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-slate-900">
                ProofMind <span className="text-indigo-600">AI</span>
              </h1>
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200/60">
                Decision Engine
              </span>
            </div>
            <p className="text-xs text-slate-500 font-medium">
              Every decision needs evidence.
            </p>
          </div>
        </div>

        {/* Backend & AI status tags */}
        <div className="flex items-center gap-2.5 text-xs">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-100 border border-slate-200 text-slate-600">
            <Database className="w-3.5 h-3.5 text-slate-500" />
            <span>
              {loadingHealth ? 'Connecting...' : `${health?.document_count ?? 0} Docs (${health?.total_chunks ?? 0} Passages)`}
            </span>
          </div>

          <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg border ${
            health?.gemini_configured
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-amber-50 border-amber-200 text-amber-800'
          }`}>
            <Sparkles className="w-3.5 h-3.5" />
            <span className="font-medium">
              {health?.gemini_configured ? `Gemini Active (${health.gemini_model})` : 'Offline Verification Mode'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
