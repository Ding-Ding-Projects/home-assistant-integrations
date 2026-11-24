# Handoff

State: monorepo with six integrations (hello_package, bin_day, countdown, github_releases,
seed_tray, sun_hours), packaging with an update index, a generated GitHub Pages site, and a
release workflow that also deploys the site.

Verified: pytest (logic, packaging, site generation). Not verified: running any integration in a
live Home Assistant, since pytest-homeassistant-custom-component was not installed (entity and
config-flow code is unexercised). See the latest workflow run and release for pipeline results.

Per-integration page styling lives in `integrations/<domain>/site.json` and is placeholder
until the design boards arrive.
