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
    {
        "slug": "rir-and-rpe-for-better-progression",
        "title": "RIR & RPE: practical auto-regulation",
        "excerpt": "How to use RIR and RPE to push progress without burning out.",
        "content_md": """# RIR & RPE: practical auto-regulation

RIR (reps in reserve) shows how many clean reps are left in the tank.

- RIR 3-4: technique work and easier accumulation
- RIR 2: core work zone for stable progression
- RIR 0-1: rare hard exposure, not every session

In this project test week uses **RIR 2** to estimate strength safely and then
recalculate working weights.
""",
    },
    {
        "slug": "weekly-volume-what-actually-drives-growth",
        "title": "Weekly volume: what drives growth",
        "excerpt": "A simple way to manage weekly sets and avoid junk volume.",
        "content_md": """# Weekly volume: what drives growth

For most lifters, progress comes from sustainable weekly quality volume.

Rules of thumb:

1. Start with moderate weekly sets per muscle.
2. Increase only when recovery stays good.
3. If performance drops for several sessions, reduce stress and recover.

Consistency beats random high-volume spikes.
""",
    },
    {
        "slug": "deload-weeks-without-losing-momentum",
        "title": "Deload weeks without losing momentum",
        "excerpt": "Why deloads help long-term gains and how to run them correctly.",
        "content_md": """# Deload weeks without losing momentum

Deload is not a step back - it is a strategic reduction of fatigue.

Typical deload setup:

- Lower load (~10%)
- Lower set count (1-2 sets less per exercise)
- Keep movement quality high

After deload, most athletes return stronger and more stable.
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
