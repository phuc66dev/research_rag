import React, { createContext, useContext, useEffect, useState } from 'react';
import { ApiError } from '../../api/client';
import { authApi } from './api';
import type { LoginPayload, RegisterPayload, User } from './types';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function formatErrorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (typeof err.detail === 'object' && err.detail !== null) {
      const d = err.detail as { code?: string; message?: string };
      if (d.message) return d.message;
      if (d.code === 'invalid_credentials') return 'Tên đăng nhập hoặc mật khẩu không chính xác.';
      if (d.code === 'username_already_exists') return 'Tên đăng nhập này đã được sử dụng.';
      if (d.code === 'email_already_exists') return 'Địa chỉ email này đã được sử dụng.';
      if (d.code === 'unauthorized') return 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.';
    }
    if (typeof err.detail === 'string') return err.detail;
  }
  if (err instanceof Error) return err.message;
  return 'Đã có lỗi xảy ra. Vui lòng thử lại.';
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check current session on initial load
    authApi
      .getMe()
      .then((currentUser) => {
        setUser(currentUser);
      })
      .catch(() => {
        setUser(null);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const login = async (payload: LoginPayload) => {
    setError(null);
    try {
      const res = await authApi.login(payload);
      setUser(res.user);
    } catch (err) {
      const msg = formatErrorMessage(err);
      setError(msg);
      throw err;
    }
  };

  const register = async (payload: RegisterPayload) => {
    setError(null);
    try {
      await authApi.register(payload);
      // User must log in separately after registering
    } catch (err) {
      const msg = formatErrorMessage(err);
      setError(msg);
      throw err;
    }
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch {
      // Ignore logout network failures
    } finally {
      setUser(null);
    }
  };

  const clearError = () => setError(null);

  return (
    <AuthContext.Provider value={{ user, loading, error, login, register, logout, clearError }}>
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
