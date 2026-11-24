#!/usr/bin/env python3
"""Generate the GitHub Pages site into _site/ from the integration folders.

Standard library only. Each integration's look comes from
integrations/<domain>/site.json (accent, secondary, heading_font, body_font, tagline,
description). Page content comes from README.md and CHANGELOG.md.

Usage:
    python scripts/build_site.py
"""

from __future__ import annotations

import html
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import quote_plus

ROOT = Path(__file__).resolve().parent.parent
INTEGRATIONS = ROOT / "integrations"
OUT = ROOT / "_site"
REPOSITORY = "Ding-Ding-Projects/home-assistant-integrations"
REPO_URL = f"https://github.com/{REPOSITORY}"
DEFAULTS = {
    "accent": "#1565c0",
    "secondary": "#4dd0e1",
    "heading_font": "Roboto",
    "body_font": "Roboto",
    "tagline": "",
    "description": "",
}
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
FONT = re.compile(r"^[A-Za-z0-9 ]{1,40}$")


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def inline(text: str) -> str:
    """Render inline Markdown: code, bold, links."""
    parts = re.split(r"(`[^`]+`)", text)
    out = []
    for part in parts:
        if part.startswith("`") and part.endswith("`") and len(part) > 1:
            out.append(f"<code>{esc(part[1:-1])}</code>")
            continue
        safe = esc(part)
        safe = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", safe)
        safe = re.sub(
            r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
            r'<a href="\2" rel="noopener">\1</a>',
            safe,
        )
        out.append(safe)
    return "".join(out)


def render_markdown(source: str, skip_title: bool = True, heading_offset: int = 0) -> str:
    """Render the small Markdown subset used by the integration docs."""
    lines = source.splitlines()
    out: list[str] = []
    paragraph: list[str] = []
    list_kind: str | None = None
    in_code = False
    code: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            out.append(f"<p>{inline(' '.join(paragraph))}</p>")
            paragraph = []

    def close_list() -> None:
        nonlocal list_kind
        if list_kind:
            out.append(f"</{list_kind}>")
            list_kind = None

    for raw in lines:
        line = raw.rstrip()
        if line.startswith("```"):
            if in_code:
                out.append("<pre><code>" + esc("\n".join(code)) + "</code></pre>")
                code, in_code = [], False
            else:
                flush_paragraph()
                close_list()
                in_code = True
            continue
        if in_code:
            code.append(raw)
            continue
        heading = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading:
            flush_paragraph()
            close_list()
            level = len(heading.group(1))
            if level == 1 and skip_title:
                continue
            level = min(6, level + heading_offset)
            text = heading.group(2)
            slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
            out.append(f'<h{level} id="{slug}">{inline(text)}</h{level}>')
            continue
        item = re.match(r"^(\d+\.|[-*])\s+(.*)$", line)
        if item:
            flush_paragraph()
            kind = "ol" if item.group(1)[0].isdigit() else "ul"
            if list_kind != kind:
                close_list()
                out.append(f"<{kind}>")
                list_kind = kind
            out.append(f"<li>{inline(item.group(2))}</li>")
            continue
        if not line.strip():
            flush_paragraph()
            close_list()
            continue
        close_list()
        paragraph.append(line.strip())
    flush_paragraph()
    close_list()
    return "\n".join(out)


def first_paragraph(readme: str) -> str:
    for block in re.split(r"\n\s*\n", readme):
        block = block.strip()
        if block and not block.startswith("#"):
            return " ".join(block.split())
    return ""


