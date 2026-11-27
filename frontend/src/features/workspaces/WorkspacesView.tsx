import { useEffect, useRef, useState } from 'react';
import { api } from '../../api/client';
import type { Workspace } from '../../api/types';
import { visibleWorkspaces, workspaceError, workspaceNameError } from './presentation';
import type { WorkspaceSort } from './presentation';
import { WorkspaceActions } from './WorkspaceActions';
import './workspaces.css';

interface Props {
  startCreating?: boolean;
  onOpenDocuments: (workspaceId: string) => void;
  onOpenStudy: (workspaceId: string) => void;
}

type WorkspaceDialog = { kind: 'rename' | 'delete'; workspace: Workspace };

function BookIcon() {
  return <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor"
    strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M12 5C9 3 5 3 2 4v15c3-1 7-1 10 1 3-2 7-2 10-1V4c-3-1-7-1-10 1Zm0 0v15" />
  </svg>;
}

function RequestError({ message, expired }: { message: string; expired?: boolean }) {
  return <div className="workspace-error" role="alert">{message}
    {expired && <a href="/" target="_blank" rel="noreferrer">Mở trang đăng nhập ở tab khác</a>}
  </div>;
}

export function WorkspacesView({ startCreating = false, onOpenDocuments, onOpenStudy }: Props) {
  const [items, setItems] = useState<Workspace[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [error, setError] = useState('');
  const [expired, setExpired] = useState(false);
  const [revision, setRevision] = useState(0);
  const [query, setQuery] = useState('');
  const [sort, setSort] = useState<WorkspaceSort>('updated');
  const [creating, setCreating] = useState(startCreating);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [nameError, setNameError] = useState('');
  const [dialog, setDialog] = useState<WorkspaceDialog | null>(null);
  const [rename, setRename] = useState('');
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  const pending = useRef(false);
  const dataVersion = useRef(0);
  const mounted = useRef(true);
  const nameInput = useRef<HTMLInputElement>(null);
  const renameInput = useRef<HTMLInputElement>(null);
  const modal = useRef<HTMLDialogElement>(null);
  const pageTitle = useRef<HTMLHeadingElement>(null);
  const createButton = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);

  useEffect(() => {
    let active = true;
    const requestedVersion = dataVersion.current;
    setLoading(true); setLoadError('');
    api.listWorkspaces().then(values => {
      if (active && requestedVersion === dataVersion.current) { setItems(values); setExpired(false); }
    }).catch(cause => {
      if (active && requestedVersion === dataVersion.current) {
        setLoadError(workspaceError(cause));
        setExpired(cause?.status === 401);
      }
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [revision]);

  useEffect(() => {
    if (creating) nameInput.current?.focus();
  }, [creating]);

  useEffect(() => {
    if (dialog && !modal.current?.open) modal.current?.showModal();
    if (!dialog && modal.current?.open) modal.current.close();
  }, [dialog]);

  const resetError = () => { setError(''); setNameError(''); setExpired(false); };

  const beginCreate = () => {
    resetError(); setNotice(''); setCreating(true);
  };

  const closeCreate = () => {
    if (pending.current) return;
    setCreating(false); resetError();
    requestAnimationFrame(() => createButton.current?.focus());
  };

  const closeDialog = () => {
    if (pending.current) return;
    setDialog(null); resetError();
  };

  const runMutation = async (action: () => Promise<void>) => {
    if (pending.current) return;
    pending.current = true; setBusy(true); setError(''); setExpired(false);
    try { await action(); }
    catch (cause) {
      if (mounted.current) {
        setError(workspaceError(cause));
        setExpired((cause as { status?: number })?.status === 401);
      }
    } finally {
      pending.current = false;
      if (mounted.current) setBusy(false);
    }
  };

  const filtered = visibleWorkspaces(items, query, sort);

  return <section className="workspaces-page" aria-labelledby="workspaces-title">
    {creating ? <>
      <button className="workspace-back" type="button" disabled={busy} onClick={closeCreate}>
        <span aria-hidden="true">←</span> Sổ tay môn học
      </button>
      <header><h1 id="workspaces-title">Tạo sổ tay môn học</h1>
        <p>Đặt tên môn học để gom tài liệu vào một nơi.</p></header>
      <form className="workspace-create-form" aria-busy={busy} noValidate onSubmit={event => {
        event.preventDefault();
        if (pending.current) return;
        const invalid = workspaceNameError(name);
        setNameError(invalid);
        if (invalid) { nameInput.current?.focus(); return; }
        void runMutation(async () => {
          const created = await api.createWorkspace(name.trim(), description.trim());
          if (!mounted.current) return;
          dataVersion.current += 1;
          setLoadError('');
          setItems(previous => [created, ...previous.filter(item => item.id !== created.id)]);
          setQuery(''); setSort('updated'); setName(''); setDescription('');
          setCreating(false); setNotice(`Đã tạo sổ tay “${created.name}”. Chọn Thêm tài liệu để tải PDF.`);
          requestAnimationFrame(() => pageTitle.current?.focus());
        });
      }}>
        <label htmlFor="workspace-name">Tên môn học <span aria-hidden="true">*</span></label>
        <input ref={nameInput} id="workspace-name" name="name" type="text" value={name}
          maxLength={100} required disabled={busy} autoComplete="off" placeholder="Ví dụ: Cơ sở dữ liệu"
          aria-invalid={!!nameError} aria-describedby={nameError ? 'workspace-name-error' : 'workspace-name-help'}
          onChange={event => { setName(event.target.value); setNameError(''); }} />
        {nameError ? <p id="workspace-name-error" className="workspace-field-error" role="alert">{nameError}</p>
          : <p id="workspace-name-help" className="workspace-help">Bắt buộc · Tối đa 100 ký tự</p>}
        <label htmlFor="workspace-description">Mô tả <span className="workspace-optional">(tùy chọn)</span></label>
        <textarea id="workspace-description" name="description" value={description} maxLength={500}
          rows={4} disabled={busy} placeholder="Nội dung môn học, học kỳ hoặc mục tiêu học tập…"
          aria-describedby="workspace-description-count" onChange={event => setDescription(event.target.value)} />
        <p id="workspace-description-count" className="workspace-help workspace-character-count">{description.length}/500 ký tự</p>
        {error && <RequestError message={error} expired={expired} />}
        <div className="workspace-form-actions">
          <button type="button" disabled={busy} onClick={closeCreate}>Hủy</button>
          <button className="workspace-primary" type="submit" disabled={busy}>
            {busy ? 'Đang tạo sổ tay…' : 'Tạo sổ tay'}</button>
        </div>
      </form>
    </> : <>
      <header className="workspace-page-header"><div>
        <h1 id="workspaces-title" ref={pageTitle} tabIndex={-1}>Sổ tay môn học</h1>
        <p>Tổ chức tài liệu theo từng môn học của bạn.</p>
      </div><button ref={createButton} type="button" className="workspace-primary" disabled={busy}
        onClick={beginCreate}><span aria-hidden="true">＋</span> Tạo sổ tay</button></header>
      <div className="workspace-toolbar">
        <div className="workspace-search"><label htmlFor="workspace-search">Tìm sổ tay</label>
          <input id="workspace-search" type="search" value={query} placeholder="Tìm theo tên hoặc mô tả…"
            onChange={event => setQuery(event.target.value)} /></div>
        <div><label htmlFor="workspace-sort">Sắp xếp</label>
          <select id="workspace-sort" value={sort} onChange={event => setSort(event.target.value as WorkspaceSort)}>
            <option value="updated">Cập nhật gần nhất</option><option value="name">Tên môn A–Z</option>
          </select></div>
        <button type="button" disabled={busy || loading} onClick={() => {
          setError(''); setNotice(''); setRevision(value => value + 1);
        }}>Tải lại</button>
      </div>
      {notice && <p className="workspace-notice" role="status">{notice}</p>}
      {loadError && <RequestError message={loadError} expired={expired} />}
      {loadError && <button type="button" disabled={loading} onClick={() => setRevision(value => value + 1)}>Thử tải lại</button>}
      {error && !dialog && <RequestError message={error} expired={expired} />}
      {loading && <p role="status" className="workspace-loading">Đang tải sổ tay môn học…</p>}
      {!loading && !loadError && !items.length && <div className="workspace-empty">
        <div className="workspace-book-icon"><BookIcon /></div>
        <h2>Bắt đầu với môn học đầu tiên</h2>
        <p>Tạo một sổ tay, sau đó thêm PDF bài giảng và giáo trình của môn học.</p>
        <button type="button" className="workspace-primary" onClick={beginCreate}>Tạo sổ tay đầu tiên</button>
      </div>}
      {!loading && !loadError && !!items.length && !filtered.length && <div className="workspace-empty">
        <h2>Không tìm thấy sổ tay</h2><p>Thử tên môn hoặc từ khóa khác.</p>
        <button type="button" onClick={() => setQuery('')}>Xóa bộ lọc tìm kiếm</button>
      </div>}
      {!!filtered.length && <>
        <p className="workspace-result-count">{filtered.length} sổ tay{query.trim() ? ' phù hợp' : ''}</p>
        <ul className="workspace-list" aria-label="Danh sách sổ tay môn học" aria-busy={loading}>
          {filtered.map(item => <li key={item.id} className="workspace-card">
            <div className="workspace-book-icon"><BookIcon /></div>
            <div className="workspace-card-content"><h2>{item.name}</h2>
              {item.description && <p className="workspace-description">{item.description}</p>}
              <div className="workspace-metadata"><span>{item.document_count} tài liệu</span>
                <span>Cập nhật <time dateTime={item.updated_at}>{new Date(item.updated_at)
                  .toLocaleString('vi-VN', { dateStyle: 'short', timeStyle: 'short' })}</time></span></div>
            </div>
            <div className="workspace-card-actions"><button type="button" className="workspace-primary" disabled={busy}
              onClick={() => onOpenStudy(item.id)} aria-label={`Hỏi AI trong ${item.name}`}>Hỏi AI</button>
              <button type="button" disabled={busy}
              aria-label={`Thêm tài liệu vào ${item.name}`} onClick={() => onOpenDocuments(item.id)}>Thêm tài liệu</button>
              <WorkspaceActions name={item.name} disabled={busy} onRename={() => {
                resetError(); setRename(item.name); setDialog({ kind: 'rename', workspace: item });
              }} onDelete={() => {
                resetError(); setDialog({ kind: 'delete', workspace: item });
              }} />
            </div>
          </li>)}
        </ul>
      </>}
    </>}
    <dialog ref={modal} className="workspace-dialog" aria-labelledby="workspace-dialog-title"
      aria-describedby="workspace-dialog-description" onCancel={event => {
        if (pending.current) event.preventDefault(); else closeDialog();
      }} onClose={closeDialog}>
      {dialog && <form noValidate aria-busy={busy} onSubmit={event => {
        event.preventDefault();
        if (pending.current) return;
        if (dialog.kind === 'rename') {
          const invalid = workspaceNameError(rename);
          setNameError(invalid);
          if (invalid) { renameInput.current?.focus(); return; }
        }
        const target = dialog.workspace;
        void runMutation(async () => {
          if (dialog.kind === 'rename') {
            const updated = await api.renameWorkspace(target.id, rename.trim());
            if (!mounted.current) return;
            dataVersion.current += 1;
            setItems(previous => previous.map(item => item.id === target.id ? updated : item));
            setNotice(`Đã đổi tên sổ tay thành “${updated.name}”.`);
          } else {
            await api.deleteWorkspace(target.id);
            if (!mounted.current) return;
            dataVersion.current += 1;
            setItems(previous => previous.filter(item => item.id !== target.id));
            setNotice(`Đã xóa sổ tay “${target.name}” cùng tài liệu và lịch sử.`);
            requestAnimationFrame(() => pageTitle.current?.focus());
          }
          setDialog(null);
        });
      }}>
        <h2 id="workspace-dialog-title">{dialog.kind === 'rename' ? 'Đổi tên sổ tay' : 'Xóa sổ tay?'}</h2>
        <p id="workspace-dialog-description">{dialog.kind === 'rename' ? 'Cập nhật tên môn học của bạn.'
          : `Sổ tay “${dialog.workspace.name}”, các tệp tài liệu, chỉ mục tìm kiếm và lịch sử hội thoại sẽ bị xóa. Không thể hoàn tác.`}</p>
        {dialog.kind === 'rename' && <>
          <label htmlFor="workspace-rename">Tên môn học</label>
          <input autoFocus ref={renameInput} id="workspace-rename" value={rename} maxLength={100}
            required disabled={busy} aria-invalid={!!nameError}
            aria-describedby={nameError ? 'workspace-rename-error' : undefined}
            onChange={event => { setRename(event.target.value); setNameError(''); }} />
          {nameError && <p id="workspace-rename-error" className="workspace-field-error" role="alert">{nameError}</p>}
        </>}
        {error && <RequestError message={error} expired={expired} />}
        <div className="workspace-form-actions">
          <button autoFocus={dialog.kind === 'delete'} type="button" disabled={busy} onClick={closeDialog}>Hủy</button>
          <button type="submit" disabled={busy} className={dialog.kind === 'delete' ? 'workspace-danger-button' : 'workspace-primary'}>
            {busy ? 'Đang lưu…' : dialog.kind === 'rename' ? 'Lưu tên' : 'Xóa sổ tay'}</button>
        </div>
      </form>}
    </dialog>
  </section>;
}
