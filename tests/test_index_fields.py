import hashlib
import json

import build_packages as bp

REPO_URL = "https://github.com/Ding-Ding-Projects/home-assistant-integrations"
DOMAINS = {"hello_package", "bin_day", "countdown", "github_releases", "seed_tray", "sun_hours"}


def make_integration(root, domain="demo"):
    folder = root / domain
    folder.mkdir(parents=True)
    (folder / "manifest.json").write_text(json.dumps({"domain": domain, "name": "Demo", "version": "1.2.3"}))
    (folder / "__init__.py").write_text("# init\n")
    return folder


def test_hapkg_json_has_update_url(tmp_path):
    hapkg, _ = bp.build_one(make_integration(tmp_path))
    assert hapkg["update_url"] == f"{REPO_URL}/releases/latest/download/index.json"


def test_index_fields(tmp_path, monkeypatch):
    monkeypatch.setattr(bp, "DIST", tmp_path / "dist")
    assert bp.main(["--tag", "build-42"]) == 0
    index = json.loads((tmp_path / "dist" / "index.json").read_text())
    assert {p["domain"] for p in index["packages"]} == DOMAINS
    for entry in index["packages"]:
        assert set(entry) >= {"domain", "kind", "title", "version", "url", "sha256", "size", "notes"}
        assert entry["kind"] == "integration"
        assert entry["url"] == f"{REPO_URL}/releases/download/build-42/{entry['file']}"
        data = (tmp_path / "dist" / entry["file"]).read_bytes()
        assert entry["size"] == len(data)
        assert hashlib.sha256(data).hexdigest() == entry["sha256"]
        assert entry["notes"].startswith("Initial release")


def test_default_tag_is_local(tmp_path, monkeypatch):
    monkeypatch.setattr(bp, "DIST", tmp_path / "dist")
    bp.main([])
    index = json.loads((tmp_path / "dist" / "index.json").read_text())
    assert "/releases/download/local/" in index["packages"][0]["url"]


def test_changelog_note(tmp_path):
    folder = make_integration(tmp_path)
    assert bp.changelog_note(folder) == ""
    (folder / "CHANGELOG.md").write_text(
        "# Changelog\n\n## 1.2.3\n\n- Fixed a thing\n- older\n\n## 1.0.0\n\n- first\n"
    )
    assert bp.changelog_note(folder) == "Fixed a thing"
