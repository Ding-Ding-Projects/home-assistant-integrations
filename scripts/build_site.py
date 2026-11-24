#!/usr/bin/env python3
"""Generate the GitHub Pages site into _site/ from the integration folders.

Standard library only, no runtime scripting in the output. The look of every page is ported from
the design boards in design/canvases/integration-packages/ (CSS lives in scripts/site_css/).
Content comes from each integration's manifest.json, README.md, CHANGELOG.md and site.json.

site.json keys: theme, accent, secondary, heading_font, body_font, card_color, fonts_url,
tagline, description, hero_lead, what_heading.

Usage:
    python scripts/build_site.py
"""

from __future__ import annotations

import html
import json
import math
import re
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INTEGRATIONS = ROOT / "integrations"
CSS_DIR = ROOT / "scripts" / "site_css"
OUT = ROOT / "_site"
REPOSITORY = "Ding-Ding-Projects/home-assistant-integrations"
REPO_URL = f"https://github.com/{REPOSITORY}"
DEFAULTS = {
    "theme": "home",
    "accent": "#2f5bff",
    "secondary": "#4dd0e1",
    "heading_font": "Roboto",
    "body_font": "Roboto",
    "card_color": "#7aa2ff",
    "fonts_url": "",
    "tagline": "",
    "description": "",
    "hero_lead": "",
    "what_heading": "What it does",
}
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
FONT = re.compile(r"^[A-Za-z0-9 ]{1,40}$")
FONTS_PREFIX = "https://fonts.googleapis.com/css2?family="
DL_ICON = (
    '<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M12 4v11M7 11l5 5 5-5M5 20h14"></path></svg>'
)
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]
DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def inline(text: str) -> str:
    """Render inline Markdown: code, bold, links."""
    out = []
    for part in re.split(r"(`[^`]+`)", text):
        if part.startswith("`") and part.endswith("`") and len(part) > 1:
            out.append(f"<code>{esc(part[1:-1])}</code>")
            continue
        safe = esc(part)
        safe = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", safe)
        safe = re.sub(
            r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" rel="noopener">\1</a>', safe
        )
        out.append(safe)
    return "".join(out)


def render_markdown(source: str, skip_title: bool = True, heading_offset: int = 0) -> str:
    """Render the small Markdown subset used by the integration docs."""
    out: list[str] = []
    paragraph: list[str] = []
    list_kind: str | None = None
    in_code = False
    code: list[str] = []

    def flush() -> None:
        nonlocal paragraph
        if paragraph:
            out.append(f"<p>{inline(' '.join(paragraph))}</p>")
            paragraph = []

    def close_list() -> None:
        nonlocal list_kind
        if list_kind:
            out.append(f"</{list_kind}>")
            list_kind = None

    for raw in source.splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            if in_code:
                out.append("<pre><code>" + esc("\n".join(code)) + "</code></pre>")
                code, in_code = [], False
            else:
                flush()
                close_list()
                in_code = True
            continue
        if in_code:
            code.append(raw)
            continue
        heading = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading:
            flush()
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
            flush()
            kind = "ol" if item.group(1)[0].isdigit() else "ul"
            if list_kind != kind:
                close_list()
                out.append(f"<{kind}>")
                list_kind = kind
            out.append(f"<li>{inline(item.group(2))}</li>")
            continue
        if not line.strip():
            flush()
            close_list()
            continue
        close_list()
        paragraph.append(line.strip())
    flush()
    close_list()
    return "\n".join(out)


# ---------------------------------------------------------------- content extraction


def split_sections(readme: str) -> tuple[list[str], dict[str, list[str]]]:
    """Return (intro paragraphs, {section name lowercased: lines}) from a README."""
    intro_lines: list[str] = []
    sections: dict[str, list[str]] = {}
    current: list[str] | None = None
    for line in readme.splitlines():
        if line.startswith("## "):
            current = sections.setdefault(line[3:].strip().lower(), [])
        elif line.startswith("# "):
            continue
        elif current is not None:
            current.append(line)
        else:
            intro_lines.append(line)
    paragraphs = [" ".join(p.split()) for p in re.split(r"\n\s*\n", "\n".join(intro_lines)) if p.strip()]
    return paragraphs, sections


def list_items(lines: list[str]) -> list[str]:
    items = []
    for line in lines:
        match = re.match(r"^\s*(?:\d+\.|[-*])\s+(.*)$", line)
        if match:
            items.append(match.group(1).strip())
    return items


def paragraphs_of(lines: list[str]) -> list[str]:
    text = "\n".join(lines)
    return [" ".join(p.split()) for p in re.split(r"\n\s*\n", text) if p.strip()]


def entity_rows(items: list[str]) -> list[tuple[str, str]]:
    rows = []
    for item in items:
        match = re.match(r"^`([^`]+)`:?\s*(.*)$", item)
        rows.append((match.group(1), match.group(2)) if match else ("", item))
    return rows


