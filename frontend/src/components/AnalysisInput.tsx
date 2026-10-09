import { Search, Globe, ArrowRight, Loader2, XCircle, FileText } from 'lucide-react';
import type { DocumentMetadata } from '../types';

interface AnalysisInputProps {
  query: string;
  setQuery: (q: string) => void;
  enableWebResearch: boolean;
  setEnableWebResearch: (val: boolean) => void;
  documents: DocumentMetadata[];
  selectedDocId: string;
  setSelectedDocId: (id: string) => void;
  onAnalyze: () => Promise<void>;
  onCancel?: () => void;
  loading: boolean;
  disabled: boolean;
  hasGeminiKey: boolean;
}

export const AnalysisInput: React.FC<AnalysisInputProps> = ({
  query,
  setQuery,
  enableWebResearch,
  setEnableWebResearch,
  documents,
  selectedDocId,
  setSelectedDocId,
  onAnalyze,
  onCancel,
  loading,
  disabled,
  hasGeminiKey,
}) => {
  const quickDemos = [
    {
      title: '🎯 Resume Skills Analysis',
      query: 'What are my skills?',
      badge: 'Auto-selects Resume or Target Doc'
    },
    {
      title: '⚡ Policy Conflict Demo (Alex Rivera)',
      query: 'Is Alex Rivera eligible for scholarship renewal based on attendance and academic standing?',
      badge: 'Fictional Demo Scenario'
    },
    {
      title: '✨ Verified Supported Demo (Jordan Lee)',
      query: 'Is Jordan Lee eligible for the Standard Merit Scholarship renewal based on attendance?',
      badge: 'Fictional Demo Scenario'
    }
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || loading || disabled) return;
    onAnalyze();
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-indigo-50 text-indigo-600">
            <Search className="w-4 h-4" />
          </div>
          <h2 className="font-semibold text-slate-900 text-sm">
            Evidence-Aware Question & Decision Inquiry
          </h2>
        </div>

        {/* Document Scope Selector */}
        <div className="flex items-center gap-2">
          <FileText className="w-3.5 h-3.5 text-slate-500" />
          <span className="text-xs text-slate-600 font-medium">Scope:</span>
          <select
            value={selectedDocId}
            onChange={(e) => setSelectedDocId(e.target.value)}
            disabled={loading || documents.length === 0}
            className="text-xs rounded-lg border border-slate-200 bg-slate-50 py-1 px-2.5 text-slate-800 font-medium focus:outline-none focus:ring-1 focus:ring-indigo-500 cursor-pointer max-w-[220px] truncate"
          >
            <option value="ALL">All Indexed Documents ({documents.length})</option>
            {documents.map((doc) => (
              <option key={doc.id} value={doc.id}>
                {doc.filename}
              </option>
            ))}
          </select>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <div className="relative">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask any substantive question about your documents (e.g. 'What are my skills?' or 'What are the required attendance policies?')..."
            rows={3}
            className="w-full rounded-xl border border-slate-200 p-3.5 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 resize-none transition-all"
            disabled={loading}
          />
        </div>

        {/* Source selection toggles & Analyze Button */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-1">
          <div className="flex items-center gap-4">
            <label 
              className={`flex items-center gap-2 text-xs font-medium ${
                hasGeminiKey ? 'text-slate-700 cursor-pointer' : 'text-slate-400 cursor-not-allowed'
              } select-none`}
              title={hasGeminiKey ? 'Search internet facts via Gemini Google Search tool' : 'Requires GEMINI_API_KEY in backend .env to enable web grounding'}
            >
              <input
                type="checkbox"
                checked={enableWebResearch && hasGeminiKey}
                disabled={!hasGeminiKey}
                onChange={(e) => setEnableWebResearch(e.target.checked)}
                className="w-4 h-4 text-indigo-600 rounded border-slate-300 focus:ring-indigo-500 disabled:opacity-50"
              />
              <span className="flex items-center gap-1.5">
                <Globe className={`w-3.5 h-3.5 ${hasGeminiKey ? 'text-sky-600' : 'text-slate-400'}`} />
                <span>Include Gemini Web Grounding Research</span>
                {!hasGeminiKey && (
                  <span className="text-[10px] text-amber-600 bg-amber-50 px-1.5 py-0.2 rounded border border-amber-200">
                    Offline (Key Needed)
                  </span>
                )}
              </span>
            </label>
          </div>

          <div className="flex items-center gap-2">
            {loading && onCancel && (
              <button
                type="button"
                onClick={onCancel}
                className="inline-flex items-center justify-center gap-1.5 px-3 py-2.5 rounded-xl border border-slate-200 hover:bg-slate-100 text-slate-600 font-medium text-xs transition-colors cursor-pointer"
              >
                <XCircle className="w-3.5 h-3.5 text-rose-500" />
                <span>Cancel</span>
              </button>
            )}

            <button
              type="submit"
              disabled={!query.trim() || loading || disabled}
              className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 text-white font-medium text-xs shadow-md shadow-indigo-100 transition-all disabled:opacity-50 disabled:pointer-events-none cursor-pointer"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Retrieving & Verifying Evidence...</span>
                </>
              ) : (
                <>
                  <span>Analyze & Verify Evidence</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Preset demo queries for quick 1-click evaluation */}
      <div className="pt-2 border-t border-slate-100">
        <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2">
          Interactive Test Scenarios
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
          {quickDemos.map((demo, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => setQuery(demo.query)}
              className="text-left p-2.5 rounded-xl border border-slate-200/80 bg-slate-50/50 hover:bg-indigo-50/50 hover:border-indigo-200 transition-all cursor-pointer group"
            >
              <div className="flex items-center justify-between gap-1 mb-1">
                <span className="font-semibold text-xs text-slate-800 group-hover:text-indigo-700">
                  {demo.title}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 line-clamp-2 leading-relaxed">
                {demo.query}
              </p>
              <span className="inline-block mt-1.5 text-[10px] font-medium px-1.5 py-0.5 rounded bg-white border border-slate-200 text-slate-600">
                {demo.badge}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
