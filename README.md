# Home Assistant integrations

A monorepo of custom Home Assistant integrations, each shipped as a drag-and-drop `.hapkg`
package file for the Marketplace of [home-assistant-material](https://github.com/Ding-Ding-Projects/home-assistant-material).

## Install a package

1. Open the repository's **Releases** page and download the `.hapkg` file you want
   (for example `hello_package-1.0.0.hapkg`). `index.json` lists every package with its SHA-256.
2. In home-assistant-material, open the Marketplace page and drag the file onto it, or choose
   **Install from a package file**.
3. Add the integration from Settings, Devices and services.

## Security note

A package runs code with full access to your Home Assistant instance. Only install packages
you trust, and compare the file's SHA-256 against `index.json` from the same release.

## Repository layout

```
integrations/<domain>/     a normal custom integration plus README.md
scripts/build_packages.py  builds dist/<domain>-<version>.hapkg and dist/index.json
tests/                     pytest tests for the build script
```

Included integration: [`hello_package`](integrations/hello_package/README.md), a minimal demo
that creates one sensor reporting the integration version.

## Add a new integration

1. Create `integrations/<domain>/` containing `manifest.json` (with `domain` equal to the folder
   name, plus `name`, `version`, `codeowners`, `documentation`, `iot_class`, `requirements`),
   `__init__.py`, `config_flow.py` if it has one, and a `README.md`.
2. Run `build.bat` (Windows; installs Python through Chocolatey if missing) or
   `python scripts/build_packages.py`. Use `--check` to validate without writing.
3. Commit and push to `main`. The release workflow builds, tests, and publishes a normal
   release with every package attached.

## The .hapkg format

A `.hapkg` is a ZIP archive with `hapkg.json` and `custom_components/<domain>/...` at its root
and nothing else (`README.md` and `__pycache__` are excluded). Builds are deterministic.

```json
{
  "format": 1,
  "kind": "integration",
  "domain": "hello_package",
  "version": "1.0.0",
  "title": "Hello Package",
  "description": "...",
  "source": {"repository": "Ding-Ding-Projects/home-assistant-integrations", "path": "integrations/hello_package"},
  "files": {"custom_components/hello_package/__init__.py": "<sha256 hex>"}
}
```

Every file in the archive except `hapkg.json` is listed in `files` with its SHA-256.

## License

Apache-2.0, matching Home Assistant.