def changelog_entries(changelog: str) -> list[tuple[str, list[str]]]:
    entries: list[tuple[str, list[str]]] = []
    for line in changelog.splitlines():
        if line.startswith("## "):
            entries.append((line[3:].strip(), []))
        elif entries:
            text = line.strip().lstrip("-*").strip()
            if text:
                entries[-1][1].append(text)
    return entries


def pretty_date(day: date) -> str:
    return f"{day.day} {MONTHS[day.month - 1]} {day.year}"


# ---------------------------------------------------------------- data loading


def load_integrations(today: date | None = None) -> list[dict]:
    today = today or date.today()
    items = []
    for folder in sorted(p for p in INTEGRATIONS.iterdir() if p.is_dir()):
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        style = dict(DEFAULTS)
        site_file = folder / "site.json"
        if site_file.is_file():
            style.update(json.loads(site_file.read_text(encoding="utf-8")))
        for key in ("accent", "secondary", "card_color"):
            if not HEX.match(str(style[key])):
                style[key] = DEFAULTS[key]
        for key in ("heading_font", "body_font"):
            if not FONT.match(str(style[key])):
                style[key] = DEFAULTS[key]
        if not str(style["fonts_url"]).startswith(FONTS_PREFIX):
            style["fonts_url"] = ""
        if style["theme"] not in THEMES:
            style["theme"] = "home"
        readme_path = folder / "README.md"
        readme = readme_path.read_text(encoding="utf-8") if readme_path.is_file() else ""
        changelog_path = folder / "CHANGELOG.md"
        changelog = changelog_path.read_text(encoding="utf-8") if changelog_path.is_file() else ""
        paragraphs, sections = split_sections(readme)
        shipped = sorted(
            "/".join(p.relative_to(folder).parts)
            for p in folder.rglob("*")
            if p.is_file()
            and "__pycache__" not in p.parts
            and p.name not in {"README.md", "CHANGELOG.md", "site.json"}
            and p.suffix != ".pyc"
        )
        items.append(
            {
                "domain": folder.name,
                "title": manifest.get("name", folder.name),
                "version": str(manifest["version"]),
                "iot_class": manifest.get("iot_class", ""),
                "style": style,
                "description": style["description"] or (paragraphs[0] if paragraphs else ""),
                "intro": paragraphs[1:] if len(paragraphs) > 1 else paragraphs,
                "setup": list_items(sections.get("setup", [])),
                "entities": entity_rows(list_items(sections.get("entities", []))),
                "options": list_items(sections.get("options", [])),
                "install": paragraphs_of(sections.get("install", [])),
                "changelog": changelog_entries(changelog),
                "files": shipped,
                "built": today,
            }
        )
    return items


def download_url(item: dict) -> str:
    return f"{REPO_URL}/releases/latest/download/{item['domain']}-{item['version']}.hapkg"


def source_url(item: dict) -> str:
    return f"{REPO_URL}/tree/main/integrations/{item['domain']}"


# ---------------------------------------------------------------- page chrome


def css_for(theme: str) -> str:
    return (CSS_DIR / f"{theme}.css").read_text(encoding="utf-8")


def document(title: str, description: str, fonts_url: str, css: str, root: str, bg: str) -> str:
    fonts = ""
    if fonts_url:
        fonts = (
            '<link rel="preconnect" href="https://fonts.googleapis.com">'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            f'<link rel="stylesheet" href="{esc(fonts_url)}">'
        )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
{fonts}
<style>body{{margin:0}}{bg}
{css}</style>
</head>
<body>
{root}
</body>
</html>
"""


def install_text(item: dict) -> str:
    paragraphs = item["install"] or [
        "Download the package and drag it onto the Marketplace page in Home Assistant."
    ]
    return "".join(f"<p>{inline(p)}</p>" for p in paragraphs)


def changelog_html(item: dict, heading_tag: str = "h3") -> str:
    out = []
    for version, notes in item["changelog"]:
        out.append(f"<{heading_tag}>{esc(version)}</{heading_tag}>")
        out.extend(f"<p>{inline(n)}</p>" for n in notes)
    return "".join(out)


def entity_pairs(item: dict) -> list[tuple[str, str]]:
    return item["entities"]


# ---------------------------------------------------------------- per-theme pages
# Each builder returns the root element HTML for one integration page.


def page_bin_day(item: dict) -> str:
    today = item["built"]
    monday = today - timedelta(days=today.weekday())
    days = []
    for i in range(14):
        d = monday + timedelta(days=i)
        dow = d.weekday()
        week = i // 7
        is_today = d == today
        r = 1 if dow == 3 else 0.12
        b = 1 if (dow == 3 and week == 1) else 0.12
        g = 1 if dow == 0 else 0.12
        days.append(
            f'<div class="{"day now" if is_today else "day"}" style="animation-delay:{0.03 * i:.2f}s">'
            f'<span class="d">{DOW[dow]}</span><span class="n">{d.day}</span>'
            f'<span class="dots"><i style="background:#b4b8bd;opacity:{r}"></i>'
            f'<i style="background:#58a6ff;opacity:{b}"></i>'
            f'<i style="background:#5ecb7a;opacity:{g}"></i></span></div>'
        )
    st = item["style"]
    rows = "".join(
        f"<tr><td><code>{esc(c)}</code></td><td>{inline(t)}</td></tr>" for c, t in entity_pairs(item)
    )
    setup = "".join(f"<li>{inline(s)}</li>" for s in item["setup"])
    options = "".join(f"<p>{inline(o)}</p>" for o in item["options"])
    intro = "".join(f"<p>{inline(p)}</p>" for p in item["intro"])
    return f"""<div class="bd" style="--ac:{st['accent']}">
