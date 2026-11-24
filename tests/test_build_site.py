import json
import re
from datetime import date

import build_site as bs

DOMAINS = ("hello_package", "bin_day", "countdown", "github_releases", "seed_tray", "sun_hours")
ROOT_CLASS = {
    "bin_day": "bd", "countdown": "cd", "github_releases": "gh",
    "seed_tray": "sd", "sun_hours": "sn", "hello_package": "hp",
}


def test_markdown_basics():
    html = bs.render_markdown("# Title\n\nHello `x` **bold**\n\n1. one\n2. two\n\n- a\n\n```\n<b>\n```\n")
    assert "<h1" not in html
    assert "<code>x</code>" in html and "<strong>bold</strong>" in html
    assert "<ol>" in html and "<ul>" in html
    assert "&lt;b&gt;" in html


def test_markdown_escapes_html():
    assert "<script>" not in bs.render_markdown("<script>alert(1)</script>")


def build(tmp_path, monkeypatch):
    monkeypatch.setattr(bs, "OUT", tmp_path / "_site")
    assert bs.main() == 0
    return tmp_path / "_site"


def test_every_page_exists_with_download_and_theme(tmp_path, monkeypatch):
    site = build(tmp_path, monkeypatch)
    home = (site / "index.html").read_text(encoding="utf-8")
    assert 'class="sh"' in home and "prefers-color-scheme:dark" in home
    assert "prefers-reduced-motion" in home
    for domain in DOMAINS:
        text = (site / domain / "index.html").read_text(encoding="utf-8")
        assert f'class="{ROOT_CLASS[domain]}"' in text
        assert f'href="{domain}/"' in home
        url = f"releases/latest/download/{domain}-1.0.0.hapkg"
        assert url in home and url in text
        assert 'href="../"' in text
        assert "prefers-reduced-motion" in text
        assert "<script" not in text  # no runtime
        site_json = json.loads((bs.INTEGRATIONS / domain / "site.json").read_text())
        assert site_json["accent"] in text
        assert "fonts.googleapis.com" in text
        for anchor in ("setup", "entities", "install", "changelog"):
            assert f'id="{anchor}"' in text
        assert "Initial release" in text


def test_signature_motifs(tmp_path, monkeypatch):
    site = build(tmp_path, monkeypatch)
    page = lambda d: (site / d / "index.html").read_text(encoding="utf-8")
    assert 'class="road"' in page("bin_day") and page("bin_day").count('class="day') == 14
    assert 'class="huge"' in page("countdown") and 'class="perf"' in page("countdown")
    assert 'class="rail"' in page("github_releases") and 'class="term' in page("github_releases")
    assert 'class="tray"' in page("seed_tray") and 'class="cell' in page("seed_tray")
    assert 'class="arc"' in page("sun_hours") and 'class="band b6"' in page("sun_hours")
    assert 'class="box"' in page("hello_package") and "custom_components/hello_package/" in page("hello_package")


def test_entities_come_from_readme(tmp_path, monkeypatch):
    site = build(tmp_path, monkeypatch)
    text = (site / "bin_day" / "index.html").read_text(encoding="utf-8")
    assert "sensor.&lt;name&gt;_next_collection" in text


def test_home_lists_every_integration_with_card_colour(tmp_path, monkeypatch):
    site = build(tmp_path, monkeypatch)
    home = (site / "index.html").read_text(encoding="utf-8")
    assert home.count('<article class="c"') == len(DOMAINS)
    for domain in DOMAINS:
        card = json.loads((bs.INTEGRATIONS / domain / "site.json").read_text())["card_color"]
        assert f"--c:{card}" in home


def test_bad_style_values_fall_back():
    items = bs.load_integrations(date(2026, 11, 24))
    for item in items:
        assert bs.HEX.match(item["style"]["accent"])
        assert item["style"]["fonts_url"].startswith(bs.FONTS_PREFIX)


def test_daylight_is_seasonal():
    assert bs.daylight_minutes(43.65, date(2026, 6, 21)) > 880
    assert bs.daylight_minutes(43.65, date(2026, 12, 21)) < 560
    assert bs.daylight_minutes(43.65, date(2026, 3, 21)) - bs.daylight_minutes(43.65, date(2026, 3, 20)) > 0


def test_css_files_exist_for_every_theme():
    for theme in bs.THEMES:
        assert (bs.CSS_DIR / f"{theme}.css").is_file()
        assert re.search(r"\{", (bs.CSS_DIR / f"{theme}.css").read_text(encoding="utf-8"))
