import { useEffect, useRef, useState } from 'react';
import { api, ApiError } from '../../api/client';
import { streamChat } from '../../api/chat';
import { documentsApi } from '../../api/documents';
import { DocumentSources } from '../documents/DocumentSources';
import { readySelection } from '../documents/presentation';
import type { DocumentItem } from '../documents/types';
import { historyApi } from '../history/api';
import type { ChatMessage, ChatSession, CitationSource } from '../history/types';
import './study.css';

interface Props {
  workspaceId: string;
  initialSessionId?: string;
  onBack: () => void;
  onOpenDocuments: () => void;
}

function errorMessage(cause: unknown) {
  if (cause instanceof ApiError) {
    if (cause.status === 401) return 'Phiên đăng nhập đã hết hạn. Đăng nhập lại ở tab khác rồi thử tải lại.';
    const detail = cause.detail as { message?: string };
    if (typeof detail?.message === 'string') return detail.message;
  }
  return cause instanceof Error ? cause.message : 'Không tải được dữ liệu. Vui lòng thử lại.';
}

function sessionUrl(workspaceId: string, sessionId: string) {
  const params = new URLSearchParams({ workspace: workspaceId, session: sessionId });
  window.history.replaceState(null, '', `#study?${params}`);
}

export function StudyView({ workspaceId, initialSessionId, onBack, onOpenDocuments }: Props) {
  const [name, setName] = useState('Sổ tay môn học');
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [hasMore, setHasMore] = useState(false);
  const [sessionId, setSessionId] = useState(initialSessionId || '');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState('');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [stage, setStage] = useState('');
  const [revision, setRevision] = useState(0);
  const [source, setSource] = useState<CitationSource | null>(null);
  const [sourceError, setSourceError] = useState('');
  const [pdfUrl, setPdfUrl] = useState('');
  const mounted = useRef(true);
  const pending = useRef(false);
  const stream = useRef<AbortController | null>(null);
  const popup = useRef<HTMLDialogElement>(null);
  const log = useRef<HTMLDivElement>(null);
  const composer = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; stream.current?.abort(); };
  }, []);

  useEffect(() => {
    let active = true;
    setLoading(true); setError('');
    Promise.all([
      api.listWorkspaces(), documentsApi.list(workspaceId),
      historyApi.listWorkspaceSessions(workspaceId),
      initialSessionId ? historyApi.getSessionDetail(initialSessionId) : Promise.resolve(null),
    ]).then(([workspaces, docs, page, detail]) => {
      if (!active) return;
      const workspace = workspaces.find(item => item.id === workspaceId);
      if (!workspace) throw new Error('Không tìm thấy sổ tay môn học.');
      if (detail && detail.workspace_id !== workspaceId) throw new Error('Hội thoại không thuộc sổ tay này.');
      setName(workspace.name); setDocuments(docs); setSessions(page.items); setHasMore(page.hasMore);
      if (detail) {
        setSessionId(detail.id); setMessages(detail.messages);
        const lastQuestion = detail.messages.filter(item => item.role === 'user').at(-1);
        setSelected(readySelection(docs, lastQuestion?.sources.map(item => item.document_id) || []));
      }
    }).catch(cause => { if (active) setError(errorMessage(cause)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [workspaceId, initialSessionId, revision]);

  useEffect(() => {
    const element = log.current;
    if (element && element.scrollHeight - element.scrollTop - element.clientHeight < 220) {
      element.scrollTop = element.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    if (!source) return;
    popup.current?.showModal();
    const controller = new AbortController();
    let localUrl = '';
    setPdfUrl(''); setSourceError('');
    // Fetch first so deleted/private/version-changed sources get a useful error outside the iframe.
    documentsApi.status(source.document_id).then(async item => {
      if (item.status !== 'ready' || item.document_version !== source.document_version) {
        throw new Error('Nguồn đã thay đổi hoặc không còn sẵn sàng.');
      }
      const response = await fetch(documentsApi.fileUrl(item.id), {
        credentials: 'include', signal: controller.signal,
      });
      if (!response.ok) throw new Error('Không mở được nguồn. Tài liệu đã bị xóa hoặc bạn không còn quyền truy cập.');
      const blob = await response.blob();
      if (controller.signal.aborted) return;
      localUrl = URL.createObjectURL(blob);
      setPdfUrl(`${localUrl}#page=${source.page_number || 1}`);
    }).catch(cause => { if (!controller.signal.aborted) setSourceError(errorMessage(cause)); });
    return () => { controller.abort(); if (localUrl) URL.revokeObjectURL(localUrl); };
  }, [source]);

  async function openSession(id: string) {
    if (pending.current) return;
    pending.current = true; setLoading(true); setError('');
    try {
      const detail = id ? await historyApi.getSessionDetail(id) : null;
      if (!mounted.current) return;
      if (detail && detail.workspace_id !== workspaceId) throw new Error('Hội thoại không thuộc sổ tay.');
      setSessionId(id); setMessages(detail?.messages || []); setStage('');
      if (detail) {
        const last = detail.messages.filter(item => item.role === 'user').at(-1);
        setSelected(readySelection(documents, last?.sources.map(item => item.document_id) || []));
      }
      sessionUrl(workspaceId, id);
    } catch (cause) { if (mounted.current) setError(errorMessage(cause)); }
    finally { pending.current = false; if (mounted.current) setLoading(false); }
  }

  async function send() {
    const query = draft.trim();
    const ids = readySelection(documents, selected);
    if (pending.current || loading || !query || query.length > 4000 || !ids.length) return;
    pending.current = true; setBusy(true); setError(''); setStage('Đang gửi câu hỏi…');
    const controller = new AbortController(); stream.current = controller;
    const temporaryId = crypto.randomUUID();
    let optimistic = false;
    let completed = false;
    let currentId = sessionId;
    const updateAnswer = (patch: Partial<ChatMessage>) => {
      if (mounted.current) setMessages(values => values.map(item => item.id === temporaryId ? { ...item, ...patch } : item));
    };
    try {
      if (!currentId) {
        const created = await historyApi.createSession({ workspace_id: workspaceId });
        currentId = created.id;
        if (!mounted.current) return;
        setSessionId(currentId); setSessions(values => [created, ...values]);
        sessionUrl(workspaceId, currentId);
      }
      if (controller.signal.aborted) return;
      const now = new Date().toISOString();
      const base = { session_id: currentId, created_at: now, sources: [], status: 'completed' as const };
      setMessages(values => [...values,
        { ...base, id: crypto.randomUUID(), role: 'user', content: query },
        { ...base, id: temporaryId, role: 'assistant', content: '', status: 'interrupted' },
      ]);
      optimistic = true;
      let answer = '';
      for await (const event of streamChat(currentId, {
        workspace_id: workspaceId, document_ids: ids, query, mode: 'strict',
      }, controller.signal)) {
        if (!mounted.current) return;
        if (event.event === 'status') setStage(event.data.stage === 'retrieving' ? 'Đang tìm nguồn…' : 'AI đang trả lời…');
        if (event.event === 'citations') updateAnswer({ sources: event.data.citations });
        if (event.event === 'token') { answer += event.data.text; updateAnswer({ content: answer }); }
        if (event.event === 'done') { completed = true; updateAnswer({ status: 'completed' }); }
      }
      if (completed && mounted.current) { setDraft(''); setStage('Đã lưu hội thoại.'); }
    } catch (cause) {
      if (mounted.current) {
        updateAnswer({ status: controller.signal.aborted ? 'interrupted' : 'error' });
        setError(controller.signal.aborted ? 'Đã dừng trả lời. Nội dung đã nhận được giữ lại.' : errorMessage(cause));
        setStage('');
      }
    } finally {
      // Reload server truth to avoid duplicating optimistic messages on a failed POST.
      // If the connection is lost, keep received text; never automatically resend.
      if (mounted.current && optimistic && !controller.signal.aborted) {
        try {
          const detail = await historyApi.getSessionDetail(currentId);
          if (mounted.current) setMessages(detail.messages);
        } catch { /* Keep the local transcript until a manual reload. */ }
      }
      if (mounted.current) {
        historyApi.listWorkspaceSessions(workspaceId).then(page => {
          if (mounted.current) { setSessions(page.items); setHasMore(page.hasMore); }
        }).catch(() => {});
        setBusy(false); composer.current?.focus();
      }
      pending.current = false; stream.current = null;
    }
  }

  return <section className="study-page" aria-labelledby="study-title">
    <header className="study-header"><div><button type="button" onClick={onBack}>← Sổ tay môn học</button>
      <h1 id="study-title">{name}</h1></div>
      <button type="button" onClick={() => void openSession('')} disabled={busy || loading}>Hội thoại mới</button></header>
    <div className="study-grid"><aside>
      <DocumentSources documents={documents} selectedIds={selected} onChange={setSelected} loading={loading} />
      <button type="button" onClick={onOpenDocuments}>Quản lý tài liệu</button>
      <button type="button" disabled={busy || loading} onClick={async () => {
        try { const docs = await documentsApi.list(workspaceId); if (mounted.current) { setDocuments(docs); setSelected(readySelection(docs, selected)); } }
        catch (cause) { if (mounted.current) setError(errorMessage(cause)); }
      }}>Tải lại nguồn</button>
    </aside><section className="study-chat" aria-label="Trợ lý AI">
      <div className="study-session-picker"><label htmlFor="study-session">Cuộc hội thoại</label>
        <select id="study-session" value={sessionId} disabled={busy || loading}
          onChange={event => void openSession(event.target.value)}>
          <option value="">Hội thoại mới</option>
          {!!sessionId && !sessions.some(item => item.id === sessionId) && <option value={sessionId}>Hội thoại đang mở</option>}
          {sessions.map(item => <option key={item.id} value={item.id}>{item.title}</option>)}
        </select>
        {hasMore && <button type="button" disabled={busy || loading} onClick={async () => {
          try { const page = await historyApi.listWorkspaceSessions(workspaceId, { offset: sessions.length });
            if (mounted.current) { setSessions(values => [...values, ...page.items]); setHasMore(page.hasMore); }
          } catch (cause) { if (mounted.current) setError(errorMessage(cause)); }
        }}>Tải thêm hội thoại</button>}
      </div>
      <div className="study-messages" ref={log} role="log" aria-label="Tin nhắn" aria-live="off">
        {loading && <p role="status">Đang tải cuộc hội thoại…</p>}
        {!loading && !messages.length && <div className="study-empty"><h2>Hỏi từ tài liệu của bạn</h2>
          <p>Chọn nguồn bên cạnh, sau đó đặt câu hỏi. Câu trả lời và nguồn trích dẫn sẽ được lưu trong lịch sử.</p></div>}
        {messages.map(message => <article key={message.id} className={`study-message ${message.role}`}>
          <strong>{message.role === 'user' ? 'Bạn' : 'Trợ lý AI'}</strong>
          <p>{message.content || (busy ? 'Đang chuẩn bị câu trả lời…' : 'Chưa nhận được nội dung trả lời.')}</p>
          {message.role === 'assistant' && message.status !== 'completed' && <small>
            {message.status === 'error' ? 'Lỗi khi trả lời' : 'Chưa hoàn tất'}
          </small>}
          {message.role === 'assistant' && !!message.sources.length && <div className="study-citations">
            {message.sources.map((citation, index) => <button type="button" key={`${citation.id}-${index}`}
              onClick={() => setSource(citation)}>[{index + 1}] {citation.document_title}{citation.page_number ? ` · Trang ${citation.page_number}` : ''}</button>)}
          </div>}
        </article>)}
      </div>
      <div className="study-feedback"><p role="status">{stage}</p>
        {error && <div role="alert"><p>{error}</p><button type="button" disabled={busy || loading}
          onClick={() => sessionId ? void openSession(sessionId) : setRevision(value => value + 1)}>Tải lại hội thoại</button></div>}</div>
      <form className="study-composer" onSubmit={event => { event.preventDefault(); void send(); }}>
        <label htmlFor="study-question">Câu hỏi của bạn</label>
        <textarea ref={composer} id="study-question" value={draft} maxLength={4000} rows={3} disabled={busy}
          placeholder="Ví dụ: Giải thích khái niệm chính trong bài giảng…"
          onChange={event => setDraft(event.target.value)} onKeyDown={event => {
            if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
              event.preventDefault(); event.currentTarget.form?.requestSubmit();
            }
          }} />
        <p className="study-help">Câu hỏi và đoạn tài liệu liên quan được gửi đến nhà cung cấp AI do backend cấu hình. Kiểm tra nguồn trước khi sử dụng câu trả lời.</p>
        <div className="study-send"><small>{draft.length}/4000 · Shift+Enter để xuống dòng</small>
          {busy ? <button key="stop" type="button" onClick={event => {
            event.preventDefault(); stream.current?.abort();
          }}>Dừng trả lời</button>
            : <button key="send" className="study-primary" type="submit" disabled={loading || !draft.trim() || !readySelection(documents, selected).length}>Gửi câu hỏi</button>}</div>
      </form>
    </section></div>
    <dialog ref={popup} className="study-source-dialog" onClose={() => setSource(null)} aria-labelledby="study-source-title">
      <header><h2 id="study-source-title">{source?.document_title}</h2>
        <button type="button" autoFocus onClick={() => popup.current?.close()}>Đóng nguồn</button></header>
      <p>{source?.page_number ? `Trang ${source.page_number}. ` : ''}Chưa có tọa độ để tô sáng chính xác đoạn trích.</p>
      {!sourceError && <blockquote>{source?.snippet}</blockquote>}
      {sourceError ? <p role="alert">{sourceError}</p> : pdfUrl
        ? <iframe title="Tài liệu PDF nguồn" src={pdfUrl} /> : <p role="status">Đang mở tài liệu…</p>}
    </dialog>
  </section>;
}
