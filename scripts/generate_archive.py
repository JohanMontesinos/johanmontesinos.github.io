#!/usr/bin/env python3
"""
generate_archive.py
-------------------
Reads every <article class="post-card"> from index.html and
regenerates archive.html, grouping posts by year → month.

Run locally:  python scripts/generate_archive.py
Run via CI:   triggered automatically by GitHub Actions on every push.
"""

import re
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from html.parser import HTMLParser

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT         = Path(__file__).parent.parent   # repo root
INDEX_FILE   = ROOT / "index.html"
ARCHIVE_FILE = ROOT / "archive.html"

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

# ── Minimal HTML parser to extract post cards ────────────────────────────────
class PostCardParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.posts = []
        self._in_article   = False
        self._in_title_a   = False
        self._in_excerpt   = False
        self._in_meta      = False
        self._current      = {}
        self._meta_text    = ""
        self._depth        = 0          # tracks nesting inside article

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        if tag == "article" and "post-card" in attrs.get("class", ""):
            self._in_article = True
            self._current    = {"title": "", "href": "", "excerpt": "",
                                 "date_str": "", "read_time": ""}
            self._depth      = 0
            return

        if not self._in_article:
            return

        self._depth += 1

        cls = attrs.get("class", "")

        if tag == "a" and "post-card-title" in cls:
            # <a> directly on the title element (older markup)
            self._in_title_a = True
            self._current["href"] = attrs.get("href", "")

        if tag == "a" and self._in_article:
            # <a> inside .post-card-title
            parent_is_title = "post-card-title" in cls
            if parent_is_title or self._current.get("_title_tag_open"):
                self._in_title_a = True
                self._current["href"] = attrs.get("href", "")

        if tag in ("h2", "h3", "h4") and "post-card-title" in cls:
            self._current["_title_tag_open"] = True

        if tag == "a" and self._current.get("_title_tag_open") and not self._current["href"]:
            self._in_title_a = True
            self._current["href"] = attrs.get("href", "")

        if tag == "p" and "post-card-text" in cls:
            self._in_excerpt = True

        if tag == "div" and "post-meta" in cls:
            self._in_meta    = True
            self._meta_text  = ""

    def handle_endtag(self, tag):
        if not self._in_article:
            return

        if tag == "a" and self._in_title_a:
            self._in_title_a = False

        if tag == "p" and self._in_excerpt:
            self._in_excerpt = False

        if tag == "div" and self._in_meta:
            self._in_meta = False
            text = self._meta_text.strip()
            m_date = re.search(r'([A-Z][a-z]+ \d{1,2}, \d{4})', text)
            m_time = re.search(r'(\d+ min read)', text)
            if m_date: self._current["date_str"]  = m_date.group(1)
            if m_time: self._current["read_time"] = m_time.group(1)

        if tag == "article":
            self._in_article = False
            self._current.pop("_title_tag_open", None)
            if self._current.get("title") or self._current.get("href"):
                self.posts.append(dict(self._current))

    def handle_data(self, data):
        if self._in_title_a:
            self._current["title"] += data
        if self._in_excerpt:
            self._current["excerpt"] += data
        if self._in_meta:
            self._meta_text += data


# ── Parse posts from index.html ───────────────────────────────────────────────
def parse_posts(index_path: Path) -> list[dict]:
    html = index_path.read_text(encoding="utf-8")
    parser = PostCardParser()
    parser.feed(html)

    posts = []
    for p in parser.posts:
        title    = p["title"].strip()
        href     = p["href"].strip()
        excerpt  = p["excerpt"].strip()
        date_str = p["date_str"].strip()
        read_time = p["read_time"].strip()

        date_obj = None
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, "%B %d, %Y")
            except ValueError:
                pass

        posts.append({
            "title":     title,
            "href":      href,
            "excerpt":   excerpt,
            "date_str":  date_str,
            "date_obj":  date_obj,
            "read_time": read_time,
        })

    # Sort newest → oldest
    posts.sort(key=lambda p: p["date_obj"] or datetime.min, reverse=True)
    return posts


# ── Group posts by year → month ───────────────────────────────────────────────
def group_posts(posts: list[dict]) -> dict:
    grouped = defaultdict(lambda: defaultdict(list))
    for p in posts:
        year  = p["date_obj"].year  if p["date_obj"] else "Unknown"
        month = p["date_obj"].month if p["date_obj"] else 0
        grouped[year][month].append(p)
    return grouped


# ── HTML generation ───────────────────────────────────────────────────────────
def render_post_item(p: dict) -> str:
    excerpt_html = (
        f'<p class="post-item-excerpt">{p["excerpt"]}</p>' if p["excerpt"] else ""
    )
    meta_html = (
        f'<i class="far fa-clock"></i> {p["read_time"]}' if p["read_time"] else ""
    )
    return f"""
                        <li class="post-item">
                            <div class="post-item-date">{p['date_str'] or 'Date unknown'}</div>
                            <h4 class="post-item-title">
                                <a href="{p['href']}">{p['title']}</a>
                            </h4>
                            {excerpt_html}
                            <div class="post-item-meta">{meta_html}</div>
                        </li>"""


