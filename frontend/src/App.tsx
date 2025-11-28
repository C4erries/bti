import { BrowserRouter, Routes, Route, Link, Navigate, Outlet } from 'react-router-dom';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import AuthPage from './pages/AuthPage';
import ServiceCatalogPage from './pages/client/ServiceCatalogPage';
import CreateOrderPage from './pages/client/CreateOrderPage';
import ClientOrdersPage from './pages/client/OrdersPage';
import ClientOrderDetailsPage from './pages/client/OrderDetailsPage';
import ClientChatPage from './pages/client/ClientChatPage';
import ClientChatLandingPage from './pages/client/ClientChatLandingPage';
import PriceCalculatorPage from './pages/client/PriceCalculatorPage';
import ExecutorOrdersPage from './pages/executor/ExecutorOrdersPage';
import ExecutorOrderDetailsPage from './pages/executor/ExecutorOrderDetailsPage';
import ExecutorCalendarPage from './pages/executor/ExecutorCalendarPage';
import AdminUsersPage from './pages/admin/AdminUsersPage';
import AdminExecutorsPage from './pages/admin/AdminExecutorsPage';
import AdminOrdersPage from './pages/admin/AdminOrdersPage';
import AdminCatalogsPage from './pages/admin/AdminCatalogsPage';
import { RequireAuth, RequireRole } from './components/Protected';
import { cardClass, sectionTitleClass, subtleButtonClass } from './components/ui';
import ClientChatShell from './layouts/ClientChatShell';

const ExecutorLayout = () => (
  <div className="space-y-3">
    <div className={cardClass}>
      <div className="flex flex-wrap gap-2">
        <Link className={subtleButtonClass} to="/executor/orders">
          Заказы
        </Link>
        <Link className={subtleButtonClass} to="/executor/calendar">
          Календарь заказов
        </Link>
        <Link className={subtleButtonClass} to="/executor/tools">
          Инструменты
        </Link>
      </div>
    </div>
    <Outlet />
  </div>
);

const AdminLayout = () => (
  <div className="space-y-3">
    <div className={cardClass}>
      <div className="flex flex-wrap gap-2">
        <Link className={subtleButtonClass} to="/admin/users">
          Пользователи
        </Link>
        <Link className={subtleButtonClass} to="/admin/executors">
          Исполнители
        </Link>
        <Link className={subtleButtonClass} to="/admin/orders">
          Заказы
        </Link>
        <Link className={subtleButtonClass} to="/admin/catalogs">
          Справочники
        </Link>
      </div>
    </div>
    <Outlet />
  </div>
);

const NotFound = () => (
  <div className={cardClass}>
    <h2 className={sectionTitleClass}>Страница не найдена</h2>
    <p className="text-sm text-slate-700">Проверьте адрес или вернитесь на главную.</p>
    <Link className={subtleButtonClass + ' mt-2 inline-flex'} to="/">
      На главную
    </Link>
  </div>
);

const App = () => {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/auth" element={<AuthPage />} />

          <Route
            path="/client"
            element={
              <RequireAuth>
                <RequireRole roleKey="isClient">
                  <ClientChatShell />
                </RequireRole>
              </RequireAuth>
            }
          >
            <Route index element={<ClientChatLandingPage />} />
            <Route path="services" element={<ServiceCatalogPage />} />
            <Route path="orders" element={<ClientOrdersPage />} />
            <Route path="orders/new" element={<CreateOrderPage />} />
            <Route path="orders/:orderId" element={<ClientOrderDetailsPage />} />
            <Route path="chat/:chatId" element={<ClientChatPage />} />
            <Route path="calculator" element={<PriceCalculatorPage />} />
          </Route>

          <Route
            path="/executor"
            element={
              <RequireAuth>
                <RequireRole roleKey="isExecutor">
                  <ExecutorLayout />
                </RequireRole>
              </RequireAuth>
            }
          >
            <Route index element={<Navigate to="/executor/orders" replace />} />
            <Route path="orders" element={<ExecutorOrdersPage />} />
            <Route path="orders/:orderId" element={<ExecutorOrderDetailsPage />} />
            <Route path="calendar" element={<ExecutorCalendarPage />} />
            <Route path="tools" element={<div className={cardClass}>Инструменты (скоро)</div>} />
          </Route>

          <Route
            path="/admin"
            element={
              <RequireAuth>
                <RequireRole roleKey="isAdmin">
                  <AdminLayout />
                </RequireRole>
              </RequireAuth>
            }
          >
            <Route index element={<Navigate to="/admin/users" replace />} />
            <Route path="users" element={<AdminUsersPage />} />
            <Route path="executors" element={<AdminExecutorsPage />} />
            <Route path="orders" element={<AdminOrdersPage />} />
            <Route path="catalogs" element={<AdminCatalogsPage />} />
          </Route>

          <Route path="*" element={<NotFound />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
};

export default App;