<nav class="w nav" aria-label="Site"><a href="../" style="margin-right:auto">All integrations</a>
<a href="#setup">Setup</a><a href="#entities">Entities</a><a href="#install">Install</a><a href="#changelog">Changelog</a></nav>
<header class="w hero"><h1 class="dsp">Bin<br>day</h1>
<div class="side"><p style="margin:0;font-size:19px">{esc(st['hero_lead'])}</p>
<a class="btn" href="{esc(download_url(item))}">{DL_ICON}Download {esc(item['domain'])}-{esc(item['version'])}.hapkg</a>
<span style="font-size:13px;color:#a5a8a1">Version {esc(item['version'])}, built {pretty_date(item['built'])}</span></div></header>
<svg class="road" aria-hidden="true"><line x1="0" y1="7" x2="100%" y2="7" stroke="#f2f2ec" stroke-width="4" stroke-dasharray="36 20"></line></svg>
<div class="w">
<div class="strip" role="img" aria-label="Sample: two weeks from Monday {monday.day} {MONTHS[monday.month - 1]}, compost on Mondays, rubbish every Thursday, recycling every second Thursday">{''.join(days)}</div>
<div class="key"><span><i style="background:#b4b8bd"></i>Rubbish, weekly</span><span><i style="background:#58a6ff"></i>Recycling, every 2 weeks</span><span><i style="background:#5ecb7a"></i>Compost, weekly</span><span><i style="background:var(--ac)"></i>Today, {DOW[today.weekday()]} {today.day} {MONTHS[today.month - 1]} (sample streams)</span></div>
<section class="sec"><h2 class="dsp">{esc(st['what_heading'])}</h2><div class="body">{intro}</div></section>
<section class="sec" id="setup"><h2 class="dsp">Setup</h2><div class="body"><ol class="ol">{setup}</ol></div></section>
<section class="sec" id="entities"><h2 class="dsp">Entities</h2><div class="body scroll"><table class="tbl"><thead><tr><th scope="col">Entity</th><th scope="col">Shows</th></tr></thead><tbody>{rows}</tbody></table></div></section>
<section class="sec"><h2 class="dsp">Options</h2><div class="body">{options}</div></section>
<section class="sec" id="install"><h2 class="dsp">Install</h2><div class="body">{install_text(item)}</div></section>
<section class="sec" id="changelog"><h2 class="dsp">Changelog</h2><div class="body">{changelog_html(item)}</div></section>
<footer class="foot">Source: <a href="{esc(source_url(item))}">{REPOSITORY}/integrations/{esc(item['domain'])}</a></footer>
</div></div>"""


def days_until_yearly(month: int, day: int, today: date) -> tuple[int, date]:
    for year in (today.year, today.year + 1):
        try:
            candidate = date(year, month, day)
        except ValueError:
            candidate = date(year, month, 28)
        if candidate >= today:
            return (candidate - today).days, candidate
    raise AssertionError("unreachable")


def page_countdown(item: dict) -> str:
    today = item["built"]
    st = item["style"]
    xmas, _ = days_until_yearly(12, 25, today)
    mum, _ = days_until_yearly(12, 3, today)
    leaves_src = [
        ("Mum's birthday", 12, 3, "yearly"),
        ("Car insurance renewal", 12, 14, "one-off"),
        ("Christmas Day", 12, 25, "yearly"),
        ("Wedding anniversary", 2, 6, "yearly"),
    ]
    leaves = []
    for i, (name, month, day, kind) in enumerate(leaves_src):
        n, when = days_until_yearly(month, day, today)
        leaves.append(
            f'<div class="leaf" style="animation-delay:{0.08 * i + 0.2:.2f}s">'
            '<div class="perf" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></div>'
            f'<span class="mono" style="padding-top:10px">days until</span><b>{n}</b>'
            f'<span class="t">{esc(name)}</span>'
            f'<span class="mono">{when.day} {MONTHS[when.month - 1][:3]} / {kind}</span></div>'
        )
    ents = "".join(
        f"<li><code>{esc(c)}</code><span>{inline(t)}</span></li>" for c, t in entity_pairs(item)
    )
    setup = "".join(f"<li>{inline(s)}</li>" for s in item["setup"])
    options = "".join(f"<p>{inline(o)}</p>" for o in item["options"])
    intro = "".join(f"<p>{inline(p)}</p>" for p in item["intro"])
    return f"""<div class="cd" style="--ac:{st['accent']}">
