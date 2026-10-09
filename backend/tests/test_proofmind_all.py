import os
import io
import pytest
from fastapi.testclient import TestClient
import pymupdf

from app.main import app
from app.config import settings
from app.models.schemas import (
    EvidenceStatus,
    Claim,
    ClaimCitation,
    EvidenceSource,
    Contradiction,
    EvidenceIndicators
)
from app.services.pdf_service import pdf_service, PDFProcessingError
from app.services.evidence_engine import evidence_engine
from app.services.gemini_service import gemini_service
from app.db import database as db
from app.db.vector_store import vector_store

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_db():
    db.init_db()
    yield

def create_sample_pdf_bytes(title: str, text: str, page_count: int = 1) -> bytes:
    doc = pymupdf.open()
    for p in range(page_count):
        page = doc.new_page(width=595, height=842)
        page.insert_text((50, 50), f"{title} - Page {p+1}", fontsize=14)
        page.insert_text((50, 100), text, fontsize=10)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes

# 1. Test PDF Extraction and Page References
def test_pdf_extraction_and_page_references():
    pdf_bytes = create_sample_pdf_bytes("Policy Document", "Section 1: Minimum attendance is 75% for scholarship.", page_count=2)
    chunks, page_count = pdf_service.extract_and_chunk(pdf_bytes, "policy.pdf", "DOC-TEST-1")
    
    assert page_count == 2
    assert len(chunks) >= 2
    pages_found = {c.page_number for c in chunks}
    assert 1 in pages_found
    assert 2 in pages_found
    assert all(c.filename == "policy.pdf" for c in chunks)
    assert all(c.document_id == "DOC-TEST-1" for c in chunks)

# 2. Test Upload Validation (Invalid formats, empty file)
def test_upload_validation():
    with pytest.raises(PDFProcessingError, match="empty"):
        pdf_service.validate_file("empty.pdf", b"")

    with pytest.raises(PDFProcessingError, match="Only PDF"):
        pdf_service.validate_file("document.docx", b"dummy content")

# 3. Test Retrieval Pipeline
def test_retrieval_and_vector_store():
    test_chunk_text = "Honors scholars must maintain an attendance record exceeding 80%."
    pdf_bytes = create_sample_pdf_bytes("Honors Rider", test_chunk_text, page_count=1)
    chunks, _ = pdf_service.extract_and_chunk(pdf_bytes, "honors.pdf", "DOC-VEC-1")
    
    vector_store.add_chunks(chunks)
    assert vector_store.count() > 0
    
    results = vector_store.query("Honors scholars attendance record exceeding 80%", n_results=5, min_score=0.2)
    assert len(results) > 0
    assert any("80%" in r["text"] for r in results)

# 4. Test Invalid Citation IDs Detection
def test_invalid_citation_id_handling():
    sources = [
        EvidenceSource(
            evidence_id="EVD-1",
            source_type="document",
            filename="general_policy.pdf",
            page_number=1,
            passage="General policy attendance is 75%.",
            retrieval_date="2026-10-09 12:00:00"
        )
    ]
    
    llm_output = {
        "claims": [
            {
                "claim_id": "CLM-1",
                "claim_text": "Student must have 95% attendance.",
                "importance": "critical",
                "citations": [
                    {
                        "evidence_id": "EVD-999",
                        "relationship": "supports",
                        "rationale": "Non-existent citation"
                    }
                ]
            }
        ],
        "contradictions": [],
        "missing_information": [],
        "follow_up_questions": []
    }
    
    status, reasoning, claims, conflicts, indicators = evidence_engine.verify_and_synthesize(llm_output, sources)
    
    assert len(claims) == 1
    assert claims[0].verification_status == "invalid_citation"
    assert claims[0].citations[0].verified is False
    assert "does not exist" in claims[0].citations[0].verification_issue
    assert indicators.citation_validity == 0.0
    assert status == EvidenceStatus.NEEDS_VERIFICATION

