#!/usr/bin/env python3
"""
Build the fw-consulting.io blog from markdown source files.

Usage:
    python3 scripts/build_blog.py

What it does:
    - Reads every *.md file in blog/_posts/
    - Each file needs YAML front matter (title, date, description) followed
      by the post body in markdown
    - Renders each post to its own static page at blog/posts/<slug>.html,
      using blog/_templates/post_template.html
    - Rewrites the post list on blog/index.html (between the
      <!-- POSTS:START --> / <!-- POSTS:END --> markers), newest first

Adding a new post:
    1. Copy blog/_posts/_example.md to blog/_posts/YYYY-MM-DD-your-slug.md
    2. Fill in the front matter and write the post in markdown
    3. Run this script
    4. Commit + push blog/_posts/<file>.md, blog/posts/<slug>.html and
       the regenerated blog/index.html

No server, no database, no comments – every post is still a plain static
HTML file, this script just saves you from hand-editing the template and
the index each time.
"""

import re
import sys
from pathlib import Path
from datetime import datetime

import markdown
import yaml

ROOT = Path(__file__).resolve().parent.parent
POSTS_SRC = ROOT / "blog" / "_posts"
POSTS_OUT = ROOT / "blog" / "posts"
BLOG_INDEX = ROOT / "blog" / "index.html"
POST_TEMPLATE = ROOT / "blog" / "_templates" / "post_template.html"

FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n(.*)$", re.DOTALL)


def load_post(path: Path):
    raw = path.read_text(encoding="utf-8")
    m = FRONT_MATTER_RE.match(raw)
    if not m:
        raise ValueError(f"{path.name}: missing YAML front matter (--- ... ---)")

    meta = yaml.safe_load(m.group(1)) or {}
    body_md = m.group(2).strip()

    for field in ("title", "date", "description"):
        if not meta.get(field):
            raise ValueError(f"{path.name}: front matter is missing '{field}'")

    date = meta["date"]
    if isinstance(date, str):
        date = datetime.strptime(date, "%Y-%m-%d").date()

    slug = meta.get("slug") or slugify(path.stem)

    excerpt = meta.get("excerpt") or meta["description"]

    body_html = markdown.markdown(body_md, extensions=["extra", "sane_lists"])

    return {
        "title": meta["title"],
        "description": meta["description"],
        "excerpt": excerpt,
        "date": date,
        "slug": slug,
        "body_html": body_html,
        "source": path.name,
    }


def slugify(text: str) -> str:
    text = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", text)  # strip leading date
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def render_post(post: dict) -> str:
    tpl = POST_TEMPLATE.read_text(encoding="utf-8")
    date_display = post["date"].strftime("%B %-d, %Y")
    # indent body to match the template's <article> nesting
    body_indented = "\n".join(
        ("      " + line if line.strip() else line)
        for line in post["body_html"].splitlines()
    )
    out = tpl
    out = out.replace("{{TITLE}}", post["title"])
    out = out.replace("{{DESCRIPTION}}", post["description"])
    out = out.replace("{{SLUG}}", post["slug"])
    out = out.replace("{{DATE_DISPLAY}}", date_display)
    out = out.replace("{{BODY}}", body_indented)
    return out


def render_card(post: dict) -> str:
    date_display = post["date"].strftime("%B %-d, %Y")
    return (
        f'      <a class="post-card" href="/blog/posts/{post["slug"]}.html">\n'
        f'        <div class="post-date">{date_display}</div>\n'
        f'        <h2 class="post-title">{post["title"]}</h2>\n'
        f'        <p class="post-excerpt">{post["excerpt"]}</p>\n'
        f"      </a>"
    )


def update_index(posts: list):
    html = BLOG_INDEX.read_text(encoding="utf-8")
    start_marker = "<!-- POSTS:START -->"
    end_marker = "<!-- POSTS:END -->"
    if start_marker not in html or end_marker not in html:
        raise ValueError(
            "blog/index.html is missing the POSTS:START/POSTS:END markers"
        )

    if posts:
        cards = "\n".join(render_card(p) for p in posts)
        block = f"{start_marker}\n{cards}\n{end_marker}"
    else:
        block = (
            f"{start_marker}\n"
            "      <div class=\"empty\">\n"
            "        The first post is coming soon.\n"
            "      </div>\n"
            f"{end_marker}"
        )

    new_html = re.sub(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        block.replace("\\", "\\\\"),
        html,
        flags=re.DOTALL,
    )
    BLOG_INDEX.write_text(new_html, encoding="utf-8")


def update_sitemap(posts: list):
    sitemap = ROOT / "sitemap.xml"
    xml = sitemap.read_text(encoding="utf-8")
    entries = []
    for p in posts:
        url = f"https://fw-consulting.io/blog/posts/{p['slug']}.html"
        if url not in xml:
            entries.append(
                f"  <url>\n    <loc>{url}</loc>\n"
                f"    <changefreq>monthly</changefreq>\n    <priority>0.6</priority>\n  </url>"
            )
    if entries:
        xml = xml.replace("</urlset>", "\n".join(entries) + "\n</urlset>")
        sitemap.write_text(xml, encoding="utf-8")


def main():
    POSTS_OUT.mkdir(parents=True, exist_ok=True)
    md_files = sorted(
        p for p in POSTS_SRC.glob("*.md") if not p.name.startswith("_")
    )

    if not md_files:
        print("No posts found in blog/_posts/ – writing empty state to the index.")
        update_index([])
        return

    posts = []
    for path in md_files:
        try:
            posts.append(load_post(path))
        except ValueError as e:
            print(f"Skipping {path.name}: {e}", file=sys.stderr)

    posts.sort(key=lambda p: p["date"], reverse=True)

    for post in posts:
        out_path = POSTS_OUT / f"{post['slug']}.html"
        out_path.write_text(render_post(post), encoding="utf-8")
        print(f"wrote {out_path.relative_to(ROOT)}")

    update_index(posts)
    update_sitemap(posts)
    print(f"updated {BLOG_INDEX.relative_to(ROOT)} and sitemap.xml with {len(posts)} post(s)")


if __name__ == "__main__":
    main()