<nav class="w mast mono" aria-label="Site"><a href="../" style="margin-right:auto">All integrations</a>
<a href="#setup">Setup</a><a href="#entities">Entities</a><a href="#install">Install</a><a href="#changelog">Changelog</a></nav>
<header class="w hero"><span class="huge" role="img" aria-label="{xmas} days until Christmas (sample)">{xmas}</span>
<div class="txt"><span class="mono">Countdown / version {esc(item['version'])} / {pretty_date(today)}</span>
<h1>days until Christmas. <i>And {mum} until Mum's birthday.</i></h1>
<p style="margin:0;max-width:46ch">{esc(st['hero_lead'])}</p>
<a class="btn" href="{esc(download_url(item))}">{DL_ICON}Download {esc(item['domain'])}-{esc(item['version'])}.hapkg</a></div></header>
<div class="w">
<div class="leaves" role="group" aria-label="Sample dates">{''.join(leaves)}</div>
<div class="cols">
<section class="col"><span class="mono">i. what it does</span><h2>{esc(st['what_heading'])}</h2>{intro}</section>
<section class="col" id="setup"><span class="mono">ii. setup</span><h2>Add it, then add dates</h2><ol>{setup}</ol></section>
<section class="col" id="entities"><span class="mono">iii. entities created</span><h2>Two per date</h2><ul class="ents">{ents}</ul></section>
<section class="col"><span class="mono">iv. options</span><h2>Change or remove a date</h2>{options}</section>
<section class="col" id="install"><span class="mono">v. install</span><h2>Drag, drop, confirm</h2>{install_text(item)}</section>
<section class="col" id="changelog"><span class="mono">vi. changelog</span><h2>Changelog</h2>{changelog_html(item, "h3")}</section>
</div>
<footer class="foot mono">Source: <a href="{esc(source_url(item))}">{REPOSITORY}/integrations/{esc(item['domain'])}</a></footer>
</div></div>"""


def page_github_releases(item: dict) -> str:
    st = item["style"]
    sample = [("home-assistant/core", "2026.11.3"), ("esphome/esphome", "2026.11.1"),
              ("home-assistant/frontend", "20261118.0"), ("Koenkk/zigbee2mqtt", "2.9.1")]
    rows = "".join(
        f'<div class="r" style="animation-delay:{0.12 * i + 0.3:.2f}s"><span>{esc(n)}</span><span class="t">{esc(t)}</span></div>'
        for i, (n, t) in enumerate(sample)
    )
    kv = "".join(
        f"<div><code>{esc(c)}</code><span>{inline(t)}</span></div>" for c, t in entity_pairs(item)
    )
    setup = "".join(f"<li>{inline(s)}</li>" for s in item["setup"])
    options = "".join(f"<p>{inline(o)}</p>" for o in item["options"])
    intro = "".join(f"<p>{inline(p)}</p>" for p in item["intro"])
    latest = item["changelog"][0][0] if item["changelog"] else item["version"]
    return f"""<div class="gh" style="--ac:{st['accent']}">
