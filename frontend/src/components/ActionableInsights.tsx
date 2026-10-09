import React from 'react';
import { HelpCircle, AlertCircle, ShieldAlert, ArrowRight, CornerDownRight } from 'lucide-react';

interface ActionableInsightsProps {
  missingInfo: string[];
  followUpQuestions: string[];
  limitations: string[];
  onSelectQuestion: (question: string) => void;
}

export const ActionableInsights: React.FC<ActionableInsightsProps> = ({
  missingInfo,
  followUpQuestions,
  limitations,
  onSelectQuestion,
}) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* Missing Information */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex flex-col gap-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-amber-50 text-amber-600">
            <AlertCircle className="w-4 h-4" />
          </div>
          <h3 className="font-semibold text-slate-900 text-sm">
            Missing Information & Unresolved Context
          </h3>
        </div>

        {missingInfo && missingInfo.length > 0 ? (
          <ul className="space-y-2 text-xs text-slate-700">
            {missingInfo.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2 p-2 rounded-lg bg-slate-50 border border-slate-100">
                <CornerDownRight className="w-3.5 h-3.5 text-amber-600 mt-0.5 shrink-0" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-slate-500 italic">
            No missing contextual parameters detected. All requisite conditions are established in evidence.
          </p>
        )}
      </div>

      {/* Smart Follow-Up Questions */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex flex-col gap-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-indigo-50 text-indigo-600">
            <HelpCircle className="w-4 h-4" />
          </div>
          <h3 className="font-semibold text-slate-900 text-sm">
            Targeted Follow-Up Inquiries
          </h3>
        </div>

        {followUpQuestions && followUpQuestions.length > 0 ? (
          <div className="space-y-2">
            {followUpQuestions.map((q, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => onSelectQuestion(q)}
                className="w-full text-left p-2.5 rounded-xl border border-slate-200/80 bg-slate-50/50 hover:bg-indigo-50 hover:border-indigo-200 transition-all text-xs font-medium text-slate-800 hover:text-indigo-700 flex items-center justify-between gap-2 cursor-pointer group"
              >
                <span>{q}</span>
                <ArrowRight className="w-3.5 h-3.5 opacity-40 group-hover:opacity-100 transition-opacity shrink-0" />
              </button>
            ))}
          </div>
        ) : (
          <p className="text-xs text-slate-500 italic">
            No follow-up questions required.
          </p>
        )}
      </div>

      {/* Decision Governance & Limitations Banner */}
      <div className="md:col-span-2 bg-slate-100/70 rounded-xl p-3.5 border border-slate-200 text-slate-600 text-[11px] flex items-start gap-2.5">
        <ShieldAlert className="w-4 h-4 text-slate-500 mt-0.5 shrink-0" />
        <div>
          <span className="font-bold text-slate-800">Governance & Decision Support Notice: </span>
          <span>
            ProofMind AI is designed strictly as an evidence verification and decision-support engine. It does not replace administrative authority, legal counsel, or official institutional judgment. 
            {limitations && limitations.length > 0 && ` Active boundary: ${limitations.join(' ')}`}
          </span>
        </div>
      </div>
    </div>
  );
};
