#!/usr/bin/env python3
"""Build static HTML from research/*/README.md and generate research/index.html."""

import glob
import os
from datetime import date, datetime
from html.parser import HTMLParser

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader

SITE_URL = os.environ.get("SITE_URL", "").rstrip("/")
SITE_TITLE = "Benedikt"
RESEARCH_DIR = "research"

_jinja_env = Environment(
    loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")),
    autoescape=False,  # body_html is trusted rendered Markdown; metadata is plain text
)


def url_for(path):
    """Return absolute URL when SITE_URL is set, otherwise root-relative path."""
    return f"{SITE_URL}{path}" if SITE_URL else path


# ── Markdown rendering ────────────────────────────────────────────────────────

def md_to_html(md_text):
    """Render Markdown to HTML. Returns (body_html, h2_tokens)."""
    md = markdown.Markdown(
        extensions=["extra", "sane_lists", "toc", "codehilite"],
        extension_configs={
            "codehilite": {"css_class": "codehilite", "linenums": False, "guess_lang": True},
        },
    )
    html = md.convert(md_text)

    def extract_h2(nodes):
        for node in nodes:
            if node.get("level") == 2:
                yield node
            elif node.get("level") == 1:
                yield from extract_h2(node.get("children", []))

    h2s = list(extract_h2(getattr(md, "toc_tokens", [])))
    return html, h2s


# ── HTML post-processing ──────────────────────────────────────────────────────

class _FigureWrapper(HTMLParser):
    """Transforms <p><img alt="…"></p> into <figure><img><figcaption>…</figcaption></figure>."""

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.out = []
        self._p_buf = None    # None outside a <p>; list while collecting <p> contents
        self._p_img = None    # (serialised_tag, alt_text) if an <img> was seen
        self._p_has_text = False

    def _serialise_attrs(self, attrs):
        parts = []
        for k, v in attrs:
            parts.append(k if v is None else f'{k}="{v}"')
        return (" " + " ".join(parts)) if parts else ""

    def handle_starttag(self, tag, attrs):
        serialised = f"<{tag}{self._serialise_attrs(attrs)}>"
        if tag == "p":
            self._p_buf = []
            self._p_img = None
            self._p_has_text = False
        elif self._p_buf is not None:
            if tag == "img":
                alt = dict(attrs).get("alt", "")
                self._p_img = (serialised, alt)
            self._p_buf.append(serialised)
        else:
            self.out.append(serialised)

    def handle_endtag(self, tag):
        if tag == "p" and self._p_buf is not None:
            if self._p_img and not self._p_has_text:
                img_tag, alt = self._p_img
                caption = f"<figcaption>{alt}</figcaption>" if alt else ""
                self.out.append(f"<figure>{img_tag}{caption}</figure>")
            else:
                self.out.append("<p>")
                self.out.extend(self._p_buf)
                self.out.append("</p>")
            self._p_buf = None
        elif self._p_buf is not None:
            self._p_buf.append(f"</{tag}>")
        else:
            self.out.append(f"</{tag}>")

    def handle_data(self, data):
        if self._p_buf is not None:
            if data.strip():
                self._p_has_text = True
            self._p_buf.append(data)
        else:
            self.out.append(data)

    def handle_entityref(self, name):
        s = f"&{name};"
        (self._p_buf if self._p_buf is not None else self.out).append(s)

    def handle_charref(self, name):
        s = f"&#{name};"
        (self._p_buf if self._p_buf is not None else self.out).append(s)


def wrap_images_in_figures(html):
    parser = _FigureWrapper()
    parser.feed(html)
    return "".join(parser.out)


# ── Metadata helpers ──────────────────────────────────────────────────────────