<nav class="w nav mono" aria-label="Site"><a href="../" style="margin-right:auto">../all-integrations</a>
<a href="#setup">setup</a><a href="#entities">entities</a><a href="#install">install</a><a href="#changelog">changelog</a></nav>
<div class="w split">
<header class="left"><span class="tag mono">github_releases v{esc(item['version'])}</span>
<h1>Know when it <span>ships</span>.</h1><p>{esc(st['hero_lead'])}</p>
<a class="btn" href="{esc(download_url(item))}">{DL_ICON}Download .hapkg</a>
<div class="term mono" role="img" aria-label="Sample output: four watched repositories and their latest release tags"><div class="bar"><i></i><i></i><i></i></div>
<div class="rows">{rows}<div><span style="color:#b3b6c6">sample output</span> <span class="cur"></span></div></div></div></header>
<main class="rail">
<section class="e"><span class="tag mono">what it does</span><h2>{esc(st['what_heading'])}</h2>{intro}</section>
<section class="e" id="setup"><span class="tag mono">setup</span><h2>Type owner/name</h2><ol>{setup}</ol></section>
<section class="e" id="entities"><span class="tag mono">entities created</span><h2>Two sensors each</h2><div class="kv">{kv}</div></section>
<section class="e"><span class="tag mono">options</span><h2>Options</h2>{options}</section>
<section class="e" id="install"><span class="tag mono">install</span><h2>Drop the file on the Marketplace</h2>{install_text(item)}</section>
<section class="e" id="changelog"><span class="tag mono">v{esc(latest)}</span><h2>Changelog</h2>{changelog_html(item, "h3")}</section>
</main></div>
<footer class="w foot mono">source: <a href="{esc(source_url(item))}">{REPOSITORY}/integrations/{esc(item['domain'])}</a></footer></div>"""


def seed_icon(kind: int) -> str:
    head = ('<svg aria-hidden="true" width="72" height="72" viewBox="0 0 24 24" fill="none" '
            'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">')
    if kind == 0:
        return head + '<ellipse cx="12" cy="17" rx="2.6" ry="1.8"></ellipse><path d="M5 21h14"></path></svg>'
    if kind == 1:
        return head + ('<path d="M5 21h14"></path><g class="grow"><path d="M12 21v-7M12 14c0-2.6-2-4-4.5-4 0 2.6 2 4 4.5 4z'
                       'M12 15.5c0-2 1.6-3.2 3.8-3.2 0 2-1.6 3.2-3.8 3.2z"></path></g></svg>')
    return head + ('<path d="M5 21h14"></path><g class="grow"><path d="M12 21V8M12 12c0-4-3-6-7-6 0 4 3 6 7 6z'
                   'M12 15c0-3 2.5-5 6-5 0 3-2.5 5-6 5zM12 8c0-2 1-3.5 2.6-4.4"></path></g></svg>')


def page_seed_tray(item: dict) -> str:
    st = item["style"]
    sample = [("Radish", 8, 4, 14), ("Lettuce", 14, 5, 28), ("Spinach", 12, 7, 28), ("Carrot", 6, 14, 35),
              ("Sugar snap pea", 21, 8, 21), ("Mung bean", 4, 5, 18), ("Adzuki bean", 10, 7, 21)]
    cells = []
    for i, (name, age, germ, transplant) in enumerate(sample):
        left = max(0, transplant - age)
        kind = 0 if age < germ else (1 if left > 0 else 2)
        stage = ["Germinating", "Growing on", "Ready to transplant"][kind]
        text = f"{left} days to transplant" if left > 0 else "Plant out now"
        cells.append(
            f'<div class="{"cell ready" if kind == 2 else "cell"}" style="animation-delay:{0.07 * i:.2f}s">'
            f'{seed_icon(kind)}<b class="bg">{esc(name)}</b><span>{stage}</span><span>{text}</span></div>'
        )
    rows = "".join(
        f"<tr><td><code>{esc(c)}</code></td><td>{inline(t)}</td></tr>" for c, t in entity_pairs(item)
    )
    setup = "".join(f"<li>{inline(s)}</li>" for s in item["setup"])
    options = "".join(f"<p>{inline(o)}</p>" for o in item["options"])
    intro = "".join(f"<p>{inline(p)}</p>" for p in item["intro"])
    return f"""<div class="sd" style="--ac:{st['accent']}">
