import { notFound } from "next/navigation";
import { API_URL } from "@/lib/constants";

export const dynamic = "force-dynamic";

type Post = {
  slug: string; title: string; content_html: string;
  cover_url: string | null;
  created_at: string;
  category: { name: string } | null;
};

async function fetchPost(slug: string): Promise<Post | null> {
  const res = await fetch(`${API_URL}/blog/posts/${slug}`, { cache: "no-store" });
  if (!res.ok) return null;
  return (await res.json()) as Post;
}

export default async function BlogPostPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const post = await fetchPost(slug);
  if (!post) return notFound();

  return (
    <article className="mx-auto max-w-3xl py-8 prose prose-invert dark:prose-invert">
      {post.category && <div className="text-xs text-brand-500 uppercase">{post.category.name}</div>}
      <h1 className="display text-3xl md:text-5xl font-extrabold mb-4">{post.title}</h1>
      {post.cover_url && (
        <img
          src={post.cover_url}
          alt={post.title}
          className="w-full h-auto max-h-[420px] object-cover rounded-2xl mb-5 border border-[var(--border)]"
        />
      )}
      <div
        className="glass-card p-6 prose max-w-none dark:prose-invert"
        dangerouslySetInnerHTML={{ __html: post.content_html }}
      />
    </article>
  );
}
