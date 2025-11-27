import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { apiFetch } from '../api/client';
import type { AuthTokenResponse, CurrentUserResponse } from '../types';

interface AuthContextValue {
  token: string | null;
  user: CurrentUserResponse | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
  setToken: (token: string | null) => void;
}

const STORAGE_KEY = 'sbti_token';

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [token, setTokenState] = useState<string | null>(() =>
    localStorage.getItem(STORAGE_KEY),
  );
  const [user, setUser] = useState<CurrentUserResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const saveToken = (value: string | null) => {
    setTokenState(value);
    if (value) {
      localStorage.setItem(STORAGE_KEY, value);
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  };

  const refresh = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const data = await apiFetch<CurrentUserResponse>('/auth/me', {}, token);
      setUser(data);
      setError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Не удалось загрузить пользователя';
      setError(message);
      saveToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch<AuthTokenResponse>('/auth/login', {
        method: 'POST',
        data: { email, password },
      });
      saveToken(data.accessToken);
      const me = await apiFetch<CurrentUserResponse>('/auth/me', {}, data.accessToken);
      setUser(me);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Ошибка входа';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    saveToken(null);
    setUser(null);
  };

  useEffect(() => {
    if (token) {
      void refresh();
    }
  }, [token]);

  const value = useMemo(
    () => ({
      token,
      user,
      loading,
      error,
      login,
      logout,
      refresh,
      setToken: saveToken,
    }),
    [token, user, loading, error],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
