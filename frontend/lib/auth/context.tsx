"use client";

/**
 * Client-side auth session.
 *
 * Holds the JWT in React state (hydrated from `localStorage` on mount) and
 * exposes `login` / `register` / `logout`. Screens read `isAuthenticated` and
 * `isLoading` to gate protected content; the actual per-request Authorization
 * header is added by the API client, so components never touch the raw token.
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { login as loginRequest, register as registerRequest } from "@/lib/api/auth";
import { clearToken, getToken, saveToken } from "@/lib/auth/session";

type AuthContextValue = {
  token: string | null;
  isAuthenticated: boolean;
  /** True until the token is hydrated from storage, to avoid a flash of the
   *  logged-out state on first paint. */
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setToken(getToken());
    setIsLoading(false);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const { token: newToken } = await loginRequest(email, password);
    saveToken(newToken);
    setToken(newToken);
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    const { token: newToken } = await registerRequest(email, password);
    saveToken(newToken);
    setToken(newToken);
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setToken(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      isAuthenticated: token !== null,
      isLoading,
      login,
      register,
      logout,
    }),
    [token, isLoading, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (ctx === null) {
    throw new Error("useAuth must be used within an <AuthProvider>");
  }
  return ctx;
}
