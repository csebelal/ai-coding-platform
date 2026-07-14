'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { User } from '@/lib/types';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const loadUser = useCallback(async () => {
    if (api.isAuthenticated()) {
      try {
        const userData = await api.getCurrentUser();
        setUser(userData);
      } catch {
        api.clearTokens();
        setUser(null);
      }
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const login = async (email: string, password: string) => {
    const tokens = await api.login(email, password);
    api.setTokens(tokens);
    const userData = await api.getCurrentUser();
    setUser(userData);
  };

  const register = async (email: string, password: string, fullName: string) => {
    const tokens = await api.register(email, password, fullName);
    api.setTokens(tokens);
    const userData = await api.getCurrentUser();
    setUser(userData);
  };

  const logout = () => {
    api.clearTokens();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
