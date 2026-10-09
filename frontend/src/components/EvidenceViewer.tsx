import React, { useState, useEffect, useRef } from 'react';
import { BookOpen, Globe, FileText, ExternalLink } from 'lucide-react';
import type { EvidenceSource } from '../types';

interface EvidenceViewerProps {
  evidenceSources: EvidenceSource[];
  selectedEvidenceId: string | null;
  onSelectEvidence: (id: string) => void;
}

export const EvidenceViewer: React.FC<EvidenceViewerProps> = ({
  evidenceSources,
  selectedEvidenceId,
  onSelectEvidence,
}) => {
  const [activeTab, setActiveTab] = useState<'all' | 'document' | 'web'>('all');
  const selectedSnippetRef = useRef<HTMLDivElement | null>(null);

  const filtered = evidenceSources.filter(e => {
    if (activeTab === 'all') return true;
    return e.source_type === activeTab;
  });

  const docCount = evidenceSources.filter(e => e.source_type === 'document').length;
  const webCount = evidenceSources.filter(e => e.source_type === 'web').length;

  useEffect(() => {
    if (selectedEvidenceId && selectedSnippetRef.current) {
      selectedSnippetRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [selectedEvidenceId]);

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex flex-col gap-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-indigo-50 text-indigo-600">
            <BookOpen className="w-4 h-4" />
          </div>
          <h3 className="font-semibold text-slate-900 text-sm">
            Evidence Snippets
          </h3>
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
            {evidenceSources.length}
          </span>
        </div>

        {/* Tab Filters */}
        <div className="flex items-center gap-1 bg-slate-100 p-0.5 rounded-lg text-xs self-start sm:self-auto">
          <button
            type="button"
            onClick={() => setActiveTab('all')}
            className={`px-2.5 py-1 rounded-md font-medium transition-colors cursor-pointer ${
              activeTab === 'all' ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            All ({evidenceSources.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('document')}
            className={`px-2.5 py-1 rounded-md font-medium transition-colors cursor-pointer ${
              activeTab === 'document' ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            PDF Documents ({docCount})
          </button>
          {webCount > 0 && (
            <button
              type="button"
              onClick={() => setActiveTab('web')}
              className={`px-2.5 py-1 rounded-md font-medium transition-colors cursor-pointer ${
                activeTab === 'web' ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Web Sources ({webCount})
            </button>
          )}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="text-center py-8 text-xs text-slate-500">
          No evidence snippets retrieved for this view.
        </div>
      ) : (
        <div className="space-y-3 max-h-[480px] overflow-y-auto pr-1">
          {filtered.map((evd) => {
            const isSelected = selectedEvidenceId === evd.evidence_id;

            return (
              <div
                key={evd.evidence_id}
                ref={isSelected ? selectedSnippetRef : null}
                onClick={() => onSelectEvidence(evd.evidence_id)}
                className={`p-4 rounded-xl border transition-all cursor-pointer flex flex-col gap-2.5 ${
                  isSelected
                    ? 'border-indigo-500 bg-indigo-50/40 ring-2 ring-indigo-500/20 shadow-xs'
                    : 'border-slate-200 bg-slate-50/30 hover:border-slate-300 hover:bg-slate-50/70'
                }`}
              >
                {/* Source & Page Header */}
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    {evd.source_type === 'document' ? (
                      <div className="flex items-center gap-1.5 min-w-0">
                        <FileText className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
                        <span className="text-xs font-semibold text-slate-800 truncate">
                          {evd.filename}
                        </span>
                        {evd.page_number != null && (
                          <span className="text-[11px] font-medium text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200/60 shrink-0">
                            Page {evd.page_number}
                          </span>
                        )}
                      </div>
                    ) : (
                      <div className="flex items-center gap-1.5 min-w-0">
                        <Globe className="w-3.5 h-3.5 text-sky-600 shrink-0" />
                        <span className="text-xs font-semibold text-slate-800 truncate">
                          {evd.web_title || 'Web Result'}
                        </span>
                      </div>
                    )}
                  </div>

                  {evd.web_url && (
                    <a
                      href={evd.web_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-indigo-600 hover:underline flex items-center gap-0.5 text-[11px] font-medium shrink-0"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <span>Visit URL</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>

                {/* Exact Passage Snippet */}
                <div className="text-xs text-slate-700 bg-white p-3.5 rounded-lg border border-slate-200/80 leading-relaxed shadow-xs relative pl-4 border-l-3 border-l-indigo-400">
                  <p className="italic text-slate-700 font-normal">
                    &ldquo;{evd.passage}&rdquo;
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
