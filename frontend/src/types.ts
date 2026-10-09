export type EvidenceStatus = 'SUPPORTED' | 'NEEDS_VERIFICATION' | 'INSUFFICIENT_EVIDENCE' | 'CLARIFICATION_NEEDED';
export type DocumentStatus = 'PROCESSING' | 'INDEXED' | 'ERROR';

export interface DocumentMetadata {
  id: string;
  filename: string;
  file_size_bytes: number;
  page_count: number;
  chunk_count: number;
  upload_date: string;
  status: DocumentStatus;
  sha256_hash: string;
  error_message?: string | null;
}

export interface DocumentDetail extends DocumentMetadata {
  chunks: Array<{
    id: string;
    document_id: string;
    filename: string;
    page_number: number;
    chunk_index: number;
    text: string;
    token_count?: number;
  }>;
}

export interface EvidenceSource {
  evidence_id: string;
  source_type: 'document' | 'web';
  document_id?: string;
  filename?: string;
  page_number?: number;
  web_title?: string;
  web_url?: string;
  passage: string;
  relevance_score?: number;
  publication_date?: string;
  retrieval_date: string;
}

export interface ClaimCitation {
  evidence_id: string;
  relationship: 'supports' | 'contradicts' | 'mentions' | 'insufficient';
  rationale?: string;
  verified: boolean;
  verification_issue?: string | null;
}

export interface Claim {
  claim_id: string;
  claim_text: string;
  importance: 'critical' | 'supporting' | 'contextual';
  verification_status: 'verified_supported' | 'verified_contradicted' | 'unsupported' | 'invalid_citation';
  citations: ClaimCitation[];
  explanation?: string;
}

export interface Contradiction {
  conflict_id: string;
  claim_a: string;
  source_a: string;
  passage_a: string;
  claim_b: string;
  source_b: string;
  passage_b: string;
  conflict_nature: string;
  scope_differences?: string;
  is_unresolved: boolean;
}

export interface EvidenceIndicators {
  evidence_coverage: number;
  citation_validity: number;
  claim_support: number;
  source_quality: number;
  unresolved_conflicts_count: number;
  context_completeness: number;
  indicator_explanations: Record<string, string>;
}

export interface AnalysisResponse {
  analysis_id: string;
  query: string;
  document_scope?: string;
  detected_intent?: string;
  answer_summary: string;
  evidence_status: EvidenceStatus;
  status_reasoning: string;
  claims: Claim[];
  evidence_sources: EvidenceSource[];
  contradictions: Contradiction[];
  evidence_indicators: EvidenceIndicators;
  limitations: string[];
  missing_information: string[];
  follow_up_questions: string[];
  retrieval_status: {
    retrieval_timestamp: string;
    document_passages_retrieved: number;
    web_research_requested: boolean;
    web_research_status: string;
    model_used: string;
  };
  timestamp: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  gemini_configured: boolean;
  gemini_model: string;
  embedding_provider?: string;
  document_count: number;
  total_chunks: number;
}
