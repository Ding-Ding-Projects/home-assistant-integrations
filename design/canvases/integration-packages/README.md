# Integration packages design canvas

Design boards for the integration packages and their website. The live canvas is a private design
file; this folder is a checked-in snapshot of its boards (`*.dc.html`) and `canvas.json`. The boards
reference `./support.js`, which is not included, so they do not render on their own. The website
generator `scripts/build_site.py` ports their CSS (into `scripts/site_css/`) and markup into static
pages.

## Pages and boards

| Page | Boards |
| --- | --- |
| Marketplace packages | `PackageDrop` (phone), `PackageDropWide` (desktop), `PackageUpdates` (phone) |
| Integrations website | `SiteHome` (desktop), `SiteHomePhone` (phone) |
| Bin day | `BinDayPage` (website), `BinDayCard` (Home Assistant card) |
| Countdown | `CountdownPage`, `CountdownCard` |
| GitHub releases | `GithubReleasesPage`, `GithubReleasesCard` |
| Seed tray | `SeedTrayPage`, `SeedTrayCard` |
| Sun hours | `SunHoursPage`, `SunHoursCard` |
| Hello package | `HelloPackagePage`, `HelloPackageCard` |

## Identities

| Integration | Palette | Fonts | Motif |
| --- | --- | --- | --- |
| Website home | warm white and ink, accent blue `#2f5bff`, light and dark | Plus Jakarta Sans, JetBrains Mono | tinted icon cards, three install steps |
| Bin day | near-black with lime `#d7f23a` | Big Shoulders Display, Public Sans | dashed road line and a two-week strip of day tiles |
| Countdown | cream with red `#c8331d` | Fraunces, DM Mono | giant flip numeral and tear-off leaves |
| GitHub releases | midnight with violet `#a78bfa` and mint | Space Grotesk, IBM Plex Mono | release rail and terminal block |
| Seed tray | parchment with green `#2f7a2c` | Bricolage Grotesque, Newsreader | dark tray of cells with seedlings |
| Sun hours | peach to night gradient with orange `#ff9a1f` | Unbounded, Figtree | sun arc with dawn-to-night bands |
| Hello package | off-white with blue `#2f5bff` | Instrument Serif, Geist Mono | self-drawing wireframe box and file tree |

Per-integration site settings (accent, fonts, card colour, hero text) live in
`integrations/<domain>/site.json`.
