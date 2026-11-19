import React, { useState } from 'react';
import { useAuth } from './AuthContext';

export const AuthPage: React.FC = () => {
  const { login, register, error, clearError } = useAuth();
  const [tab, setTab] = useState<'login' | 'register'>('login');

  // Login form state
  const [loginIdentifier, setLoginIdentifier] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [showLoginPassword, setShowLoginPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  // Register form state
  const [regFullName, setRegFullName] = useState('');
  const [regUsername, setRegUsername] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [showRegPassword, setShowRegPassword] = useState(false);

  // UI state
  const [submitting, setSubmitting] = useState(false);
  const [inlineErrors, setInlineErrors] = useState<Record<string, string>>({});
  const [successToast, setSuccessToast] = useState<string | null>(null);

  const clearFieldError = (field: string) => {
    if (inlineErrors[field]) {
      setInlineErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
  };

  const switchTab = (newTab: 'login' | 'register') => {
    clearError();
    setInlineErrors({});
    setTab(newTab);
  };

  // 4-Bar Password Strength Calculator
  const getPasswordStrength = (pass: string) => {
    if (!pass) return { level: 0, text: '', color: 'bg-slate-200', textColor: '' };
    let score = 0;
    if (pass.length >= 8) score++;
    if (/[a-z]/.test(pass) && /[A-Z]/.test(pass)) score++;
    if (/\d/.test(pass)) score++;
    if (/[^A-Za-z0-9]/.test(pass)) score++;
    const level = Math.max(1, score);

    const states: Record<number, { text: string; color: string; textColor: string }> = {
      1: { text: 'Yếu', color: '#DC2626', textColor: '#DC2626' },
      2: { text: 'Trung bình', color: '#F59E0B', textColor: '#D97706' },
      3: { text: 'Khá tốt', color: '#244573', textColor: '#1B365D' },
      4: { text: 'Rất mạnh', color: '#10B981', textColor: '#059669' },
    };
    return { level, ...states[level] };
  };

  const passwordStrength = getPasswordStrength(regPassword);

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessToast(null);
    clearError();
    const errors: Record<string, string> = {};

    if (!loginIdentifier.trim()) {
      errors.loginIdentifier = 'Vui lòng nhập tên đăng nhập hoặc email.';
    }
    if (!loginPassword) {
      errors.loginPassword = 'Vui lòng nhập mật khẩu của bạn.';
    }

    if (Object.keys(errors).length > 0) {
      setInlineErrors(errors);
      return;
    }

    setSubmitting(true);
    try {
      await login({
        username_or_email: loginIdentifier.trim(),
        password: loginPassword,
      });
    } catch {
      // Handled by AuthContext
    } finally {
      setSubmitting(false);
    }
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessToast(null);
    clearError();
    const errors: Record<string, string> = {};

    if (regUsername.trim().length < 3) {
      errors.regUsername = 'Tên đăng nhập cần có ít nhất 3 ký tự.';
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(regEmail.trim())) {
      errors.regEmail = 'Vui lòng nhập địa chỉ email hợp lệ.';
    }
    if (regPassword.length < 8) {
      errors.regPassword = 'Mật khẩu phải có tối thiểu 8 ký tự.';
    }

    if (Object.keys(errors).length > 0) {
      setInlineErrors(errors);
      return;
    }

    setSubmitting(true);
    try {
      await register({
        username: regUsername.trim(),
        email: regEmail.trim(),
        password: regPassword,
        full_name: regFullName.trim() || undefined,
      });

      // Successful registration: switch to login tab and pre-fill username/email
      setSuccessToast(`Tạo tài khoản thành công! Bạn có thể đăng nhập ngay bây giờ.`);
      setLoginIdentifier(regEmail.trim() || regUsername.trim());
      setLoginPassword('');
      setRegPassword('');
      setTab('login');
    } catch {
      // Handled by AuthContext
    } finally {
      setSubmitting(false);
    }
  };

  const handleForgotPassword = () => {
    setSuccessToast('Tính năng khôi phục mật khẩu sẽ gửi liên kết xác thực về email sinh viên/giảng viên của bạn.');
  };

  return (
    <div className="auth-split-layout">
      {/* LEFT SHOWCASE PANEL (48% on desktop — Editorial Academic Navy) */}
      <aside className="auth-showcase-panel">
        {/* Crisp Architectural Dot Grid Overlay */}
        <div className="auth-grid-overlay-dark" />
        <div className="auth-ambient-glow" />

        {/* Top Brand Pill & Status */}
        <header className="auth-header-top">
          <a href="#" className="auth-brand-pill">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              aria-hidden="true"
              style={{ flexShrink: 0 }}
            >
              <path
                d="M4 5.5C4 4.67157 4.67157 4 5.5 4H10.5C11.3284 4 12 4.67157 12 5.5V19.5C12 18.6716 11.3284 18 10.5 18H5.5C4.67157 18 4 17.3284 4 16.5V5.5Z"
                stroke="#F8FAFC"
                strokeWidth="1.75"
                strokeLinejoin="round"
              />
              <path
                d="M20 5.5C20 4.67157 19.3284 4 18.5 4H13.5C12.6716 4 12 4.67157 12 5.5V19.5C12 18.6716 12.6716 18 13.5 18H18.5C19.3284 18 20 17.3284 20 16.5V5.5Z"
                stroke="#94A3B8"
                strokeWidth="1.75"
                strokeLinejoin="round"
              />
              <circle cx="16.5" cy="9.5" r="1.6" fill="#7CA0C8" />
              <path d="M7 8.5H9.5" stroke="#94A3B8" strokeWidth="1.5" strokeLinecap="round" />
              <path d="M7 11.5H9.5" stroke="#94A3B8" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
            <span>EduRAG-VN</span>
          </a>

          <span className="auth-status-pill">
            <span className="status-dot-emerald" />
            <span>Hệ thống sẵn sàng</span>
          </span>
        </header>

        {/* Middle Content: Hero + RAG Citation Preview + Feature List */}
        <div className="auth-showcase-content">
          <div>
            <h1 className="auth-hero-headline">
              Trợ lý học tập &amp; nghiên cứu thông minh
            </h1>
            <p className="auth-hero-desc">
              Hệ thống hỗ trợ sinh viên và giảng viên tra cứu giáo trình, giải đáp câu hỏi học thuật với nguồn trích dẫn xác thực 100%.
            </p>
          </div>

          {/* Authentic RAG Citation Preview Card */}
          <div className="rag-citation-card">
            <div className="rag-query-row">
              <span className="rag-search-icon-box">
                <svg
                  width="12"
                  height="12"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <circle cx="11" cy="11" r="8"></circle>
                  <path d="m21 21-4.3-4.3"></path>
                </svg>
              </span>
              <p className="rag-query-text">
                Điều kiện để một lược đồ quan hệ đạt dạng chuẩn 3NF là gì?
              </p>
            </div>

            <div className="rag-card-divider" />

            <div>
              <p className="rag-answer-text">
                Lược đồ quan hệ đạt 3NF khi đã ở dạng chuẩn 2NF và không có thuộc tính không khóa nào phụ thuộc bắc cầu vào khóa chính
                <span className="rag-badge-citation">[1]</span>.
              </p>
              <div className="rag-source-footer" style={{ marginTop: '8px' }}>
                <div className="rag-source-chip">
                  <svg
                    width="12"
                    height="12"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="#7CA0C8"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"></path>
                  </svg>
                  <span>Giáo trình Hệ cơ sở dữ liệu · Chương 4, Tr. 118</span>
                </div>
                <span className="rag-verified-label">Xác thực nguồn</span>
              </div>
            </div>
          </div>

          {/* 3 Feature Items Separated by Subtle Thin Dividers */}
          <div className="auth-feature-group">
            <div className="auth-feature-row">
              <div className="auth-feature-icon-box">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"></path>
                  <path d="M8 7h6"></path>
                  <path d="M8 11h8"></path>
                </svg>
              </div>
              <div>
                <h4 className="auth-feature-title">Sổ tay môn học thông minh</h4>
                <p className="auth-feature-text">Tổ chức tài liệu, slide, bài tập theo từng học phần riêng biệt.</p>
              </div>
            </div>

            <div className="auth-feature-row">
              <div className="auth-feature-icon-box">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                  <path d="m9 15 2 2 4-4"></path>
                </svg>
              </div>
              <div>
                <h4 className="auth-feature-title">Hỏi đáp RAG có căn cứ</h4>
                <p className="auth-feature-text">Mỗi câu trả lời của AI đều dẫn chiếu chính xác số trang và tài liệu gốc.</p>
              </div>
            </div>

            <div className="auth-feature-row">
              <div className="auth-feature-icon-box">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"></path>
                  <path d="m9 12 2 2 4-4"></path>
                </svg>
              </div>
              <div>
                <h4 className="auth-feature-title">Bảo mật &amp; Lưu trữ liên tục</h4>
                <p className="auth-feature-text">Lịch sử thảo luận cá nhân được bảo vệ theo từng tài khoản.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="auth-footer-brand">
          &copy; 2026 EduRAG-VN · Nền tảng AI hỗ trợ giáo dục đại học
        </footer>
      </aside>

      {/* RIGHT AUTHENTICATION PANEL (52% on desktop) */}
      <main className="auth-form-side">
        {/* Subtle Architectural Dot Grid Overlay */}
        <div className="auth-grid-overlay-light" />
        <div className="auth-card-wrapper">
          <div className="academic-auth-card">
            {/* 3px Top Accent Bar */}
            <div className="card-top-accent-bar" />

            <div className="card-inner-padding">
              {/* Segmented Tab Switcher with sliding background indicator */}
              <div className="auth-segmented-tabs" role="tablist">
                <div
                  className="tab-sliding-indicator"
                  style={{
                    transform: tab === 'login' ? 'translateX(0%)' : 'translateX(100%)',
                  }}
                />
                <button
                  type="button"
                  role="tab"
                  className={`auth-tab-choice ${tab === 'login' ? 'active' : ''}`}
                  onClick={() => switchTab('login')}
                >
                  Đăng nhập
                </button>
                <button
                  type="button"
                  role="tab"
                  className={`auth-tab-choice ${tab === 'register' ? 'active' : ''}`}
                  onClick={() => switchTab('register')}
                >
                  Đăng ký
                </button>
              </div>

              {/* Toast / Alert Banners */}
              {successToast && (
                <div className="auth-toast-alert success animate-toast">
                  <span>✓</span>
                  <span>{successToast}</span>
                </div>
              )}

              {error && (
                <div className="auth-toast-alert error animate-toast">
                  <span>⚠️</span>
                  <span>{error}</span>
                </div>
              )}

              {/* TAB 1: LOGIN FORM */}
              {tab === 'login' ? (
                <section className="animate-form-in">
                  <div className="auth-card-title-box">
                    <h2>Chào mừng trở lại</h2>
                    <p>Đăng nhập để tiếp tục không gian học tập của bạn</p>
                  </div>

                  <form onSubmit={handleLoginSubmit} className="auth-form-fields" noValidate autoComplete="off">
                    {/* Identifier */}
                    <div className="field-group">
                      <label htmlFor="login-identifier">Tên đăng nhập hoặc Email</label>
                      <div className="input-box-relative">
                        <span className="field-icon-left">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path>
                            <circle cx="12" cy="7" r="4"></circle>
                          </svg>
                        </span>
                        <input
                          id="login-identifier"
                          type="text"
                          autoComplete="off"
                          placeholder="sinhvien@edurag.vn"
                          value={loginIdentifier}
                          onChange={(e) => {
                            setLoginIdentifier(e.target.value);
                            clearFieldError('loginIdentifier');
                          }}
                          className={`academic-input-field ${inlineErrors.loginIdentifier ? 'input-error' : ''}`}
                        />
                      </div>
                      {inlineErrors.loginIdentifier && (
                        <p className="field-inline-error">{inlineErrors.loginIdentifier}</p>
                      )}
                    </div>

                    {/* Password */}
                    <div className="field-group">
                      <div className="field-header-row">
                        <label htmlFor="login-password">Mật khẩu</label>
                        <button
                          type="button"
                          className="forgot-pass-btn"
                          onClick={handleForgotPassword}
                        >
                          Quên mật khẩu?
                        </button>
                      </div>
                      <div className="input-box-relative">
                        <span className="field-icon-left">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                            <rect width="18" height="11" x="3" y="11" rx="2" ry="2"></rect>
                            <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                          </svg>
                        </span>
                        <input
                          id="login-password"
                          type={showLoginPassword ? 'text' : 'password'}
                          autoComplete="new-password"
                          placeholder="Nhập mật khẩu"
                          value={loginPassword}
                          onChange={(e) => {
                            setLoginPassword(e.target.value);
                            clearFieldError('loginPassword');
                          }}
                          className={`academic-input-field ${inlineErrors.loginPassword ? 'input-error' : ''}`}
                        />
                        <button
                          type="button"
                          className="field-toggle-eye"
                          onClick={() => setShowLoginPassword(!showLoginPassword)}
                          aria-label="Ẩn hoặc hiện mật khẩu"
                        >
                          {showLoginPassword ? (
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                              <path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"></path>
                              <path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"></path>
                              <path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"></path>
                              <line x1="2" x2="22" y1="2" y2="22"></line>
                            </svg>
                          ) : (
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                              <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"></path>
                              <circle cx="12" cy="12" r="3"></circle>
                            </svg>
                          )}
                        </button>
                      </div>
                      {inlineErrors.loginPassword && (
                        <p className="field-inline-error">{inlineErrors.loginPassword}</p>
                      )}
                    </div>

                    {/* Remember me */}
                    <div style={{ paddingTop: '2px', paddingBottom: '2px' }}>
                      <label className="remember-row">
                        <input
                          type="checkbox"
                          checked={rememberMe}
                          onChange={(e) => setRememberMe(e.target.checked)}
                          className="custom-checkbox-input"
                        />
                        <span className="remember-label-text">Ghi nhớ đăng nhập</span>
                      </label>
                    </div>

                    {/* CTA Button */}
                    <button
                      type="submit"
                      disabled={submitting}
                      className="academic-primary-btn"
                    >
                      <span>{submitting ? 'Đang xác thực...' : 'Đăng nhập'}</span>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M5 12h14"></path>
                        <path d="m12 5 7 7-7 7"></path>
                      </svg>
                    </button>
                  </form>

                  <p className="auth-bottom-switch-row">
                    Chưa có tài khoản?
                    <button
                      type="button"
                      className="switch-inline-link"
                      onClick={() => switchTab('register')}
                    >
                      Đăng ký ngay
                    </button>
                  </p>
                </section>
              ) : (
                /* TAB 2: REGISTER FORM */
                <section className="animate-form-in">
                  <div className="auth-card-title-box">
                    <h2>Tạo tài khoản mới</h2>
                    <p>Bắt đầu trải nghiệm học tập thông minh cùng EduRAG-VN</p>
                  </div>

                  <form onSubmit={handleRegisterSubmit} className="auth-form-fields" noValidate>
                    {/* Full Name */}
                    <div className="field-group">
                      <label htmlFor="reg-fullname">
                        Họ và tên <span style={{ color: '#94A3B8', fontWeight: 'normal' }}>(tùy chọn)</span>
                      </label>
                      <div className="input-box-relative">
                        <span className="field-icon-left">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path>
                            <circle cx="12" cy="7" r="4"></circle>
                          </svg>
                        </span>
                        <input
                          id="reg-fullname"
                          type="text"
                          autoComplete="name"
                          placeholder="Nguyễn Văn A"
                          value={regFullName}
                          onChange={(e) => setRegFullName(e.target.value)}
                          className="academic-input-field"
                        />
                      </div>
                    </div>

                    {/* Username */}
                    <div className="field-group">
                      <label htmlFor="reg-username">Tên đăng nhập</label>
                      <div className="input-box-relative">
                        <span className="field-icon-left">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                            <circle cx="12" cy="12" r="4"></circle>
                            <path d="M16 8v5a3 3 0 0 0 6 0v-1a10 10 0 1 0-4 8"></path>
                          </svg>
                        </span>
                        <input
                          id="reg-username"
                          type="text"
                          autoComplete="username"
                          placeholder="nguyenvana (ít nhất 3 ký tự)"
                          value={regUsername}
                          onChange={(e) => {
                            setRegUsername(e.target.value);
                            clearFieldError('regUsername');
                          }}
                          className={`academic-input-field ${inlineErrors.regUsername ? 'input-error' : ''}`}
                        />
                      </div>
                      {inlineErrors.regUsername && (
                        <p className="field-inline-error">{inlineErrors.regUsername}</p>
                      )}
                    </div>

                    {/* Email */}
                    <div className="field-group">
                      <label htmlFor="reg-email">Địa chỉ Email</label>
                      <div className="input-box-relative">
                        <span className="field-icon-left">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                            <rect width="20" height="16" x="2" y="4" rx="2"></rect>
                            <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"></path>
                          </svg>
                        </span>
                        <input
                          id="reg-email"
                          type="email"
                          autoComplete="email"
                          placeholder="sinhvien@edurag.vn"
                          value={regEmail}
                          onChange={(e) => {
                            setRegEmail(e.target.value);
                            clearFieldError('regEmail');
                          }}
                          className={`academic-input-field ${inlineErrors.regEmail ? 'input-error' : ''}`}
                        />
                      </div>
                      {inlineErrors.regEmail && (
                        <p className="field-inline-error">{inlineErrors.regEmail}</p>
                      )}
                    </div>

                    {/* Password + Strength Meter */}
                    <div className="field-group">
                      <label htmlFor="reg-password">Mật khẩu</label>
                      <div className="input-box-relative">
                        <span className="field-icon-left">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                            <rect width="18" height="11" x="3" y="11" rx="2" ry="2"></rect>
                            <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                          </svg>
                        </span>
                        <input
                          id="reg-password"
                          type={showRegPassword ? 'text' : 'password'}
                          autoComplete="new-password"
                          placeholder="Tối thiểu 8 ký tự"
                          value={regPassword}
                          onChange={(e) => {
                            setRegPassword(e.target.value);
                            clearFieldError('regPassword');
                          }}
                          className={`academic-input-field ${inlineErrors.regPassword ? 'input-error' : ''}`}
                        />
                        <button
                          type="button"
                          className="field-toggle-eye"
                          onClick={() => setShowRegPassword(!showRegPassword)}
                          aria-label="Ẩn hoặc hiện mật khẩu"
                        >
                          {showRegPassword ? (
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                              <path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"></path>
                              <path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"></path>
                              <path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"></path>
                              <line x1="2" x2="22" y1="2" y2="22"></line>
                            </svg>
                          ) : (
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                              <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"></path>
                              <circle cx="12" cy="12" r="3"></circle>
                            </svg>
                          )}
                        </button>
                      </div>

                      {/* 4-Bar Strength Meter */}
                      {regPassword && (
                        <div className="strength-meter-box">
                          <div className="strength-bars-grid">
                            {[1, 2, 3, 4].map((barIndex) => (
                              <div
                                key={barIndex}
                                className="strength-segment-bar"
                                style={{
                                  backgroundColor:
                                    barIndex <= passwordStrength.level
                                      ? passwordStrength.color
                                      : '#E2E8F0',
                                }}
                              />
                            ))}
                          </div>
                          <div className="strength-meta-text">
                            <span style={{ color: '#64748B' }}>Độ mạnh mật khẩu</span>
                            <span style={{ color: passwordStrength.textColor, fontWeight: 600 }}>
                              {passwordStrength.text}
                            </span>
                          </div>
                        </div>
                      )}

                      {inlineErrors.regPassword && (
                        <p className="field-inline-error">{inlineErrors.regPassword}</p>
                      )}
                    </div>

                    {/* CTA Button */}
                    <button
                      type="submit"
                      disabled={submitting}
                      className="academic-primary-btn"
                    >
                      <span>{submitting ? 'Đang khởi tạo tài khoản...' : 'Đăng ký tài khoản'}</span>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M5 12h14"></path>
                        <path d="m12 5 7 7-7 7"></path>
                      </svg>
                    </button>
                  </form>

                  <p className="auth-bottom-switch-row">
                    Đã có tài khoản?
                    <button
                      type="button"
                      className="switch-inline-link"
                      onClick={() => switchTab('login')}
                    >
                      Đăng nhập
                    </button>
                  </p>
                </section>
              )}
            </div>
          </div>

          {/* Academic Trust Footer Below Form Card */}
          <div className="academic-trust-footer">
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#1B365D"
              strokeWidth="1.75"
              strokeLinecap="round"
              strokeLinejoin="round"
              style={{ flexShrink: 0 }}
            >
              <path d="M22 10v6M2 10l10-5 10 5-10 5z"></path>
              <path d="M6 12v5c3 3 9 3 12 0v-5"></path>
            </svg>
            <span>Dành cho sinh viên &amp; giảng viên các trường đại học tại Việt Nam</span>
          </div>
        </div>
      </main>
    </div>
  );
};
