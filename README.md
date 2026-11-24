# Home Assistant integrations

A monorepo of custom Home Assistant integrations, each shipped as a drag-and-drop `.hapkg`
package file for the Marketplace of [home-assistant-material](https://github.com/Ding-Ding-Projects/home-assistant-material).

Website: https://ding-ding-projects.github.io/home-assistant-integrations/ (generated from the
integration folders on every push to `main`).

## Integrations

| Integration | What it does |
| --- | --- |
| [`bin_day`](integrations/bin_day/README.md) | Rubbish and recycling collection schedule, with a "put the bins out tonight" sensor |
| [`countdown`](integrations/countdown/README.md) | Days until named dates, yearly or one-off |
| [`github_releases`](integrations/github_releases/README.md) | Latest release of public GitHub repositories, no token needed |
| [`seed_tray`](integrations/seed_tray/README.md) | Seed-starting tray stage and days to transplant |
| [`sun_hours`](integrations/sun_hours/README.md) | Daylight minutes today and change versus yesterday |
| [`hello_package`](integrations/hello_package/README.md) | Minimal example and template |

None of them needs an account or an API key.

## Install a package

1. Open the website or the repository's **Releases** page and download the `.hapkg` file you want
   (for example `bin_day-1.0.0.hapkg`). `index.json` lists every package with its SHA-256.
2. In home-assistant-material, open the Marketplace page and drag the file onto it, or choose
   **Install from a package file**.
3. Add the integration from Settings, Devices and services.

## Automatic updates

To ship an update: bump `version` in the integration's `manifest.json`, add an entry to its
`CHANGELOG.md`, and push to `main`. The release workflow rebuilds every package, publishes a new
release marked as latest with every `.hapkg` plus `index.json`, and installed copies update
themselves from `https://github.com/Ding-Ding-Projects/home-assistant-integrations/releases/latest/download/index.json`
unless the owner switched automatic updates off. Each `hapkg.json` carries that address as `update_url`.

`index.json` lists, for every package: `domain`, `kind`, `title`, `version`, `file`, `url` (the
release asset for that build), `sha256` and `size` of the `.hapkg`, and `notes` (the first line
of the newest `CHANGELOG.md` entry).

## Security note

A package runs code with full access to your Home Assistant instance. Only install packages
you trust, and compare the file's SHA-256 against `index.json` from the same release.

## Repository layout

```
integrations/<domain>/       a normal custom integration, README.md, CHANGELOG.md, site.json
scripts/build_packages.py    builds dist/<domain>-<version>.hapkg and dist/index.json
scripts/build_site.py        builds the website into _site/
tests/                       pytest tests (logic modules, packaging, site)
```

## Add a new integration

1. Create `integrations/<domain>/` containing `manifest.json` (with `domain` equal to the folder
   name, plus `name`, `version`, `codeowners`, `documentation`, `iot_class`, `requirements`),
   `__init__.py`, `config_flow.py` if it has one, `README.md` (with Setup, Entities and Options
   sections), `CHANGELOG.md`, and optionally `site.json` for the page styling (`accent`,
   `secondary`, `heading_font`, `body_font`, `tagline`, `description`).
2. Keep date and schedule maths in a `logic.py` with no Home Assistant imports so it can be
   tested; add tests under `tests/<domain>/`.
3. Run `build.bat` (Windows; installs Python through Chocolatey if missing) or
   `python scripts/build_packages.py`. Use `--check` to validate without writing, and
   `python scripts/build_site.py` to preview the site in `_site/`.
4. Push to `main`. The workflow builds, tests, releases, and deploys the site.

## The .hapkg format

A `.hapkg` is a ZIP archive with `hapkg.json` and `custom_components/<domain>/...` at its root
and nothing else (`README.md`, `CHANGELOG.md`, `site.json` and `__pycache__` are excluded).
Builds are deterministic.

```json
{
  "format": 1,
  "kind": "integration",
  "domain": "hello_package",
  "version": "1.0.0",
  "title": "Hello Package",
  "description": "...",
  "source": {"repository": "Ding-Ding-Projects/home-assistant-integrations", "path": "integrations/hello_package"},
  "update_url": "https://github.com/Ding-Ding-Projects/home-assistant-integrations/releases/latest/download/index.json",
  "files": {"custom_components/hello_package/__init__.py": "<sha256 hex>"}
}
```

Every file in the archive except `hapkg.json` is listed in `files` with its SHA-256.

## Testing

`python -m pytest` runs the packaging tests, the site tests, and pure-logic tests for each
integration's `logic.py` (which has no Home Assistant imports; `sun_hours` needs `astral`).
Entity and config-flow code is not covered by a live Home Assistant test run.

## License

Apache-2.0, matching Home Assistant.
