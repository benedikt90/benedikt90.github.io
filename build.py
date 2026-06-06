#!/usr/bin/env python3
"""Build static HTML from research/*/README.md and generate research/index.html."""

import glob
import os
import re
from datetime import date, datetime

import markdown
import yaml

SITE_URL = os.environ.get("SITE_URL", "").rstrip("/")
SITE_TITLE = "Benedikt"
RESEARCH_DIR = "research"


def url_for(path):
    """Return absolute URL if SITE_URL is set, otherwise root-relative path."""
    return f"{SITE_URL}{path}" if SITE_URL else path

# ── HTML template shared by all post pages ────────────────────────────────────

POST_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} – {site_title}</title>
  <meta name="description" content="{description}" />
  <link rel="canonical" href="{canonical}" />
  <!-- Open Graph -->
  <meta property="og:type" content="article" />
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{description}" />
  <meta property="og:url" content="{canonical}" />
  <meta property="og:image" content="{og_image_url}" />
  <meta property="og:site_name" content="{site_title}" />
  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{title}" />
  <meta name="twitter:description" content="{description}" />
  <meta name="twitter:image" content="{og_image_url}" />
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    html, body {{
      height: 100%;
      background: #080c08;
      font-family: 'Courier New', Courier, monospace;
      overflow-x: hidden;
    }}

    html {{ scroll-behavior: smooth; }}

    #bg {{
      position: fixed;
      inset: 0;
      z-index: 0;
      opacity: 0.14;
    }}

    /* ── Top bar ── */
    .topbar {{
      position: relative;
      z-index: 2;
      padding: 1rem 2rem;
      display: flex;
      align-items: center;
      border-bottom: 1px solid rgba(100, 140, 255, 0.1);
    }}

    .topbar a {{
      color: #7a9acc;
      text-decoration: none;
      font-size: 0.78rem;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      transition: color 0.2s;
    }}

    .topbar a:hover {{ color: #c8d8f0; }}
    .topbar a::before {{ content: '← '; }}

    /* ── Layout ── */
    main {{
      position: relative;
      z-index: 1;
      max-width: 780px;
      margin: 0 auto;
      padding: 2rem 2rem 4rem;
    }}

    /* ── Glass reading panel ── */
    .content {{
      background: rgba(8, 12, 20, 0.62);
      backdrop-filter: blur(10px) saturate(1.1);
      -webkit-backdrop-filter: blur(10px) saturate(1.1);
      border: 1px solid rgba(100, 140, 255, 0.13);
      border-radius: 8px;
      padding: 2.5rem 3rem;
    }}

    /* ── Post header ── */
    .post-meta {{
      margin-bottom: 2.5rem;
      padding-bottom: 1.5rem;
      border-bottom: 1px solid rgba(100, 140, 255, 0.12);
    }}

    .post-date {{
      font-size: 0.72rem;
      letter-spacing: 0.16em;
      text-transform: uppercase;
      color: #4a6a9a;
      margin-bottom: 0.9rem;
    }}

    .post-title {{
      font-family: 'Courier New', Courier, monospace;
      font-size: clamp(1.4rem, 4vw, 2rem);
      line-height: 1.3;
      letter-spacing: 0.04em;
      color: #e8f0ff;
      text-shadow: 0 0 24px rgba(100, 140, 255, 0.4);
      margin-bottom: 1rem;
    }}

    .post-description {{
      font-size: 0.95rem;
      line-height: 1.65;
      color: #7a9acc;
      font-family: -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }}

    .post-tags {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.4rem;
      margin-top: 1rem;
    }}

    .post-tag {{
      font-size: 0.68rem;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      border: 1px solid rgba(100, 140, 255, 0.2);
      border-radius: 2px;
      padding: 0.2rem 0.55rem;
      color: #5a7aaa;
      background: rgba(80, 120, 255, 0.05);
      font-family: 'Courier New', Courier, monospace;
    }}

    /* ── Article body ── */
    article {{
      font-family: -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      font-size: 1.02rem;
      line-height: 1.82;
      color: #b8cce4;
    }}

    article h1, article h2, article h3, article h4 {{
      font-family: 'Courier New', Courier, monospace;
      color: #e8f0ff;
      text-shadow: 0 0 16px rgba(100, 140, 255, 0.35);
      letter-spacing: 0.05em;
      margin-top: 2.4rem;
      margin-bottom: 0.75rem;
      line-height: 1.3;
      scroll-margin-top: 1.5rem;
    }}

    article h1 {{ font-size: 1.65rem; display: none; }}
    article h2 {{ font-size: 1.25rem; border-bottom: 1px solid rgba(100,140,255,0.1); padding-bottom: 0.4rem; }}
    article h3 {{ font-size: 1.05rem; color: #b8d0ff; text-shadow: none; }}
    article h4 {{ font-size: 0.95rem; color: #8aaad0; text-shadow: none; letter-spacing: 0.08em; text-transform: uppercase; }}

    article p {{ margin-bottom: 1.2rem; }}

    article a {{
      color: #6a9adf;
      text-decoration: underline;
      text-underline-offset: 3px;
      transition: color 0.2s;
    }}
    article a:hover {{ color: #a8c8ff; }}

    article strong {{ color: #d0e4ff; font-weight: 600; }}
    article em {{ color: #9ab8d8; font-style: italic; }}

    article ul, article ol {{ margin: 0.4rem 0 1.2rem 1.6rem; }}
    article li {{ margin-bottom: 0.4rem; }}
    article li p {{ margin-bottom: 0; }}

    article blockquote {{
      border-left: 3px solid rgba(100, 140, 255, 0.35);
      margin: 1.5rem 0;
      padding: 0.75rem 1.25rem;
      background: rgba(80, 120, 255, 0.05);
      border-radius: 0 4px 4px 0;
      color: #8aaad0;
      font-style: italic;
    }}

    article hr {{
      border: none;
      border-top: 1px solid rgba(100, 140, 255, 0.15);
      margin: 2.5rem 0;
    }}

    /* ── Code ── */
    article code {{
      font-family: 'Courier New', Courier, monospace;
      font-size: 0.88em;
      color: #7dd3c0;
      background: rgba(80, 200, 180, 0.08);
      padding: 0.15em 0.4em;
      border-radius: 3px;
      border: 1px solid rgba(100, 200, 180, 0.12);
    }}

    article pre {{
      background: rgba(4, 8, 16, 0.7);
      border: 1px solid rgba(100, 140, 255, 0.15);
      border-radius: 6px;
      padding: 1.2rem 1.4rem;
      overflow-x: auto;
      margin: 1.4rem 0;
    }}

    article pre code {{
      background: none;
      border: none;
      padding: 0;
      font-size: 0.875rem;
      color: #a8c8a0;
      line-height: 1.6;
    }}

    /* Pygments codehilite */
    .codehilite {{ background: rgba(4,8,16,0.7) !important; border: 1px solid rgba(100,140,255,0.15); border-radius: 6px; padding: 1.2rem 1.4rem; overflow-x: auto; margin: 1.4rem 0; }}
    .codehilite pre {{ background: none; border: none; padding: 0; margin: 0; }}
    .codehilite .hll {{ background-color: rgba(100,140,255,0.1); }}
    .codehilite .c  {{ color: #556670; font-style: italic; }}
    .codehilite .k  {{ color: #7ab4f5; font-weight: bold; }}
    .codehilite .s, .codehilite .s1, .codehilite .s2 {{ color: #7ec8a0; }}
    .codehilite .n  {{ color: #c8d8f0; }}
    .codehilite .na {{ color: #a8d8b0; }}
    .codehilite .nb {{ color: #7ab4f5; }}
    .codehilite .nc {{ color: #e0c878; }}
    .codehilite .nf {{ color: #a8c8ff; }}
    .codehilite .o  {{ color: #7a9acc; }}
    .codehilite .mi, .codehilite .mf {{ color: #f0a878; }}
    .codehilite .cm, .codehilite .c1, .codehilite .cs {{ color: #556670; font-style: italic; }}
    .codehilite .cp {{ color: #7a9acc; }}

    /* ── Figures + captions ── */
    article figure {{
      margin: 2rem 0;
      text-align: center;
    }}

    article figure img {{
      display: block;
      max-width: 100%;
      height: auto;
      margin: 0 auto;
      border-radius: 6px;
      border: 1px solid rgba(100, 140, 255, 0.15);
      box-shadow: 0 4px 32px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(100, 140, 255, 0.06);
    }}

    article figcaption {{
      font-family: -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      font-size: 0.8rem;
      line-height: 1.55;
      color: #4a6a8a;
      margin-top: 0.65rem;
      padding: 0 1rem;
      font-style: italic;
    }}

    /* fallback for bare <img> not wrapped in figure */
    article img {{
      display: block;
      max-width: 100%;
      height: auto;
      margin: 2rem auto;
      border-radius: 6px;
      border: 1px solid rgba(100, 140, 255, 0.15);
      box-shadow: 0 4px 32px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(100, 140, 255, 0.06);
    }}

    /* ── Tables ── */
    article table {{
      width: 100%;
      border-collapse: collapse;
      margin: 1.5rem 0;
      font-size: 0.9rem;
    }}
    article th {{
      font-family: 'Courier New', Courier, monospace;
      font-size: 0.75rem;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: #7a9acc;
      border-bottom: 1px solid rgba(100, 140, 255, 0.25);
      padding: 0.6rem 0.8rem;
      text-align: left;
    }}
    article td {{
      padding: 0.6rem 0.8rem;
      border-bottom: 1px solid rgba(100, 140, 255, 0.08);
      color: #a8bcd8;
    }}
    article tr:hover td {{ background: rgba(80, 120, 255, 0.04); }}

    /* ── TOC sidebar (desktop ≥ 1200px) ── */
    .toc-sidebar {{
      display: none;
    }}

    @media (min-width: 1200px) {{
      .toc-sidebar {{
        display: block;
        position: fixed;
        top: 5rem;
        left: calc(50% - 590px);
        width: 170px;
        z-index: 2;
      }}

      .toc-sidebar nav {{
        font-family: 'Courier New', Courier, monospace;
        font-size: 0.7rem;
        letter-spacing: 0.06em;
      }}

      .toc-sidebar .toc-label {{
        font-size: 0.62rem;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: #2a4a6a;
        margin-bottom: 0.6rem;
      }}

      .toc-sidebar a {{
        display: block;
        color: #4a6a8a;
        text-decoration: none;
        padding: 0.22rem 0;
        border-left: 2px solid transparent;
        padding-left: 0.6rem;
        line-height: 1.35;
        transition: color 0.15s, border-color 0.15s;
      }}

      .toc-sidebar a:hover {{ color: #a8c8e8; border-color: rgba(100,140,255,0.3); }}
      .toc-sidebar a.active {{ color: #8ab8e0; border-color: rgba(100,140,255,0.6); }}
    }}

    /* ── TOC mobile bar ── */
    .toc-bar {{
      display: none;
    }}

    @media (max-width: 1199px) {{
      .toc-bar {{
        display: flex;
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        z-index: 10;
        background: rgba(6, 10, 18, 0.92);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border-top: 1px solid rgba(100, 140, 255, 0.12);
        padding: 0.55rem 1rem;
        gap: 0.5rem;
        align-items: center;
        font-family: 'Courier New', Courier, monospace;
        font-size: 0.72rem;
        letter-spacing: 0.1em;
      }}

      .toc-bar button {{
        background: none;
        border: 1px solid rgba(100, 140, 255, 0.2);
        border-radius: 3px;
        color: #7a9acc;
        font-family: inherit;
        font-size: inherit;
        letter-spacing: inherit;
        padding: 0.3rem 0.7rem;
        cursor: pointer;
        transition: background 0.15s, color 0.15s;
        flex-shrink: 0;
      }}

      .toc-bar button:hover {{ background: rgba(80,120,255,0.1); color: #c8d8f0; }}

      .toc-bar .toc-top {{
        margin-left: auto;
      }}

      .toc-dropdown {{
        display: none;
        position: fixed;
        bottom: 2.8rem;
        left: 0;
        right: 0;
        background: rgba(6, 10, 18, 0.96);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-top: 1px solid rgba(100, 140, 255, 0.12);
        padding: 0.75rem 1rem 0.5rem;
        z-index: 9;
        max-height: 60vh;
        overflow-y: auto;
      }}

      .toc-dropdown.open {{ display: block; }}

      .toc-dropdown a {{
        display: block;
        color: #6a8aaa;
        text-decoration: none;
        font-family: 'Courier New', Courier, monospace;
        font-size: 0.78rem;
        letter-spacing: 0.06em;
        padding: 0.45rem 0;
        border-bottom: 1px solid rgba(100,140,255,0.06);
        transition: color 0.15s;
      }}

      .toc-dropdown a:hover {{ color: #c8d8f0; }}
      .toc-dropdown a:last-child {{ border-bottom: none; }}
    }}

    /* ── Ko-fi block ── */
    .kofi-block {{
      margin-top: 3rem;
      padding-top: 2rem;
      border-top: 1px solid rgba(100, 140, 255, 0.1);
      text-align: center;
    }}

    .kofi-block a {{
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
      text-decoration: none;
      font-family: 'Courier New', Courier, monospace;
      font-size: 0.72rem;
      letter-spacing: 0.12em;
      color: #3a5a7a;
      border: 1px solid rgba(100, 140, 255, 0.1);
      border-radius: 2px;
      padding: 0.45rem 0.9rem;
      background: rgba(80, 120, 255, 0.03);
      transition: background 0.2s, color 0.2s, border-color 0.2s;
    }}

    .kofi-block a:hover {{
      background: rgba(80, 120, 255, 0.1);
      color: #a0bce8;
      border-color: rgba(100, 140, 255, 0.25);
    }}

    .kofi-block svg {{
      width: 14px;
      height: 14px;
      fill: currentColor;
      flex-shrink: 0;
    }}

    /* ── Footer ── */
    footer {{
      position: relative;
      z-index: 1;
      text-align: center;
      padding: 2rem;
      font-size: 0.72rem;
      letter-spacing: 0.1em;
      color: #2a4a7a;
      border-top: 1px solid rgba(100, 140, 255, 0.08);
    }}

    @media (max-width: 1199px) {{
      footer {{ padding-bottom: 4rem; }}
    }}

    @media (max-width: 600px) {{
      main {{ padding: 1rem 0.8rem 3rem; }}
      .content {{ padding: 1.5rem 1.2rem; }}
      .topbar {{ padding: 0.8rem 1.2rem; }}
    }}
  </style>
</head>
<body>

<canvas id="bg"></canvas>

{toc_sidebar_html}

<nav class="topbar">
  <a href="/">Benedikt</a>
</nav>

<main>
  <div class="content">
    <header class="post-meta">
      <div class="post-date">{date_str}</div>
      <h1 class="post-title">{title}</h1>
      <p class="post-description">{description}</p>
      {tags_html}
    </header>
    <article>
      {body_html}
    </article>
    <div class="kofi-block">
      <a href="https://ko-fi.com/bened1kt" target="_blank" rel="noopener">
        <svg viewBox="0 0 24 24"><path d="M23.881 8.948c-.773-4.085-4.859-4.593-4.859-4.593H.723c-.604 0-.679.798-.679.798s-.082 7.324-.022 11.822c.164 2.424 2.586 2.672 2.586 2.672s8.267-.023 11.966-.049c2.438-.426 2.683-2.566 2.658-3.734 4.352.24 7.422-2.831 6.649-6.916zm-11.062 3.511c-1.246 1.453-4.011 3.976-4.011 3.976s-.121.119-.31.023c-.076-.057-.108-.09-.108-.09-.443-.441-3.368-3.049-4.034-3.954-.709-.965-1.041-2.7-.091-3.71.951-1.01 3.005-1.086 4.363.407 0 0 1.565-1.782 3.468-.963 1.904.82 1.832 3.011.723 4.311zm6.173.478c-.928.116-1.682.028-1.682.028V7.284h1.77s1.971.551 1.971 2.638c0 1.913-.985 2.667-2.059 3.015z"/></svg>
        If you found this useful, consider buying me a coffee
      </a>
    </div>
  </div>
</main>

{toc_bar_html}

<footer>// {site_title} &nbsp;·&nbsp; research</footer>

<script>
(function () {{
  const canvas = document.getElementById('bg');
  const ctx    = canvas.getContext('2d');
  const TAU    = Math.PI * 2;
  const CHARS  = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&?!<>[]{{}}αβγδεζθλμξπσφψω';

  let W, H, cx, cy, R, t = 0;

  const N_SPHERE = 2200;
  const spherePts = [];

  (function buildFibSphere() {{
    const golden = Math.PI * (3 - Math.sqrt(5));
    for (let i = 0; i < N_SPHERE; i++) {{
      const y   = 1 - (i / (N_SPHERE - 1)) * 2;
      const r   = Math.sqrt(1 - y * y);
      const phi = golden * i;
      spherePts.push({{ x: Math.cos(phi) * r, y, z: Math.sin(phi) * r,
                       ch: CHARS[i % CHARS.length] }});
    }}
  }})();

  function rotateYX(x, y, z, ry, rx) {{
    let x1 =  x * Math.cos(ry) + z * Math.sin(ry);
    let y1 =  y;
    let z1 = -x * Math.sin(ry) + z * Math.cos(ry);
    let x2 = x1;
    let y2 =  y1 * Math.cos(rx) - z1 * Math.sin(rx);
    let z2 =  y1 * Math.sin(rx) + z1 * Math.cos(rx);
    return [x2, y2, z2];
  }}

  function project(x, y, z) {{
    const camZ = 2.2;
    const dz   = camZ + z;
    const scale = R / camZ;
    const px   = cx + (x / dz) * scale * camZ;
    const py   = cy + (y / dz) * scale * camZ;
    return [px, py, dz];
  }}

  function init() {{
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
    W = canvas.width; H = canvas.height;
    cx = W / 2; cy = H / 2;
    R  = Math.min(W, H) * 1.25;
  }}

  function draw() {{
    t += 0.012;
    ctx.fillStyle = 'rgba(8,12,8,0.35)';
    ctx.fillRect(0, 0, W, H);

    const ry = t * 0.18;
    const rx = Math.sin(t * 0.11) * 0.4;
    const breathe = 1 + 0.04 * Math.sin(t * 0.9);

    const visible = [];
    for (const p of spherePts) {{
      const theta = Math.atan2(p.z, p.x);
      const phi   = Math.asin(Math.max(-1, Math.min(1, p.y)));
      const disp  = 1
        + 0.028 * Math.sin(4 * theta + t * 1.3)
        + 0.018 * Math.sin(6 * phi  + t * 0.9)
        + 0.012 * Math.sin(9 * theta - t * 1.8)
        + 0.008 * Math.sin(3 * phi  + t * 2.1);
      const r = breathe * disp;

      const [rx2, ry2, rz2] = rotateYX(p.x * r, p.y * r, p.z * r, ry, rx);
      const [sx, sy, sdz]   = project(rx2, ry2, rz2);

      const lx = -0.5, ly = -0.7, lz = 0.5;
      const nl = Math.sqrt(lx*lx+ly*ly+lz*lz);
      const lit = Math.max(0, (rx2*lx + ry2*ly + rz2*lz) / (r * nl));
      const facing = rz2 / r;
      const hueShift = (p.y + 1) * 0.5;
      visible.push({{ sx, sy, sdz, lit, facing, ch: p.ch, hueShift }});
    }}

    visible.sort((a, b) => a.sdz - b.sdz);

    ctx.font = '11px monospace';
    for (const v of visible) {{
      const brightness = 0.15 + v.lit * 0.85;
      const alpha = v.facing > -0.1 ? brightness * 0.9 : brightness * 0.15;
      const hue = 120 + v.hueShift * 80;
      const sat = 80 + Math.floor(v.lit * 20);
      const lgt = 20 + Math.floor(v.lit * 45);
      ctx.globalAlpha = alpha;
      ctx.fillStyle = `hsl(${{hue}},${{sat}}%,${{lgt}}%)`;
      ctx.fillText(v.ch, v.sx, v.sy);
    }}
    ctx.globalAlpha = 1;
    requestAnimationFrame(draw);
  }}

  init();
  window.addEventListener('resize', init);
  requestAnimationFrame(draw);
}})();

// ── TOC scroll-spy + mobile toggle ──────────────────────────────────────────
(function () {{
  // Desktop scroll-spy
  const sidebarLinks = document.querySelectorAll('.toc-sidebar a');
  if (sidebarLinks.length) {{
    const headings = Array.from(document.querySelectorAll('article h2'));
    const observer = new IntersectionObserver(entries => {{
      entries.forEach(entry => {{
        if (entry.isIntersecting) {{
          const id = entry.target.getAttribute('id');
          sidebarLinks.forEach(a => {{
            a.classList.toggle('active', a.getAttribute('href') === '#' + id);
          }});
        }}
      }});
    }}, {{ rootMargin: '-10% 0px -80% 0px', threshold: 0 }});
    headings.forEach(h => observer.observe(h));
  }}

  // Mobile: Contents toggle
  const contentsBtn = document.getElementById('toc-contents-btn');
  const dropdown    = document.getElementById('toc-dropdown');
  if (contentsBtn && dropdown) {{
    contentsBtn.addEventListener('click', () => {{
      dropdown.classList.toggle('open');
    }});
    dropdown.querySelectorAll('a').forEach(a => {{
      a.addEventListener('click', () => dropdown.classList.remove('open'));
    }});
    document.addEventListener('click', e => {{
      if (!dropdown.contains(e.target) && e.target !== contentsBtn)
        dropdown.classList.remove('open');
    }});
  }}

  // Mobile: ↑ Top
  const topBtn = document.getElementById('toc-top-btn');
  if (topBtn) {{
    topBtn.addEventListener('click', () => window.scrollTo({{ top: 0, behavior: 'smooth' }}));
  }}
}})();
</script>
</body>
</html>
"""

# ── Research listing page template ───────────────────────────────────────────

LISTING_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Research – {site_title}</title>
  <meta name="description" content="Security research and writing by {site_title}." />
  <link rel="canonical" href="{canonical}" />
  <meta property="og:title" content="Research – {site_title}" />
  <meta property="og:description" content="Security research and writing by {site_title}." />
  <meta property="og:url" content="{canonical}" />
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html, body {{
      height: 100%;
      background: #080c08;
      font-family: 'Courier New', Courier, monospace;
      overflow-x: hidden;
    }}
    #bg {{ position: fixed; inset: 0; z-index: 0; opacity: 0.18; }}
    .topbar {{
      position: relative; z-index: 2;
      padding: 1rem 2rem;
      border-bottom: 1px solid rgba(100,140,255,0.1);
    }}
    .topbar a {{
      color: #7a9acc; text-decoration: none;
      font-size: 0.78rem; letter-spacing: 0.14em; text-transform: uppercase;
      transition: color 0.2s;
    }}
    .topbar a:hover {{ color: #c8d8f0; }}
    .topbar a::before {{ content: '← '; }}
    main {{
      position: relative; z-index: 1;
      max-width: 780px; margin: 0 auto;
      padding: 3rem 2rem 5rem;
    }}
    h1 {{
      font-size: 1.5rem; letter-spacing: 0.08em;
      color: #e8f0ff; text-shadow: 0 0 20px rgba(100,140,255,0.4);
      margin-bottom: 0.4rem;
    }}
    .section-sub {{
      font-size: 0.75rem; letter-spacing: 0.16em; text-transform: uppercase;
      color: #4a6a9a; margin-bottom: 2.5rem;
    }}
    .post-list {{ list-style: none; }}
    .post-item {{
      border: 1px solid rgba(100,140,255,0.1);
      border-radius: 6px;
      background: rgba(6,10,18,0.3);
      backdrop-filter: blur(6px);
      padding: 1.5rem 1.8rem;
      margin-bottom: 1.2rem;
      transition: border-color 0.2s, background 0.2s;
    }}
    .post-item:hover {{
      border-color: rgba(100,140,255,0.25);
      background: rgba(6,10,18,0.5);
    }}
    .post-item a {{ text-decoration: none; }}
    .item-date {{
      font-size: 0.68rem; letter-spacing: 0.14em; text-transform: uppercase;
      color: #4a6a9a; margin-bottom: 0.5rem;
    }}
    .item-title {{
      font-size: 1.05rem; letter-spacing: 0.04em;
      color: #c8d8f0; line-height: 1.4;
      transition: color 0.2s; margin-bottom: 0.6rem;
    }}
    .post-item:hover .item-title {{ color: #e8f0ff; text-shadow: 0 0 12px rgba(100,140,255,0.3); }}
    .item-desc {{
      font-family: -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      font-size: 0.88rem; line-height: 1.65; color: #6a8aaa;
    }}
    .item-tags {{
      display: flex; flex-wrap: wrap; gap: 0.35rem; margin-top: 0.75rem;
    }}
    .item-tag {{
      font-size: 0.65rem; letter-spacing: 0.1em; text-transform: uppercase;
      border: 1px solid rgba(100,140,255,0.15); border-radius: 2px;
      padding: 0.15rem 0.45rem; color: #4a6a9a;
      background: rgba(80,120,255,0.04);
    }}
    footer {{
      position: relative; z-index: 1; text-align: center;
      padding: 2rem; font-size: 0.72rem; letter-spacing: 0.1em;
      color: #2a4a7a; border-top: 1px solid rgba(100,140,255,0.08);
    }}
    @media (max-width: 600px) {{
      main {{ padding: 2rem 1.2rem 3rem; }}
      .topbar {{ padding: 0.8rem 1.2rem; }}
    }}
  </style>
</head>
<body>
<canvas id="bg"></canvas>
<nav class="topbar"><a href="/">Benedikt</a></nav>
<main>
  <h1>Research</h1>
  <p class="section-sub">Security research &amp; writing</p>
  <ul class="post-list">
    {post_items}
  </ul>
</main>
<footer>// {site_title} &nbsp;·&nbsp; research</footer>
<script>
(function () {{
  const canvas = document.getElementById('bg');
  const ctx    = canvas.getContext('2d');
  const CHARS  = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&?!<>[]{{}}αβγδεζθλμξπσφψω';
  let W, H, cx, cy, R, t = 0;
  const N = 2200, pts = [];
  (function build() {{
    const g = Math.PI * (3 - Math.sqrt(5));
    for (let i = 0; i < N; i++) {{
      const y = 1 - (i/(N-1))*2, r = Math.sqrt(1-y*y), p = g*i;
      pts.push({{x: Math.cos(p)*r, y, z: Math.sin(p)*r, ch: CHARS[i%CHARS.length]}});
    }}
  }})();
  function rotYX(x,y,z,ry,rx) {{
    let x1=x*Math.cos(ry)+z*Math.sin(ry),z1=-x*Math.sin(ry)+z*Math.cos(ry);
    return [x1, y*Math.cos(rx)-z1*Math.sin(rx), y*Math.sin(rx)+z1*Math.cos(rx)];
  }}
  function proj(x,y,z) {{ const c=2.2,d=c+z,s=R/c; return [cx+(x/d)*s*c, cy+(y/d)*s*c, d]; }}
  function init() {{ canvas.width=W=window.innerWidth; canvas.height=H=window.innerHeight; cx=W/2; cy=H/2; R=Math.min(W,H)*1.25; }}
  function draw() {{
    t+=0.012;
    ctx.fillStyle='rgba(8,12,8,0.35)'; ctx.fillRect(0,0,W,H);
    const ry=t*0.18, rx=Math.sin(t*0.11)*0.4, br=1+0.04*Math.sin(t*0.9);
    const vis=[];
    for (const p of pts) {{
      const th=Math.atan2(p.z,p.x),ph=Math.asin(Math.max(-1,Math.min(1,p.y)));
      const r=br*(1+0.028*Math.sin(4*th+t*1.3)+0.018*Math.sin(6*ph+t*0.9)+0.012*Math.sin(9*th-t*1.8)+0.008*Math.sin(3*ph+t*2.1));
      const [rx2,ry2,rz2]=rotYX(p.x*r,p.y*r,p.z*r,ry,rx);
      const [sx,sy,sdz]=proj(rx2,ry2,rz2);
      const lx=-0.5,ly=-0.7,lz=0.5,nl=Math.sqrt(0.25+0.49+0.25);
      const lit=Math.max(0,(rx2*lx+ry2*ly+rz2*lz)/(r*nl));
      vis.push({{sx,sy,sdz,lit,facing:rz2/r,ch:p.ch,hs:(p.y+1)*0.5}});
    }}
    vis.sort((a,b)=>a.sdz-b.sdz);
    ctx.font='11px monospace';
    for (const v of vis) {{
      const br2=0.15+v.lit*0.85;
      ctx.globalAlpha=v.facing>-0.1?br2*0.9:br2*0.15;
      ctx.fillStyle=`hsl(${{120+v.hs*80}},${{80+Math.floor(v.lit*20)}}%,${{20+Math.floor(v.lit*45)}}%)`;
      ctx.fillText(v.ch,v.sx,v.sy);
    }}
    ctx.globalAlpha=1;
    requestAnimationFrame(draw);
  }}
  init(); window.addEventListener('resize',init); requestAnimationFrame(draw);
}})();
</script>
</body>
</html>
"""

POST_ITEM_TEMPLATE = """\
    <li class="post-item">
      <a href="/{research_dir}/{slug}/">
        <div class="item-date">{date_str}</div>
        <div class="item-title">{title}</div>
        <div class="item-desc">{description}</div>
        {tags_html}
      </a>
    </li>"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_front_matter(text):
    """Split YAML front matter from markdown body. Returns (meta_dict, body_str)."""
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
    for line in md_text.splitlines():
        m = re.match(r"^#{1,2}\s+\**(.*?)\**\s*$", line)
        if m:
            return m.group(1).strip()
    return "Untitled"


def first_paragraph(html):
    m = re.search(r"<p>(.*?)</p>", html, re.DOTALL)
    if m:
        text = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        return text[:280] + ("…" if len(text) > 280 else "")
    return ""


def first_image_src(md_text):
    m = re.search(r"!\[.*?\]\(([^)]+)\)", md_text)
    return m.group(1) if m else None


def render_tags(tags):
    if not tags:
        return ""
    items = "".join(f'<span class="post-tag">{t}</span>' for t in tags)
    return f'<div class="post-tags">{items}</div>'


def render_listing_tags(tags):
    if not tags:
        return ""
    items = "".join(f'<span class="item-tag">{t}</span>' for t in tags)
    return f'<div class="item-tags">{items}</div>'


def format_date(d):
    if isinstance(d, (date, datetime)):
        return d.strftime("%-d %B %Y") if hasattr(d, "strftime") else str(d)
    return str(d) if d else ""


def md_to_html(md_text):
    """Return (body_html, h2_tokens) where h2_tokens is [{id, name}, ...]."""
    md = markdown.Markdown(
        extensions=["extra", "sane_lists", "toc", "codehilite"],
        extension_configs={
            "codehilite": {"css_class": "codehilite", "linenums": False, "guess_lang": True},
        },
    )
    html = md.convert(md_text)
    tokens = getattr(md, "toc_tokens", [])
    # toc_tokens is a nested tree; H2s sit as children of the root H1 (or top-level)
    def extract_h2(nodes):
        for node in nodes:
            if node.get("level") == 2:
                yield node
            elif node.get("level") == 1:
                yield from extract_h2(node.get("children", []))
    h2s = list(extract_h2(tokens))
    return html, h2s


def build_toc_html(h2s):
    """Build sidebar and mobile-bar HTML from a list of {id, name} dicts."""
    if not h2s:
        return "", ""

    links = "".join(
        f'<a href="#{t["id"]}">{t["name"]}</a>\n' for t in h2s
    )

    sidebar = (
        '<aside class="toc-sidebar">\n'
        '  <nav>\n'
        '    <div class="toc-label">Contents</div>\n'
        f'    {links}'
        '  </nav>\n'
        '</aside>\n'
    )

    dropdown_links = "".join(
        f'<a href="#{t["id"]}">{t["name"]}</a>\n' for t in h2s
    )
    bar = (
        '<div id="toc-dropdown" class="toc-dropdown">\n'
        f'  {dropdown_links}'
        '</div>\n'
        '<div class="toc-bar">\n'
        '  <button id="toc-contents-btn">Contents</button>\n'
        '  <button id="toc-top-btn" class="toc-top">↑ Top</button>\n'
        '</div>\n'
    )
    return sidebar, bar


def wrap_images_in_figures(html):
    """Turn <p><img alt="..." src="..."></p> into <figure><img><figcaption>...</figcaption></figure>."""
    def replacer(m):
        img_tag = m.group(1)
        alt_match = re.search(r'alt="([^"]*)"', img_tag)
        alt = alt_match.group(1) if alt_match else ""
        caption = f"<figcaption>{alt}</figcaption>" if alt else ""
        return f"<figure>{img_tag}{caption}</figure>"

    return re.sub(r"<p>(<img\b[^>]+>)</p>", replacer, html)


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
    toc_sidebar_html, toc_bar_html = build_toc_html(h2s)

    # Resolve metadata with fallbacks
    title = meta.get("title") or first_heading(body_md)
    description = meta.get("description") or first_paragraph(body_html)
    tags = meta.get("tags") or []
    raw_date = meta.get("date")
    if raw_date:
        post_date = raw_date
    else:
        mtime = os.path.getmtime(readme_path)
        post_date = datetime.fromtimestamp(mtime).date()

    og_image_file = meta.get("og_image") or first_image_src(body_md)
    if og_image_file:
        og_image_url = url_for(f"/{RESEARCH_DIR}/{slug}/{og_image_file}")
    else:
        og_image_url = url_for("/me.webp")

    canonical = url_for(f"/{RESEARCH_DIR}/{slug}/")
    date_str = format_date(post_date)

    html = POST_TEMPLATE.format(
        title=title,
        site_title=SITE_TITLE,
        description=description,
        canonical=canonical,
        og_image_url=og_image_url,
        date_str=date_str,
        tags_html=render_tags(tags),
        body_html=body_html,
        toc_sidebar_html=toc_sidebar_html,
        toc_bar_html=toc_bar_html,
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
    items_html = "\n".join(
        POST_ITEM_TEMPLATE.format(
            research_dir=RESEARCH_DIR,
            slug=p["slug"],
            date_str=p["date_str"],
            title=p["title"],
            description=p["description"],
            tags_html=render_listing_tags(p["tags"]),
        )
        for p in posts_sorted
    )
    html = LISTING_TEMPLATE.format(
        site_title=SITE_TITLE,
        canonical=url_for("/research/"),
        post_items=items_html,
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
        slug_path = f"/research/{p['slug']}/"
        urls.append(
            f"  <url><loc>{url_for(slug_path)}</loc>"
            f"<lastmod>{d}</lastmod><priority>0.9</priority></url>"
        )
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
    robots = f"User-agent: *\nAllow: /\n{sitemap_line}"
    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(robots)
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
