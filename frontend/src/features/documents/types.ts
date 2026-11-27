export interface DocumentItem {
  id: string;
  workspace_id: string;
  title: string;
  document_version: string;
  size_bytes: number;
  status: 'queued' | 'processing' | 'ready' | 'failed' | 'deleting';
  error_code: string | null;
  page_count: number | null;
  chunk_count: number;
  embedding_model: string | null;
  created_at: string;
  updated_at: string;
}

export interface SourceChunk {
  id: string;
  document_id: string;
  document_version: string;
  document_title: string;
  text: string;
  page_number: number;
  section_title: string | null;
  bbox: null;
  score: number;
}
