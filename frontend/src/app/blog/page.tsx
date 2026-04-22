import Link from "next/link";
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

export default async function BlogPage() {
  const posts = await fetchPosts();
  return (
    <div className="py-6">
      <h1 className="display text-3xl md:text-4xl font-extrabold mb-6">Блог / Исследования</h1>
      {posts.length === 0 ? (
        <div className="glass-card p-8 text-muted">Статьи скоро появятся.</div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {posts.map((p) => (
            <Link key={p.id} href={`/blog/${p.slug}`} className="glass-card p-4 hover:scale-[1.01] transition">
              <div className="h-40 rounded-xl bg-gradient-to-br from-violet-500/20 via-brand-500/10 to-transparent mb-3" />
              {p.category && <div className="text-[11px] text-brand-500 uppercase">{p.category.name}</div>}
              <div className="display font-bold text-lg">{p.title}</div>
              <p className="text-sm text-muted mt-1 line-clamp-2">{p.excerpt}</p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
