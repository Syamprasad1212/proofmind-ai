import React, { useState } from 'react';
import { Gauge, CheckCircle2, FileCheck, ShieldAlert, Sparkles, BookOpen, ChevronDown, ChevronUp } from 'lucide-react';
import type { EvidenceIndicators } from '../types';

interface IndicatorsPanelProps {
  indicators: EvidenceIndicators;
}

export const IndicatorsPanel: React.FC<IndicatorsPanelProps> = ({ indicators }) => {
  const [expanded, setExpanded] = useState(false);

  const cards = [
    {
      title: 'Evidence Coverage',
      value: `${Math.round(indicators.evidence_coverage * 100)}%`,
      pct: indicators.evidence_coverage,
      desc: indicators.indicator_explanations?.evidence_coverage || 'Query premises covered by retrieved evidence.',
      icon: <BookOpen className="w-3.5 h-3.5 text-indigo-600" />,
      barColor: 'bg-indigo-600'
    },
    {
      title: 'Citation Validity',
      value: `${Math.round(indicators.citation_validity * 100)}%`,
      pct: indicators.citation_validity,
      desc: indicators.indicator_explanations?.citation_validity || 'Citations verified against authentic page numbers.',
      icon: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />,
      barColor: 'bg-emerald-600'
    },
    {
      title: 'Claim Support',
      value: `${Math.round(indicators.claim_support * 100)}%`,
      pct: indicators.claim_support,
      desc: indicators.indicator_explanations?.claim_support || 'Claims substantiated by cited passages.',
      icon: <FileCheck className="w-3.5 h-3.5 text-sky-600" />,
      barColor: 'bg-sky-600'
    },
    {
      title: 'Source Quality',
      value: `${Math.round(indicators.source_quality * 100)}%`,
      pct: indicators.source_quality,
      desc: indicators.indicator_explanations?.source_quality || 'Structured institutional document integrity.',
      icon: <Sparkles className="w-3.5 h-3.5 text-violet-600" />,
      barColor: 'bg-violet-600'
    },
    {
      title: 'Conflicts',
      value: `${indicators.unresolved_conflicts_count}`,
      pct: indicators.unresolved_conflicts_count === 0 ? 1 : 0.2,
      desc: indicators.indicator_explanations?.unresolved_conflicts || 'Material contradictions across sources.',
      icon: <ShieldAlert className={`w-3.5 h-3.5 ${indicators.unresolved_conflicts_count > 0 ? 'text-amber-600' : 'text-emerald-600'}`} />,
      barColor: indicators.unresolved_conflicts_count > 0 ? 'bg-amber-500' : 'bg-emerald-500'
    },
    {
      title: 'Completeness',
      value: `${Math.round(indicators.context_completeness * 100)}%`,
      pct: indicators.context_completeness,
      desc: indicators.indicator_explanations?.context_completeness || 'Key decision parameters and riders established.',
      icon: <Gauge className="w-3.5 h-3.5 text-teal-600" />,
      barColor: 'bg-teal-600'
    }
  ];

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs flex flex-col gap-3">
      <div 
        className="flex items-center justify-between cursor-pointer select-none"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-indigo-50 text-indigo-600">
            <Gauge className="w-4 h-4" />
          </div>
          <h3 className="font-semibold text-slate-900 text-xs sm:text-sm">
            Verification Metrics
          </h3>
          <span className="text-xs text-slate-500 hidden sm:inline">
            • Coverage: {Math.round(indicators.evidence_coverage * 100)}% • Validity: {Math.round(indicators.citation_validity * 100)}% • Support: {Math.round(indicators.claim_support * 100)}%
          </span>
        </div>

        <button
          type="button"
          className="text-xs text-slate-500 hover:text-indigo-600 flex items-center gap-1 font-medium transition-colors"
        >
          <span>{expanded ? 'Hide Details' : 'View Breakdown'}</span>
          {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      {expanded && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5 pt-2 border-t border-slate-100">
          {cards.map((card, idx) => (
            <div
              key={idx}
              className="p-3 rounded-xl border border-slate-200/80 bg-slate-50/50 flex flex-col justify-between gap-1.5 hover:border-slate-300 transition-all"
              title={card.desc}
            >
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold text-slate-600 truncate">
                  {card.title}
                </span>
                {card.icon}
              </div>

              <div>
                <div className="text-base font-bold text-slate-900">
                  {card.value}
                </div>
                <div className="w-full h-1 bg-slate-200 rounded-full mt-1 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${card.barColor}`}
                    style={{ width: `${Math.min(100, Math.max(8, card.pct * 100))}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
