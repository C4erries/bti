import React from 'react';
import { Link, NavLink } from 'react-router-dom';
import { API_URL } from '../api/client';
import { useAuth } from '../context/AuthContext';

const navLinkClass =
  'rounded-md px-3 py-2 text-sm font-medium hover:bg-slate-100';

const activeClass = 'bg-slate-200 text-slate-900';

export const Layout = ({ children }: { children: React.ReactNode }) => {
  const { user, token, logout } = useAuth();

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="container flex flex-col gap-2 py-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <Link to="/" className="text-2xl font-semibold text-slate-900">
              Smart BTI
            </Link>
            <p className="text-xs text-slate-600">API: {API_URL}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-sm text-slate-700">
            <Link to="/auth" className="rounded-full bg-slate-100 px-3 py-1">
              {token ? user?.user.email ?? 'Аккаунт' : 'Войти / Регистрация'}
            </Link>
            {user?.isClient && <span className="rounded-full bg-emerald-100 px-3 py-1">Client</span>}
            {user?.isExecutor && (
              <span className="rounded-full bg-indigo-100 px-3 py-1">Executor</span>
            )}
            {user?.isAdmin && <span className="rounded-full bg-amber-100 px-3 py-1">Admin</span>}
            {token && (
              <button
                className="rounded-md border border-slate-200 px-3 py-1 text-sm hover:bg-slate-50"
                onClick={logout}
              >
                Выйти
              </button>
            )}
          </div>
        </div>
        <div className="container flex flex-wrap gap-2 pb-3">
          <NavLink
            to="/"
            className={({ isActive }) =>
              `${navLinkClass} ${isActive ? activeClass : 'text-slate-700'}`
            }
          >
            Домой
          </NavLink>
          <NavLink
            to="/client"
            className={({ isActive }) =>
              `${navLinkClass} ${isActive ? activeClass : 'text-slate-700'}`
            }
          >
            Клиент
          </NavLink>
          <NavLink
            to="/executor"
            className={({ isActive }) =>
              `${navLinkClass} ${isActive ? activeClass : 'text-slate-700'}`
            }
          >
            Исполнитель
          </NavLink>
          <NavLink
            to="/admin"
            className={({ isActive }) =>
              `${navLinkClass} ${isActive ? activeClass : 'text-slate-700'}`
            }
          >
            Админ
          </NavLink>
        </div>
      </header>
      <main className="container py-6">{children}</main>
    </div>
  );
};

export default Layout;
