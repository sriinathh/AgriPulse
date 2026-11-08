import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactElement;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    // Could render a spinner; for now just return null to avoid flash redirects
    return null;
  }

  if (!user) {
    // Preserve intended destination
    return <Navigate to="/signin" replace state={{ from: location }} />;
  }

  return children;
};
