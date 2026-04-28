import Link from "next/link";
import { ArrowRight, Search } from "lucide-react";
import { API_URL } from "@/lib/constants";

export const dynamic = "force-dynamic";

type Post = {
  id: number; slug: string; title: string; excerpt: string;
  cover_url: string | null; created_at: string;
  category: { name: string; slug: string } | null;
};

async function fetchPosts(): Promise<Post[]> {
  try {
    const res = await fetch(`${API_URL}/blog/posts`, { cache: "no-store" });
    if (!res.ok) return [];
    return (await res.json()) as Post[];
  } catch {
    return [];
  }
}

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleDateString("ru-RU", { day: "2-digit", month: "long", year: "numeric" });
  } catch {
    return "";
  }
}

export default async function BlogPage() {
  const posts = await fetchPosts();

  return (
    <div className="py-8 space-y-8 animate-fade-up">
      <div className="text-center space-y-4">
        <h1 className="display text-3xl md:text-5xl font-extrabold tracking-tight">
          <span className="gradient-text">Science-backed</span> fitness
        </h1>
        <p className="text-muted max-w-xl mx-auto">
          Исследования. Факты. Результаты. Подборка материалов о тренировках, питании и восстановлении.
        </p>
        <div className="relative max-w-xl mx-auto">
          <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-muted pointer-events-none" />
          <input
            type="search"
            placeholder="Поиск по статьям…"
            className="w-full rounded-2xl pl-11 pr-4 py-3 text-sm bg-white/70 dark:bg-white/[0.04] border border-[var(--border)] outline-none transition placeholder:text-muted focus:border-[var(--border-strong)] focus:ring-2 focus:ring-[var(--ring)]"
          />
        </div>
      </div>

      {posts.length === 0 ? (
        <div className="glass-card p-10 text-center text-muted">Статьи скоро появятся.</div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {posts.map((p) => (
            <Link
              key={p.id}
              href={`/blog/${p.slug}`}
              className="group glass-card p-3 overflow-hidden hover-lift hover:shadow-glow-brand dark:hover:shadow-glow transition-shadow"
            >
              <div className="relative h-44 rounded-xl overflow-hidden bg-gradient-to-br from-violet-500/30 via-brand-500/15 to-pink-500/20 dark:from-accent-500/35 dark:via-violet-500/15 dark:to-pink-500/30">
                {p.cover_url ? (
                  <img
                    src={p.cover_url}
                    alt={p.title}
                    className="absolute inset-0 h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                  />
                ) : (
                  <div className="absolute inset-0 grid-bg opacity-25" />
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-black/55 to-transparent" />
                {p.category && (
                  <span className="absolute top-3 left-3 text-[10px] px-2.5 py-1 rounded-full bg-black/55 text-white font-semibold uppercase tracking-wide backdrop-blur-sm">
                    {p.category.name}
                  </span>
                )}
                <div className="absolute bottom-3 left-3 right-3 text-white">
                  <div className="display font-extrabold text-base md:text-lg leading-tight line-clamp-2">{p.title}</div>
                </div>
              </div>
              <div className="p-3 flex items-center justify-between">
                <span className="text-xs text-muted">{formatDate(p.created_at)}</span>
                <span className="text-xs font-semibold text-brand-500 dark:text-violet-300 inline-flex items-center gap-1 group-hover:gap-2 transition-all">
                  Читать далее <ArrowRight size={12} />
                </span>
              </div>
              {p.excerpt && (
                <p className="text-xs text-muted px-3 pb-3 line-clamp-2 -mt-1">{p.excerpt}</p>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
