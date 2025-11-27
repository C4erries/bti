import { useState, type FormEvent } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { apiFetch, API_URL } from '../api/client';
import { useAuth } from '../context/AuthContext';
import {
  badgeClass,
  buttonClass,
  cardClass,
  inputClass,
  sectionTitleClass,
  subtleButtonClass,
} from '../components/ui';
import type { CurrentUserResponse } from '../types';

const AuthPage = () => {
  const { login, user, token, loading } = useAuth();
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regFullName, setRegFullName] = useState('');
  const [regPhone, setRegPhone] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const navigate = useNavigate();
  const location = useLocation();
  const redirectPath = (location.state as any)?.from?.pathname || '/';

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    setMessage(null);
    try {
      await login(loginEmail, loginPassword);
      navigate(redirectPath);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Ошибка входа');
    }
  };

  const handleRegister = async (e: FormEvent) => {
    e.preventDefault();
    setMessage(null);
    try {
      await apiFetch<CurrentUserResponse['user']>('/auth/register/client', {
        method: 'POST',
        data: {
          email: regEmail,
          password: regPassword,
          fullName: regFullName,
          phone: regPhone || null,
        },
      });
      setMessage('Клиент зарегистрирован, выполняю вход...');
      await login(regEmail, regPassword);
      navigate('/');
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Ошибка регистрации');
    }
  };

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className={cardClass}>
        <div className="flex items-start justify-between">
          <div>
            <h3 className={sectionTitleClass}>Авторизация</h3>
            <p className="text-sm text-slate-600">
              API: <span className="font-mono">{API_URL}</span>
            </p>
          </div>
        </div>
        <form className="mt-4 space-y-3" onSubmit={handleLogin}>
          <label className="block text-sm font-medium text-slate-700">
            Email
            <input
              className={`${inputClass} mt-1`}
              type="email"
              value={loginEmail}
              onChange={(e) => setLoginEmail(e.target.value)}
              required
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Пароль
            <input
              className={`${inputClass} mt-1`}
              type="password"
              value={loginPassword}
              onChange={(e) => setLoginPassword(e.target.value)}
              required
            />
          </label>
          <div className="flex gap-2">
            <button type="submit" className={buttonClass} disabled={loading}>
              Войти
            </button>
            <button
              type="button"
              className={subtleButtonClass}
              onClick={() => navigate('/')}
              disabled={loading}
            >
              На главную
            </button>
          </div>
          {message && <p className="text-sm text-red-600">{message}</p>}
        </form>
        <div className="mt-4 rounded-lg bg-slate-50 p-3 text-sm">
          <p className="font-medium">Текущий пользователь</p>
          {user ? (
            <div className="mt-2 space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-semibold">{user.user.email}</span>
                <span className={badgeClass}>ID: {user.user.id.slice(0, 8)}…</span>
              </div>
              <p>Имя: {user.user.fullName}</p>
              <div className="flex flex-wrap gap-2">
                {user.isClient && <span className={badgeClass}>Client</span>}
                {user.isExecutor && <span className={badgeClass}>Executor</span>}
                {user.isAdmin && <span className={badgeClass}>Admin</span>}
              </div>
              {token ? (
                <p className="break-all font-mono text-xs text-slate-500">
                  token: {token}
                </p>
              ) : null}
            </div>
          ) : (
            <p className="text-slate-600">Не авторизован</p>
          )}
        </div>
      </div>

      <div className={cardClass}>
        <h3 className={sectionTitleClass}>Регистрация клиента</h3>
        <form className="mt-4 space-y-3" onSubmit={handleRegister}>
          <label className="block text-sm font-medium text-slate-700">
            Email
            <input
              className={`${inputClass} mt-1`}
              type="email"
              value={regEmail}
              onChange={(e) => setRegEmail(e.target.value)}
              required
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Пароль
            <input
              className={`${inputClass} mt-1`}
              type="password"
              value={regPassword}
              onChange={(e) => setRegPassword(e.target.value)}
              required
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            ФИО
            <input
              className={`${inputClass} mt-1`}
              value={regFullName}
              onChange={(e) => setRegFullName(e.target.value)}
              required
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Телефон (опционально)
            <input
              className={`${inputClass} mt-1`}
              value={regPhone}
              onChange={(e) => setRegPhone(e.target.value)}
            />
          </label>
          <button type="submit" className={buttonClass} disabled={loading}>
            Зарегистрировать и войти
          </button>
        </form>
        {message && <p className="mt-2 text-sm text-slate-700">{message}</p>}
      </div>
    </div>
  );
};

export default AuthPage;
