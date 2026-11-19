import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { api } from '../../api/client';
import type { Workspace } from '../../api/types';
import { historyApi } from './api';
import type { ChatSession } from './types';

interface HistoryViewProps {
  onOpenSession?: (workspaceId: string, sessionId: string, sessionTitle: string) => void;
}

function formatRelativeTime(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffMin = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMin / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMin < 1) return 'Vừa xong';
    if (diffMin < 60) return `${diffMin} phút trước`;
    if (diffHours < 24) return `${diffHours} giờ trước`;
    if (diffDays === 1) return 'Hôm qua';
    if (diffDays < 7) return `${diffDays} ngày trước`;
    return d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });
  } catch {
    return dateStr;
  }
}

function removeVietnameseTones(str: string): string {
  if (!str) return '';
  return str
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[đĐ]/g, 'd')
    .toLowerCase()
    .trim();
}

type TimelineGroupKey = 'Hôm nay' | 'Hôm qua' | '7 ngày trước' | 'Cũ hơn';

function getTimelineGroup(dateStr: string): TimelineGroupKey {
  try {
    const d = new Date(dateStr);
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const sevenDaysAgo = new Date(today);
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

    if (d >= today) return 'Hôm nay';
    if (d >= yesterday) return 'Hôm qua';
    if (d >= sevenDaysAgo) return '7 ngày trước';
    return 'Cũ hơn';
  } catch {
    return 'Cũ hơn';
  }
}

const PAGE_SIZE = 20;

