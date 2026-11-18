/** Contract source: contracts/rag.md and contracts/openapi.json. */
export interface Workspace {
  id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
  document_count: number;
}

export interface ChatRequest {
  workspace_id: string;
  document_ids: string[];
  query: string;
  mode?: 'strict';
}

export interface Citation {
  id: string;
  document_id: string;
  document_version: string;
  document_title: string;
  page_number: number;
  snippet: string;
  bbox: [number, number, number, number] | null;
}

export type ChatEvent =
  | { event: 'status'; data: { stage: string; mock?: boolean } }
  | { event: 'citations'; data: { citations: Citation[]; mock?: boolean } }
  | { event: 'token'; data: { text: string } }
  | { event: 'done'; data: { message_id: string; provider: string; mock?: boolean } }
  | { event: 'error'; data: { code: string; message: string } };

export interface Health {
  status: string;
  version: string;
  mode: string;
  rag_ready: boolean;
  mock_chat_enabled: boolean;
}
