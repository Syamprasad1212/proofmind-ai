import React from 'react';
import { AlertTriangle, CheckCircle2 } from 'lucide-react';
import type { Contradiction } from '../types';

interface ContradictionMatrixProps {
  contradictions: Contradiction[];
}

export const ContradictionMatrix: React.FC<ContradictionMatrixProps> = ({ contradictions }) => {
  if (!contradictions || contradictions.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-emerald-50 text-emerald-600">
            <CheckCircle2 className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-900 text-sm">
              Side-by-Side Contradiction Comparison
            </h3>
            <p className="text-xs text-slate-500">
              No material policy or numerical contradictions detected across retrieved evidence.
            </p>
          </div>
        </div>
        <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
          0 Discrepancies
        </span>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl border border-amber-200 p-5 shadow-xs flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-amber-50 text-amber-600">
            <AlertTriangle className="w-4 h-4" />
          </div>
          <h3 className="font-semibold text-slate-900 text-sm">
            Side-by-Side Contradiction & Discrepancy Matrix
          </h3>
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800">
            {contradictions.length} Conflict{contradictions.length === 1 ? '' : 's'}
          </span>
        </div>
        <span className="text-[11px] font-medium text-amber-700">
          Unresolved Discrepancies Requiring Clarification
        </span>
      </div>

      <div className="space-y-4">
        {contradictions.map((conflict, idx) => (
          <div
            key={conflict.conflict_id || idx}
            className="rounded-xl border border-amber-200/80 bg-amber-50/20 p-4 flex flex-col gap-3"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-amber-800 bg-amber-100 px-2 py-0.5 rounded border border-amber-200">
                {conflict.conflict_id || `CONFLICT-${idx + 1}`}
              </span>
              <span className="text-[11px] font-semibold text-amber-800 bg-amber-100/70 px-2 py-0.5 rounded-full">
                {conflict.is_unresolved ? 'Unresolved Material Conflict' : 'Resolved Condition'}
              </span>
            </div>

            {/* Side-by-side comparison grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {/* Source A */}
              <div className="bg-white rounded-xl p-3.5 border border-slate-200 shadow-xs flex flex-col gap-1.5">
                <div className="flex items-center justify-between text-xs font-semibold text-indigo-700 border-b border-slate-100 pb-1.5">
                  <span>Source A Provision</span>
                  <span className="text-slate-500 font-normal">{conflict.source_a}</span>
                </div>
                <p className="text-xs font-semibold text-slate-900">
                  {conflict.claim_a}
                </p>
                <div className="text-[11px] text-slate-600 bg-slate-50 p-2 rounded-lg border border-slate-100 italic">
                  &ldquo;{conflict.passage_a}&rdquo;
                </div>
              </div>

              {/* Source B */}
              <div className="bg-white rounded-xl p-3.5 border border-slate-200 shadow-xs flex flex-col gap-1.5">
                <div className="flex items-center justify-between text-xs font-semibold text-purple-700 border-b border-slate-100 pb-1.5">
                  <span>Source B Provision</span>
                  <span className="text-slate-500 font-normal">{conflict.source_b}</span>
                </div>
                <p className="text-xs font-semibold text-slate-900">
                  {conflict.claim_b}
                </p>
                <div className="text-[11px] text-slate-600 bg-slate-50 p-2 rounded-lg border border-slate-100 italic">
                  &ldquo;{conflict.passage_b}&rdquo;
                </div>
              </div>
            </div>

            {/* Why they conflict & Scope differences */}
            <div className="bg-white rounded-xl p-3 border border-amber-200/60 text-xs text-slate-700 space-y-1">
              <div>
                <span className="font-semibold text-slate-900">Discrepancy Nature: </span>
                <span>{conflict.conflict_nature}</span>
              </div>
              {conflict.scope_differences && (
                <div>
                  <span className="font-semibold text-slate-900">Scope & Condition Differences: </span>
                  <span>{conflict.scope_differences}</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
