import os
import uuid
import json
import shutil
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from app.config import settings
from app.models.schemas import (
    DocumentMetadata,
    DocumentDetail,
    DocumentStatus,
    AnalysisRequest,
    AnalysisResponse,
    AnalysisRecord,
    EvidenceSource,
    EvidenceStatus,
    EvidenceIndicators,
    HealthResponse
)
from app.db import database as db
from app.db.vector_store import vector_store
from app.services.pdf_service import pdf_service, PDFProcessingError
from app.services.gemini_service import gemini_service
from app.services.evidence_engine import evidence_engine
from app.services.intent_service import classify_intent, QueryIntent

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def health_check():
    doc_count = db.get_document_count()
    chunk_count = db.get_chunk_count()
    return HealthResponse(
        status="healthy",
        version="1.2.0",
        gemini_configured=gemini_service.is_configured(),
        gemini_model=settings.GEMINI_MODEL,
        embedding_provider=settings.EMBEDDING_PROVIDER,
        document_count=doc_count,
        total_chunks=chunk_count
    )

@router.get("/documents", response_model=List[DocumentMetadata])
def list_documents():
    return db.get_all_documents()

@router.get("/documents/{document_id}", response_model=DocumentDetail)
def get_document_detail(document_id: str):
    doc = db.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document with ID '{document_id}' not found.")
    
    chunks = db.get_chunks_for_document(document_id)
    chunks_data = [c.model_dump() for c in chunks]
    
    return DocumentDetail(
        id=doc["id"],
        filename=doc["filename"],
        file_size_bytes=doc["file_size_bytes"],
        page_count=doc["page_count"],
        chunk_count=doc["chunk_count"],
        upload_date=doc["upload_date"],
        status=DocumentStatus(doc["status"]),
        sha256_hash=doc["sha256_hash"],
        error_message=doc["error_message"],
        chunks=chunks_data
    )

@router.post("/documents/upload", response_model=List[DocumentMetadata])
async def upload_documents(files: List[UploadFile] = File(...)):
    results: List[DocumentMetadata] = []
    
    for file in files:
        filename = file.filename or "unknown.pdf"
        file_bytes = await file.read()
        
        # 1. Validation
        try:
            pdf_service.validate_file(filename, file_bytes, settings.MAX_FILE_SIZE_MB)
        except PDFProcessingError as ve:
            doc_id = f"DOC-{uuid.uuid4().hex[:10].upper()}"
            error_meta = DocumentMetadata(
                id=doc_id,
                filename=filename,
                file_size_bytes=len(file_bytes),
                page_count=0,
                chunk_count=0,
                upload_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                status=DocumentStatus.ERROR,
                sha256_hash="",
                error_message=str(ve)
            )
            results.append(error_meta)
            continue

        sha256 = pdf_service.compute_sha256(file_bytes)
        
        # Duplicate detection by SHA-256
        existing = db.get_document_by_hash(sha256)
        if existing:
            results.append(DocumentMetadata(
                id=existing["id"],
                filename=existing["filename"],
                file_size_bytes=existing["file_size_bytes"],
                page_count=existing["page_count"],
                chunk_count=existing["chunk_count"],
                upload_date=existing["upload_date"],
                status=DocumentStatus(existing["status"]),
                sha256_hash=existing["sha256_hash"],
                error_message="Document already indexed (duplicate SHA-256 hash)."
            ))
            continue

        doc_id = f"DOC-{uuid.uuid4().hex[:10].upper()}"
        save_path = os.path.join(settings.STORAGE_DIR, f"{doc_id}_{filename}")
        
        with open(save_path, "wb") as f:
            f.write(file_bytes)

        # 2. Text Extraction & Overlapping Chunking
        try:
            chunks, page_count = pdf_service.extract_and_chunk(file_bytes, filename, doc_id)
            
            doc_meta = DocumentMetadata(
                id=doc_id,
                filename=filename,
                file_size_bytes=len(file_bytes),
                page_count=page_count,
                chunk_count=len(chunks),
                upload_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                status=DocumentStatus.INDEXED,
                sha256_hash=sha256,
                error_message=None
            )
            
            # Save to SQLite and ChromaDB
            db.add_document(doc_meta, save_path)
            db.add_chunks(chunks)
            vector_store.add_chunks(chunks)
            
            results.append(doc_meta)
        except PDFProcessingError as pe:
            err_meta = DocumentMetadata(
                id=doc_id,
                filename=filename,
                file_size_bytes=len(file_bytes),
                page_count=0,
                chunk_count=0,
                upload_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                status=DocumentStatus.ERROR,
                sha256_hash=sha256,
                error_message=str(pe)
            )
            db.add_document(err_meta, save_path)
            results.append(err_meta)
            
    return results