<nav class="w nav bg" aria-label="Site"><a href="../" style="margin-right:auto;padding-left:0">All integrations</a>
<a href="#setup">Setup</a><a href="#entities">Entities</a><a href="#install">Install</a><a href="#changelog">Changelog</a></nav>
<div class="w"><header class="hero"><h1 class="bg">Seed tray, <em>from sown to planted out</em></h1><p>{esc(st['hero_lead'])}</p>
<a class="btn bg" href="{esc(download_url(item))}">{DL_ICON}Download {esc(item['domain'])}-{esc(item['version'])}.hapkg</a>
<span class="bg" style="font-size:14px">Version {esc(item['version'])}, built {pretty_date(item['built'])}</span></header>
<div class="tray" role="img" aria-label="Sample tray: seven sowings at different stages">{''.join(cells)}</div>
<div class="pk">
<section class="p"><span class="k bg">What it does</span><h2 class="bg">{esc(st['what_heading'])}</h2>{intro}
<div class="stages bg"><span>Germinating</span><span>Growing on</span><span>Ready to transplant</span></div></section>
<section class="p" id="setup"><span class="k bg">Setup</span><h2 class="bg">Sow, then note it down</h2><ol>{setup}</ol></section>
<section class="p" id="entities"><span class="k bg">Entities created</span><h2 class="bg">Two sensors per sowing</h2>
<div class="scroll"><table class="tb"><thead><tr><th scope="col" class="bg">Entity</th><th scope="col" class="bg">Shows</th></tr></thead><tbody>{rows}</tbody></table></div></section>
<section class="p"><span class="k bg">Options</span><h2 class="bg">Adjust as the tray tells you</h2>{options}</section>
<section class="p" id="install"><span class="k bg">Install</span><h2 class="bg">Drop the file on the Marketplace</h2>{install_text(item)}</section>
<section class="p" id="changelog"><span class="k bg">Changelog</span><h2 class="bg">Changelog</h2>{changelog_html(item, "h3")}</section>
</div>
<footer class="foot bg">Source: <a href="{esc(source_url(item))}">{REPOSITORY}/integrations/{esc(item['domain'])}</a></footer>
</div></div>"""


def daylight_minutes(lat: float, day: date) -> float:
    """Approximate daylight length in minutes (NOAA-style declination formula)."""
    n = day.timetuple().tm_yday
    decl = math.radians(23.44) * math.sin(2 * math.pi * (n - 81) / 365)
    phi = math.radians(lat)
    cos_h = (math.sin(math.radians(-0.833)) - math.sin(phi) * math.sin(decl)) / (math.cos(phi) * math.cos(decl))
    cos_h = max(-1.0, min(1.0, cos_h))
    return round(2 * math.degrees(math.acos(cos_h)) / 15 * 60)


def page_sun_hours(item: dict) -> str:
    st = item["style"]
    today = item["built"]
    lat = 43.65
    minutes = daylight_minutes(lat, today)
    delta = minutes - daylight_minutes(lat, today - timedelta(days=1))
    if delta > 0:
        trend = f"{delta:.0f} minute{'s' if delta != 1 else ''} longer"
    elif delta < 0:
        trend = f"{-delta:.0f} minute{'s' if delta != -1 else ''} shorter"
    else:
        trend = "the same length"
    sign = "+" if delta > 0 else ("-" if delta < 0 else "")
    acc = st["accent"]
    ents = "".join(
        f"<div><code>{esc(c)}</code><span>{inline(t)}</span></div>" for c, t in entity_pairs(item)
    )
    setup = "".join(f"<li>{inline(s)}</li>" for s in item["setup"])
    options = "".join(f"<p>{inline(o)}</p>" for o in item["options"])
    intro = "".join(f"<p>{inline(p)}</p>" for p in item["intro"])
    return f"""<div class="sn" style="--ac:{acc}">
<nav class="w nav" aria-label="Site"><a href="../" style="margin-right:auto">All integrations</a>
<a href="#setup">Setup</a><a href="#entities">Entities</a><a href="#install">Install</a><a href="#changelog">Changelog</a></nav>
<header class="w hero">
<svg viewBox="0 -70 1000 510" role="img" aria-label="The sun high on its arc above the horizon"><path class="arc" d="M100 420 A400 400 0 0 1 900 420" fill="none" stroke="#1d1b3a" stroke-width="3"></path>
<line x1="0" y1="420" x2="1000" y2="420" stroke="#1d1b3a" stroke-width="3"></line>
<g class="sunw"><circle class="halo" cx="390" cy="35" r="62" fill="none" stroke="{acc}" stroke-width="3"></circle><circle cx="390" cy="35" r="40" fill="{acc}"></circle></g>
<g stroke="#1d1b3a" stroke-width="3" stroke-linecap="round"><line x1="100" y1="408" x2="100" y2="432"></line><line x1="900" y1="408" x2="900" y2="432"></line></g></svg>
<div class="core"><span class="ub n">{minutes}</span><h1 class="ub">minutes of daylight today</h1>
<p>{esc(st['hero_lead'])} Sample for latitude {lat}&deg;N: today is {trend} than yesterday.</p>
<a class="btn" href="{esc(download_url(item))}">{DL_ICON}Download {esc(item['domain'])}-{esc(item['version'])}.hapkg</a></div></header>
<section class="band b2"><div class="w"><div class="when"><span>Dawn</span><b class="ub">What it does</b></div><div class="what"><h2>{esc(st['what_heading'])}</h2>{intro}</div></div></section>
<section class="band b3" id="setup"><div class="w"><div class="when"><span>Morning</span><b class="ub">Setup</b></div><div class="what"><h2>Setup steps</h2><ol>{setup}</ol></div></div></section>
<section class="band b4" id="entities"><div class="w"><div class="when"><span>Noon</span><b class="ub">Entities</b></div><div class="what"><h2>Entities created</h2><div class="ents">{ents}</div></div></div></section>
<section class="band b5"><div class="w"><div class="when"><span>Afternoon</span><b class="ub">Options</b></div><div class="what"><h2>Options</h2>{options}</div></div></section>
<section class="band b5" id="install" style="padding-top:0"><div class="w"><div class="when"><span>Dusk</span><b class="ub">Install</b></div><div class="what"><h2>Drop the file on the Marketplace</h2>{install_text(item)}</div></div></section>
<section class="band b6" id="changelog"><div class="w"><div class="when"><span>Night</span><b class="ub">Changelog</b></div><div class="what"><h2>Changelog</h2>{changelog_html(item, "h3")}<p>Source: <a href="{esc(source_url(item))}">{REPOSITORY}/integrations/{esc(item['domain'])}</a></p></div></div></section>
</div>"""


def page_hello_package(item: dict) -> str:
    st = item["style"]
    acc = st["accent"]
    domain = item["domain"]
    tree_lines = [f"{domain}-{item['version']}.hapkg", "  <b>hapkg.json</b>", "  custom_components/" + domain + "/"]
    tree_lines += ["    " + esc(f) for f in item["files"]]
    tree = "\n".join(tree_lines).replace("&lt;b&gt;", "<b>")
    manifest_view = (
        "{\n"
        f'  "title": "{esc(item["title"])}",\n'
        f'  "version": "<b>{esc(item["version"])}</b>",\n'
        '  "kind": "integration",\n'
        f'  "domain": "{esc(domain)}",\n'
        f'  "source": {{"repository": "{REPOSITORY}", "path": "integrations/{esc(domain)}"}},\n'
        f'  "update_url": "{REPO_URL}/releases/latest/download/index.json",\n'
        '  "files": { "custom_components/' + esc(domain) + '/...": "sha256 of the file" }\n'
        "}"
    )
    ents = "".join(
        f"<pre>{esc(c)}    <b>{esc(item['version'])}</b></pre><p>{inline(t)}</p>" for c, t in entity_pairs(item)
    )
    setup = "".join(f"<li>{inline(s)}</li>" for s in item["setup"])
    options = "".join(f"<p>{inline(o)}</p>" for o in item["options"])
    intro = "".join(f"<p>{inline(p)}</p>" for p in item["intro"])
    marks = "".join(
        f'<span class="mark" aria-hidden="true" style="{pos}">+</span>'
        for pos in ("top:14px;left:4px", "top:14px;right:4px", "bottom:14px;left:4px", "bottom:14px;right:4px")
    )
    return f"""<div class="hp" style="--ac:{acc}">
