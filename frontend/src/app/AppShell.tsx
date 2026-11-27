import React, { useEffect, useRef, useState } from 'react';
import { useAuth } from '../features/auth/AuthContext';
import { HistoryView } from '../features/history/HistoryView';
import { DocumentsView } from '../features/documents/DocumentsView';
import { WorkspacesView } from '../features/workspaces/WorkspacesView';
import { StudyView } from '../features/study/StudyView';

export type NavItem = 'workspaces' | 'documents' | 'drive' | 'history';

interface AppShellProps {
  children?: React.ReactNode;
  activeNav?: NavItem;
  onNavigate?: (item: NavItem) => void;
}

export const AppShell: React.FC<AppShellProps> = ({
  children,
  activeNav: controlledNav,
  onNavigate,
}) => {
  const { user, logout } = useAuth();
  const [internalNav, setInternalNav] = useState<NavItem>('workspaces');
  const activeItem = controlledNav ?? internalNav;
  const [documentWorkspaceId, setDocumentWorkspaceId] = useState<string>();
  const [startCreatingWorkspace, setStartCreatingWorkspace] = useState(false);

  // Selected session to resume in workspace
  const [openedSession, setOpenedSession] = useState<{
    workspaceId: string;
    sessionId: string;
    title: string;
  } | null>(() => {
    if (!window.location.hash.startsWith('#study?')) return null;
    const params = new URLSearchParams(window.location.hash.slice(7));
    const workspaceId = params.get('workspace');
    return workspaceId ? { workspaceId, sessionId: params.get('session') || '', title: '' } : null;
  });

  // Account Menu & Modal State
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [activeModal, setActiveModal] = useState<'profile' | 'notifications' | 'settings' | 'help' | null>(null);
  const accountWrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (accountWrapRef.current && !accountWrapRef.current.contains(event.target as Node)) {
        setIsMenuOpen(false);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsMenuOpen(false);
        setActiveModal(null);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  const handleNavClick = (item: NavItem) => {
    setOpenedSession(null);
    window.history.replaceState(null, '', window.location.pathname + window.location.search);
    setStartCreatingWorkspace(false);
    if (onNavigate) {
      onNavigate(item);
    } else {
      setInternalNav(item);
    }
  };

  const handleOpenSessionFromHistory = (workspaceId: string, sessionId: string, title: string) => {
    setOpenedSession({ workspaceId, sessionId, title });
    window.history.replaceState(null, '', `#study?${new URLSearchParams({ workspace: workspaceId, session: sessionId })}`);
    if (onNavigate) {
      onNavigate('workspaces');
    } else {
      setInternalNav('workspaces');
    }
  };

  const getInitials = (name?: string, username?: string): string => {
    const text = (name && name.trim()) || username || 'U';
    const words = text.trim().split(/\s+/);
    if (words.length >= 2) {
      return (words[0][0] + words[words.length - 1][0]).toUpperCase();
    }
    return text.substring(0, 2).toUpperCase();
  };

  return (
    <div className="app-shell-layout">
      {/* Sidebar */}
      <aside className="app-sidebar">
        {/* Brand */}
        <div className="sidebar-brand">
          <div className="brand-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M12 5C9 3 5 3 2 4v15c3-1 7-1 10 1 3-2 7-2 10-1V4c-3-1-7-1-10 1Zm0 0v15" />
            </svg>
          </div>
          <div className="brand-info">
            <span className="brand-name">EduRAG-VN</span>
            <span className="brand-badge">P0 Workspace</span>
          </div>
        </div>

        {/* Navigation list */}
        <nav className="sidebar-nav">
          <div className="nav-group-label">HỌC TẬP</div>
          <button
            type="button"
            className={`nav-item-btn ${activeItem === 'workspaces' ? 'active' : ''}`}
            onClick={() => handleNavClick('workspaces')}
          >
            <span className="nav-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M12 5C9 3 5 3 2 4v15c3-1 7-1 10 1 3-2 7-2 10-1V4c-3-1-7-1-10 1Zm0 0v15" />
              </svg>
            </span>
            <span className="nav-label">Sổ tay môn học</span>
          </button>

          <button
            type="button"
            className={`nav-item-btn ${activeItem === 'documents' ? 'active' : ''}`}
            onClick={() => handleNavClick('documents')}
          >
            <span className="nav-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Zm0 0v6h6M8 13h8M8 17h6" />
              </svg>
            </span>
            <span className="nav-label">Tài liệu của tôi</span>
          </button>

          <button
            type="button"
            className={`nav-item-btn ${activeItem === 'drive' ? 'active' : ''}`}
            onClick={() => handleNavClick('drive')}
          >
            <span className="nav-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="m8 3 7 0 7 12-3.5 6H5L1.5 15Zm0 0 7 12M15 3 5 21M1.5 15H22" />
              </svg>
            </span>
            <span className="nav-label">Google Drive</span>
            <span className="nav-soon-badge">Sắp có</span>
          </button>

          <button
            type="button"
            className={`nav-item-btn ${activeItem === 'history' ? 'active' : ''}`}
            onClick={() => handleNavClick('history')}
          >
            <span className="nav-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M3 11a9 9 0 1 1 2.5 7M3 4v7h7M12 7v5l3 2" />
              </svg>
            </span>
            <span className="nav-label">Lịch sử hỏi AI</span>
          </button>
        </nav>

        {/* User Account footer with Popover Menu & 3-dots */}
        <div className="sidebar-account-wrap" ref={accountWrapRef}>
          {isMenuOpen && (
            <div className="sidebar-account-menu" role="menu" aria-label="Tùy chọn tài khoản">
              <div className="account-menu-head">
                <strong>{user?.full_name || user?.username || 'Người dùng'}</strong>
                <span className="account-menu-email">{user?.email || ''}</span>
              </div>
              <div className="account-menu-divider" />

              <button
                type="button"
                role="menuitem"
                className="account-menu-item"
                onClick={() => {
                  setIsMenuOpen(false);
                  setActiveModal('profile');
                }}
              >
                <span className="menu-icon">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                    <circle cx="12" cy="7" r="4" />
                  </svg>
                </span>
                <span>Hồ sơ tài khoản</span>
              </button>

              <button
                type="button"
                role="menuitem"
                className="account-menu-item"
                onClick={() => {
                  setIsMenuOpen(false);
                  setActiveModal('notifications');
                }}
              >
                <span className="menu-icon">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                    <path d="M13.73 21a2 2 0 0 1-3.46 0" />
                  </svg>
                </span>
                <span>Thông báo</span>
                <span className="menu-badge">3</span>
              </button>

              <button
                type="button"
                role="menuitem"
                className="account-menu-item"
                onClick={() => {
                  setIsMenuOpen(false);
                  setActiveModal('settings');
                }}
              >
                <span className="menu-icon">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="3" />
                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
                  </svg>
                </span>
                <span>Cài đặt</span>
              </button>

              <button
                type="button"
                role="menuitem"
                className="account-menu-item"
                onClick={() => {
                  setIsMenuOpen(false);
                  setActiveModal('help');
                }}
              >
                <span className="menu-icon">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" />
                    <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                    <line x1="12" y1="17" x2="12.01" y2="17" />
                  </svg>
                </span>
                <span>Trợ giúp</span>
              </button>

              <div className="account-menu-divider" />

              <button
                type="button"
                role="menuitem"
                className="account-menu-item logout"
                onClick={logout}
              >
                <span className="menu-icon">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                    <polyline points="16 17 21 12 16 7" />
                    <line x1="21" y1="12" x2="9" y2="12"></line>
                  </svg>
                </span>
                <span>Đăng xuất</span>
              </button>
            </div>
          )}

          {/* Account Trigger Row with 3-dots */}
          <div
            className={`sidebar-account-box ${isMenuOpen ? 'open' : ''}`}
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            role="button"
            tabIndex={0}
            aria-haspopup="menu"
            aria-expanded={isMenuOpen}
            title="Mở menu tùy chọn tài khoản"
          >
            <div className="account-avatar-box">
              {getInitials(user?.full_name, user?.username)}
            </div>
            <div className="account-info-col">
              <span className="account-user-name">{user?.full_name || user?.username || 'Người dùng'}</span>
              <span className="account-user-role">Sinh viên · {user?.email || ''}</span>
            </div>
            <button
              type="button"
              className="account-dots-btn"
              onClick={(e) => {
                e.stopPropagation();
                setIsMenuOpen(!isMenuOpen);
              }}
              aria-label="Tùy chọn tài khoản"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                <circle cx="5" cy="12" r="1.8" />
                <circle cx="12" cy="12" r="1.8" />
                <circle cx="19" cy="12" r="1.8" />
              </svg>
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="app-main-content">
        {children ? (
          children
        ) : (
          <div className="app-content-slot">
            {activeItem === 'workspaces' && (openedSession ? <StudyView
              key={`${openedSession.workspaceId}/${openedSession.sessionId}`}
              workspaceId={openedSession.workspaceId} initialSessionId={openedSession.sessionId || undefined}
              onBack={() => handleNavClick('workspaces')} onOpenDocuments={() => {
                setDocumentWorkspaceId(openedSession.workspaceId); handleNavClick('documents');
              }} /> :
              <WorkspacesView startCreating={startCreatingWorkspace}
              onOpenStudy={workspaceId => handleOpenSessionFromHistory(workspaceId, '', '')}
              onOpenDocuments={workspaceId => {
                setDocumentWorkspaceId(workspaceId);
                handleNavClick('documents');
              }} />
            )}

            {activeItem === 'documents' && (
              <DocumentsView initialWorkspaceId={documentWorkspaceId} onCreateWorkspace={() => {
                handleNavClick('workspaces');
                setStartCreatingWorkspace(true);
              }} />
            )}

            {activeItem === 'drive' && (
              <div className="slot-container">
                <div className="slot-header">
                  <h2>Google Drive</h2>
                </div>
                <div className="slot-placeholder-card">
                  <span className="slot-icon">
                    <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                      <path d="m8 3 7 0 7 12-3.5 6H5L1.5 15Zm0 0 7 12M15 3 5 21M1.5 15H22" />
                    </svg>
                  </span>
                  <h3>Đồng bộ Google Drive</h3>
                </div>
              </div>
            )}

            {activeItem === 'history' && (
              <HistoryView onOpenSession={handleOpenSessionFromHistory} />
            )}
          </div>
        )}
      </main>
      {/* Modal Dialog for Account Options */}
      {activeModal && (
        <div className="modal-backdrop" onClick={() => setActiveModal(null)}>
          <div className="modal-dialog-box" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>
                {activeModal === 'profile' && 'Hồ sơ tài khoản'}
                {activeModal === 'notifications' && 'Thông báo hệ thống'}
                {activeModal === 'settings' && 'Cài đặt'}
                {activeModal === 'help' && 'Trợ giúp & Hướng dẫn'}
              </h2>
              <button
                type="button"
                className="btn-close-modal"
                onClick={() => setActiveModal(null)}
                aria-label="Đóng hộp thoại"
              >
                ✕
              </button>
            </div>

            <div className="modal-body">
              {activeModal === 'profile' && (
                <div className="modal-profile-content">
                  <div className="profile-hero-card">
                    <div className="profile-avatar-large">
                      {getInitials(user?.full_name, user?.username)}
                    </div>
                    <div>
                      <h3 className="profile-display-name">{user?.full_name || user?.username}</h3>
                      <p className="profile-display-email">{user?.email}</p>
                    </div>
                  </div>
                  <div className="profile-details-table">
                    <div className="profile-detail-row">
                      <span>Tên đăng nhập:</span>
                      <strong>{user?.username}</strong>
                    </div>
                    <div className="profile-detail-row">
                      <span>Email:</span>
                      <strong>{user?.email}</strong>
                    </div>
                    <div className="profile-detail-row">
                      <span> User ID:</span>
                      <code className="profile-code">{user?.id}</code>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="modal-footer">
              <button
                type="button"
                className="btn-modal-close-action"
                onClick={() => setActiveModal(null)}
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
