import { createContext, useContext, useState, useCallback, ReactNode } from "react";
import { api } from "../api/client";
import type { User, AuthResponse, UserRole } from "../types";

interface AuthContextValue {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  register: (data: {
    full_name: string;
    email: string;
    password: string;
    role: UserRole;
    preferred_language: string;
    district?: string;
    state?: string;
  }) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const stored = localStorage.getItem("jagriti_user");
    return stored ? JSON.parse(stored) : null;
  });

  const persist = (data: AuthResponse) => {
    localStorage.setItem("jagriti_token", data.access_token);
    localStorage.setItem("jagriti_user", JSON.stringify(data.user));
    setUser(data.user);
  };

  const login = useCallback(async (email: string, password: string) => {
    const res = await api.post<AuthResponse>("/auth/login", { email, password });
    persist(res.data);
  }, []);

  const register = useCallback(async (data: any) => {
    await api.post("/auth/register", data);
    await login(data.email, data.password);
  }, [login]);

  const logout = useCallback(() => {
    localStorage.removeItem("jagriti_token");
    localStorage.removeItem("jagriti_user");
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
