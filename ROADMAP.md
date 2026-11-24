# Roadmap

## Packaging pipeline
- [x] `.hapkg` build script with validation, deterministic output and `--check` mode (pytest)
- [x] `dist/index.json` with url, sha256, size and notes; `update_url` in every `hapkg.json` (pytest)
- [x] `build.bat` and `build-installer.bat` entrypoints (not run on a host without Python)
- [ ] Release workflow verified end to end with latest-release index download (see HANDOFF.md)

## Website
- [x] `scripts/build_site.py` generates the home page and one page per integration (pytest)
- [x] Per-integration styling from `site.json`
- [ ] Live site verified and About homepage set (see HANDOFF.md)
- [ ] Match the final per-integration designs when the design boards are delivered

## Integrations
- [x] `hello_package`, `bin_day`, `countdown`, `github_releases`, `seed_tray`, `sun_hours` written with config flows, strings and logic tests
- [ ] Load each integration in a real Home Assistant instance (entity and config-flow code is untested)
- [ ] Add pytest-homeassistant-custom-component tests for config flows and entities