<nav class="w nav" aria-label="Site"><a href="../" style="margin-right:auto">../</a>
<a href="#setup">setup</a><a href="#entities">entities</a><a href="#install">install</a><a href="#changelog">changelog</a></nav>
<hr class="rule">
<div class="w">
<header class="hero">{marks}
<svg class="box" aria-hidden="true" width="132" height="132" viewBox="0 0 48 48" fill="none" stroke="{acc}" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"><path d="M6 16l18-10 18 10v16l-18 10-18-10z"></path><path d="M6 16l18 10 18-10"></path><path d="M24 26v16"></path><path d="M15 11l18 10"></path></svg>
<h1>Hello, <i>package.</i></h1><p>{esc(st['hero_lead'])}</p>
<a class="btn" href="{esc(download_url(item))}">{DL_ICON}{esc(domain)}-{esc(item['version'])}.hapkg</a></header>
<section class="s"><span class="k"><b>01</b> / what it does</span><div class="v"><h2>{esc(st['what_heading'])}</h2>{intro}</div></section>
<section class="s"><span class="k"><b>02</b> / inside</span><div class="v"><h2>A ZIP with a manifest</h2><pre>{tree}</pre><pre>{manifest_view}</pre></div></section>
<section class="s" id="setup"><span class="k"><b>03</b> / setup</span><div class="v"><h2>Add it, press Submit</h2><ol>{setup}</ol></div></section>
<section class="s" id="entities"><span class="k"><b>04</b> / entities</span><div class="v"><h2>Entities created</h2>{ents}</div></section>
<section class="s"><span class="k"><b>05</b> / options</span><div class="v"><h2>Options</h2>{options}</div></section>
<section class="s" id="install"><span class="k"><b>06</b> / install</span><div class="v"><h2>Drag, drop, confirm</h2>{install_text(item)}</div></section>
<section class="s" id="changelog"><span class="k"><b>07</b> / changelog</span><div class="v"><h2>Changelog</h2>{changelog_html(item, "h3")}</div></section>
<footer class="foot">source: <a href="{esc(source_url(item))}">{REPOSITORY}/integrations/{esc(domain)}</a></footer>
</div></div>"""


THEMES = {
    "home": None,
    "bin_day": (page_bin_day, "#17191b"),
    "countdown": (page_countdown, "#f6efe4"),
    "github_releases": (page_github_releases, "#0b0d12"),
    "seed_tray": (page_seed_tray, "#f3ead7"),
    "sun_hours": (page_sun_hours, "#ffe8d2"),
    "hello_package": (page_hello_package, "#fafafa"),
}

HOME_FONTS = (
    "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;800"
    "&family=JetBrains+Mono:wght@400;500&display=swap"
)

HOME_ICONS = {
    "bin_day": '<path d="M5 7h14l-1.5 12a2 2 0 0 1-2 1.8h-7a2 2 0 0 1-2-1.8z"></path><path d="M3.5 7h17M9 4h6M10 11v6M14 11v6"></path>',
    "countdown": '<rect x="4" y="5" width="16" height="16" rx="3"></rect><path d="M4 10h16M8 3v4M16 3v4M10 14h1.5v4M14 14h2v2h-2v2h2"></path>',
    "github_releases": '<path d="M3 12V4h8l10 10-8 8z"></path><circle cx="8" cy="9" r="1.6"></circle>',
    "seed_tray": '<path d="M12 21v-9M12 12c0-4-3-6-7-6 0 4 3 6 7 6zM12 15c0-3 2.5-5 6-5 0 3-2.5 5-6 5zM6 21h12"></path>',
    "sun_hours": '<path d="M2 18h20M6 18a6 6 0 0 1 12 0M12 5v3M4.5 9.5l2 2M19.5 9.5l-2 2"></path>',
    "hello_package": '<path d="M3 8l9-5 9 5v8l-9 5-9-5z"></path><path d="M3 8l9 5 9-5M12 13v8"></path>',
}


def build_home(items: list[dict]) -> str:
    built = items[0]["built"]
    cards = []
    for i, item in enumerate(items):
        st = item["style"]
        icon = HOME_ICONS.get(item["domain"], HOME_ICONS["hello_package"])
        cards.append(
            f"""<article class="c" style="--c:{st['card_color']};animation-delay:{0.08 * i:.2f}s">
