import { useEffect, useId, useRef, useState } from 'react';

interface Props {
  name: string;
  disabled: boolean;
  onRename: () => void;
  onDelete: () => void;
}

export function WorkspaceActions({ name, disabled, onRename, onDelete }: Props) {
  const [open, setOpen] = useState(false);
  const wrapper = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const menu = useRef<HTMLDivElement>(null);
  const menuId = useId();

  useEffect(() => {
    if (!open) return;
    menu.current?.querySelector<HTMLButtonElement>('button')?.focus();
    const outside = (event: PointerEvent) => {
      if (!wrapper.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener('pointerdown', outside);
    return () => document.removeEventListener('pointerdown', outside);
  }, [open]);

  return <div ref={wrapper} className="workspace-menu" onBlur={event => {
    if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setOpen(false);
  }}>
    <button ref={trigger} type="button" className="workspace-icon-button"
      disabled={disabled} aria-label={`Tùy chọn sổ tay ${name}`} aria-haspopup="menu"
      aria-expanded={open} aria-controls={open ? menuId : undefined}
      onClick={() => setOpen(value => !value)} onKeyDown={event => {
        if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
          event.preventDefault(); setOpen(true);
        }
      }}>
      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
        <circle cx="5" cy="12" r="1.5" /><circle cx="12" cy="12" r="1.5" /><circle cx="19" cy="12" r="1.5" />
      </svg>
    </button>
    {open && <div ref={menu} id={menuId} role="menu" aria-label={`Thao tác với ${name}`}
      className="workspace-menu-items" onKeyDown={event => {
        const items = Array.from(menu.current?.querySelectorAll<HTMLButtonElement>('button') || []);
        const index = items.indexOf(document.activeElement as HTMLButtonElement);
        if (event.key === 'Escape') {
          event.preventDefault(); event.stopPropagation(); setOpen(false); trigger.current?.focus();
        } else if (['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) {
          event.preventDefault();
          const next = event.key === 'Home' ? 0 : event.key === 'End' ? items.length - 1
            : (index + (event.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length;
          items[next]?.focus();
        }
      }}>
      <button type="button" role="menuitem" onClick={() => {
        setOpen(false); trigger.current?.focus(); onRename();
      }}>Đổi tên</button>
      <button type="button" role="menuitem" className="workspace-danger" onClick={() => {
        setOpen(false); trigger.current?.focus(); onDelete();
      }}>Xóa sổ tay</button>
    </div>}
  </div>;
}
