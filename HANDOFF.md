# Handoff

State: monorepo with seven integrations (hello_package, bin_day, countdown, edge_tts,
github_releases, seed_tray, sun_hours), packaging with an update index, a generated GitHub Pages site, and a
release workflow that also deploys the site.

Verified: pytest (logic, packaging, site generation). Not verified: running any integration in a
live Home Assistant, since pytest-homeassistant-custom-component was not installed (entity and
config-flow code is unexercised). See the latest workflow run and release for pipeline results.

Per-integration page styling lives in `integrations/<domain>/site.json` and is placeholder
until the design boards arrive.

edge_tts (1.0.0): text to speech via the edge-tts package (pinned 7.3.1). Pure logic and the engine
(streaming, voice cache) are tested without Home Assistant; the config flow, options flow and TTS
entity were not loaded in a real Home Assistant. Its site page and home card follow the Edge TTS
boards in `design/canvases/integration-packages/`.
