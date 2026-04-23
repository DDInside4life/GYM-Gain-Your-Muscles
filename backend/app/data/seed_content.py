from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.blog import BlogPost
from app.models.forum import ForumQuestion

FAQ_SEED = [
    {"title": "How many sets to failure are safe weekly?", "body": "Keep failure sets mostly in test weeks. In work weeks stop 1-2 reps before failure."},
    {"title": "What if my knee hurts on squats?", "body": "Replace barbell squats with goblet squat or leg press and reduce load until pain-free."},
    {"title": "How do I use test week data?", "body": "Log reps and weight for each test set. The system calculates 1RM via Epley and updates work loads."},
    {"title": "Can I train 5 days with beginner experience?", "body": "Possible, but recovery must be controlled. Start with 3-4 days and increase only with stable sleep and soreness."},
    {"title": "What does fatigue control do in week 4?", "body": "It lowers total stress (usually fewer sets) to keep progression sustainable into re-test week."},
]

BLOG_SEED = [
    {
        "slug": "epley-formula-in-practice",
        "title": "Epley Formula in Practice",
        "excerpt": "How to convert test-set reps into usable training weights.",
        "content_md": """# Epley Formula in Practice

Use: `1RM = weight * (1 + reps / 30)`.

If you perform 80kg x 10 reps, estimated 1RM is `106.7kg`.

For hypertrophy, start around 65-80% 1RM. For strength, 80-90%.
""",
    },
    {
        "slug": "periodization-for-natural-lifters",
        "title": "Periodization for Natural Lifters",
        "excerpt": "Simple month cycle: test, build, manage fatigue, re-test.",
        "content_md": """# Periodization for Natural Lifters

The practical cycle:

1. Week 1: test week
2. Week 2-3: progressive overload
3. Week 4: fatigue control
4. Week 5: re-test
""",
    },
    {
        "slug": "when-to-adjust-working-weight",
        "title": "When to Adjust Working Weight",
        "excerpt": "Use performance and recovery, not ego, to drive load changes.",
        "content_md": """# When to Adjust Working Weight

Increase weight when:

- You hit top reps across all sets with clean form.
- Recovery markers are stable.

Decrease or hold when:

- Technique breaks early.
- Joint discomfort accumulates.
""",
    },
]


async def ensure_seed_content(db: AsyncSession, author_id: int) -> None:
    existing_q = {t for t in (await db.execute(select(ForumQuestion.title))).scalars().all()}
    existing_posts = {s for s in (await db.execute(select(BlogPost.slug))).scalars().all()}

    for item in FAQ_SEED:
        if item["title"] in existing_q:
            continue
        db.add(ForumQuestion(
            user_id=author_id,
            title=item["title"],
            body=item["body"],
            tags=["training", "faq"],
            is_approved=True,
        ))

    for post in BLOG_SEED:
        if post["slug"] in existing_posts:
            continue
        db.add(BlogPost(
            slug=post["slug"],
            title=post["title"],
            excerpt=post["excerpt"],
            content_md=post["content_md"],
            is_published=True,
            author_id=author_id,
        ))

    await db.commit()
