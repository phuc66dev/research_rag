import React from 'react';
import { AppShell } from './app/AppShell';
import { AuthPage } from './features/auth/AuthPage';
import { AuthProvider, useAuth } from './features/auth/AuthContext';

const MainRouter: React.FC = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="app-loading-screen">
        <div className="app-spinner"></div>
        <p>Đang tải không gian học tập EduRAG-VN...</p>
      </div>
    );
  }

  if (!user) {
    return <AuthPage />;
  }

  return <AppShell />;
};

export function App() {
  return (
    <AuthProvider>
      <MainRouter />
    </AuthProvider>
  );
}
