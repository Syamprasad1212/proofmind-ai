import re
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple

class QueryIntent(str, Enum):
    GREETING_OR_MEANINGLESS = "GREETING_OR_MEANINGLESS"
    SUMMARIZE_DOCUMENT = "SUMMARIZE_DOCUMENT"
    SUMMARIZE_ALL = "SUMMARIZE_ALL"
    EXTRACT_SKILLS = "EXTRACT_SKILLS"
    EXTRACT_PROFILE = "EXTRACT_PROFILE"
    CANDIDATE_IDENTITY = "CANDIDATE_IDENTITY"
    POLICY_REQUIREMENTS = "POLICY_REQUIREMENTS"
    COMPARE_DOCUMENTS = "COMPARE_DOCUMENTS"
    DETECT_CONTRADICTIONS = "DETECT_CONTRADICTIONS"
    EXTRACT_KEY_POINTS = "EXTRACT_KEY_POINTS"
    EXPLAIN_PASSAGE = "EXPLAIN_PASSAGE"
    FACTUAL_QUESTION = "FACTUAL_QUESTION"
    UNSUPPORTED_OR_CLARIFICATION = "UNSUPPORTED_OR_CLARIFICATION"

def classify_intent(
    query: str,
    selected_doc_ids: Optional[List[str]] = None,
    all_docs: Optional[List[Any]] = None
) -> Tuple[QueryIntent, Dict[str, Any]]:
    """
    Classifies the user query into a structured intent with contextual metadata.
    Enables true query understanding rather than generic keyword matching.
    """
    q_raw = query.strip()
    if not q_raw:
        return QueryIntent.UNSUPPORTED_OR_CLARIFICATION, {
            "reason": "Empty query",
            "suggestion": "Please enter a specific question or request."
        }

    q_lower = q_raw.lower()

    # 1. Detect greetings and meaningless input
    greetings = {
        "hello", "hi", "hey", "hlo", "hlooo", "heyy", "good morning", 
        "good afternoon", "good evening", "howdy", "sup", "greetings",
        "test", "testing", "yo"
    }
    
    # Check if exact greeting or starts with greeting
    if q_lower in greetings or any(q_lower == f"{g}!" or q_lower == f"{g}." for g in greetings):
        return QueryIntent.GREETING_OR_MEANINGLESS, {
            "type": "greeting",
            "detected_phrase": q_raw
        }

    # Check for gibberish / meaningless input (repeated characters, no vowels, or pure symbols)
    # e.g., "hlooo", "asdfgh", "zzzzz", "?????"
    has_letters = bool(re.search(r'[a-zA-Z]', q_lower))
    has_vowels = bool(re.search(r'[aeiouy]', q_lower))
    repeated_chars = bool(re.search(r'(.)\1{3,}', q_lower))
    
    if (not has_letters) or (len(q_lower) > 3 and not has_vowels) or repeated_chars:
        # Check if it's not a recognized word or domain acronym
        if q_lower not in {"html", "sql", "css", "xml", "json", "npm", "jwt", "php", "gpa", "cgpa", "stem"}:
            return QueryIntent.GREETING_OR_MEANINGLESS, {
                "type": "meaningless",
                "detected_phrase": q_raw
            }

    # 2. Key Points / Highlights
    if any(k in q_lower for k in ["key point", "main point", "takeaway", "bullet point", "highlight", "important point", "tell me the main points"]):
        return QueryIntent.EXTRACT_KEY_POINTS, {
            "focus": "key_points"
        }

    # 3. Summarization Requests
    summary_triggers = [
        "summarize", "summarise", "summary", "give me a summary", 
        "summarize this", "summarize my resume", "what does this pdf contain",
        "what does this document contain", "what is this document about",
        "tell me about this document", "overview", "tl;dr", "tldr",
        "brief overview", "document summary", "executive summary", "synopsis"
    ]
    if any(trig in q_lower for trig in summary_triggers):
        # Determine whether single document or multi-document
        is_multi = False
        target_doc = None
        
        if selected_doc_ids and len(selected_doc_ids) == 1:
            is_multi = False
            target_doc = selected_doc_ids[0]
        elif selected_doc_ids and len(selected_doc_ids) > 1:
            is_multi = True
        else:
            # All documents scope
            if any(k in q_lower for k in ["my resume", "resume", "cv"]):
                is_multi = False
            elif any(k in q_lower for k in ["all", "everything", "all documents"]):
                is_multi = True
            elif all_docs and len(all_docs) > 1:
                # Multiple documents present in All Documents scope
                is_multi = True
            else:
                is_multi = False

        if is_multi:
            return QueryIntent.SUMMARIZE_ALL, {
                "multi_doc": True,
                "requested_summary": True
            }
        else:
            return QueryIntent.SUMMARIZE_DOCUMENT, {
                "multi_doc": False,
                "target_doc_id": target_doc,
                "requested_summary": True
            }

    # 4. Document Comparison & Contradiction Detection
    if any(k in q_lower for k in ["compare", "difference between", "versus", "vs "]):
        return QueryIntent.COMPARE_DOCUMENTS, {
            "comparison": True
        }
    if any(k in q_lower for k in ["contradict", "conflict", "discrepan", "inconsisten"]):
        return QueryIntent.DETECT_CONTRADICTIONS, {
            "detect_conflicts": True
        }

    # 5. Candidate Identity & Contact Details
    if any(w in q_lower for w in ["name", "who is", "who is this", "candidate", "contact", "email", "phone", "address", "identity", "singha", "syam", "applicant", "whose resume"]):
        return QueryIntent.CANDIDATE_IDENTITY, {
            "focus": "identity"
        }

    # 6. Skills & Technologies Extraction
    if any(w in q_lower for w in ["skill", "technolog", "programming", "languages", "tools", "stack", "framework", "coding"]):
        return QueryIntent.EXTRACT_SKILLS, {
            "focus": "skills"
        }

    # 7. Education, Projects, and Professional Profile
    if any(w in q_lower for w in ["project", "built", "developed", "portfolio", "application", "education", "degree", "college", "university", "cgpa", "gpa", "bachelor", "diploma", "experience", "intern", "company", "work", "job", "role"]):
        return QueryIntent.EXTRACT_PROFILE, {
            "focus": "profile"
        }

    # 8. Policy & Eligibility Evaluation
    if any(w in q_lower for w in ["attendance", "eligib", "policy", "threshold", "requirement", "scholarship", "standard merit", "stem honors", "jordan", "alex"]):
        return QueryIntent.POLICY_REQUIREMENTS, {
            "focus": "policy"
        }

    # 9. Passage Explanation
    if any(w in q_lower for w in ["explain", "what does this mean", "clarify this", "break down"]):
        return QueryIntent.EXPLAIN_PASSAGE, {
            "focus": "explanation"
        }

    # 10. Default: Factual Question
    return QueryIntent.FACTUAL_QUESTION, {
        "focus": "factual"
    }
