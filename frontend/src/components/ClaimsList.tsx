import React from 'react';
import { FileCheck, FileText, Globe, ExternalLink, Link2 } from 'lucide-react';
import type { Claim, EvidenceSource } from '../types';

interface ClaimsListProps {
  claims: Claim[];
  evidenceSources: EvidenceSource[];
  selectedEvidenceId: string | null;
  onSelectEvidence: (evidenceId: string) => void;
}

export const ClaimsList: React.FC<ClaimsListProps> = ({
  claims,
  evidenceSources,
  selectedEvidenceId,
  onSelectEvidence,
}) => {
  const getEvidenceDetails = (evdId: string) => {
    return evidenceSources.find(e => e.evidence_id === evdId);
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex flex-col gap-4">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-indigo-50 text-indigo-600">
            <FileCheck className="w-4 h-4" />
          </div>
          <h3 className="font-semibold text-slate-900 text-sm">
            Claims & Citations
          </h3>
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
            {claims.length}
          </span>
        </div>
        <span className="text-[11px] text-slate-500 font-medium">
          Click citations to inspect source snippet
        </span>
      </div>

      {claims.length === 0 ? (
        <div className="text-center py-8 text-xs text-slate-500">
          No individual verified claims generated for this query.
        </div>
      ) : (
        <div className="space-y-3">
          {claims.map((claim, idx) => (
            <div
              key={claim.claim_id || idx}
              className="p-3.5 rounded-xl border border-slate-200/90 bg-slate-50/40 hover:bg-white hover:border-slate-300 transition-all flex flex-col gap-2.5"
            >
              {/* Claim Statement */}
              <p className="text-xs font-medium text-slate-800 leading-relaxed">
                {claim.claim_text}
              </p>

              {/* Clickable Citations */}
              {claim.citations && claim.citations.length > 0 && (
                <div className="flex flex-wrap items-center gap-1.5 pt-1 border-t border-slate-100">
                  <span className="text-[10px] font-semibold text-slate-500 flex items-center gap-1 mr-0.5">
                    <Link2 className="w-3 h-3 text-slate-400" />
                    Sources:
                  </span>
                  {claim.citations.map((cit, citIdx) => {
                    const evd = getEvidenceDetails(cit.evidence_id);
                    const isSelected = selectedEvidenceId === cit.evidence_id;

                    const docName = evd?.filename || (evd?.web_title ? evd.web_title : 'Source');
                    const pageText = evd?.source_type === 'document' && evd?.page_number != null
                      ? `Page ${evd.page_number}`
                      : null;

                    return (
                      <button
                        key={citIdx}
                        type="button"
                        onClick={() => onSelectEvidence(cit.evidence_id)}
                        className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all cursor-pointer border ${
                          isSelected
                            ? 'bg-indigo-600 text-white border-indigo-700 shadow-xs'
                            : 'bg-white text-slate-700 border-slate-200 hover:border-indigo-300 hover:text-indigo-600 hover:bg-indigo-50/50'
                        }`}
                        title={cit.rationale || 'Click to view evidence snippet'}
                      >
                        {evd?.source_type === 'document' ? (
                          <FileText className="w-3 h-3 shrink-0" />
                        ) : (
                          <Globe className="w-3 h-3 shrink-0" />
                        )}
                        <span className="max-w-[180px] truncate">{docName}</span>
                        {pageText && (
                          <span className={`text-[10px] font-normal ${isSelected ? 'text-indigo-100' : 'text-slate-500'}`}>
                            • {pageText}
                          </span>
                        )}
                        <ExternalLink className="w-2.5 h-2.5 ml-0.5 opacity-60" />
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
