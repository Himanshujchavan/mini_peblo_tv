import { createContext, useContext, useState, ReactNode } from "react";
import { login as apiLogin } from "./api/client";
import type { Role } from "./types";

interface AuthState {
  email: string | null;
  role: Role | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [email, setEmail] = useState<string | null>(localStorage.getItem("peblo_email"));
  const [role, setRole] = useState<Role | null>(localStorage.getItem("peblo_role") as Role | null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function login(emailIn: string, password: string) {
    setLoading(true);
    setError(null);
    try {
      const res = await apiLogin(emailIn, password);
      localStorage.setItem("peblo_token", res.access_token);
      localStorage.setItem("peblo_email", res.email);
      localStorage.setItem("peblo_role", res.role);
      setEmail(res.email);
      setRole(res.role as Role);
    } catch (e: any) {
      setError(e.message || "Login failed");
      throw e;
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    localStorage.removeItem("peblo_token");
    localStorage.removeItem("peblo_email");
    localStorage.removeItem("peblo_role");
    setEmail(null);
    setRole(null);
  }

  return (
    <AuthContext.Provider value={{ email, role, loading, error, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