# 5. Test Unsupported Claims
def test_unsupported_claim_detection():
    sources = [
        EvidenceSource(
            evidence_id="EVD-1",
            source_type="document",
            filename="policy.pdf",
            page_number=1,
            passage="General attendance threshold is 75%.",
            retrieval_date="2026-10-09 12:00:00"
        )
    ]
    llm_output = {
        "claims": [
            {
                "claim_id": "CLM-1",
                "claim_text": "Student receives free housing and $10,000 stipend.",
                "importance": "critical",
                "citations": []
            }
        ],
        "contradictions": [],
        "missing_information": [],
        "follow_up_questions": []
    }
    status, reasoning, claims, conflicts, indicators = evidence_engine.verify_and_synthesize(llm_output, sources)
    assert claims[0].verification_status == "unsupported"
    assert indicators.claim_support == 0.0

# 6. Test Genuine Contradictions Detection
def test_contradiction_detection():
    sources = [
        EvidenceSource(
            evidence_id="EVD-1",
            source_type="document",
            filename="Policy_A.pdf",
            page_number=1,
            passage="Standard mandatory attendance requirement is 75%.",
            retrieval_date="2026-10-09 12:00:00"
        ),
        EvidenceSource(
            evidence_id="EVD-2",
            source_type="document",
            filename="Policy_B.pdf",
            page_number=1,
            passage="STEM Honors scholarship mandatory attendance is 80%.",
            retrieval_date="2026-10-09 12:00:00"
        )
    ]
    llm_output = {
        "claims": [
            {
                "claim_id": "CLM-1",
                "claim_text": "Policy A requires 75% attendance.",
                "importance": "critical",
                "citations": [{"evidence_id": "EVD-1", "relationship": "supports"}]
            },
            {
                "claim_id": "CLM-2",
                "claim_text": "Policy B requires 80% attendance.",
                "importance": "critical",
                "citations": [{"evidence_id": "EVD-2", "relationship": "supports"}]
            }
        ],
        "contradictions": [
            {
                "conflict_id": "CONF-1",
                "claim_a": "Policy A requires 75% attendance",
                "source_a": "Policy_A.pdf (Page 1)",
                "passage_a": "Standard mandatory attendance requirement is 75%.",
                "claim_b": "Policy B requires 80% attendance",
                "source_b": "Policy_B.pdf (Page 1)",
                "passage_b": "STEM Honors scholarship mandatory attendance is 80%.",
                "conflict_nature": "Numerical policy discrepancy: 75% vs 80% attendance requirement.",
                "scope_differences": "General scholarship vs STEM Honors rider.",
                "is_unresolved": True
            }
        ],
        "missing_information": ["Applicable scholarship rider for the student."],
        "follow_up_questions": ["Is the student classified under the STEM Honors rider?"]
    }
    status, reasoning, claims, conflicts, indicators = evidence_engine.verify_and_synthesize(llm_output, sources)
    assert status == EvidenceStatus.NEEDS_VERIFICATION
    assert len(conflicts) >= 1
    assert conflicts[0].is_unresolved is True
    assert indicators.unresolved_conflicts_count >= 1

# 7. Test Missing Evidence Scenario -> INSUFFICIENT_EVIDENCE
def test_missing_evidence_scenario():
    sources = []
    llm_output = {
        "claims": [],
        "contradictions": [],
        "missing_information": ["No documents found."],
        "follow_up_questions": ["Please upload relevant files."]
    }
    status, reasoning, claims, conflicts, indicators = evidence_engine.verify_and_synthesize(llm_output, sources)
    assert status == EvidenceStatus.INSUFFICIENT_EVIDENCE
    assert "insufficient" in reasoning.lower()

# 8. Test Non-Conflicting Clean Case -> SUPPORTED
def test_clean_supported_scenario():
    sources = [
        EvidenceSource(
            evidence_id="EVD-1",
            source_type="document",
            filename="Standard_Policy.pdf",
            page_number=1,
            passage="Merit scholars must maintain at least 75% attendance.",
            retrieval_date="2026-10-09 12:00:00"
        ),
        EvidenceSource(
            evidence_id="EVD-2",
            source_type="document",
            filename="Jordan_Record.pdf",
            page_number=1,
            passage="Jordan Lee attendance record is 88.0%.",
            retrieval_date="2026-10-09 12:00:00"
        )
    ]
    llm_output = {
        "claims": [
            {
                "claim_id": "CLM-1",
                "claim_text": "Merit policy requires 75% attendance.",
                "importance": "critical",
                "citations": [{"evidence_id": "EVD-1", "relationship": "supports"}]
            },
            {
                "claim_id": "CLM-2",
                "claim_text": "Jordan Lee attendance is 88.0%.",
                "importance": "critical",
                "citations": [{"evidence_id": "EVD-2", "relationship": "supports"}]
            }
        ],
        "contradictions": [],
        "missing_information": [],
        "follow_up_questions": []
    }
    status, reasoning, claims, conflicts, indicators = evidence_engine.verify_and_synthesize(llm_output, sources)
    assert status == EvidenceStatus.SUPPORTED
    assert indicators.citation_validity == 1.0
    assert indicators.claim_support == 1.0
    assert indicators.unresolved_conflicts_count == 0

