import React from 'react';
import { AlertTriangle, HelpCircle, CheckCircle2, FileText, Info } from 'lucide-react';
import type { EvidenceStatus } from '../types';

interface StatusBannerProps {
  status: EvidenceStatus;
  statusReasoning: string;
  answerSummary: string;
  documentScope?: string;
  detectedIntent?: string;
}

export const StatusBanner: React.FC<StatusBannerProps> = ({
  status,
  statusReasoning,
  answerSummary,
  documentScope,
  detectedIntent,
}) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'SUPPORTED':
        return {
          badgeText: 'Supported',
          badgeBg: 'bg-emerald-600 text-white',
          containerBg: 'bg-emerald-50/70 border-emerald-300',
          iconContainer: 'bg-emerald-100 text-emerald-700',
          icon: <CheckCircle2 className="w-5 h-5 text-emerald-600" />,
          title: 'Evidence Status: Supported & Grounded',
          desc: 'Claims and conclusions are verified by authenticated document passages.'
        };
      case 'NEEDS_VERIFICATION':
        return {
          badgeText: 'Needs Verification',
          badgeBg: 'bg-amber-600 text-white',
          containerBg: 'bg-amber-50/70 border-amber-300',
          iconContainer: 'bg-amber-100 text-amber-700',
          icon: <AlertTriangle className="w-5 h-5 text-amber-600" />,
          title: 'Evidence Status: Needs Verification',
          desc: 'Discrepancies, differing thresholds, or missing conditions detected across sources.'
        };
      case 'CLARIFICATION_NEEDED':
        return {
          badgeText: 'Clarification Needed',
          badgeBg: 'bg-sky-600 text-white',
          containerBg: 'bg-sky-50/70 border-sky-300',
          iconContainer: 'bg-sky-100 text-sky-700',
          icon: <HelpCircle className="w-5 h-5 text-sky-600" />,
          title: 'Evidence Status: Clarification Needed',
          desc: 'A specific document inquiry or clearer instruction is needed.'
        };
      case 'INSUFFICIENT_EVIDENCE':
      default:
        return {
          badgeText: 'Insufficient Evidence',
          badgeBg: 'bg-rose-600 text-white',
          containerBg: 'bg-rose-50/70 border-rose-300',
          iconContainer: 'bg-rose-100 text-rose-700',
          icon: <HelpCircle className="w-5 h-5 text-rose-600" />,
          title: 'Evidence Status: Insufficient Evidence',
          desc: 'No adequate document passages were found in the active index to answer this query.'
        };
    }
  };

  const config = getStatusConfig();

  return (
    <div className={`rounded-2xl border ${config.containerBg} p-5 shadow-xs flex flex-col gap-4`}>
      {/* Top Status Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200/60 pb-3.5">
        <div className="flex items-center gap-3">
          <div className={`p-2.5 rounded-xl ${config.iconContainer} shadow-xs`}>
            {config.icon}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-slate-900">
                {config.title}
              </h2>
            </div>
            <p className="text-xs text-slate-600 mt-0.5">
              {config.desc}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 self-start sm:self-center">
          {detectedIntent && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-lg text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
              {detectedIntent.replace(/_/g, ' ')}
            </span>
          )}
          {documentScope && (
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-lg text-xs font-medium bg-white border border-slate-200 text-slate-700">
              <FileText className="w-3 h-3 text-slate-400" />
              <span>{documentScope}</span>
            </span>
          )}
          <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold tracking-wide uppercase shadow-xs ${config.badgeBg}`}>
            {config.badgeText}
          </span>
        </div>
      </div>

      {/* Answer / Summary Card */}
      <div className="bg-white rounded-xl p-4.5 border border-slate-200/90 shadow-xs flex flex-col gap-2">
        <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-indigo-700">
          <Info className="w-3.5 h-3.5" />
          <span>Answer & Summary</span>
        </div>
        <div className="text-sm font-normal text-slate-800 leading-relaxed whitespace-pre-wrap">
          {answerSummary}
        </div>
      </div>

      {/* Concise Rationale if present */}
      {statusReasoning && (
        <div className="text-xs text-slate-600 bg-white/70 rounded-xl px-3.5 py-2.5 border border-slate-200/60 flex items-start gap-2">
          <span className="font-semibold text-slate-700 shrink-0">Rationale:</span>
          <span>{statusReasoning}</span>
        </div>
      )}
    </div>
  );
};