def load_integrations() -> list[dict]:
    items = []
    for folder in sorted(p for p in INTEGRATIONS.iterdir() if p.is_dir()):
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        style = dict(DEFAULTS)
        site_file = folder / "site.json"
        if site_file.is_file():
            style.update(json.loads(site_file.read_text(encoding="utf-8")))
        for key in ("accent", "secondary"):
            if not HEX.match(str(style[key])):
                style[key] = DEFAULTS[key]
        for key in ("heading_font", "body_font"):
            if not FONT.match(str(style[key])):
                style[key] = DEFAULTS[key]
        readme_path = folder / "README.md"
        readme = readme_path.read_text(encoding="utf-8") if readme_path.is_file() else ""
        changelog_path = folder / "CHANGELOG.md"
        changelog = changelog_path.read_text(encoding="utf-8") if changelog_path.is_file() else ""
        items.append(
            {
                "domain": folder.name,
                "title": manifest.get("name", folder.name),
                "version": str(manifest["version"]),
                "iot_class": manifest.get("iot_class", ""),
                "style": style,
                "description": style["description"] or first_paragraph(readme),
                "readme": readme,
                "changelog": changelog,
            }
        )
    return items


def download_url(item: dict) -> str:
    return f"{REPO_URL}/releases/latest/download/{item['domain']}-{item['version']}.hapkg"


def font_link(*families: str) -> str:
    unique = sorted({f for f in families if f})
    params = "&".join(f"family={quote_plus(f)}:wght@400;600;700" for f in unique)
    return (
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?{params}&display=swap">'
    )


BASE_CSS = """
:root{color-scheme:light dark;--bg:#fbfbfd;--surface:#fff;--text:#1b1d22;--muted:#5d6370;--line:#dfe2e8;--code:#eef0f4}
@media (prefers-color-scheme:dark){:root{--bg:#121316;--surface:#1b1d22;--text:#eceef3;--muted:#a0a6b3;--line:#2c2f37;--code:#262932}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:16px/1.6 var(--body),system-ui,sans-serif}
a{color:var(--accent)}
.wrap{max-width:60rem;margin:0 auto;padding:0 16px}
header.site{padding:12px 0;border-bottom:1px solid var(--line);background:var(--surface)}
header.site a{font-family:var(--heading),system-ui,sans-serif;font-weight:700;text-decoration:none;color:var(--text)}
h1,h2,h3{font-family:var(--heading),system-ui,sans-serif;line-height:1.2}
.hero{padding:40px 0 28px;background:linear-gradient(135deg,color-mix(in srgb,var(--accent) 22%,var(--bg)),color-mix(in srgb,var(--secondary) 22%,var(--bg)))}
.hero h1{margin:0 0 8px;font-size:clamp(1.8rem,6vw,2.8rem)}
.hero p{margin:0 0 16px;color:var(--muted);max-width:40rem}
.btn{display:inline-block;padding:12px 20px;border-radius:999px;background:var(--accent);color:#fff;font-weight:600;text-decoration:none;min-height:44px}
.btn.alt{background:transparent;color:var(--accent);border:2px solid var(--accent)}
.btn:focus-visible{outline:3px solid var(--secondary);outline-offset:2px}
.facts{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0 0;padding:0;list-style:none}
.facts li{padding:4px 12px;border-radius:999px;background:var(--surface);border:1px solid var(--line);font-size:.9rem}
main{padding:24px 0 48px}
code{background:var(--code);padding:1px 6px;border-radius:6px;font-size:.92em}
pre{background:var(--code);padding:12px;border-radius:12px;overflow-x:auto}
pre code{padding:0;background:none}
.grid{display:grid;gap:16px;grid-template-columns:repeat(auto-fill,minmax(min(100%,17rem),1fr));padding:0;list-style:none}
.card{display:flex;flex-direction:column;gap:8px;height:100%;padding:18px;border-radius:20px;background:var(--surface);border:1px solid var(--line);border-top:6px solid var(--accent)}
.card h2{margin:0;font-size:1.25rem}
.card p{margin:0;color:var(--muted);flex:1}
.card .row{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.ver{font-size:.85rem;color:var(--muted)}
footer{padding:24px 0;border-top:1px solid var(--line);color:var(--muted);font-size:.9rem}
@media (prefers-reduced-motion:no-preference){.card{transition:transform .15s}.card:hover{transform:translateY(-3px)}}
"""


