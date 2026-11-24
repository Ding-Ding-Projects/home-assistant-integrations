# Roadmap

## Packaging pipeline
- [x] `.hapkg` build script with validation, deterministic output and `--check` mode (verified by pytest)
- [x] `dist/index.json` package index
- [x] `build.bat` and `build-installer.bat` entrypoints (written; `build.bat` not run on a fresh host)
- [ ] Release workflow verified end to end (see HANDOFF.md for the latest result)
- [ ] GitHub Pages site listing packages

## Integrations
- [x] `hello_package` demo integration (packaging verified; not loaded into a live Home Assistant instance)
- [ ] Load-test `hello_package` inside a real Home Assistant instance
