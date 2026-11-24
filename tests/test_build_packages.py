import hashlib
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import build_packages as bp  # noqa: E402


def make_integration(root: Path, domain: str, version: str = "1.2.3", manifest_domain=None):
    folder = root / domain
    folder.mkdir(parents=True)
    (folder / "manifest.json").write_text(
        json.dumps(
            {"domain": manifest_domain or domain, "name": "Demo", "version": version}
        )
    )
    (folder / "__init__.py").write_text("# init\n")
    (folder / "README.md").write_text("docs\n")
    (folder / "__pycache__").mkdir()
    (folder / "__pycache__" / "x.pyc").write_bytes(b"junk")
    return folder


def test_build_one_contents(tmp_path):
    folder = make_integration(tmp_path, "demo")
    hapkg, data = bp.build_one(folder)
    out = tmp_path / "demo.zip"
    out.write_bytes(data)
    with zipfile.ZipFile(out) as z:
        names = z.namelist()
        assert names == sorted(names)
        assert set(names) == {
            "hapkg.json",
            "custom_components/demo/__init__.py",
            "custom_components/demo/manifest.json",
        }
        meta = json.loads(z.read("hapkg.json"))
        assert meta["format"] == 1 and meta["kind"] == "integration"
        assert set(meta["files"]) == set(names) - {"hapkg.json"}
        for name, digest in meta["files"].items():
            assert hashlib.sha256(z.read(name)).hexdigest() == digest
    assert hapkg["version"] == "1.2.3"


def test_deterministic(tmp_path):
    folder = make_integration(tmp_path, "demo")
    assert bp.build_one(folder)[1] == bp.build_one(folder)[1]


def test_domain_mismatch_rejected(tmp_path):
    folder = make_integration(tmp_path, "demo", manifest_domain="other")
    try:
        bp.build_one(folder)
    except bp.PackageError as err:
        assert "does not match" in str(err)
    else:
        raise AssertionError("expected PackageError")


def test_missing_version_rejected(tmp_path):
    folder = make_integration(tmp_path, "demo", version="")
    try:
        bp.build_one(folder)
    except bp.PackageError as err:
        assert "version" in str(err)
    else:
        raise AssertionError("expected PackageError")


def test_real_repo_check_passes():
    assert bp.main(["--check"]) == 0


def test_real_repo_build_writes_index(tmp_path, monkeypatch):
    monkeypatch.setattr(bp, "DIST", tmp_path / "dist")
    assert bp.main([]) == 0
    index = json.loads((tmp_path / "dist" / "index.json").read_text())
    entry = next(p for p in index["packages"] if p["domain"] == "hello_package")
    package = tmp_path / "dist" / entry["file"]
    assert hashlib.sha256(package.read_bytes()).hexdigest() == entry["sha256"]
