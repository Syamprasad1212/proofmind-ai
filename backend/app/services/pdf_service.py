import os
import hashlib
import uuid
from typing import List, Tuple
import pymupdf  # PyMuPDF
from app.models.schemas import Chunk, DocumentMetadata, DocumentStatus

class PDFProcessingError(Exception):
    pass

class PDFService:
    @staticmethod
    def compute_sha256(file_bytes: bytes) -> str:
        return hashlib.sha256(file_bytes).hexdigest()

    @staticmethod
    def validate_file(filename: str, file_bytes: bytes, max_size_mb: int = 25) -> None:
        if not filename.lower().endswith(".pdf"):
            raise PDFProcessingError(f"Invalid file type for '{filename}'. Only PDF documents are supported.")
        
        file_size_mb = len(file_bytes) / (1024 * 1024)
        if file_size_mb > max_size_mb:
            raise PDFProcessingError(f"File '{filename}' exceeds maximum allowed size of {max_size_mb}MB (Actual: {file_size_mb:.2f}MB).")
        
        if len(file_bytes) == 0:
            raise PDFProcessingError(f"File '{filename}' is completely empty (0 bytes).")

    @classmethod
    def extract_and_chunk(cls, file_bytes: bytes, filename: str, doc_id: str) -> Tuple[List[Chunk], int]:
        try:
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        except Exception as e:
            raise PDFProcessingError(f"Failed to open/parse PDF '{filename}'. It may be corrupted or encrypted: {str(e)}")

        page_count = len(doc)
        if page_count == 0:
            doc.close()
            raise PDFProcessingError(f"PDF '{filename}' contains 0 pages.")

        all_chunks: List[Chunk] = []
        global_chunk_idx = 0
        total_extracted_text = ""

        for page_num in range(1, page_count + 1):
            page = doc.load_page(page_num - 1)
            raw_text = page.get_text("text")
            clean_text = raw_text.strip()
            total_extracted_text += clean_text

            if not clean_text:
                continue

            # Split text by paragraphs or sections
            paragraphs = [p.strip() for p in clean_text.split("\n\n") if p.strip()]
            
            # If paragraphs are huge, split with sliding window or sentences
            page_chunks_text = []
            for p in paragraphs:
                if len(p) > 900:
                    # Split into ~450 char segments
                    sentences = p.replace(". ", ".\n").split("\n")
                    curr_buf = ""
                    for s in sentences:
                        if len(curr_buf) + len(s) > 600:
                            if curr_buf:
                                page_chunks_text.append(curr_buf.strip())
                            curr_buf = s + " "
                        else:
                            curr_buf += s + " "
                    if curr_buf.strip():
                        page_chunks_text.append(curr_buf.strip())
                else:
                    page_chunks_text.append(p)

            for p_text in page_chunks_text:
                if len(p_text.strip()) < 15:
                    continue
                    
                chunk_id = f"CHK-{doc_id[:8]}-P{page_num}-{global_chunk_idx + 1}"
                approx_tokens = len(p_text.split())
                
                chunk = Chunk(
                    id=chunk_id,
                    document_id=doc_id,
                    filename=filename,
                    page_number=page_num,
                    chunk_index=global_chunk_idx,
                    text=p_text,
                    token_count=approx_tokens
                )
                all_chunks.append(chunk)
                global_chunk_idx += 1

        doc.close()

        if not total_extracted_text.strip():
            raise PDFProcessingError(f"PDF '{filename}' contains no extractable text (might be scanned image without OCR).")

        return all_chunks, page_count

pdf_service = PDFService()
