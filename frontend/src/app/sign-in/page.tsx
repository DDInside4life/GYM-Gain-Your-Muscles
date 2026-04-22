"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/input";
import { useAuth } from "@/lib/auth-store";

export default function SignInPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const login = useAuth((s) => s.login);
  const router = useRouter();

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err) {
      setError(String((err as Error).message || "Ошибка входа"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md mt-10">
      <div className="glass-card p-6 md:p-8 space-y-5 animate-fade-up">
        <h1 className="display text-2xl font-extrabold">С возвращением</h1>
        <p className="text-sm text-muted">Войди, чтобы продолжить прогресс.</p>
        <form className="space-y-4" onSubmit={onSubmit}>
          <div>
            <Label>Email</Label>
            <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div>
            <Label>Пароль</Label>
            <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} />
          </div>
          {error && <p className="text-xs text-brand-500">{error}</p>}
          <Button disabled={loading} className="w-full" size="lg">
            {loading ? "Вход…" : "Войти"}
          </Button>
        </form>
        <p className="text-sm text-muted text-center">
          Нет аккаунта? <Link href="/sign-up" className="text-brand-500">Регистрация</Link>
        </p>
      </div>
    </div>
  );
}