# 9. Test Resume Skills Extraction & Document Scope Isolation (Regression Tests A & B)
def test_resume_skills_extraction_and_scope_isolation():
    # Create synthetic resume
    resume_text = (
        "SKILLS "
        "Programming Languages: Python, Java, SQL "
        "Libraries & Frameworks: React, Flutter "
        "Databases: PostgreSQL "
    )
    resume_bytes = create_sample_pdf_bytes("John Doe Resume", resume_text, page_count=1)
    
    # Create unrelated course report
    report_text = (
        "Course Report on CSV Data Importer Feature. "
        "The system processes CSV inputs and computes summary tables. "
    )
    report_bytes = create_sample_pdf_bytes("Course Report", report_text, page_count=1)
    
    # Upload both
    upload_res = client.post("/documents/upload", files=[
        ("files", ("john_resume.pdf", resume_bytes, "application/pdf")),
        ("files", ("unrelated_report.pdf", report_bytes, "application/pdf"))
    ])
    assert upload_res.status_code == 200
    docs = upload_res.json()
    resume_id = next(d["id"] for d in docs if "resume" in d["filename"])
    
    # Query with resume-only scope
    res = client.post("/analyze", json={
        "query": "What are the technical skills?",
        "document_ids": [resume_id]
    })
    assert res.status_code == 200
    data = res.json()
    assert data["evidence_status"] == EvidenceStatus.SUPPORTED
    assert "john_resume.pdf" in data["document_scope"]
    # Verify course report never appears in sources or claims
    assert all("unrelated_report.pdf" not in s["filename"] for s in data["evidence_sources"])
    assert any("Python" in c["claim_text"] for c in data["claims"])
    assert any("React" in c["claim_text"] for c in data["claims"])
    assert not any("CSV" in c["claim_text"] for c in data["claims"])

# 10. Test Meaningless Query Detection ("hlooo")
def test_meaningless_query_rejection():
    res = client.post("/analyze", json={"query": "hlooo", "enable_web_research": False})
    assert res.status_code == 200
    data = res.json()
    assert data["evidence_status"] in ["CLARIFICATION_NEEDED", "INSUFFICIENT_EVIDENCE"]
    assert len(data["claims"]) == 0
    assert any(w in data["answer_summary"].lower() for w in ["recognized", "instruction", "specific query", "conversational", "greeting", "clarif"])

# 11. Test API Endpoints (Health, Upload, Details, Delete)
def test_api_health():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "document_count" in data
    assert "embedding_provider" in data

