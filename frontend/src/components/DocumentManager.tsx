import React, { useRef, useState } from 'react';
import { 
  UploadCloud, 
  FileText, 
  Trash2, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  Sparkles, 
  Layers, 
  FolderOpen,
  Eye,
  X
} from 'lucide-react';
import type { DocumentMetadata, DocumentDetail } from '../types';
import { fetchDocumentDetail } from '../api';

interface DocumentManagerProps {
  documents: DocumentMetadata[];
  onUpload: (files: File[]) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  onLoadDemo: () => Promise<void>;
  uploading: boolean;
  loadingDemo: boolean;
}

export const DocumentManager: React.FC<DocumentManagerProps> = ({
  documents,
  onUpload,
  onDelete,
  onLoadDemo,
  uploading,
  loadingDemo,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [inspectingDoc, setInspectingDoc] = useState<DocumentDetail | null>(null);
  const [loadingInspect, setLoadingInspect] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const pdfFiles = Array.from(files).filter(f => f.name.toLowerCase().endsWith('.pdf'));
    if (pdfFiles.length === 0) {
      alert('Please select valid PDF documents (.pdf).');
      return;
    }
    await onUpload(pdfFiles);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this document and remove its indexed passages?')) return;
    setDeletingId(id);
    try {
      await onDelete(id);
      if (inspectingDoc?.id === id) {
        setInspectingDoc(null);
      }
    } finally {
      setDeletingId(null);
    }
  };

  const handleInspect = async (id: string) => {
    setLoadingInspect(id);
    try {
      const detail = await fetchDocumentDetail(id);
      setInspectingDoc(detail);
    } catch (err: any) {
      alert(err.message || 'Failed to inspect document passages');
    } finally {
      setLoadingInspect(null);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-indigo-50 text-indigo-600">
            <Layers className="w-4 h-4" />
          </div>
          <h2 className="font-semibold text-slate-900 text-sm">
            Document Repository & Evidence Sources
          </h2>
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
            {documents.length}
          </span>
        </div>

        <button
          onClick={onLoadDemo}
          disabled={loadingDemo || uploading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-50 text-indigo-700 hover:bg-indigo-100 hover:text-indigo-800 text-xs font-medium transition-colors border border-indigo-200/70 disabled:opacity-50 cursor-pointer"
          title="Load optional fictional scholarship policies and student profiles for testing"
        >
          {loadingDemo ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Sparkles className="w-3.5 h-3.5" />
          )}
          Load Fictional Demo Pack (5 PDFs)
        </button>
      </div>

      {/* Drag and Drop Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragOver(false);
          handleFiles(e.dataTransfer.files);
        }}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-5 text-center transition-all cursor-pointer flex flex-col items-center justify-center gap-2 ${
          isDragOver
            ? 'border-indigo-500 bg-indigo-50/50'
            : 'border-slate-200 hover:border-indigo-400 bg-slate-50/60 hover:bg-slate-50'
        } ${uploading ? 'opacity-60 pointer-events-none' : ''}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,application/pdf"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
        <div className="w-10 h-10 rounded-full bg-white shadow-xs border border-slate-200 flex items-center justify-center text-indigo-600">
          {uploading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <UploadCloud className="w-5 h-5" />
          )}
        </div>
        <div>
          <p className="text-xs font-semibold text-slate-800">
            {uploading ? 'Extracting & Indexing PDFs...' : 'Click or drag PDF files to upload'}
          </p>
          <p className="text-[11px] text-slate-500 mt-0.5">
            PyMuPDF page-by-page text extraction • Max 25MB per PDF
          </p>
        </div>
      </div>

      {/* Uploaded Documents List */}
      {documents.length > 0 ? (
        <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="flex items-center justify-between p-2.5 rounded-xl border border-slate-200/80 bg-white hover:border-slate-300 transition-all text-xs"
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <div className={`p-2 rounded-lg shrink-0 ${
                  doc.status === 'INDEXED'
                    ? 'bg-emerald-50 text-emerald-600'
                    : doc.status === 'PROCESSING'
                    ? 'bg-amber-50 text-amber-600'
                    : 'bg-rose-50 text-rose-600'
                }`}>
                  <FileText className="w-4 h-4" />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5">
                    <p className="font-semibold text-slate-800 truncate" title={doc.filename}>
                      {doc.filename}
                    </p>
                    {doc.filename.includes("Policy_") || doc.filename.includes("Student_Record_") ? (
                      <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-amber-50 text-amber-700 border border-amber-200 shrink-0">
                        Demo
                      </span>
                    ) : null}
                  </div>
                  <div className="flex items-center gap-2 text-[11px] text-slate-500 mt-0.5">
                    <span>{doc.page_count} page{doc.page_count === 1 ? '' : 's'}</span>
                    <span>•</span>
                    <span>{doc.chunk_count} chunk{doc.chunk_count === 1 ? '' : 's'}</span>
                    <span>•</span>
                    <span>{formatBytes(doc.file_size_bytes)}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-1.5 shrink-0 ml-3">
                <button
                  onClick={() => handleInspect(doc.id)}
                  disabled={loadingInspect === doc.id}
                  className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors cursor-pointer"
                  title="View extracted passages and page details"
                >
                  {loadingInspect === doc.id ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Eye className="w-3.5 h-3.5" />
                  )}
                </button>

                {doc.status === 'INDEXED' && (
                  <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 border border-emerald-200/60 px-2 py-0.5 rounded-md">
                    <CheckCircle2 className="w-3 h-3" />
                    Indexed
                  </span>
                )}
                {doc.status === 'ERROR' && (
                  <span className="inline-flex items-center gap-1 text-[11px] font-medium text-rose-700 bg-rose-50 border border-rose-200 px-2 py-0.5 rounded-md" title={doc.error_message || 'Error'}>
                    <AlertCircle className="w-3 h-3" />
                    Failed
                  </span>
                )}
                <button
                  onClick={() => handleDelete(doc.id)}
                  disabled={deletingId === doc.id}
                  className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
                  title="Delete document and erase indexed vectors"
                >
                  {deletingId === doc.id ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Trash2 className="w-3.5 h-3.5" />
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="py-4 text-center border border-dashed border-slate-200 rounded-xl bg-slate-50/50">
          <FolderOpen className="w-6 h-6 text-slate-400 mx-auto mb-1 stroke-1" />
          <p className="text-xs text-slate-500 font-medium">No documents uploaded yet</p>
          <p className="text-[11px] text-slate-400">Upload your PDF files above or click &quot;Load Fictional Demo Pack&quot;.</p>
        </div>
      )}

      {/* Document Detail Modal */}
      {inspectingDoc && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[80vh] flex flex-col shadow-xl border border-slate-200 overflow-hidden">
            <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <div>
                <h3 className="font-bold text-sm text-slate-900">{inspectingDoc.filename}</h3>
                <p className="text-xs text-slate-500">
                  ID: {inspectingDoc.id} • {inspectingDoc.page_count} pages • {inspectingDoc.chunks.length} extracted chunks
                </p>
              </div>
              <button
                onClick={() => setInspectingDoc(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200 cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="p-4 overflow-y-auto space-y-3 flex-1">
              {inspectingDoc.chunks.map((chk, i) => (
                <div key={chk.id || i} className="p-3 rounded-xl border border-slate-200 bg-slate-50/50 text-xs">
                  <div className="flex items-center justify-between text-[11px] font-semibold text-indigo-700 mb-1">
                    <span>Chunk #{chk.chunk_index + 1} (Page {chk.page_number})</span>
                    <span className="text-slate-400 font-mono text-[10px]">{chk.id}</span>
                  </div>
                  <p className="text-slate-800 leading-relaxed font-mono text-[11px]">{chk.text}</p>
                </div>
              ))}
            </div>
            <div className="p-3 border-t border-slate-200 bg-slate-50 text-right">
              <button
                onClick={() => setInspectingDoc(null)}
                className="px-3 py-1.5 rounded-lg bg-slate-200 hover:bg-slate-300 text-xs font-semibold text-slate-700 cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
