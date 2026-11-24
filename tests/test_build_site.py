import build_site as bs


def test_markdown_basics():
    html = bs.render_markdown("# Title\n\nHello `x` **bold**\n\n1. one\n2. two\n\n- a\n\n```\n<b>\n```\n")
    assert "<h1" not in html
    assert "<code>x</code>" in html and "<strong>bold</strong>" in html
    assert "<ol>" in html and "<ul>" in html
    assert "&lt;b&gt;" in html


def test_markdown_escapes_html():
    assert "<script>" not in bs.render_markdown("<script>alert(1)</script>")


def test_site_pages(tmp_path, monkeypatch):
    monkeypatch.setattr(bs, "OUT", tmp_path / "_site")
    assert bs.main() == 0
    home = (tmp_path / "_site" / "index.html").read_text(encoding="utf-8")
    for domain in ("hello_package", "bin_day", "countdown", "github_releases", "seed_tray", "sun_hours"):
        page = tmp_path / "_site" / domain / "index.html"
        assert page.is_file()
        assert f"{domain}/index.html" in home
        assert f"releases/latest/download/{domain}-1.0.0.hapkg" in home
        text = page.read_text(encoding="utf-8")
        assert "Changelog" in text and "Setup" in text
    assert "prefers-color-scheme:dark" in home


def test_bad_style_values_fall_back(tmp_path, monkeypatch):
    items = bs.load_integrations()
    for item in items:
        assert bs.HEX.match(item["style"]["accent"])
