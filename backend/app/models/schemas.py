from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class EvidenceStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    NEEDS_VERIFICATION = "NEEDS_VERIFICATION"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CLARIFICATION_NEEDED = "CLARIFICATION_NEEDED"

class DocumentStatus(str, Enum):
    PROCESSING = "PROCESSING"
    INDEXED = "INDEXED"
    ERROR = "ERROR"

class DocumentMetadata(BaseModel):
    id: str
    filename: str
    file_size_bytes: int
    page_count: int
    chunk_count: int
    upload_date: str
    status: DocumentStatus
    sha256_hash: str
    error_message: Optional[str] = None

class DocumentDetail(BaseModel):
    id: str
    filename: str
    file_size_bytes: int
    page_count: int
    chunk_count: int
    upload_date: str
    status: DocumentStatus
    sha256_hash: str
    error_message: Optional[str] = None
    chunks: List[Dict[str, Any]] = Field(default_factory=list)

class Chunk(BaseModel):
    id: str
    document_id: str
    filename: str
    page_number: int
    chunk_index: int
    text: str
    token_count: Optional[int] = None

class EvidenceSource(BaseModel):
    evidence_id: str
    source_type: str = Field(description="'document' or 'web'")
    document_id: Optional[str] = None
    filename: Optional[str] = None
    page_number: Optional[int] = None
    web_title: Optional[str] = None
    web_url: Optional[str] = None
    passage: str
    relevance_score: Optional[float] = None
    publication_date: Optional[str] = None
    retrieval_date: str

class ClaimCitation(BaseModel):
    evidence_id: str
    relationship: str = Field(default="supports", description="'supports', 'contradicts', 'mentions', or 'insufficient'")
    rationale: Optional[str] = None
    verified: bool = True
    verification_issue: Optional[str] = None

class Claim(BaseModel):
    claim_id: str
    claim_text: str
    importance: str = Field(default="critical", description="'critical', 'supporting', 'contextual'")
    verification_status: str = Field(default="verified_supported", description="'verified_supported', 'partially_supported', 'verified_contradicted', 'unsupported', 'invalid_citation'")
    citations: List[ClaimCitation] = Field(default_factory=list)
    explanation: Optional[str] = None

class Contradiction(BaseModel):
    conflict_id: str
    claim_a: str
    source_a: str
    passage_a: str
    claim_b: str
    source_b: str
    passage_b: str
    conflict_nature: str
    scope_differences: Optional[str] = None
    is_unresolved: bool = True

class EvidenceIndicators(BaseModel):
    evidence_coverage: float = Field(ge=0.0, le=1.0, description="Portion of required question premises covered by evidence")
    citation_validity: float = Field(ge=0.0, le=1.0, description="Percentage of citations that accurately match indexed sources")
    claim_support: float = Field(ge=0.0, le=1.0, description="Ratio of claims solidly grounded in evidence passages")
    source_quality: float = Field(ge=0.0, le=1.0, description="Integrity and specificity of source documents/passages")
    unresolved_conflicts_count: int = Field(ge=0, description="Count of unresolved material disagreements")
    context_completeness: float = Field(ge=0.0, le=1.0, description="Evaluation of whether key decision conditions are established")
    indicator_explanations: Dict[str, str] = Field(default_factory=dict)

class AnalysisRequest(BaseModel):
    query: str
    enable_web_research: bool = False
    document_ids: Optional[List[str]] = None

class AnalysisResponse(BaseModel):
    analysis_id: str
    query: str
    document_scope: str = Field(default="All Documents", description="Scope of documents consulted: 'All Documents' or comma-separated document names")
    detected_intent: Optional[str] = Field(default=None, description="Classified intent of the user query")
    answer_summary: str
    evidence_status: EvidenceStatus
    status_reasoning: str
    claims: List[Claim]
    evidence_sources: List[EvidenceSource]
    contradictions: List[Contradiction]
    evidence_indicators: EvidenceIndicators
    limitations: List[str]
    missing_information: List[str]
    follow_up_questions: List[str]
    retrieval_status: Dict[str, Any]
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    version: str
    gemini_configured: bool
    gemini_model: str
    embedding_provider: str
    document_count: int
    total_chunks: int

class AnalysisRecord(BaseModel):
    id: str
    query: str
    evidence_status: str
    created_at: str
    response: Dict[str, Any]
