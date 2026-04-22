"use client";

import { useEffect } from "react";
import { useAuth } from "@/lib/auth-store";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const refreshMe = useAuth((s) => s.refreshMe);
  useEffect(() => {
    refreshMe();
  }, [refreshMe]);
  return <>{children}</>;
}
