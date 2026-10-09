import { useState, useEffect, useCallback, useRef } from 'react';
import { 
  fetchHealth, 
  fetchDocuments, 
  uploadDocuments, 
  deleteDocument, 
  loadDemoDocuments, 
  runAnalysis 
} from './api';
import type { 
  DocumentMetadata, 
  AnalysisResponse, 
  HealthResponse 
} from './types';
import { Header } from './components/Header';
import { DocumentManager } from './components/DocumentManager';
import { AnalysisInput } from './components/AnalysisInput';
import { StatusBanner } from './components/StatusBanner';
import { IndicatorsPanel } from './components/IndicatorsPanel';
import { ClaimsList } from './components/ClaimsList';
import { ContradictionMatrix } from './components/ContradictionMatrix';
import { EvidenceViewer } from './components/EvidenceViewer';
import { ActionableInsights } from './components/ActionableInsights';
import { AlertCircle, FileSearch } from 'lucide-react';

export function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loadingHealth, setLoadingHealth] = useState(true);
  
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [uploading, setUploading] = useState(false);
  const [loadingDemo, setLoadingDemo] = useState(false);
  
  const [query, setQuery] = useState('');
  const [enableWebResearch, setEnableWebResearch] = useState(false);
  const [selectedDocId, setSelectedDocId] = useState<string>('ALL');
  const [analyzing, setAnalyzing] = useState(false);
  const [isStale, setIsStale] = useState(false);
  
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null);
  const [selectedEvidenceId, setSelectedEvidenceId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  const loadInitialData = useCallback(async () => {
    try {
      setLoadingHealth(true);
      const [h, docs] = await Promise.all([
        fetchHealth().catch(() => null),
        fetchDocuments().catch(() => [])
      ]);
      setHealth(h);
      setDocuments(docs);
    } catch (err) {
      console.error('Failed to load initial data:', err);
    } finally {
      setLoadingHealth(false);
    }
  }, []);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  const handleUpload = async (files: File[]) => {
    setUploading(true);
    setErrorMessage(null);
    try {
      await uploadDocuments(files);
      const refreshedDocs = await fetchDocuments();
      setDocuments(refreshedDocs);
      const h = await fetchHealth();
      setHealth(h);
    } catch (err: any) {
      setErrorMessage(err.message || 'Document upload failed.');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: string) => {
    setErrorMessage(null);
    try {
      await deleteDocument(id);
      setDocuments(prev => prev.filter(d => d.id !== id));
      const h = await fetchHealth();
      setHealth(h);
      // Mark existing analysis as stale if it referenced deleted document
      if (analysisResult?.evidence_sources.some(s => s.document_id === id)) {
        setIsStale(true);
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to delete document.');
    }
  };

  const handleLoadDemo = async () => {
    setLoadingDemo(true);
    setErrorMessage(null);
    try {
      await loadDemoDocuments();
      const docs = await fetchDocuments();
      setDocuments(docs);
      const h = await fetchHealth();
      setHealth(h);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load demo pack.');
    } finally {
      setLoadingDemo(false);
    }
  };

  const handleCancelAnalysis = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setAnalyzing(false);
  };

  const handleAnalyze = async () => {
    if (!query.trim()) return;

    // Cancel any previous in-flight request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    // Immediately clear previous result or mark stale to avoid showing outdated answers
    setAnalysisResult(null);
    setIsStale(false);
    setAnalyzing(true);
    setErrorMessage(null);

    try {
      const docIds = selectedDocId !== 'ALL' ? [selectedDocId] : undefined;
      const res = await runAnalysis(query, enableWebResearch, docIds, controller.signal);
      setAnalysisResult(res);
      if (res.evidence_sources && res.evidence_sources.length > 0) {
        setSelectedEvidenceId(res.evidence_sources[0].evidence_id);
      }
    } catch (err: any) {
      if (err.name === 'AbortError') {
        // Request intentionally aborted
        return;
      }
      setErrorMessage(err.message || 'Analysis failed. Please check backend connection.');
    } finally {
      setAnalyzing(false);
      abortControllerRef.current = null;
    }
  };

  const handleSelectQuestion = (q: string) => {
    setQuery(q);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col">
      <Header health={health} loadingHealth={loadingHealth} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex-1 w-full space-y-6">
        {/* Error notification banner */}
        {errorMessage && (
          <div className="bg-rose-50 border border-rose-200 text-rose-800 rounded-xl p-3.5 flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-rose-600 hover:text-rose-900 font-bold ml-3 cursor-pointer"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Top Split: Document Manager & Question Input */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-5">
            <DocumentManager
              documents={documents}
              onUpload={handleUpload}
              onDelete={handleDelete}
              onLoadDemo={handleLoadDemo}
              uploading={uploading}
              loadingDemo={loadingDemo}
            />
          </div>

          <div className="lg:col-span-7">
            <AnalysisInput
              query={query}
              setQuery={setQuery}
              enableWebResearch={enableWebResearch}
              setEnableWebResearch={setEnableWebResearch}
              documents={documents}
              selectedDocId={selectedDocId}
              setSelectedDocId={setSelectedDocId}
              onAnalyze={handleAnalyze}
              onCancel={handleCancelAnalysis}
              loading={analyzing}
              disabled={documents.length === 0}
              hasGeminiKey={Boolean(health?.gemini_configured)}
            />
          </div>
        </div>

        {/* Stale warning banner if doc was deleted */}
        {isStale && analysisResult && (
          <div className="bg-amber-50 border border-amber-200 text-amber-800 rounded-xl p-3 text-xs flex items-center justify-between">
            <span>A document associated with this analysis was deleted. Re-run analysis for current results.</span>
            <button
              onClick={() => handleAnalyze()}
              className="px-2.5 py-1 bg-amber-600 text-white rounded-lg font-medium cursor-pointer"
            >
              Re-analyze
            </button>
          </div>
        )}

        {/* Empty state when no analysis yet */}
        {!analysisResult && !analyzing && (
          <div className="border border-dashed border-slate-200 rounded-2xl p-10 text-center bg-white/50 flex flex-col items-center justify-center gap-2">
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 mb-1">
              <FileSearch className="w-6 h-6" />
            </div>
            <h3 className="font-semibold text-sm text-slate-800">No Query Analyzed Yet</h3>
            <p className="text-xs text-slate-500 max-w-md">
              Upload your PDF documents and submit a question above. ProofMind AI will retrieve authentic passages, run deterministic citation verification, detect contradictions, and synthesize verified claims.
            </p>
          </div>
        )}

        {/* Loading placeholder state */}
        {analyzing && (
          <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center flex flex-col items-center justify-center gap-3">
            <div className="w-10 h-10 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin"></div>
            <p className="text-sm font-semibold text-slate-800">Retrieving passages and verifying evidence...</p>
            <p className="text-xs text-slate-500">Matching cosine similarity thresholds and checking citation integrity.</p>
          </div>
        )}

        {/* Bottom Section: Real Evidence Report */}
        {analysisResult && !analyzing && (
          <div className="space-y-6 pt-2 animate-in fade-in duration-300">
            {/* Status Banner with Answer Summary & Document Scope */}
            <StatusBanner
              status={analysisResult.evidence_status}
              statusReasoning={analysisResult.status_reasoning}
              answerSummary={analysisResult.answer_summary}
              documentScope={analysisResult.document_scope}
              detectedIntent={analysisResult.detected_intent}
            />

            {/* Contradictions Alert (shown only when discrepancies detected) */}
            {analysisResult.contradictions && analysisResult.contradictions.length > 0 && (
              <ContradictionMatrix contradictions={analysisResult.contradictions} />
            )}

            {/* Core Interactive Columns: Claims & Citations + Evidence Snippets */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
              <div className="lg:col-span-6">
                <ClaimsList
                  claims={analysisResult.claims}
                  evidenceSources={analysisResult.evidence_sources}
                  selectedEvidenceId={selectedEvidenceId}
                  onSelectEvidence={(id) => setSelectedEvidenceId(id)}
                />
              </div>

              {/* Evidence Inspector / Passage Viewer */}
              <div className="lg:col-span-6">
                <EvidenceViewer
                  evidenceSources={analysisResult.evidence_sources}
                  selectedEvidenceId={selectedEvidenceId}
                  onSelectEvidence={(id) => setSelectedEvidenceId(id)}
                />
              </div>
            </div>

            {/* Verification Integrity Indicators */}
            <IndicatorsPanel indicators={analysisResult.evidence_indicators} />

            {/* Missing Info, Follow-ups, and Limitations */}
            {((analysisResult.missing_information && analysisResult.missing_information.length > 0) ||
              (analysisResult.follow_up_questions && analysisResult.follow_up_questions.length > 0)) && (
              <ActionableInsights
                missingInfo={analysisResult.missing_information}
                followUpQuestions={analysisResult.follow_up_questions}
                limitations={analysisResult.limitations}
                onSelectQuestion={handleSelectQuestion}
              />
            )}

          </div>
        )}
      </main>

      <footer className="bg-white border-t border-slate-200 py-4 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-800">ProofMind AI</span>
            <span>—</span>
            <span>Evidence-Aware AI Decision Engine</span>
          </div>
          <div>
            <span>Official Google GenAI SDK • PyMuPDF • ChromaDB (all-MiniLM-L6-v2) • FastAPI • React</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
