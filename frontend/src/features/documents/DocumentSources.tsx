import type { DocumentItem } from './types';
import { readySelection, statusLabels } from './presentation';
import './documents.css';

interface Props {
  documents: DocumentItem[];
  selectedIds: string[];
  onChange: (ids: string[]) => void;
  loading?: boolean;
  error?: string;
  onRetry?: () => void;
}

/** Controlled source picker for Phúc. Parent owns loading and the request source snapshot. */
export function DocumentSources({ documents, selectedIds, onChange, loading, error, onRetry }: Props) {
  const selected = readySelection(documents, selectedIds);
  const ready = documents.filter(item => item.status === 'ready');
  return <section className="document-sources" aria-label="Nguồn tài liệu" aria-busy={loading}>
    <h2>Nguồn tài liệu</h2>
    <p aria-live="polite">Đang chọn {selected.length} nguồn</p>
    {loading && <p role="status">Đang tải nguồn…</p>}
    {error && <p role="alert">{error} {onRetry && <button onClick={onRetry}>Thử lại</button>}</p>}
    {!loading && !error && !documents.length && <p>Chưa có tài liệu. Hãy tải PDF ở Tài liệu của tôi.</p>}
    {!!ready.length && <button type="button" onClick={() => onChange(
      selected.length === ready.length ? [] : ready.map(item => item.id)
    )}>{selected.length === ready.length ? 'Bỏ chọn tất cả' : 'Chọn tất cả nguồn sẵn sàng'}</button>}
    {documents.map(item => <label key={item.id} className="source-choice">
      <input type="checkbox" checked={selected.includes(item.id)} disabled={item.status !== 'ready'}
        onChange={event => onChange(event.target.checked ? [...selected, item.id]
          : selected.filter(value => value !== item.id))} />
      <span>{item.title}<small>{statusLabels[item.status]}</small></span>
    </label>)}
  </section>;
}
