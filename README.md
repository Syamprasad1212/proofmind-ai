# ProofMind AI — Evidence-Aware AI Decision Engine

> **Tagline:** *Every decision needs evidence.*

ProofMind AI is an evidence-aware verification system and decision-support engine. Rather than treating an LLM as an unquestioned authority or using hardcoded canned responses, ProofMind AI extracts page-level document passages, executes semantic vector retrieval with cosine similarity scoring, conducts deterministic citation integrity verification, identifies material policy contradictions, computes transparent evidence indicators, and classifies conclusions into unambiguous evidence statuses.

---

## Table of Contents

1. [Product Overview](#product-overview)
2. [Architecture & System Flow](#architecture--system-flow)
3. [Dynamic Retrieval & Local Semantic Embeddings](#dynamic-retrieval--local-semantic-embeddings)
4. [Evidence Verification Engine](#evidence-verification-engine)
5. [Project Structure](#project-structure)
6. [Installation and Quickstart](#installation-and-quickstart)
7. [API Documentation](#api-documentation)
8. [Automated Testing](#automated-testing)
9. [Acceptance Verification Scenarios](#acceptance-verification-scenarios)
10. [Governance & Limitations](#governance--limitations)

---

## 1. Product Overview

In high-stakes domains (legal compliance, scholarship adjudication, insurance policies, academic grants), ungrounded chatbots hallucinate facts and invent confidence percentages. ProofMind AI ensures strict evidence grounding:

- **Page-Level Grounding:** Extracts text page-by-page with PyMuPDF, preserving document filenames, page numbers, and stable chunk identifiers.
- **Genuine Semantic Retrieval:** Uses an ONNX-runtime `all-MiniLM-L6-v2` 384-dimensional dense semantic embedding model (with a local fast hashing fallback) to retrieve passages using cosine distance and a configurable similarity threshold (`SIMILARITY_THRESHOLD=0.60`).
- **Citation Integrity Verification:** Verifies every citation against stored passages, distinguishing whether a citation exists, is relevant, and actually supports the claim.
- **Side-by-Side Contradiction Matrix:** Compares conflicting rules, numerical thresholds (e.g., 75% vs. 80%), and conditional scopes across multiple documents.
- **Three Primary Evidence Statuses:**
  - `SUPPORTED`: Critical claims verified with citations and zero unresolved material contradictions.
  - `NEEDS_VERIFICATION`: Material disagreements, differing conditions, or missing contextual parameters detected.
  - `INSUFFICIENT_EVIDENCE`: Available repository cannot substantiate an answer or query is non-substantive.
- **Transparent Indicators:** Replaces arbitrary confidence percentages with 6 documented, auditable metrics (Evidence Coverage, Citation Validity, Claim Support, Source Quality, Unresolved Conflicts, Context Completeness).
- **Honest Web Research Handling:** Only enables web research when `GEMINI_API_KEY` is provided; clearly communicates availability status and keeps web sources isolated with explicit source URLs.

---

## 2. Architecture & System Flow

```
                     ┌──────────────────────────────────┐
                     │   React + Vite + TS Frontend    │
                     │  (Tailwind CSS + Lucide Icons)   │
                     └────────────────┬─────────────────┘
                                      │ HTTP / REST API (Port 8000)
                                      ▼
                     ┌──────────────────────────────────┐
                     │      FastAPI Backend Engine      │
                     └───────┬─────────────┬────────────┘
                             │             │
              ┌──────────────┴──────┐      └──────────────┬───────────────┐
              ▼                     ▼                     ▼               ▼
     ┌────────────────┐    ┌─────────────────┐   ┌────────────────┐   ┌────────────────┐
     │ PyMuPDF (fitz) │    │ SQLite Metadata │   │ ChromaDB Vector│   │ Official Google│
     │ PDF Extraction │    │  & Audit Logs   │   │  (ONNX MiniLM) │   │  GenAI SDK     │
     └────────────────┘    └─────────────────┘   └────────────────┘   └────────────────┘
```

---

## 3. Dynamic Retrieval & Local Semantic Embeddings

ProofMind AI avoids static, hardcoded responses:
- **Embedding Provider:** `onnx_minilm` (ONNX Runtime `all-MiniLM-L6-v2`, 384 dimensions) provides local dense vector retrieval with cosine distance matching.
- **Configurable Fallback:** `local_fast` (128-dimensional deterministic n-gram hash with L2 normalization) operates if ONNX is disabled.
- **Configurable Relevance Threshold:** `SIMILARITY_THRESHOLD=0.60` ensures irrelevant queries (such as asking for cooking recipes on academic documents) yield `INSUFFICIENT_EVIDENCE` rather than false positives.
- **Document Persistence & Detail Inspection:** Document records and chunk text persist across restarts in SQLite (`proofmind.db`) and ChromaDB (`chroma_db/`). Detailed chunk extraction can be viewed at `GET /documents/{document_id}`.

---

## 4. Evidence Verification Engine

ProofMind AI separates semantic interpretation from deterministic verification:

1. **Citation Verification:** Checks if cited `evidence_id` exists in the retrieved set. Flags invalid or hallucinated citation IDs.
2. **Claim Verification:** Validates whether each claim has at least one authentic supporting citation.
3. **Contradiction Scanner:** Detects numerical and conditional discrepancies across sources.
4. **Transparent Indicator Scoring:**
   - **Evidence Coverage:** Proportion of claims grounded in at least one valid retrieved source.
   - **Citation Validity:** Ratio of valid, authentic citations over total citations.
   - **Claim Support:** Ratio of claims solidly substantiated by evidence.
   - **Source Quality:** Weighted score of average relevance and authentic document metadata.
   - **Unresolved Conflicts:** Number of active material disagreements.
   - **Context Completeness:** Score reflecting missing administrative riders or student conditions.

---

## 5. Project Structure

```
proofmind-ai/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes.py              # REST API endpoints (/health, /documents, /documents/{id}, /analyze, /demo/load)
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── database.py            # SQLite schema, document metadata, chunks & audit history
│   │   │   └── vector_store.py        # ChromaDB persistent vector retrieval (ONNX MiniLM semantic & fallback)
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py             # Pydantic data schemas & response models
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── pdf_service.py         # PyMuPDF page-level extraction, chunking & SHA-256 deduplication
│   │   │   ├── gemini_service.py      # Google GenAI SDK client & dynamic evidence synthesizer
│   │   │   └── evidence_engine.py     # Deterministic verification, contradiction matrix & indicators
│   │   ├── config.py                  # Environment settings & retrieval thresholds
│   │   └── main.py                    # FastAPI application with CORS middleware
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_proofmind_all.py      # Automated pytest suite (12 test cases)
│   ├── pytest.ini
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.tsx             # ProofMind AI branding, tagline & live engine status
│   │   │   ├── DocumentManager.tsx    # Drag-and-drop PDF uploader, library manager, inspect modal & demo loader
│   │   │   ├── AnalysisInput.tsx      # Question input box, cancel button & honest Web search toggle
│   │   │   ├── StatusBanner.tsx       # Primary status banner (SUPPORTED, NEEDS_VERIFICATION, INSUFFICIENT)
│   │   │   ├── IndicatorsPanel.tsx    # 6 transparent evidence quality indicators with visual progress bars
│   │   │   ├── ClaimsList.tsx         # Granular claims with verification status & interactive citation chips
│   │   │   ├── ContradictionMatrix.tsx# Side-by-side comparison of conflicting provisions & scopes
│   │   │   ├── EvidenceViewer.tsx     # Tabbed passage inspector (PDF passages & Web grounding sources)
│   │   │   └── ActionableInsights.tsx # Missing context parameters, follow-up inquiries & governance notice
│   │   ├── api.ts                     # REST client connecting to FastAPI backend
│   │   ├── types.ts                   # TypeScript interfaces matching backend models
│   │   ├── App.tsx                    # Master single-page application with abort controller & stale result clearing
│   │   ├── main.tsx                   # React root mount
│   │   └── index.css                  # Tailwind styles
│   ├── package.json
│   └── vite.config.ts
├── demo-data/
│   ├── create_demo_docs.py            # Python PyMuPDF generator for fictional scholarship documents
│   ├── Policy_A_General_Scholarship_2024.pdf   # 75% attendance threshold
│   ├── Policy_B_STEM_Honors_Rider_2024.pdf     # 80% attendance threshold for STEM
│   ├── Student_Record_Alex_Rivera.pdf          # Physics major with 78% attendance (Conflict test)
│   ├── Policy_Standard_Merit_2024.pdf          # Standard merit 75% attendance
│   └── Student_Record_Jordan_Lee.pdf           # English major with 88% attendance (Supported test)
├── .env.example
├── .gitignore
└── README.md
```

---

## 6. Installation and Quickstart

### Prerequisites
- Python 3.11+ (Tested on Python 3.13)
- Node.js 18+ (Tested on Node v24)
- npm

### 1. Backend Setup
```bash
# Navigate to backend folder
cd backend

# Activate virtual environment
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Set your Gemini API key in backend/.env
# If no key is provided, the dynamic offline evidence engine runs with local semantic embeddings.
# GEMINI_API_KEY="your_api_key_here"

# Start the backend server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
The backend API will be live at `http://127.0.0.1:8000` (Swagger docs at `http://127.0.0.1:8000/docs`).

### 2. Frontend Setup
```bash
# Navigate to frontend folder
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 7. API Documentation

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Returns server health, Gemini config state, embedding provider (`onnx_minilm`), document count, and chunk count. |
| `GET` | `/documents` | Lists all indexed documents with page count and status. |
| `GET` | `/documents/{document_id}` | Returns document metadata and all extracted chunk passages. |
| `POST` | `/documents/upload` | Multipart upload for one or multiple PDF documents with validation and SHA-256 deduplication. |
| `DELETE` | `/documents/{document_id}` | Deletes document, SQLite metadata, and ChromaDB vector embeddings. |
| `POST` | `/demo/load` | Indexes the bundled demo PDFs into the library in 1 click. |
| `POST` | `/analyze` | Executes evidence retrieval with similarity thresholding, citation integrity verification, contradiction detection, and indicator synthesis. |
| `GET` | `/analyses/{analysis_id}` | Retrieves a previously stored analysis record from SQLite. |

---

## 8. Automated Testing

Run the test suite from the backend directory:

```bash
cd backend
.\venv\Scripts\pytest -v
```

### Test Coverage (12 passed):
1. `test_pdf_extraction_and_page_references` — Verifies PyMuPDF page-number preservation and chunk boundary extraction.
2. `test_upload_validation` — Tests rejection of empty files and non-PDF extensions.
3. `test_retrieval_and_vector_store` — Tests ChromaDB vector insertion and semantic similarity retrieval.
4. `test_invalid_citation_id_handling` — Tests deterministic detection and flagging of hallucinated or non-existent citation IDs.
5. `test_unsupported_claim_detection` — Tests detection of claims with missing or unsupported citations.
6. `test_contradiction_detection` — Tests detection of conflicting numerical attendance thresholds (75% vs. 80%).
7. `test_missing_evidence_scenario` — Tests assignment of `INSUFFICIENT_EVIDENCE` status when evidence is absent.
8. `test_clean_supported_scenario` — Tests assignment of `SUPPORTED` status when all conditions are satisfied without conflict.
9. `test_api_health` — Tests `/health` endpoint response schema and embedding provider info.
10. `test_api_upload_detail_and_delete` — Tests document upload, detail inspection, and deletion cleanup.
11. `test_meaningless_query_rejection` — Tests that meaningless/conversational inputs (e.g., "hlooo") are not given fabricated support.
12. `test_api_analyze_flow` — Tests the end-to-end `/analyze` pipeline.

---

## 9. Acceptance Verification Scenarios

- **Scenario A — Empty Repository:** If no documents are uploaded, the UI displays zero documents and an informative empty state ("No Query Analyzed Yet").
- **Scenario B — Upload & Inspection:** Upload a PDF. PyMuPDF extracts text page by page. Click the eye icon next to the document to inspect extracted passages and chunk boundaries.
- **Scenario C — Relevant Query:** Ask a question answered by the PDF. The system retrieves relevant passages, displays exact page numbers, and links claims to citations.
- **Scenario D — Unsupported / Irrelevant Query:** Ask an irrelevant question (e.g., "What is the recipe for baking chocolate cake with frosting?"). The cosine similarity threshold (`0.60`) rejects unrelated passages, producing `INSUFFICIENT_EVIDENCE`.
- **Scenario E — Meaningless Query:** Submitting "hlooo" produces `INSUFFICIENT_EVIDENCE` and requests a substantive factual question instead of inventing claims.
- **Scenario F — Contradictory Evidence:** When analyzing conflicting policies (e.g. 75% vs. 80% attendance), the engine displays `NEEDS_VERIFICATION` with a side-by-side contradiction matrix.
- **Scenario G — Stale Results & Deletion:** Deleting a document marks active results referencing that document as stale, removes its vectors, and updates library counts.
- **Scenario H — Offline Mode:** When `GEMINI_API_KEY` is not present, the system runs with local semantic embeddings and dynamic passage synthesis, clearly labeling web search as unavailable.

---

## 10. Governance & Limitations

- **Decision Support Tool:** ProofMind AI provides evidence extraction, verification, and comparison to support human analysts. It is not an automated legal, financial, or administrative authority.
- **Document Scope:** Analysis is strictly bounded by the uploaded document repository and optional web search grounding.
- **Untrusted Input Handling:** All PDF texts and web snippets are treated as untrusted data and sanitized during processing.
