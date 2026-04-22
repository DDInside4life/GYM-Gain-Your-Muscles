"use client";

import { create } from "zustand";
import { api, tokenStore } from "./api";

export type User = {
  id: number;
  email: string;
  full_name: string | null;
  is_admin: boolean;
  sex: "male" | "female" | null;
  weight_kg: number | null;
  height_cm: number | null;
  experience: "beginner" | "intermediate" | "advanced" | null;
  goal: string | null;
  activity_factor: number;
};

type Store = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, full_name?: string) => Promise<void>;
  refreshMe: () => Promise<void>;
  logout: () => void;
};

export const useAuth = create<Store>((set) => ({
  user: null,
  loading: false,
  async login(email, password) {
    const tokens = await api<{ access_token: string; refresh_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    tokenStore.set(tokens);
    const me = await api<User>("/auth/me", { auth: true });
    set({ user: me });
  },
  async register(email, password, full_name) {
    await api("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name }),
    });
    const tokens = await api<{ access_token: string; refresh_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    tokenStore.set(tokens);
    const me = await api<User>("/auth/me", { auth: true });
    set({ user: me });
  },
  async refreshMe() {
    set({ loading: true });
    try {
      if (!tokenStore.get()) {
        set({ user: null });
        return;
      }
      const me = await api<User>("/auth/me", { auth: true });
      set({ user: me });
    } catch {
      tokenStore.clear();
      set({ user: null });
    } finally {
      set({ loading: false });
    }
  },
  logout() {
    tokenStore.clear();
    set({ user: null });
  },
}));
