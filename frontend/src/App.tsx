import { useState } from 'react';
import { API_URL } from './api/client';
import { useAuth } from './context/AuthContext';
import { AuthSection } from './sections/AuthSection';
import { ClientSection } from './sections/ClientSection';
import { ExecutorSection } from './sections/ExecutorSection';
import { AdminSection } from './sections/AdminSection';
import { subtleButtonClass } from './components/ui';

type TabKey = 'auth' | 'client' | 'executor' | 'admin';

const tabs: { key: TabKey; label: string }[] = [
  { key: 'auth', label: 'Auth' },
  { key: 'client', label: 'Client' },
  { key: 'executor', label: 'Executor' },
  { key: 'admin', label: 'Admin' },
];

const TabButton = ({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) => (
  <button
    className={`${subtleButtonClass} ${active ? 'border-blue-600 bg-blue-50 text-blue-700' : ''}`}
    onClick={onClick}
  >
    {label}
  </button>
);

const App = () => {
  const { user, token } = useAuth();
  const [tab, setTab] = useState<TabKey>('auth');

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="container flex flex-col gap-2 py-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">Smart BTI Test UI</h1>
            <p className="text-sm text-slate-600">
              Базовый URL API: <span className="font-mono">{API_URL}</span>
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-sm text-slate-700">
            <span className="rounded-full bg-slate-100 px-3 py-1">
              {token ? user?.user.email || 'Авторизовано' : 'Не авторизован'}
            </span>
            {user?.isClient && <span className="rounded-full bg-emerald-100 px-3 py-1">Client</span>}
            {user?.isExecutor && (
              <span className="rounded-full bg-indigo-100 px-3 py-1">Executor</span>
            )}
            {user?.isAdmin && <span className="rounded-full bg-amber-100 px-3 py-1">Admin</span>}
          </div>
        </div>
        <div className="container flex flex-wrap gap-2 pb-3">
          {tabs.map((t) => (
            <TabButton key={t.key} active={tab === t.key} label={t.label} onClick={() => setTab(t.key)} />
          ))}
        </div>
      </header>

      <main className="container py-6">
        {tab === 'auth' && <AuthSection />}
        {tab === 'client' && <ClientSection />}
        {tab === 'executor' && <ExecutorSection />}
        {tab === 'admin' && <AdminSection />}
      </main>
    </div>
  );
};

export default App;
