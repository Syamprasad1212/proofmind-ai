import type { DocumentMetadata, DocumentDetail, AnalysisResponse, HealthResponse } from './types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Health check failed (${res.status} ${res.statusText})`);
  return res.json();
}

export async function fetchDocuments(): Promise<DocumentMetadata[]> {
  const res = await fetch(`${API_BASE}/documents`);
  if (!res.ok) throw new Error(`Failed to fetch documents (${res.status} ${res.statusText})`);
  return res.json();
}

export async function fetchDocumentDetail(documentId: string): Promise<DocumentDetail> {
  const res = await fetch(`${API_BASE}/documents/${documentId}`);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Failed to fetch document' }));
    throw new Error(errorData.detail || `Failed to fetch document ${documentId}`);
  }
  return res.json();
}

export async function uploadDocuments(files: File[]): Promise<DocumentMetadata[]> {
  const formData = new FormData();
  files.forEach(f => formData.append('files', f));

  const res = await fetch(`${API_BASE}/documents/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(errorData.detail || `Upload failed with status ${res.status}`);
  }

  return res.json();
}

export async function deleteDocument(documentId: string): Promise<{ status: string; message: string }> {
  const res = await fetch(`${API_BASE}/documents/${documentId}`, {
    method: 'DELETE',
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Deletion failed' }));
    throw new Error(errorData.detail || `Failed to delete document ${documentId}`);
  }

  return res.json();
}

export async function loadDemoDocuments(): Promise<DocumentMetadata[]> {
  const res = await fetch(`${API_BASE}/demo/load`, {
    method: 'POST',
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Failed to load demo pack' }));
    throw new Error(errorData.detail || 'Failed to load demo documents');
  }

  return res.json();
}

export async function runAnalysis(
  query: string,
  enableWebResearch: boolean = false,
  documentIds?: string[],
  signal?: AbortSignal
): Promise<AnalysisResponse> {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    signal,
    body: JSON.stringify({
      query,
      enable_web_research: enableWebResearch,
      document_ids: documentIds && documentIds.length > 0 ? documentIds : null,
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Analysis failed' }));
    throw new Error(errorData.detail || `Analysis request failed with status ${res.status}`);
  }

  return res.json();
}