def render_archive(posts: list[dict], grouped: dict) -> str:
    # Stats
    total_posts   = len(posts)
    total_years   = len([y for y in grouped if y != "Unknown"])
    active_months = sum(len(months) for months in grouped.values())

    # Year/month sections
    archive_sections = ""
    for year in sorted(grouped.keys(), reverse=True):
        month_sections = ""
        for month in sorted(grouped[year].keys(), reverse=True):
            month_name   = MONTHS[month - 1] if month else "Unknown"
            posts_html   = "".join(render_post_item(p) for p in grouped[year][month])
            month_sections += f"""
                    <div class="month-section">
                        <h3 class="month-header">
                            <i class="far fa-calendar"></i> {month_name}
                        </h3>
                        <ul class="post-list">
                            {posts_html}
                        </ul>
                    </div>"""

        archive_sections += f"""
                <div class="year-section">
                    <h2 class="year-header">{year}</h2>
                    {month_sections}
                </div>"""

    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Archive - JoHaN's Blog</title>

    <!-- Bootstrap CSS -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.2/css/bootstrap.min.css" rel="stylesheet">

    <!-- FontAwesome -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">

    <!-- Custom CSS Files -->
    <link href="sticky-footer-navbar.css" rel="stylesheet">
    <link href="cmun-serif.css" rel="stylesheet">
    <link href="cmun-serif-slanted.css" rel="stylesheet">

    <style>
        body {{
            font-family: 'Computer Modern Serif', 'CMU Serif', Georgia, serif;
            background-color: #fefefe;
            color: #2d2d2d;
            line-height: 1.6;
        }}

        .navbar {{
            background-color: #fff;
            border-bottom: 1px solid #ddd;
            padding: 1rem 0;
        }}

        .navbar-brand {{
            font-size: 1.5rem;
            font-weight: 600;
            letter-spacing: 0.5px;
        }}

        main {{
            padding-top: 6rem;
            padding-bottom: 4rem;
        }}

        .archive-header {{
            text-align: center;
            margin-bottom: 3rem;
            padding: 2rem 0;
        }}

        .archive-header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            letter-spacing: 1px;
        }}

        .archive-header p {{
            font-style: italic;
            color: #666;
            font-size: 1.1rem;
        }}

        .archive-container {{
            max-width: 900px;
            margin: 0 auto;
        }}

        .year-section {{
            margin-bottom: 3rem;
        }}

        .year-header {{
            font-size: 2rem;
            font-weight: 700;
            color: #0056b3;
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 3px solid #0056b3;
        }}

        .month-section {{
            margin-bottom: 2rem;
            margin-left: 1rem;
        }}

        .month-header {{
            font-size: 1.4rem;
            font-weight: 600;
            color: #555;
            margin-bottom: 1rem;
        }}

        .post-list {{
            list-style: none;
            padding-left: 0;
        }}

        .post-item {{
            padding: 1rem;
            margin-bottom: 0.75rem;
            background: #fff;
            border: 1px solid #e0e0e0;
            transition: all 0.3s ease;
        }}

        .post-item:hover {{
            border-color: #0056b3;
            box-shadow: 0 2px 8px rgba(0, 86, 179, 0.1);
        }}

        .post-item-date {{
            font-size: 0.9rem;
            color: #888;
            margin-bottom: 0.5rem;
        }}

        .post-item-title {{
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }}

        .post-item-title a {{
            color: #2d2d2d;
            text-decoration: none;
        }}

        .post-item-title a:hover {{
            color: #0056b3;
        }}

        .post-item-excerpt {{
            font-size: 0.95rem;
            color: #555;
            font-style: italic;
            margin-bottom: 0.5rem;
        }}

        .post-item-meta {{
            font-size: 0.85rem;
            color: #999;
        }}

        .post-item-meta i {{
            margin-right: 0.3rem;
        }}

        .search-box {{
            margin-bottom: 2rem;
            padding: 1.5rem;
            background: #f9f9f9;
            border: 1px solid #e0e0e0;
        }}

        .search-box input {{
            font-family: 'Computer Modern Serif', 'CMU Serif', Georgia, serif;
            font-size: 1rem;
        }}

        .stats-box {{
            background-color: #f9f9f9;
            border-left: 4px solid #0056b3;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }}

        .stats-box h3 {{
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 1rem;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
        }}

        .stat-item {{
            text-align: center;
        }}

        .stat-number {{
            font-size: 2rem;
            font-weight: 700;
            color: #0056b3;
        }}

        .stat-label {{
            font-size: 0.9rem;
            color: #666;
        }}

        .generated-note {{
            text-align: right;
            font-size: 0.8rem;
            color: #bbb;
            font-style: italic;
            margin-bottom: 1rem;
        }}

        #no-results {{
            display: none;
            text-align: center;
            padding: 2rem;
            font-style: italic;
            color: #888;
        }}

        footer {{
            background-color: #f8f9fa;
            border-top: 1px solid #e0e0e0;
            padding: 2rem 0;
            margin-top: 3rem;
        }}

        @media (max-width: 768px) {{
            .archive-header h1 {{ font-size: 2rem; }}
            .month-section {{ margin-left: 0; }}
        }}
    </style>
