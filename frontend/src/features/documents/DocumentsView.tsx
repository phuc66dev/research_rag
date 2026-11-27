import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '../../api/client';
import { documentsApi } from '../../api/documents';
import type { Workspace } from '../../api/types';
import { documentError, statusLabels } from './presentation';
import type { DocumentItem } from './types';
import './documents.css';

interface Props {
  initialWorkspaceId?: string;
  onCreateWorkspace?: () => void;
}

export function DocumentsView({ initialWorkspaceId, onCreateWorkspace }: Props = {}) {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [workspaceId, setWorkspaceId] = useState(initialWorkspaceId || '');
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionError, setActionError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<DocumentItem | null>(null);
  const [revision, setRevision] = useState(0);
  const fileInput = useRef<HTMLInputElement>(null);
  const deleteDialog = useRef<HTMLDialogElement>(null);
  const activeWorkspace = useRef(workspaceId);
  activeWorkspace.current = workspaceId;

  useEffect(() => {
    let active = true;
    setLoading(true);
    api.listWorkspaces().then(items => {
      if (!active) return;
      setWorkspaces(items);
      setWorkspaceId(previous => items.some(item => item.id === previous) ? previous : items[0]?.id || '');
      setError('');
    }).catch(cause => { if (active) setError(documentError(cause)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [revision]);

  useEffect(() => {
    if (!workspaceId) { setDocuments([]); return; }
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    setDocuments([]);
    setLoading(true);
    const load = async () => {
      try {
        const items = await documentsApi.list(workspaceId, controller.signal);
        if (controller.signal.aborted) return;
        setDocuments(items);
        setError('');
        // Poll only real pending jobs. No simulated percentage or stage transitions.
        if (items.some(item => ['queued', 'processing', 'deleting'].includes(item.status))) {
          timer = setTimeout(load, 2000);
        }
      } catch (cause) {
        if (!controller.signal.aborted) setError(documentError(cause));
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    };
    void load();
    return () => { controller.abort(); clearTimeout(timer); };
  }, [workspaceId, revision]);

  useEffect(() => {
    if (pendingDelete && !deleteDialog.current?.open) deleteDialog.current?.showModal();
    if (!pendingDelete) deleteDialog.current?.close();
  }, [pendingDelete]);

  const chooseFile = (chosen: File | undefined) => {
    if (!chosen) return;
    setFile(chosen);
    setActionError(!chosen.name.toLowerCase().endsWith('.pdf') ? 'Bản demo chỉ nhận PDF có văn bản.'
      : chosen.size > 50 * 1024 * 1024 ? 'Tệp vượt quá 50 MiB.' : '');
  };

  const runAction = useCallback(async (action: () => Promise<unknown>, message: string) => {
    setBusy(true); setActionError(''); setNotice('');
    try {
      await action();
      setNotice(message);
      setRevision(value => value + 1);
      return true;
    } catch (cause) { setActionError(documentError(cause)); return false; }
    finally { setBusy(false); }
  }, []);

  return <section className="documents-page" aria-labelledby="documents-title">
    <header><h1 id="documents-title">Tài liệu của tôi</h1>
      <p>Quản lý nguồn học tập theo sổ tay môn học.</p></header>
    <div className="documents-toolbar"><label htmlFor="document-workspace">Môn học</label>
      <select id="document-workspace" value={workspaceId} disabled={busy || !workspaces.length}
        onChange={event => { setWorkspaceId(event.target.value); setNotice(''); setActionError(''); }}>
        {!workspaces.length && <option value="">Chưa có sổ tay</option>}
        {workspaces.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
      </select>
      <button type="button" disabled={busy} onClick={() => setRevision(value => value + 1)}>Tải lại</button>
      {onCreateWorkspace && !!workspaces.length && <button type="button" disabled={busy}
        onClick={onCreateWorkspace}>Tạo sổ tay</button>}
    </div>
    {!loading && !workspaces.length && !error && <div className="document-empty">
      <h2>Chưa có sổ tay</h2><p>Tạo sổ tay môn học trước khi tải tài liệu.</p>
      {onCreateWorkspace && <button type="button" onClick={onCreateWorkspace}>Tạo sổ tay đầu tiên</button>}
    </div>}
    <form className="document-upload" onSubmit={async event => {
      event.preventDefault();
      if (!file || !workspaceId || busy) return;
      const selectedWorkspace = workspaceId;
      if (await runAction(() => documentsApi.upload(selectedWorkspace, file), 'Đã tải tệp. Tài liệu đang chờ xử lý.')) {
        if (activeWorkspace.current === selectedWorkspace) {
          setFile(null);
          if (fileInput.current) fileInput.current.value = '';
        }
      }
    }}>
      <div className="document-dropzone" onDragOver={event => event.preventDefault()}
        onDrop={event => { event.preventDefault(); if (!busy) chooseFile(event.dataTransfer.files[0]); }}>
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true"><path d="M12 16V3m-5 5 5-5 5 5M4 16v5h16v-5" /></svg>
        <label htmlFor="document-upload">Kéo thả PDF vào đây hoặc chọn tệp</label>
        <input ref={fileInput} id="document-upload" type="file" accept=".pdf,application/pdf"
          disabled={busy || !workspaceId} onChange={event => chooseFile(event.target.files?.[0])} />
        <p id="upload-help">PDF có văn bản · Tối đa 50 MiB · Chưa hỗ trợ OCR, DOCX và TXT</p>
        {file && <p className="document-filename">Đã chọn: {file.name}</p>}
      </div>
      <button className="document-primary" type="submit" disabled={busy || !workspaceId || !file
        || !file.name.toLowerCase().endsWith('.pdf') || file.size > 50 * 1024 * 1024}>
        {busy ? 'Đang thực hiện…' : 'Tải tài liệu'}</button>
    </form>
    {(error || actionError) && <div className="document-error" role="alert">{actionError || error}
      {error && <button type="button" onClick={() => setRevision(value => value + 1)}>Thử tải lại</button>}
    </div>}
    {notice && <p role="status">{notice}</p>}
    {loading && <p role="status">Đang tải danh sách tài liệu…</p>}
    {!loading && workspaceId && !documents.length && !error && <div className="document-empty">
      <h2>Chưa có tài liệu</h2><p>Chọn một PDF có văn bản để bắt đầu tạo nguồn tìm kiếm.</p></div>}
    {!!documents.length && <div className="documents-table-wrap"><table>
      <caption>{documents.length} tài liệu trong môn học đã chọn</caption>
      <thead><tr><th scope="col">Tên tài liệu</th><th scope="col">Dung lượng</th>
        <th scope="col">Trạng thái</th><th scope="col">Thao tác</th></tr></thead>
      <tbody>{documents.map(item => <tr key={item.id}>
        <th scope="row"><span className="document-filename" title={item.title}>{item.title}</span>
          {item.page_count !== null && <small>{item.page_count} trang · {item.chunk_count} đoạn</small>}</th>
        <td>{(item.size_bytes / (item.size_bytes < 1024 * 1024 ? 1024 : 1024 * 1024))
          .toLocaleString('vi-VN', { maximumFractionDigits: 2 })} {item.size_bytes < 1024 * 1024 ? 'KiB' : 'MiB'}</td>
        <td><span className={`document-status ${item.status}`}>{statusLabels[item.status]}</span>
          {item.error_code && <small className="document-error-text">{documentError(item.error_code)}</small>}</td>
        <td><div className="document-actions">
          {item.status === 'ready' && <a href={documentsApi.fileUrl(item.id)} target="_blank" rel="noreferrer"
            aria-label={`Mở PDF ${item.title}`}>Mở PDF</a>}
          {item.status === 'failed' && <button disabled={busy} type="button"
            onClick={() => void runAction(() => documentsApi.retry(item.id), 'Đã đưa tài liệu vào hàng đợi thử lại.')}>
            Thử lại</button>}
          <button type="button" disabled={busy} onClick={() => setPendingDelete(item)}
            aria-label={`Xóa ${item.title}`}>Xóa</button>
        </div></td>
      </tr>)}</tbody></table></div>}
    <dialog ref={deleteDialog} className="document-delete-dialog" aria-labelledby="document-delete-title"
      onCancel={event => { if (busy) event.preventDefault(); else setPendingDelete(null); }}
      onClose={() => { if (!busy) setPendingDelete(null); }}>
      <h2 id="document-delete-title">Xóa tài liệu?</h2>
      <p className="document-filename">{pendingDelete?.title}</p>
      <p>Tệp gốc và chỉ mục sẽ bị xóa. Nguồn trong lịch sử sẽ được đánh dấu không còn khả dụng.</p>
      {actionError && <p role="alert" className="document-error-text">{actionError}</p>}
      <div className="document-actions"><button type="button" autoFocus disabled={busy}
        onClick={() => setPendingDelete(null)}>Hủy</button>
      <button type="button" disabled={busy} className="document-danger" onClick={async () => {
        if (!pendingDelete) return;
        if (await runAction(() => documentsApi.delete(pendingDelete.id), 'Đã xóa tài liệu và chỉ mục.')) {
          setPendingDelete(null);
        }
      }}>{busy ? 'Đang xóa…' : 'Xóa tài liệu'}</button></div>
    </dialog>
  </section>;
}
