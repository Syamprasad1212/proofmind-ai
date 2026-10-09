import sqlite3
import json
from typing import Optional, List, Dict, Any
from app.config import settings
from app.models.schemas import DocumentMetadata, DocumentStatus, Chunk

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Documents table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        filename TEXT NOT NULL,
        file_size_bytes INTEGER NOT NULL,
        page_count INTEGER NOT NULL,
        chunk_count INTEGER NOT NULL,
        upload_date TEXT NOT NULL,
        status TEXT NOT NULL,
        sha256_hash TEXT NOT NULL,
        error_message TEXT,
        file_path TEXT NOT NULL
    )
    """)
    
    # Chunks table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chunks (
        id TEXT PRIMARY KEY,
        document_id TEXT NOT NULL,
        filename TEXT NOT NULL,
        page_number INTEGER NOT NULL,
        chunk_index INTEGER NOT NULL,
        text TEXT NOT NULL,
        token_count INTEGER,
        FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
    )
    """)
    
    # Analyses history table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS analyses (
        id TEXT PRIMARY KEY,
        query TEXT NOT NULL,
        evidence_status TEXT NOT NULL,
        response_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)
    
    conn.commit()
    conn.close()

def add_document(doc_meta: DocumentMetadata, file_path: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO documents 
    (id, filename, file_size_bytes, page_count, chunk_count, upload_date, status, sha256_hash, error_message, file_path)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        doc_meta.id,
        doc_meta.filename,
        doc_meta.file_size_bytes,
        doc_meta.page_count,
        doc_meta.chunk_count,
        doc_meta.upload_date,
        doc_meta.status.value,
        doc_meta.sha256_hash,
        doc_meta.error_message,
        file_path
    ))
    conn.commit()
    conn.close()

def get_document_by_hash(sha256_hash: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE sha256_hash = ?", (sha256_hash,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def get_document(doc_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def get_all_documents() -> List[DocumentMetadata]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents ORDER BY upload_date DESC")
    rows = cursor.fetchall()
    conn.close()
    
    docs = []
    for r in rows:
        docs.append(DocumentMetadata(
            id=r["id"],
            filename=r["filename"],
            file_size_bytes=r["file_size_bytes"],
            page_count=r["page_count"],
            chunk_count=r["chunk_count"],
            upload_date=r["upload_date"],
            status=DocumentStatus(r["status"]),
            sha256_hash=r["sha256_hash"],
            error_message=r["error_message"]
        ))
    return docs

def update_document_status(doc_id: str, status: DocumentStatus, chunk_count: Optional[int] = None, error_message: Optional[str] = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if chunk_count is not None:
        cursor.execute("UPDATE documents SET status = ?, chunk_count = ?, error_message = ? WHERE id = ?", 
                       (status.value, chunk_count, error_message, doc_id))
    else:
        cursor.execute("UPDATE documents SET status = ?, error_message = ? WHERE id = ?", 
                       (status.value, error_message, doc_id))
    conn.commit()
    conn.close()

def delete_document(doc_id: str) -> Optional[str]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT file_path FROM documents WHERE id = ?", (doc_id,))
    row = cursor.fetchone()
    file_path = row["file_path"] if row else None
    
    cursor.execute("DELETE FROM chunks WHERE document_id = ?", (doc_id,))
    cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()
    return file_path

def add_chunks(chunks: List[Chunk]):
    conn = get_db_connection()
    cursor = conn.cursor()
    for chk in chunks:
        cursor.execute("""
        INSERT OR REPLACE INTO chunks
        (id, document_id, filename, page_number, chunk_index, text, token_count)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            chk.id,
            chk.document_id,
            chk.filename,
            chk.page_number,
            chk.chunk_index,
            chk.text,
            chk.token_count
        ))
    conn.commit()
    conn.close()

def get_chunks_for_document(doc_id: str) -> List[Chunk]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chunks WHERE document_id = ? ORDER BY page_number ASC, chunk_index ASC", (doc_id,))
    rows = cursor.fetchall()
    conn.close()
    return [Chunk(**dict(r)) for r in rows]

def get_all_chunks() -> List[Chunk]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chunks ORDER BY document_id ASC, page_number ASC, chunk_index ASC")
    rows = cursor.fetchall()
    conn.close()
    return [Chunk(**dict(r)) for r in rows]

def save_analysis(analysis_id: str, query: str, evidence_status: str, response_json: str, created_at: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO analyses (id, query, evidence_status, response_json, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, (analysis_id, query, evidence_status, response_json, created_at))
    conn.commit()
    conn.close()

def get_analysis(analysis_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "id": row["id"],
            "query": row["query"],
            "evidence_status": row["evidence_status"],
            "response": json.loads(row["response_json"]),
            "created_at": row["created_at"]
        }
    return None

def get_document_count() -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM documents")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_chunk_count() -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM chunks")
    count = cursor.fetchone()[0]
    conn.close()
    return count