<span class="m"><svg aria-hidden="true" width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{icon}</svg></span>
<h2>{esc(item['title'])}</h2><p>{esc(item['description'])}</p>
<div class="meta mono"><span class="dot"></span><span>{esc(item['domain'])}</span><span>v{esc(item['version'])}</span><span>{pretty_date(built)}</span></div>
<div class="cf"><a class="b k" href="{esc(download_url(item))}">{DL_ICON}Download .hapkg</a>
<a class="more" href="{esc(item['domain'])}/">About {esc(item['title'])}</a></div></article>"""
        )
    count = len(items)
    root = f"""<div class="sh" style="--ac:#2f5bff">
<header class="w nav"><a class="brand" href="#top"><svg aria-hidden="true" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8l9-5 9 5v8l-9 5-9-5z"></path><path d="M3 8l9 5 9-5M12 13v8"></path></svg>Home Assistant integrations</a>
<a class="l" href="#integrations">Integrations</a><a class="l" href="#install">How to install</a><a class="l" href="{REPO_URL}">GitHub</a></header>
<main id="top">
<section class="w hero"><span class="mono" style="font-size:13px;color:var(--mut)">{count} integrations / one .hapkg file each</span>
<h1>Small integrations you install by <em>dropping a file</em>.</h1>
<p>Each integration here is a single package file. Download it, drag it onto the Marketplace page in Home Assistant, confirm, and it keeps itself up to date from then on.</p>
<div class="cta"><a class="b p" href="#integrations">Browse the integrations</a><a class="b s" href="#install">How installing works</a></div></section>
<section id="integrations" class="w grid" aria-label="All integrations">{''.join(cards)}</section>
<section id="install" class="how"><div class="w"><h2>Installing takes three steps</h2>
<ol class="steps">
<li><span class="num mono">01</span><b>Download the file</b>Every integration is one .hapkg file, built and published from the repository by its release workflow.</li>
<li><span class="num mono">02</span><b>Drop it on the Marketplace</b>Drag the file anywhere onto the Marketplace page, or use Install from a package file on a phone or with a keyboard.</li>
<li><span class="num mono">03</span><b>Confirm and restart</b>Home Assistant checks every file against its checksum, shows where the package came from, and asks before adding it.</li>
</ol></div></section></main>
<footer class="w foot"><span style="min-height:44px;display:inline-flex;align-items:center">Open source, one folder per integration.</span>
<a href="{REPO_URL}">{REPOSITORY}</a><a href="{REPO_URL}/releases">All releases</a></footer></div>"""
    bg = "html{background:#fbfaf7}@media (prefers-color-scheme:dark){html{background:#0f1012}}"
    return document(
        "Home Assistant integrations",
        "Custom Home Assistant integrations shipped as drag-and-drop .hapkg packages",
        HOME_FONTS,
        css_for("home"),
        root,
        bg,
    )


def build_detail(item: dict) -> str:
    st = item["style"]
    theme = st["theme"] if THEMES.get(st["theme"]) else "hello_package"
    builder, color = THEMES[theme]
    return document(
        f"{item['title']} for Home Assistant",
        item["description"],
        st["fonts_url"],
        css_for(theme),
        builder(item),
        f"html{{background:{color}}}",
    )


def main() -> int:
    items = load_integrations()
    if not items:
        print("No integrations found", file=sys.stderr)
        return 1
    if OUT.exists():
        for child in OUT.iterdir():
            shutil.rmtree(child) if child.is_dir() else child.unlink()
    OUT.mkdir(exist_ok=True)
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