</head>
<body class="d-flex flex-column min-vh-100">

    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg fixed-top navbar-light">
        <div class="container">
            <a class="navbar-brand" href="index.html">
                <i class="fas fa-feather-alt"></i> JoHaN's Blog
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link" href="index.html">Home</a></li>
                    <li class="nav-item"><a class="nav-link" href="about.html">About</a></li>
                    <li class="nav-item"><a class="nav-link active" href="archive.html">Archive</a></li>
                    <li class="nav-item"><a class="nav-link" href="contact.html">Contact</a></li>
                </ul>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="flex-fill">
        <div class="container">
            <div class="archive-header">
                <h1>Article Archive</h1>
                <p>A complete collection of all published articles</p>
            </div>

            <div class="archive-container">

                <!-- Search Box -->
                <div class="search-box">
                    <div class="input-group">
                        <span class="input-group-text"><i class="fas fa-search"></i></span>
                        <input type="text" id="search-input" class="form-control"
                               placeholder="Search articles by title or keyword...">
                    </div>
                </div>

                <!-- Statistics -->
                <div class="stats-box">
                    <h3><i class="fas fa-chart-bar"></i> Archive Statistics</h3>
                    <div class="stats-grid">
                        <div class="stat-item">
                            <div class="stat-number">{total_posts}</div>
                            <div class="stat-label">Total Articles</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">{total_years}</div>
                            <div class="stat-label">Years</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">{active_months}</div>
                            <div class="stat-label">Active Months</div>
                        </div>
                    </div>
                </div>

                <!-- Auto-generated note -->
                <p class="generated-note">
                    <i class="fas fa-robot"></i> Auto-generated by GitHub Actions · {generated_at}
                </p>

                <!-- Archive sections -->
                <div id="archive-root">
                    {archive_sections}
                </div>

                <p id="no-results">No articles matched your search.</p>

            </div>
        </div>
    </main>

    <!-- Footer -->
    <footer>
        <div class="container">
            <div class="row">
                <div class="col-md-6">
                    <p class="mb-0">&copy; 2024 JoHaN's Blog. All rights reserved.</p>
                </div>
                <div class="col-md-6 text-md-end">
                    <a href="https://github.com/JohanMontesinos/" class="text-decoration-none me-3">
                        <i class="fab fa-github"></i> GitHub</a>
                    <a href="https://x.com/johanmontesinos" class="text-decoration-none me-3">
                        <i class="fab fa-twitter"></i> X</a>
                    <a href="mailto:johan.montesinos@outlook.com" class="text-decoration-none">
                        <i class="fas fa-envelope"></i> Email</a>
                </div>
            </div>
        </div>
    </footer>

    <!-- Bootstrap JS -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.2/js/bootstrap.bundle.min.js"></script>

    <!-- GoatCounter Analytics -->
    <script data-goatcounter="https://johanmontesinos.goatcounter.com/count"
            async src="//gc.zgo.at/count.js"></script>

    <!-- Live search (client-side filter over the static list) -->
    <script>
    document.getElementById('search-input').addEventListener('input', function () {{
        const q = this.value.toLowerCase().trim();
        const items = document.querySelectorAll('.post-item');
        let visible = 0;
        items.forEach(item => {{
            const text = item.textContent.toLowerCase();
            const show = !q || text.includes(q);
            item.style.display = show ? '' : 'none';
            if (show) visible++;
        }});
        // Hide empty month/year sections
        document.querySelectorAll('.month-section').forEach(sec => {{
            const any = [...sec.querySelectorAll('.post-item')].some(i => i.style.display !== 'none');
            sec.style.display = any ? '' : 'none';
        }});
        document.querySelectorAll('.year-section').forEach(sec => {{
            const any = [...sec.querySelectorAll('.post-item')].some(i => i.style.display !== 'none');
            sec.style.display = any ? '' : 'none';
        }});
        document.getElementById('no-results').style.display = visible === 0 ? 'block' : 'none';
    }});
    </script>

</body>
</html>
"""


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    if not INDEX_FILE.exists():
        print(f"ERROR: {INDEX_FILE} not found.", file=sys.stderr)
        sys.exit(1)

    print(f"Parsing posts from {INDEX_FILE} …")
    posts   = parse_posts(INDEX_FILE)
    grouped = group_posts(posts)

    print(f"Found {len(posts)} post(s) across {len(grouped)} year(s).")
    for year in sorted(grouped.keys(), reverse=True):
        for month, ps in sorted(grouped[year].items(), reverse=True):
            month_name = MONTHS[month - 1] if month else "Unknown"
            print(f"  {year} / {month_name}: {len(ps)} post(s)")

    html = render_archive(posts, grouped)
    ARCHIVE_FILE.write_text(html, encoding="utf-8")
    print(f"✓ {ARCHIVE_FILE} written successfully.")


if __name__ == "__main__":
    main()
