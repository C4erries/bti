import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { cardClass } from './ui';

export const RequireAuth = ({ children }: { children: React.ReactNode }) => {
  const { token, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className={cardClass}>
        <p>Загрузка профиля...</p>
      </div>
    );
  }

  if (!token) {
    return <Navigate to="/auth" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};

export const RequireRole = ({
  roleKey,
  children,
}: {
  roleKey: 'isClient' | 'isExecutor' | 'isAdmin';
  children: React.ReactNode;
}) => {
  const { user } = useAuth();

  if (!user || !user[roleKey]) {
    return (
      <div className={cardClass}>
        <p>Нет доступа к разделу. Проверьте роль пользователя.</p>
      </div>
    );
  }

  return <>{children}</>;
};
