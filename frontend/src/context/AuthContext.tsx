// AuthContext.tsx – provides authentication state and actions for the app
import React, { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { apiClient } from '../services/api';
import { useNavigate, useLocation } from 'react-router-dom';

export interface User {
  id: number;
  full_name: string;
  email: string;
  phone?: string | null;
}

interface AuthContextProps {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (full_name: string, email: string, password: string) => Promise<void>;
  updateUser: (updatedData: { full_name?: string; email?: string; phone?: string }) => Promise<void>;
}

const AuthContext = createContext<AuthContextProps | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const navigate = useNavigate();
  const location = useLocation();

  // Restore session on mount
  useEffect(() => {
    const token = localStorage.getItem('agripulse_token');
    if (!token) {
      setLoading(false);
      return;
    }
    // Attempt to fetch current user
    apiClient
      .get('/auth/me')
      .then((res) => {
        setUser(res.data);
      })
      .catch(() => {
        // Invalid/expired token – clear it
        localStorage.removeItem('agripulse_token');
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = async (email: string, password: string) => {
    const payload = { email, password };
    const response = await apiClient.post('/auth/login', payload);
    const token = response.data.access_token;
    localStorage.setItem('agripulse_token', token);
    // Fetch user profile
    const meRes = await apiClient.get('/auth/me');
    setUser(meRes.data);
    // Redirect to originally requested page or dashboard
    const redirectTo = (location.state as any)?.from?.pathname || '/dashboard';
    navigate(redirectTo, { replace: true });
  };

  const register = async (full_name: string, email: string, password: string) => {
    const payload = { full_name, email, password };
    const response = await apiClient.post('/auth/register', payload);
    const token = response.data.access_token;
    localStorage.setItem('agripulse_token', token);
    const meRes = await apiClient.get('/auth/me');
    setUser(meRes.data);
    navigate('/dashboard', { replace: true });
  };

  const logout = () => {
    localStorage.removeItem('agripulse_token');
    setUser(null);
    navigate('/signin', { replace: true });
  };

  const updateUser = async (updatedData: { full_name?: string; email?: string; phone?: string }) => {
    const res = await apiClient.put('/auth/me', updatedData);
    setUser(res.data);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, register, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
};
