# Handoff

Initial setup of the monorepo: build script, tests, demo integration `hello_package`, batch
entrypoints, and the release workflow.

Verified: `python -m pytest` (6 tests) and a local build of `hello_package-1.0.0.hapkg`.
Not verified: running the integration inside a live Home Assistant, and `build.bat` on a host
without Python. No GitHub Pages site exists yet.