export const HistoryView: React.FC<HistoryViewProps> = ({ onOpenSession }) => {
  // Data state
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [totalSessions, setTotalSessions] = useState<number>(0);
  const [hasMore, setHasMore] = useState<boolean>(false);
  const [isLoadingMore, setIsLoadingMore] = useState<boolean>(false);

  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Status state
  const [isInitialLoading, setIsInitialLoading] = useState<boolean>(true);
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Modals state
  const [deletingSession, setDeletingSession] = useState<ChatSession | null>(null);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);

  const [renamingSession, setRenamingSession] = useState<ChatSession | null>(null);
  const [newTitle, setNewTitle] = useState<string>('');
  const [isRenaming, setIsRenaming] = useState<boolean>(false);

  const [isCreatingModal, setIsCreatingModal] = useState<boolean>(false);
  const [createWorkspaceId, setCreateWorkspaceId] = useState<string>('');
  const [createTitle, setCreateTitle] = useState<string>('Hội thoại mới');
  const [isCreating, setIsCreating] = useState<boolean>(false);

  // Load workspaces once on mount
  useEffect(() => {
    async function fetchWorkspaces() {
      try {
        const wsList = await api.listWorkspaces();
        setWorkspaces(wsList);
        if (wsList.length > 0) {
          setCreateWorkspaceId(wsList[0].id);
        }
      } catch (err) {
        console.warn('Không thể tải danh sách sổ tay môn học:', err);
      }
    }
    fetchWorkspaces();
  }, []);

  // Workspace dictionary for fast name lookup
  const workspaceMap = useMemo(() => {
    const map = new Map<string, string>();
    for (const ws of workspaces) {
      map.set(ws.id, ws.name);
    }
    return map;
  }, [workspaces]);

  // Load sessions from API (smooth: skeleton only on initial mount, inline indicator during search)
  const isFirstLoadRef = useRef(true);

  const loadSessions = useCallback(async () => {
    if (isFirstLoadRef.current) {
      setIsInitialLoading(true);
    } else {
      setIsSearching(true);
    }
    setError(null);
    try {
      const res = await historyApi.listAllSessions({
        workspaceId: selectedWorkspaceId !== 'all' ? selectedWorkspaceId : undefined,
        query: searchQuery.trim() || undefined,
        limit: PAGE_SIZE,
        offset: 0,
      });
      setSessions(res.items);
      setTotalSessions(res.total);
      setHasMore(res.hasMore);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Không thể tải lịch sử trò chuyện.');
    } finally {
      setIsInitialLoading(false);
      setIsSearching(false);
      isFirstLoadRef.current = false;
    }
  }, [selectedWorkspaceId, searchQuery]);

  // Handle Load More (Pagination)
  const handleLoadMore = async () => {
    if (isLoadingMore || !hasMore) return;
    setIsLoadingMore(true);
    try {
      const res = await historyApi.listAllSessions({
        workspaceId: selectedWorkspaceId !== 'all' ? selectedWorkspaceId : undefined,
        query: searchQuery.trim() || undefined,
        limit: PAGE_SIZE,
        offset: sessions.length,
      });
      setSessions((prev) => [...prev, ...res.items]);
      setTotalSessions(res.total);
      setHasMore(res.hasMore);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Không thể tải thêm cuộc trò chuyện cũ.');
    } finally {
      setIsLoadingMore(false);
    }
  };

  // Debounced search / filter reload (300ms)
  useEffect(() => {
    const timer = setTimeout(() => {
      loadSessions();
    }, isFirstLoadRef.current ? 0 : 300);
    return () => clearTimeout(timer);
  }, [loadSessions]);

  // Client-side instant filter: supports Vietnamese diacritic-insensitive and case-insensitive search
  const filteredSessions = useMemo(() => {
    if (!searchQuery.trim()) return sessions;
    const normQuery = removeVietnameseTones(searchQuery);
    const queryWords = normQuery.split(/\s+/).filter(Boolean);
    return sessions.filter((s) => {
      const normTitle = removeVietnameseTones(s.title);
      const wsName = workspaceMap.get(s.workspace_id) || '';
      const normWs = removeVietnameseTones(wsName);
      return (
        normTitle.includes(normQuery) ||
        normWs.includes(normQuery) ||
        (queryWords.length > 0 && queryWords.every((w) => normTitle.includes(w) || normWs.includes(w)))
      );
    });
  }, [sessions, searchQuery, workspaceMap]);

  // Group filtered sessions by timeline
  const groupedSessions = useMemo(() => {
    const groups: Record<TimelineGroupKey, ChatSession[]> = {
      'Hôm nay': [],
      'Hôm qua': [],
      '7 ngày trước': [],
      'Cũ hơn': [],
    };
    for (const session of filteredSessions) {
      const groupKey = getTimelineGroup(session.updated_at);
      groups[groupKey].push(session);
    }
    return groups;
  }, [filteredSessions]);

  // Total messages count across filtered sessions
  const totalMessagesCount = useMemo(() => {
    return filteredSessions.reduce((acc, s) => acc + (s.message_count || 0), 0);
  }, [filteredSessions]);

  // Handle Opening Session (Navigates to Workspace)
  const handleOpenClick = (session: ChatSession) => {
    if (onOpenSession) {
      onOpenSession(session.workspace_id, session.id, session.title);
    } else {
      alert(`Chuyển đến Sổ tay môn học để tiếp tục hội thoại: "${session.title}"`);
    }
  };

  // Handle Delete Session
  const handleDeleteConfirm = async () => {
    if (!deletingSession) return;
    setIsDeleting(true);
    try {
      await historyApi.deleteSession(deletingSession.id);
      setDeletingSession(null);
      await loadSessions();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Không thể xóa cuộc trò chuyện.');
    } finally {
      setIsDeleting(false);
    }
  };

  // Handle Rename Session
  const handleRenameConfirm = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!renamingSession || !newTitle.trim()) return;
    setIsRenaming(true);
    try {
      const updated = await historyApi.renameSession(renamingSession.id, newTitle.trim());
      setRenamingSession(null);
      setSessions((prev) =>
        prev.map((s) => (s.id === updated.id ? { ...s, title: updated.title, updated_at: updated.updated_at } : s))
      );
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Không thể đổi tên cuộc trò chuyện.');
    } finally {
      setIsRenaming(false);
    }
  };

  // Handle Create New Session
  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createWorkspaceId) {
      alert('Vui lòng chọn một sổ tay môn học để tạo cuộc trò chuyện.');
      return;
    }
    setIsCreating(true);
    try {
      const created = await historyApi.createSession({
        workspace_id: createWorkspaceId,
        title: createTitle.trim() || 'Hội thoại mới',
      });
      setIsCreatingModal(false);
      setCreateTitle('Hội thoại mới');
      // Navigate directly into the newly created session in the workspace!
      if (onOpenSession) {
        onOpenSession(created.workspace_id, created.id, created.title);
      } else {
        await loadSessions();
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Không thể tạo cuộc trò chuyện mới.');
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="history-page-dashboard">
      {/* TOP HEADER & CONTROLS */}
      <header className="history-dash-header">
        <div className="history-dash-title-block">
          <div className="history-icon-badge">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 11a9 9 0 1 1 2.5 7M3 4v7h7M12 7v5l3 2" />
            </svg>
          </div>
          <div>
            <h2 className="history-dash-title">Lịch sử hỏi AI</h2>
            <p className="history-dash-desc">
              Quản lý các cuộc trò chuyện học thuật. Nhấn vào một phiên để tiếp tục hỏi đáp trong Sổ tay môn học tương ứng.
            </p>
          </div>
        </div>

        {/* Action Button: Create New */}
        <button
          type="button"
          className="btn-dash-create"
          onClick={() => setIsCreatingModal(true)}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          <span>Bắt đầu hội thoại mới</span>
        </button>
      </header>

      {/* STATS & FILTER BAR */}
      <div className="history-dash-bar">
        {/* Stats Pill */}
        <div className="history-stats-pill">
          <span className="stats-metric">
            <strong>{searchQuery ? filteredSessions.length : (totalSessions || filteredSessions.length)}</strong> phiên hội thoại
          </span>
          <span className="stats-divider">·</span>
          <span className="stats-metric">
            <strong>{totalMessagesCount}</strong> lượt hỏi đáp
          </span>
        </div>

        {/* Filter inputs */}
        <div className="history-filters-group">
          {/* Search box */}
          <div className="history-search-input-box">
            {isSearching ? (
              <div className="search-loading-spinner" aria-label="Đang tìm kiếm..." />
            ) : (
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="search-ico">
                <circle cx="11" cy="11" r="8"></circle>
                <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              </svg>
            )}
            <input
              type="text"
              placeholder="Tìm kiếm câu hỏi, chủ đề..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="dash-search-input"
            />
            {searchQuery && (
              <button
                type="button"
                className="dash-clear-search-btn"
                onClick={() => setSearchQuery('')}
                aria-label="Xóa tìm kiếm"
              >
                ✕
              </button>
            )}
          </div>

          {/* Workspace select */}
          <select
            value={selectedWorkspaceId}
            onChange={(e) => setSelectedWorkspaceId(e.target.value)}
            className="dash-workspace-filter"
            aria-label="Lọc theo môn học"
          >
            <option value="all">Tất cả môn học ({workspaces.length})</option>
            {workspaces.map((ws) => (
              <option key={ws.id} value={ws.id}>
                {ws.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* CONTENT LIST */}
      <div className="history-dash-content">
        {isInitialLoading ? (
          <div className="history-dash-skeleton-list">
            <div className="dash-skeleton-row" />
            <div className="dash-skeleton-row" />
            <div className="dash-skeleton-row" />
            <div className="dash-skeleton-row" />
          </div>
        ) : error ? (
          <div className="history-dash-error">
            <span>⚠️</span>
            <p>{error}</p>
            <button type="button" onClick={loadSessions} className="btn-dash-retry">
              Thử lại
            </button>
          </div>
        ) : filteredSessions.length === 0 ? (
          <div className="history-dash-empty">
            <div className="empty-book-icon">
              <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#7CA0C8" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"></path>
                <path d="M8 7h6"></path>
                <path d="M8 11h8"></path>
              </svg>
            </div>
            <h3>{searchQuery ? 'Không tìm thấy cuộc trò chuyện phù hợp' : 'Chưa có cuộc trò chuyện nào'}</h3>
            <p>
              {searchQuery
                ? 'Hãy thử tìm kiếm với từ khóa khác hoặc bỏ chọn bộ lọc môn học.'
                : 'Hãy bắt đầu một cuộc trò chuyện trong Sổ tay môn học. Toàn bộ câu hỏi và trích dẫn sẽ được lưu trữ tại đây.'}
            </p>
            {!searchQuery && (
              <button
                type="button"
                className="btn-dash-start-first"
                onClick={() => setIsCreatingModal(true)}
              >
                + Bắt đầu phiên đầu tiên
              </button>
            )}
          </div>
        ) : (
          <div className="history-dash-timeline-container">
            {(['Hôm nay', 'Hôm qua', '7 ngày trước', 'Cũ hơn'] as TimelineGroupKey[]).map((groupKey) => {
              const items = groupedSessions[groupKey];
              if (items.length === 0) return null;

              return (
                <section key={groupKey} className="dash-timeline-section">
                  <h3 className="dash-group-header">
                    <span className="group-header-text">{groupKey}</span>
                    <span className="group-header-badge">{items.length}</span>
                  </h3>

                  <div className="dash-sessions-list">
                    {items.map((session) => {
                      const wsName = workspaceMap.get(session.workspace_id) || 'Sổ tay môn học';

                      return (
                        <div
                          key={session.id}
                          className="dash-session-row"
                          onClick={() => handleOpenClick(session)}
                          role="button"
                          tabIndex={0}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                              handleOpenClick(session);
                            }
                          }}
                        >
                          <div className="row-left-content">
                            <div className="row-chat-icon" aria-hidden="true">
                              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                              </svg>
                            </div>
                            <div className="row-info-col">
                              <h4 className="row-title-text" title={session.title}>
                                {session.title}
                              </h4>
                              <div className="row-meta-line">
                                <span className="row-ws-badge" title={wsName}>
                                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
                                    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
                                  </svg>
                                  {wsName}
                                </span>
                                <span className="row-dot-sep">·</span>
                                <span className="row-meta-subtext">
                                  {session.message_count === 0 ? 'Chưa có tin nhắn' : `${session.message_count} tin nhắn`}
                                </span>
                              </div>
                            </div>
                          </div>

                          <div className="row-right-content">
                            <span className="row-time-text">
                              {formatRelativeTime(session.updated_at)}
                            </span>

                            {/* Actions Buttons */}
                            <div className="row-actions-group" onClick={(e) => e.stopPropagation()}>
                              <button
                                type="button"
                                className="dash-action-icon-btn rename"
                                title="Đổi tên cuộc trò chuyện"
                                onClick={() => {
                                  setRenamingSession(session);
                                  setNewTitle(session.title);
                                }}
                              >
                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                                </svg>
                              </button>
                              <button
                                type="button"
                                className="dash-action-icon-btn delete"
                                title="Xóa cuộc trò chuyện"
                                onClick={() => setDeletingSession(session)}
                              >
                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                  <polyline points="3 6 5 6 21 6"></polyline>
                                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                </svg>
                              </button>
                            </div>

                            <div className="row-open-indicator" title="Mở trong Sổ tay môn học">
                              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                                <line x1="5" y1="12" x2="19" y2="12"></line>
                                <polyline points="12 5 19 12 12 19"></polyline>
                              </svg>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </section>
              );
            })}

            {/* Pagination Controls */}
            {hasMore && (
              <div className="dash-pagination-wrap">
                <button
                  type="button"
                  className="btn-dash-load-more"
                  onClick={handleLoadMore}
                  disabled={isLoadingMore}
                  aria-label="Tải thêm hội thoại cũ hơn"
                >
                  {isLoadingMore ? (
                    <>
                      <span className="load-more-spinner" aria-hidden="true" />
                      <span>Đang tải thêm...</span>
                    </>
                  ) : (
                    <>
                      <span>Tải thêm hội thoại cũ hơn</span>
                      <span className="load-more-count">
                        ({sessions.length} / {totalSessions})
                      </span>
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="6 9 12 15 18 9"></polyline>
                      </svg>
                    </>
                  )}
                </button>
              </div>
            )}

            {!hasMore && sessions.length > 0 && (
              <div className="dash-pagination-end">
                <span>Đã hiển thị toàn bộ {sessions.length} phiên hội thoại</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* MODAL 1: DELETE CONFIRMATION */}
      {deletingSession && (
        <div className="modal-backdrop" onClick={() => !isDeleting && setDeletingSession(null)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <span className="modal-warn-icon">⚠️</span>
              <h3>Xác nhận xóa cuộc trò chuyện</h3>
            </div>
            <div className="modal-body">
              <p>
                Bạn có chắc chắn muốn xóa cuộc trò chuyện{' '}
                <strong>&ldquo;{deletingSession.title}&rdquo;</strong> không?
              </p>
              <p className="modal-subtext">
                Toàn bộ câu hỏi, câu trả lời và trích dẫn trong phiên này sẽ bị xóa vĩnh viễn khỏi hệ thống.
              </p>
            </div>
            <div className="modal-footer">
              <button
                type="button"
                className="btn-modal-cancel"
                disabled={isDeleting}
                onClick={() => setDeletingSession(null)}
              >
                Hủy bỏ
              </button>
              <button
                type="button"
                className="btn-modal-danger"
                disabled={isDeleting}
                onClick={handleDeleteConfirm}
              >
                {isDeleting ? 'Đang xóa...' : 'Xóa vĩnh viễn'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 2: RENAME SESSION */}
      {renamingSession && (
        <div className="modal-backdrop" onClick={() => !isRenaming && setRenamingSession(null)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()}>
            <form onSubmit={handleRenameConfirm}>
              <div className="modal-header">
                <h3>Đổi tên cuộc trò chuyện</h3>
              </div>
              <div className="modal-body">
                <label htmlFor="rename-input" className="modal-label">
                  Tiêu đề cuộc trò chuyện
                </label>
                <input
                  id="rename-input"
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="modal-text-input"
                  maxLength={200}
                  autoFocus
                  required
                />
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn-modal-cancel"
                  disabled={isRenaming}
                  onClick={() => setRenamingSession(null)}
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  className="btn-modal-primary"
                  disabled={isRenaming || !newTitle.trim()}
                >
                  {isRenaming ? 'Đang lưu...' : 'Lưu thay đổi'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 3: CREATE NEW SESSION */}
      {isCreatingModal && (
        <div className="modal-backdrop" onClick={() => !isCreating && setIsCreatingModal(false)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()}>
            <form onSubmit={handleCreateSubmit}>
              <div className="modal-header">
                <h3>Bắt đầu cuộc trò chuyện mới</h3>
              </div>
              <div className="modal-body">
                <div className="modal-form-group">
                  <label htmlFor="create-ws-select" className="modal-label">
                    Sổ tay môn học *
                  </label>
                  {workspaces.length === 0 ? (
                    <p className="modal-alert-text">
                      Bạn chưa có Sổ tay môn học nào. Hãy tạo một Sổ tay trước khi bắt đầu hỏi đáp.
                    </p>
                  ) : (
                    <select
                      id="create-ws-select"
                      value={createWorkspaceId}
                      onChange={(e) => setCreateWorkspaceId(e.target.value)}
                      className="modal-select-input"
                      required
                    >
                      {workspaces.map((ws) => (
                        <option key={ws.id} value={ws.id}>
                          {ws.name}
                        </option>
                      ))}
                    </select>
                  )}
                </div>

                <div className="modal-form-group" style={{ marginTop: '14px' }}>
                  <label htmlFor="create-title-input" className="modal-label">
                    Tiêu đề (tùy chọn)
                  </label>
                  <input
                    id="create-title-input"
                    type="text"
                    value={createTitle}
                    onChange={(e) => setCreateTitle(e.target.value)}
                    placeholder="Ví dụ: Ôn tập chương 4"
                    className="modal-text-input"
                    maxLength={200}
                  />
                  <p className="modal-hint">
                    Tiêu đề sẽ tự động cập nhật theo câu hỏi đầu tiên của bạn nếu để mặc định.
                  </p>
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn-modal-cancel"
                  disabled={isCreating}
                  onClick={() => setIsCreatingModal(false)}
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  className="btn-modal-primary"
                  disabled={isCreating || workspaces.length === 0}
                >
                  {isCreating ? 'Đang tạo...' : 'Tạo & Mở Sổ tay'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