@router.delete("/documents/{document_id}")
def delete_document(document_id: str):
    doc = db.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document with ID '{document_id}' not found.")
    
    file_path = db.delete_document(document_id)
    vector_store.delete_document_vectors(document_id)
    
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass
            
    return {"status": "success", "message": f"Document '{document_id}' and all associated records deleted."}

@router.post("/analyze", response_model=AnalysisResponse)
def analyze_query(req: AnalysisRequest):
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    all_docs = db.get_all_documents()
    docs_by_id = {d.id: d for d in all_docs}

    # 1. Classify Query Intent
    intent, intent_meta = classify_intent(query, req.document_ids, all_docs)

    # Empty Repository Guard: Report honest empty state immediately
    if len(all_docs) == 0:
        empty_indicators = EvidenceIndicators(
            evidence_coverage=0.0,
            citation_validity=0.0,
            claim_support=0.0,
            source_quality=0.0,
            unresolved_conflicts_count=0,
            context_completeness=0.0,
            indicator_explanations={
                "evidence_coverage": "0% coverage. No documents uploaded in library.",
                "citation_validity": "0% validity. No indexed sources exist.",
                "claim_support": "0% support. No claims evaluated.",
                "source_quality": "0% quality. Library is empty.",
                "unresolved_conflicts": "0 active conflicts.",
                "context_completeness": "0% completeness. No document repository found."
            }
        )
        return AnalysisResponse(
            analysis_id=f"ANL-{uuid.uuid4().hex[:12].upper()}",
            query=query,
            document_scope="Empty Library",
            detected_intent=intent.value,
            answer_summary="No documents are currently indexed in ProofMind AI. Please upload one or more PDF documents to analyze evidence or generate summaries.",
            evidence_status=EvidenceStatus.INSUFFICIENT_EVIDENCE,
            status_reasoning="The document repository is empty. Upload documents to perform evidence analysis.",
            claims=[],
            evidence_sources=[],
            contradictions=[],
            evidence_indicators=empty_indicators,
            limitations=["Document library is empty."],
            missing_information=["Upload at least one PDF document to begin analysis."],
            follow_up_questions=["Which PDF document would you like to upload?"],
            retrieval_status={
                "retrieval_timestamp": datetime.now().isoformat(),
                "document_passages_retrieved": 0,
                "web_research_requested": False,
                "web_research_status": "disabled",
                "model_used": "offline-empty-state"
            },
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    # Greeting / Meaningless Input Guard: Do not pretend document verification occurred
    if intent == QueryIntent.GREETING_OR_MEANINGLESS:
        raw_llm_data = gemini_service._synthesize_greeting_or_meaningless_response(query)
        evidence_status, status_reasoning, verified_claims, verified_conflicts, indicators = evidence_engine.verify_and_synthesize(
            raw_llm_data=raw_llm_data,
            evidence_sources=[],
            query=query
        )
        return AnalysisResponse(
            analysis_id=f"ANL-{uuid.uuid4().hex[:12].upper()}",
            query=query,
            document_scope="N/A",
            detected_intent=intent.value,
            answer_summary=raw_llm_data["answer_summary"],
            evidence_status=EvidenceStatus.CLARIFICATION_NEEDED,
            status_reasoning=raw_llm_data["status_reasoning"],
            claims=[],
            evidence_sources=[],
            contradictions=[],
            evidence_indicators=indicators,
            limitations=raw_llm_data.get("limitations", []),
            missing_information=raw_llm_data.get("missing_information", []),
            follow_up_questions=raw_llm_data.get("follow_up_questions", []),
            retrieval_status={
                "retrieval_timestamp": datetime.now().isoformat(),
                "document_passages_retrieved": 0,
                "web_research_requested": False,
                "web_research_status": "disabled",
                "model_used": "intent-classifier-greeting"
            },
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    # 2. Determine Document Scope
    target_doc_ids = req.document_ids

    # If user asks about their resume ("my resume", "skills", "name") and no document scope was selected,
    # automatically prioritize resume documents if present
    if not target_doc_ids:
        q_lower = query.lower()
        if any(w in q_lower for w in [
            "my resume", "my skill", "my education", "my project", "my experience", "cv",
            "name", "who is", "candidate", "contact", "email", "phone", "identity", "singha", "syam", "applicant"
        ]) or (intent in [QueryIntent.EXTRACT_SKILLS, QueryIntent.CANDIDATE_IDENTITY]):
            resume_docs = [d.id for d in all_docs if any(r in d.filename.lower() for r in ["resume", "cv", "syam"])]
            if resume_docs:
                target_doc_ids = resume_docs

    # Format human-readable document scope name
    if target_doc_ids:
        scope_names = [docs_by_id[did].filename for did in target_doc_ids if did in docs_by_id]
        scope_display = ", ".join(scope_names) if scope_names else "Filtered Documents"
    else:
        scope_display = "All Documents"

    # 3. Document-Wide Retrieval vs. Vector Search
    evidence_sources: List[EvidenceSource] = []
    evidence_for_llm: List[dict] = []

    # STRATEGY A: For Summarization or Key Points, retrieve actual document text across all pages
    if intent in [QueryIntent.SUMMARIZE_DOCUMENT, QueryIntent.SUMMARIZE_ALL, QueryIntent.EXTRACT_KEY_POINTS]:
        target_docs_to_read = target_doc_ids if target_doc_ids else [d.id for d in all_docs]
        accumulated_chunks = []
        for did in target_docs_to_read:
            d_chunks = db.get_chunks_for_document(did)
            if not d_chunks:
                continue
            if len(target_docs_to_read) == 1:
                # Full document coverage: sample across all sections up to 10 chunks
                if len(d_chunks) <= 10:
                    accumulated_chunks.extend(d_chunks)
                else:
                    step = max(1, len(d_chunks) // 10)
                    accumulated_chunks.extend(d_chunks[::step][:10])
            else:
                # Multi-document coverage: sample representative chunks per document
                if len(d_chunks) <= 4:
                    accumulated_chunks.extend(d_chunks)
                else:
                    step = max(1, len(d_chunks) // 4)
                    accumulated_chunks.extend(d_chunks[::step][:4])

        for idx, chk in enumerate(accumulated_chunks):
            evd_id = f"EVD-{idx + 1}"
            evd_item = EvidenceSource(
                evidence_id=evd_id,
                source_type="document",
                document_id=chk.document_id,
                filename=chk.filename,
                page_number=chk.page_number,
                passage=chk.text,
                relevance_score=0.95,
                publication_date=None,
                retrieval_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            evidence_sources.append(evd_item)
            evidence_for_llm.append({
                "evidence_id": evd_id,
                "filename": chk.filename,
                "page_number": chk.page_number,
                "passage": chk.text,
                "score": 0.95
            })
    else:
        # STRATEGY B: Targeted Vector Similarity Search
        augmented_query = query
        q_lower = query.lower()
        if any(w in q_lower for w in ["skill", "technolog", "programming", "languages", "tools", "stack"]):
            augmented_query = f"{query} Programming Languages Web Technologies Libraries Frameworks Developer Tools Databases"
        elif any(w in q_lower for w in ["project", "built", "developed", "portfolio"]):
            augmented_query = f"{query} Projects Developed Built Application"
        elif any(w in q_lower for w in ["education", "degree", "college", "university", "cgpa", "gpa"]):
            augmented_query = f"{query} Education Degree Bachelor Diploma CGPA Percentage"
        elif any(w in q_lower for w in ["name", "who is", "candidate", "contact", "identity", "singha", "syam", "applicant"]):
            augmented_query = f"{query} Candidate Full Name Contact Email Phone Address Profile Summary"
        elif "jordan" in q_lower:
            augmented_query = f"{query} Jordan Lee Student Academic Profile Attendance Standard Merit Scholarship"

        retrieved_chunks = vector_store.query(
            query_text=augmented_query,
            n_results=6,
            document_ids=target_doc_ids,
            min_score=min(settings.SIMILARITY_THRESHOLD, 0.45) if target_doc_ids else settings.SIMILARITY_THRESHOLD
        )

        for idx, chk in enumerate(retrieved_chunks):
            evd_id = f"EVD-{idx + 1}"
            evd_item = EvidenceSource(
                evidence_id=evd_id,
                source_type="document",
                document_id=chk.get("document_id"),
                filename=chk.get("filename"),
                page_number=chk.get("page_number", 1),
                passage=chk.get("text", ""),
                relevance_score=chk.get("score"),
                publication_date=None,
                retrieval_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            evidence_sources.append(evd_item)
            evidence_for_llm.append({
                "evidence_id": evd_id,
                "filename": chk.get("filename"),
                "page_number": chk.get("page_number", 1),
                "passage": chk.get("text", ""),
                "score": chk.get("score")
            })

    # 4. Run Analysis (Gemini if key configured, or intent-aware synthesizer)
    raw_llm_data, web_sources_data, retrieval_meta = gemini_service.analyze_with_gemini(
        query=query,
        evidence_items=evidence_for_llm,
        enable_web_research=req.enable_web_research,
        intent=intent.value,
        document_scope=scope_display
    )

    # Append any web sources
    for w_data in web_sources_data:
        evidence_sources.append(EvidenceSource(**w_data))

    # 5. Evidence Engine Verification & Indicator Synthesis
    evidence_status, status_reasoning, verified_claims, verified_conflicts, indicators = evidence_engine.verify_and_synthesize(
        raw_llm_data=raw_llm_data,
        evidence_sources=evidence_sources,
        query=query
    )

    analysis_id = f"ANL-{uuid.uuid4().hex[:12].upper()}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    response = AnalysisResponse(
        analysis_id=analysis_id,
        query=query,
        document_scope=scope_display,
        detected_intent=intent.value,
        answer_summary=raw_llm_data.get("answer_summary", "No summary generated."),
        evidence_status=evidence_status,
        status_reasoning=status_reasoning,
        claims=verified_claims,
        evidence_sources=evidence_sources,
        contradictions=verified_conflicts,
        evidence_indicators=indicators,
        limitations=raw_llm_data.get("limitations", [
            "ProofMind AI is a decision support tool, not an automated legal or administrative authority."
        ]),
        missing_information=raw_llm_data.get("missing_information", []),
        follow_up_questions=raw_llm_data.get("follow_up_questions", []),
        retrieval_status=retrieval_meta,
        timestamp=timestamp
    )

    # 5. Save analysis to SQLite
    try:
        db.save_analysis(
            analysis_id=analysis_id,
            query=query,
            evidence_status=evidence_status.value,
            response_json=response.model_dump_json(),
            created_at=timestamp
        )
    except Exception:
        pass

    return response

@router.get("/analyses/{analysis_id}")
def get_analysis_by_id(analysis_id: str):
    res = db.get_analysis(analysis_id)
    if not res:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return res

@router.post("/demo/load", response_model=List[DocumentMetadata])
def load_demo_documents():
    """
    Loads and indexes the bundled demo PDFs from demo-data/.
    """
    demo_dir = os.path.join(settings.BASE_DIR, "..", "demo-data")
    if not os.path.exists(demo_dir):
        raise HTTPException(status_code=404, detail="Demo data directory not found.")
    
    demo_files = [f for f in os.listdir(demo_dir) if f.endswith(".pdf")]
    results = []
    
    for df in demo_files:
        full_path = os.path.join(demo_dir, df)
        with open(full_path, "rb") as f:
            file_bytes = f.read()
            
        sha256 = pdf_service.compute_sha256(file_bytes)
        existing = db.get_document_by_hash(sha256)
        if existing:
            results.append(DocumentMetadata(
                id=existing["id"],
                filename=existing["filename"],
                file_size_bytes=existing["file_size_bytes"],
                page_count=existing["page_count"],
                chunk_count=existing["chunk_count"],
                upload_date=existing["upload_date"],
                status=DocumentStatus(existing["status"]),
                sha256_hash=existing["sha256_hash"],
                error_message="Already indexed in library."
            ))
            continue
            
        doc_id = f"DOC-DEMO-{uuid.uuid4().hex[:6].upper()}"
        save_path = os.path.join(settings.STORAGE_DIR, f"{doc_id}_{df}")
        shutil.copyfile(full_path, save_path)
        
        chunks, page_count = pdf_service.extract_and_chunk(file_bytes, df, doc_id)
        doc_meta = DocumentMetadata(
            id=doc_id,
            filename=df,
            file_size_bytes=len(file_bytes),
            page_count=page_count,
            chunk_count=len(chunks),
            upload_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            status=DocumentStatus.INDEXED,
            sha256_hash=sha256,
            error_message=None
        )
        db.add_document(doc_meta, save_path)
        db.add_chunks(chunks)
        vector_store.add_chunks(chunks)
        results.append(doc_meta)
        
    return results