def parse_front_matter(text):
    """Split YAML front matter from Markdown body. Returns (meta_dict, body_str)."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    yaml_block = text[3:end].strip()
    body = text[end + 4:].lstrip("\n")
    try:
        meta = yaml.safe_load(yaml_block) or {}
    except yaml.YAMLError:
        meta = {}
    return meta, body


def first_heading(md_text):
    import re
    for line in md_text.splitlines():
        m = re.match(r"^#{1,2}\s+\**(.*?)\**\s*$", line)
        if m:
            return m.group(1).strip()
    return "Untitled"


def first_paragraph(html):
    import re
    m = re.search(r"<p>(.*?)</p>", html, re.DOTALL)
    if m:
        text = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        return text[:280] + ("…" if len(text) > 280 else "")
    return ""


def first_image_src(md_text):
    import re
    m = re.search(r"!\[.*?\]\(([^)]+)\)", md_text)
    return m.group(1) if m else None


def format_date(d):
    if isinstance(d, (date, datetime)):
        return d.strftime("%-d %B %Y")
    return str(d) if d else ""


# ── Build posts ───────────────────────────────────────────────────────────────

def build_post(readme_path):
    slug = os.path.basename(os.path.dirname(readme_path))
    post_dir = os.path.dirname(readme_path)

    with open(readme_path, encoding="utf-8") as f:
        raw = f.read()

    meta, body_md = parse_front_matter(raw)

    if meta.get("draft"):
        print(f"  skip (draft): {slug}")
        return None

    body_html, h2s = md_to_html(body_md)
    body_html = wrap_images_in_figures(body_html)

    title = meta.get("title") or first_heading(body_md)
    description = meta.get("description") or first_paragraph(body_html)
    tags = meta.get("tags") or []

    raw_date = meta.get("date")
    if raw_date:
        post_date = raw_date
    else:
        post_date = datetime.fromtimestamp(os.path.getmtime(readme_path)).date()

    og_image_file = meta.get("og_image") or first_image_src(body_md)
    og_image_url = url_for(f"/{RESEARCH_DIR}/{slug}/{og_image_file}") if og_image_file else url_for("/me.webp")
    canonical = url_for(f"/{RESEARCH_DIR}/{slug}/")
    date_str = format_date(post_date)

    html = _jinja_env.get_template("post.html.j2").render(
        title=title,
        site_title=SITE_TITLE,
        description=description,
        canonical=canonical,
        og_image_url=og_image_url,
        date_str=date_str,
        tags=tags,
        body_html=body_html,
        toc_h2s=h2s,
    )

    out_path = os.path.join(post_dir, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  built: {out_path}")
    return {
        "slug": slug,
        "title": title,
        "description": description,
        "date": post_date,
        "date_str": date_str,
        "tags": tags,
    }


# ── Build listing ─────────────────────────────────────────────────────────────

def build_listing(posts):
    posts_sorted = sorted(posts, key=lambda p: p["date"], reverse=True)
    html = _jinja_env.get_template("listing.html.j2").render(
        site_title=SITE_TITLE,
        canonical=url_for("/research/"),
        posts=posts_sorted,
    )
    out_path = os.path.join(RESEARCH_DIR, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  built: {out_path}")


# ── Build sitemap + robots ────────────────────────────────────────────────────

def build_sitemap(posts):
    today = date.today().isoformat()
    urls = [
        f"  <url><loc>{url_for('/')}</loc><lastmod>{today}</lastmod><priority>1.0</priority></url>",
        f"  <url><loc>{url_for('/research/')}</loc><lastmod>{today}</lastmod><priority>0.8</priority></url>",
    ]
    for p in posts:
        d = p["date"].isoformat() if hasattr(p["date"], "isoformat") else today
        loc = url_for(f"/research/{p['slug']}/")
        urls.append(f"  <url><loc>{loc}</loc><lastmod>{d}</lastmod><priority>0.9</priority></url>")
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap)
    print("  built: sitemap.xml")

    sitemap_line = f"Sitemap: {url_for('/sitemap.xml')}\n" if SITE_URL else ""
    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\n{sitemap_line}")
    print("  built: robots.txt")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    readmes = sorted(glob.glob(f"{RESEARCH_DIR}/*/README.md"))
    if not readmes:
        print("No README.md files found in research/*/")
        return

    posts = []
    for path in readmes:
        print(f"Processing {path} ...")
        result = build_post(path)
        if result:
            posts.append(result)

    if posts:
        print("Building listing page ...")
        build_listing(posts)
        print("Building sitemap + robots.txt ...")
        build_sitemap(posts)

    print(f"\nDone. {len(posts)} post(s) built.")


if __name__ == "__main__":
    main()