def test_api_upload_detail_and_delete():
    pdf_bytes = create_sample_pdf_bytes("Upload Test", "Upload test text content.", page_count=1)
    
    files = [("files", ("test_upload_doc.pdf", pdf_bytes, "application/pdf"))]
    upload_res = client.post("/documents/upload", files=files)
    assert upload_res.status_code == 200
    uploaded_docs = upload_res.json()
    assert len(uploaded_docs) == 1
    doc_id = uploaded_docs[0]["id"]
    assert uploaded_docs[0]["status"] == "INDEXED"
    
    detail_res = client.get(f"/documents/{doc_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["id"] == doc_id
    assert len(detail_data["chunks"]) > 0
    
    del_res = client.delete(f"/documents/{doc_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"
    
    list_res_after = client.get("/documents")
    assert not any(d["id"] == doc_id for d in list_res_after.json())

# 12. Test Analysis API with Dynamic Retrieval and Verification
def test_api_analyze_flow():
    demo_res = client.post("/demo/load")
    assert demo_res.status_code == 200
    
    query_payload = {
        "query": "Is Alex Rivera eligible for the scholarship based on attendance?",
        "enable_web_research": False
    }
    anl_res = client.post("/analyze", json=query_payload)
    assert anl_res.status_code == 200
    data = anl_res.json()
    assert "analysis_id" in data
    assert data["evidence_status"] in ["NEEDS_VERIFICATION", "SUPPORTED", "INSUFFICIENT_EVIDENCE"]
    assert len(data["claims"]) > 0
    assert len(data["evidence_sources"]) > 0
    assert "evidence_indicators" in data
    assert "document_scope" in data
    
    anl_id = data["analysis_id"]
    get_anl = client.get(f"/analyses/{anl_id}")
    assert get_anl.status_code == 200

# 13. Test Jordan Lee Eligibility Evaluation (Zero false contradictions from student records)
def test_jordan_lee_all_documents_supported():
    anl_res = client.post("/analyze", json={
        "query": "Is Jordan Lee eligible for the Standard Merit Scholarship renewal based on attendance?",
        "enable_web_research": False
    })
    assert anl_res.status_code == 200
    data = anl_res.json()
    assert data["evidence_status"] == "SUPPORTED"
    assert len(data["contradictions"]) == 0
    assert any("88.0%" in c["claim_text"] for c in data["claims"])
    assert any("75%" in c["claim_text"] for c in data["claims"])

def test_candidate_identity_and_singha_mismatch():
    anl_res = client.post("/analyze", json={
        "query": "is the name Singha?",
        "enable_web_research": False
    })
    assert anl_res.status_code == 200
    data = anl_res.json()
    assert data["evidence_status"] == "SUPPORTED"
    # Should clarify candidate name and indicate Singha does not match
    assert "Singha" in data["answer_summary"] or "does NOT" in data["answer_summary"]
    assert len(data["claims"]) > 0

# ==============================================================================
# SCENARIOS A THROUGH L COMPREHENSIVE REGRESSION SUITE
# ==============================================================================

# Scenario A: Query "summarize" with 1 selected resume PDF -> returns structured summary with education, skills, projects
def test_scenario_a_summarize_single_resume():
    resume_bytes = create_sample_pdf_bytes(
        "Candidate Resume",
        "EDUCATION: BS Computer Science from State University.\n"
        "TECHNICAL SKILLS: Python, TypeScript, React, Docker, FastAPI.\n"
        "EXPERIENCE: Software Engineer building verification engines and microservices.\n"
        "PROJECTS: ProofMind AI evidence verification assistant."
    )
    upload_res = client.post("/documents/upload", files=[
        ("files", ("alice_resume.pdf", resume_bytes, "application/pdf"))
    ])
    assert upload_res.status_code == 200
    doc_id = upload_res.json()[0]["id"]
    
    res = client.post("/analyze", json={
        "query": "summarize",
        "document_ids": [doc_id]
    })
    assert res.status_code == 200
    data = res.json()
    assert data["evidence_status"] == EvidenceStatus.SUPPORTED
    assert data["detected_intent"].upper() == "SUMMARIZE_DOCUMENT"
    assert "alice_resume.pdf" in data["document_scope"]
    summary = data["answer_summary"].lower()
    assert any(term in summary for term in ["python", "skills", "experience", "education", "candidate", "software"])
    # Must not contain generic template
    assert "based on" not in summary or "retrieved document passage" not in summary

# Scenario B: Query "summarize" with 1 selected policy PDF -> returns policy summary with threshold and rules
def test_scenario_b_summarize_single_policy():
    policy_bytes = create_sample_pdf_bytes(
        "Academic Scholarship Policy 2026",
        "SECTION 1: ELIGIBILITY CRITERIA\n"
        "Candidates must maintain an overall attendance threshold of at least 75.0% across all courses.\n"
        "SECTION 2: RENEWAL REQUIREMENTS\n"
        "Scholarship renewal requires a minimum cumulative GPA of 3.20 and timely reapplication."
    )
    upload_res = client.post("/documents/upload", files=[
        ("files", ("scholarship_policy.pdf", policy_bytes, "application/pdf"))
    ])
    assert upload_res.status_code == 200
    doc_id = upload_res.json()[0]["id"]
    
    res = client.post("/analyze", json={
        "query": "summarize",
        "document_ids": [doc_id]
    })
    assert res.status_code == 200
    data = res.json()
    assert data["evidence_status"] == EvidenceStatus.SUPPORTED
    assert data["detected_intent"].upper() == "SUMMARIZE_DOCUMENT"
    assert "scholarship_policy.pdf" in data["document_scope"]
    summary = data["answer_summary"].lower()
    assert any(term in summary for term in ["policy", "attendance", "75", "scholarship", "requirement", "criteria"])
    # Must not confuse policy with resume or unrelated course report
    assert "react" not in summary
    assert "csv input" not in summary

# Scenario C: Query "summarize" with multiple PDFs -> produces structured per-document sections, never merging them into an unlabelled narrative
def test_scenario_c_summarize_multiple_documents_separated():
    doc1 = create_sample_pdf_bytes("Doc Alpha", "Content regarding financial balance sheets and fiscal quarters.")
    doc2 = create_sample_pdf_bytes("Doc Beta", "Content regarding engineering architectural guidelines and protocols.")
    upload_res = client.post("/documents/upload", files=[
        ("files", ("finance_report.pdf", doc1, "application/pdf")),
        ("files", ("engineering_guide.pdf", doc2, "application/pdf"))
    ])
    assert upload_res.status_code == 200
    doc_ids = [d["id"] for d in upload_res.json()]
    
    res = client.post("/analyze", json={
        "query": "summarize",
        "document_ids": doc_ids
    })
    assert res.status_code == 200
    data = res.json()
    assert data["evidence_status"] == EvidenceStatus.SUPPORTED
    assert data["detected_intent"].upper() == "SUMMARIZE_ALL"
    summary = data["answer_summary"]
    # Verify per-document separation
    assert "finance_report.pdf" in summary
    assert "engineering_guide.pdf" in summary
    assert "---" in summary or "### Document:" in summary

# Scenario D: Query "summarize my resume" isolates resume document
def test_scenario_d_summarize_my_resume_isolates_scope():
    res = client.post("/analyze", json={
        "query": "summarize my resume",
        "enable_web_research": False
    })
    assert res.status_code == 200
    data = res.json()
    assert data["evidence_status"] == EvidenceStatus.SUPPORTED
    assert data["detected_intent"].upper() in ["SUMMARIZE_DOCUMENT", "EXTRACT_PROFILE"]
    assert "resume" in data["document_scope"].lower()
    assert not any("CSV" in c["claim_text"] for c in data["claims"])

# Scenario E: Query "What are my skills?" returns verified skills claims
def test_scenario_e_skills_extraction_verified():
    res = client.post("/analyze", json={
        "query": "What are my skills?",
        "enable_web_research": False
    })
    assert res.status_code == 200
    data = res.json()
    assert data["evidence_status"] == EvidenceStatus.SUPPORTED
    assert data["detected_intent"].upper() == "EXTRACT_SKILLS"
    assert len(data["claims"]) > 0
    # Must have verified claims referencing actual skills
    assert any(c["verification_status"] == "verified_supported" for c in data["claims"])
    assert any("python" in c["claim_text"].lower() or "skills" in c["claim_text"].lower() for c in data["claims"])

# Scenario F: Query "hlooo" returns CLARIFICATION_NEEDED or INSUFFICIENT_EVIDENCE with 0 false claims
def test_scenario_f_meaningless_and_greetings():
    for test_query in ["hlooo", "asdfghjkl", "hello"]:
        res = client.post("/analyze", json={"query": test_query, "enable_web_research": False})
        assert res.status_code == 200
        data = res.json()
        assert data["evidence_status"] in ["CLARIFICATION_NEEDED", "INSUFFICIENT_EVIDENCE"]
        assert len(data["claims"]) == 0
        assert data["evidence_indicators"]["claim_support"] == 0.0

# Scenario G: Query with empty document scope returns honest response
def test_scenario_g_empty_scope_response():
    res = client.post("/analyze", json={
        "query": "summarize",
        "document_ids": ["NON_EXISTENT_DOC_ID"]
    })
    assert res.status_code == 200
    data = res.json()
    assert data["evidence_status"] == EvidenceStatus.INSUFFICIENT_EVIDENCE
    assert len(data["claims"]) == 0

# Scenario H: Query with no relevant evidence produces honest INSUFFICIENT_EVIDENCE
def test_scenario_h_no_relevant_evidence():
    res = client.post("/analyze", json={
        "query": "What was the quantum teleportation breakthrough recorded in 1845?",
        "enable_web_research": False
    })
    assert res.status_code == 200
    data = res.json()
    assert data["evidence_status"] == EvidenceStatus.INSUFFICIENT_EVIDENCE
    assert len(data["claims"]) == 0
    assert data["evidence_indicators"]["claim_support"] == 0.0

# Scenario I: Gemini fallback synthesizer produces valid citations with zero fabrication
def test_scenario_i_deterministic_fallback_synthesis():
    items = [
        {
            "evidence_id": "EVD-TEST-01",
            "source_type": "document",
            "document_id": "DOC-99",
            "filename": "sample.pdf",
            "page_number": 1,
            "passage": "Attendance rate is recorded at 92.5 percent.",
            "retrieval_date": "2026-10-10 12:00:00"
        }
    ]
    raw_output = gemini_service._synthesize_local_evidence(
        query="What is the attendance rate?",
        evidence_items=items,
        document_scope="sample.pdf"
    )
    assert len(raw_output["claims"]) > 0
    assert any("92.5" in c["claim_text"] or "attendance" in c["claim_text"].lower() for c in raw_output["claims"])
    assert any(c["citations"][0]["evidence_id"] == "EVD-TEST-01" for c in raw_output["claims"])
    assert "92.5" in raw_output["answer_summary"] or "attendance" in raw_output["answer_summary"].lower()

# Scenario J: Multi-page document summarization covers across sections
def test_scenario_j_multipage_document_coverage():
    doc_multi = create_sample_pdf_bytes("MultiPage Research", "Section data across multi pages.", page_count=3)
    upload_res = client.post("/documents/upload", files=[
        ("files", ("multipage_paper.pdf", doc_multi, "application/pdf"))
    ])
    assert upload_res.status_code == 200
    doc_id = upload_res.json()[0]["id"]
    
    res = client.post("/analyze", json={
        "query": "summarize this document",
        "document_ids": [doc_id]
    })
    assert res.status_code == 200
    data = res.json()
    assert data["evidence_status"] == EvidenceStatus.SUPPORTED
    assert "multipage_paper.pdf" in data["document_scope"]
    # Evidence sources should cover chunks from the document
    assert len(data["evidence_sources"]) >= 1

# Scenario K: Citations resolve to actual indexed documents and valid page numbers
def test_scenario_k_citations_resolve_to_indexed_documents():
    res = client.post("/analyze", json={
        "query": "Is Jordan Lee eligible for scholarship?",
        "enable_web_research": False
    })
    assert res.status_code == 200
    data = res.json()
    source_map = {s["evidence_id"]: s for s in data["evidence_sources"]}
    assert len(source_map) > 0
    for claim in data["claims"]:
        for cit in claim["citations"]:
            assert cit["evidence_id"] in source_map
            matched_src = source_map[cit["evidence_id"]]
            assert matched_src["document_id"] is not None
            assert matched_src["page_number"] is not None
            assert matched_src["page_number"] >= 1
            assert len(matched_src["passage"]) > 0



# Scenario L: Subsequent queries do not leak stale analysis results
def test_scenario_l_query_state_isolation():
    # Query 1: Skills query
    res1 = client.post("/analyze", json={"query": "What are my skills?", "enable_web_research": False})
    data1 = res1.json()
    assert any("skills" in c["claim_text"].lower() or "python" in c["claim_text"].lower() for c in data1["claims"])
    
    # Query 2: Policy attendance query
    res2 = client.post("/analyze", json={"query": "What is the minimum attendance requirement for the scholarship?", "enable_web_research": False})
    data2 = res2.json()
    # Query 2 must not contain skills claims from query 1
    assert not any("python" in c["claim_text"].lower() for c in data2["claims"])
    assert not any("flutter" in c["claim_text"].lower() for c in data2["claims"])
    assert any("75%" in c["claim_text"] or "attendance" in c["claim_text"].lower() for c in data2["claims"])

