#!/usr/bin/env python3
"""Build .hapkg packages for every integration under integrations/.

A .hapkg file is a ZIP archive whose root holds hapkg.json plus
custom_components/<domain>/... Builds are deterministic: entries are sorted
and timestamps are fixed.

Usage:
    python scripts/build_packages.py            # build into dist/
    python scripts/build_packages.py --check    # validate only
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INTEGRATIONS = ROOT / "integrations"
DIST = ROOT / "dist"
REPOSITORY = "Ding-Ding-Projects/home-assistant-integrations"
UPDATE_URL = f"https://github.com/{REPOSITORY}/releases/latest/download/index.json"
FIXED_TIME = (2020, 1, 1, 0, 0, 0)
EXCLUDED_NAMES = {"README.md", "CHANGELOG.md", "site.json"}
EXCLUDED_DIRS = {"__pycache__"}


class PackageError(Exception):
    """Raised when an integration is invalid."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_manifest(folder: Path) -> dict:
    manifest_path = folder / "manifest.json"
    if not manifest_path.is_file():
        raise PackageError(f"{folder.name}: manifest.json is missing")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        raise PackageError(f"{folder.name}: manifest.json is not valid JSON ({err})") from err
    if manifest.get("domain") != folder.name:
        raise PackageError(
            f"{folder.name}: manifest domain {manifest.get('domain')!r} does not match folder name"
        )
    if not manifest.get("version"):
        raise PackageError(f"{folder.name}: manifest has no version")
    if not (folder / "__init__.py").is_file():
        raise PackageError(f"{folder.name}: __init__.py is missing")
    return manifest


def collect_files(folder: Path) -> list[tuple[str, bytes]]:
    """Return sorted (archive path, content) pairs for an integration."""
    domain = folder.name
    entries: list[tuple[str, bytes]] = []
    for path in folder.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(folder)
        if any(part in EXCLUDED_DIRS for part in relative.parts):
            continue
        if path.suffix == ".pyc":
            continue
        if relative.parts == (path.name,) and path.name in EXCLUDED_NAMES:
            continue
        arcname = "/".join(("custom_components", domain, *relative.parts))
        entries.append((arcname, path.read_bytes()))
    entries.sort(key=lambda item: item[0])
    return entries


def build_one(folder: Path) -> tuple[dict, bytes]:
    """Validate one integration and return (index record without file, zip bytes)."""
    manifest = load_manifest(folder)
    domain = folder.name
    entries = collect_files(folder)
    hapkg = {
        "format": 1,
        "kind": "integration",
        "domain": domain,
        "version": str(manifest["version"]),
        "title": manifest.get("name", domain),
        "description": manifest.get("description")
        or f"{manifest.get('name', domain)} custom integration",
        "source": {"repository": REPOSITORY, "path": f"integrations/{domain}"},
        "update_url": UPDATE_URL,
        "files": {name: sha256_bytes(data) for name, data in entries},
    }
    import io

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        members = [("hapkg.json", (json.dumps(hapkg, indent=2, sort_keys=True) + "\n").encode())]
        members.extend(entries)
        members.sort(key=lambda item: item[0])
        for name, data in members:
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)
    return hapkg, buffer.getvalue()


def changelog_note(folder: Path) -> str:
    """Return a short note from the top entry of CHANGELOG.md, or an empty string."""
    path = folder / "CHANGELOG.md"
    if not path.is_file():
        return ""
    seen_heading = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            if line.startswith("##"):
                if seen_heading:
                    return ""
                seen_heading = True
            continue
        if seen_heading:
            return line.lstrip("-*").strip()
    return ""


def discover() -> list[Path]:
    if not INTEGRATIONS.is_dir():
        return []
    return sorted(p for p in INTEGRATIONS.iterdir() if p.is_dir() and not p.name.startswith("."))


def release_url(tag: str, filename: str) -> str:
    return f"https://github.com/{REPOSITORY}/releases/download/{tag}/{filename}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate without writing")
    parser.add_argument("--tag", default="local", help="release tag used in download URLs")
    args = parser.parse_args(argv)

    folders = discover()
    if not folders:
        print("No integrations found under integrations/", file=sys.stderr)
        return 1

    index = []
    try:
        built = [(folder, *build_one(folder)) for folder in folders]
    except PackageError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1

    if not args.check:
        DIST.mkdir(exist_ok=True)

    for folder, hapkg, data in built:
        filename = f"{hapkg['domain']}-{hapkg['version']}.hapkg"
        index.append(
            {
                "domain": hapkg["domain"],
                "kind": hapkg["kind"],
                "title": hapkg["title"],
                "version": hapkg["version"],
                "file": filename,
                "url": release_url(args.tag, filename),
                "sha256": sha256_bytes(data),
                "size": len(data),
                "notes": changelog_note(folder),
            }
        )
        if args.check:
            print(f"ok: {filename}")
        else:
            (DIST / filename).write_bytes(data)
            print(f"built: dist/{filename}")

    if not args.check:
        (DIST / "index.json").write_text(
            json.dumps({"packages": index}, indent=2) + "\n", encoding="utf-8"
        )
        print("wrote dist/index.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