def theme_vars(style: dict) -> str:
    return (
        f"--accent:{style['accent']};--secondary:{style['secondary']};"
        f"--heading:'{style['heading_font']}';--body:'{style['body_font']}';"
    )


def page(title: str, description: str, style: dict, body: str, depth: int, fonts: list[str]) -> str:
    prefix = "../" * depth
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
{font_link(*fonts)}
<style>{BASE_CSS}</style>
</head>
<body style="{theme_vars(style)}">
<header class="site"><div class="wrap"><a href="{prefix}index.html">Home Assistant integrations</a></div></header>
{body}
<footer><div class="wrap">Packages run code with full access to Home Assistant. Only install what you trust.
<a href="{REPO_URL}">Source on GitHub</a></div></footer>
</body>
</html>
"""


def build_home(items: list[dict]) -> str:
    cards = []
    for item in items:
        style = item["style"]
        cards.append(
            f"""<li><article class="card" style="--accent:{style['accent']};--secondary:{style['secondary']}">
<h2 style="font-family:'{style['heading_font']}',system-ui,sans-serif">{esc(item['title'])}</h2>
<p>{esc(item['description'])}</p>
<span class="ver">Version {esc(item['version'])}</span>
<div class="row"><a class="btn" href="{esc(download_url(item))}">Download .hapkg</a>
<a class="btn alt" href="{esc(item['domain'])}/index.html">Details</a></div></article></li>"""
        )
    body = f"""<section class="hero"><div class="wrap">
<h1>Home Assistant integrations</h1>
<p>Custom integrations shipped as drag-and-drop <code>.hapkg</code> package files. Download a package,
then drop it onto the Marketplace page or use Install from a package file.</p>
<a class="btn" href="{REPO_URL}/releases/latest">All releases</a></div></section>
<main><div class="wrap"><ul class="grid">{''.join(cards)}</ul></div></main>"""
    fonts = [i["style"]["heading_font"] for i in items] + [i["style"]["body_font"] for i in items]
    return page(
        "Home Assistant integrations",
        "Custom Home Assistant integrations shipped as drag-and-drop .hapkg packages",
        dict(DEFAULTS),
        body,
        0,
        fonts,
    )


def build_detail(item: dict) -> str:
    style = item["style"]
    readme_html = render_markdown(item["readme"], skip_title=True, heading_offset=0)
    changelog_html = render_markdown(item["changelog"], skip_title=True, heading_offset=1)
    facts = (
        f'<ul class="facts"><li>Version {esc(item["version"])}</li>'
        f'<li>Domain <code>{esc(item["domain"])}</code></li>'
        f'<li>{esc(item["iot_class"].replace("_", " "))}</li></ul>'
    )
    body = f"""<section class="hero"><div class="wrap">
<h1>{esc(item['title'])}</h1>
<p>{esc(style['tagline'] or item['description'])}</p>
<a class="btn" href="{esc(download_url(item))}">Download {esc(item['domain'])}-{esc(item['version'])}.hapkg</a>
{facts}</div></section>
<main><div class="wrap">
{readme_html}
<h2 id="changelog">Changelog</h2>
{changelog_html}
<p><a href="{REPO_URL}/tree/main/integrations/{esc(item['domain'])}">View the source</a></p>
</div></main>"""
    return page(
        f"{item['title']} for Home Assistant",
        item["description"],
        style,
        body,
        1,
        [style["heading_font"], style["body_font"]],
    )


def main() -> int:
    items = load_integrations()
    if not items:
        print("No integrations found", file=sys.stderr)
        return 1
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    (OUT / "index.html").write_text(build_home(items), encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    for item in items:
        folder = OUT / item["domain"]
        folder.mkdir()
        (folder / "index.html").write_text(build_detail(item), encoding="utf-8")
        print(f"page: {item['domain']}/index.html")
    print(f"wrote {len(items) + 1} pages to _site/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
