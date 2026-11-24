# GitHub Releases

Watches public GitHub repositories and reports each one's latest release tag and publish time, with no account or token.

GitHub Releases uses the public, unauthenticated GitHub API. It polls each repository every 6 hours and, if GitHub answers with a rate limit, doubles the wait up to 24 hours before trying again. Add one entry per repository.

## Setup

1. Open Settings, Devices and services, Add integration, and choose **GitHub Releases**.
2. Enter a repository as `owner/repo` or paste its GitHub address.

## Entities

- `sensor.<repo>_latest_release`: latest release tag. Attributes: `repository` and `url`. Unknown when the repository has no releases.
- `sensor.<repo>_published`: timestamp when that release was published.

## Options

- None. Polling is fixed at a polite 6 hours with automatic back-off.

## Install

Download `github_releases-1.0.0.hapkg` from the latest release (or the button on the website), then
drag it onto the Marketplace page of home-assistant-material, or use **Install from a package
file**. Restart Home Assistant if asked, then add **GitHub Releases** under Settings, Devices and services.
Installed copies update themselves from the release index unless you switch automatic updates off.
