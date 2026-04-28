"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/input";
import { useAuth } from "@/lib/auth-store";

export default function SignUpPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const register = useAuth((s) => s.register);
  const router = useRouter();

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(email, password, fullName || undefined);
      router.push("/dashboard");
    } catch (err) {
      setError(String((err as Error).message || "Ошибка регистрации"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md mt-10">
      <div className="glass-card p-6 md:p-8 space-y-5 animate-fade-up">
        <h1 className="display text-2xl font-extrabold">Создай аккаунт</h1>
        <p className="text-sm text-muted">Начни свой путь уже сегодня — это бесплатно.</p>
        <form className="space-y-4" onSubmit={onSubmit}>
          <div>
            <Label>Имя</Label>
            <Input value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </div>
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
            {loading ? "…" : "Зарегистрироваться"}
          </Button>
        </form>
        <p className="text-sm text-muted text-center">
          Уже есть аккаунт? <Link href="/sign-in" className="text-brand-500 dark:text-violet-300 hover:underline">Войти</Link>
        </p>
      </div>
    </div>
  );
}
