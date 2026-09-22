---
title: "Post title goes here"
date: 2026-01-01
description: "One or two sentences for search engines and social previews."
excerpt: "Optional – a slightly different, punchier teaser for the blog overview card. Falls back to the description above if you leave this out."
---

Write the post body here, in plain markdown: paragraphs, `## headings`,
`### sub-headings`, `**bold**`, `[links](https://example.com)`, and
`1.`/`-` lists all work.

Files starting with an underscore (like this one) are ignored by the build
script, so it's safe to leave this here as a reference. To add a real post:

1. Copy this file to `blog/_posts/YYYY-MM-DD-your-slug.md`
2. Fill in the front matter and write the body
3. Run `python3 scripts/build_blog.py` from the repo root
4. Commit the new markdown file, the generated `blog/posts/<slug>.html`,
   and the updated `blog/index.html` / `sitemap.xml`
