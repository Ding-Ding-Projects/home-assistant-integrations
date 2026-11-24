# Seed Tray

Tracks a seed-starting tray from sowing through germination to transplant day.

Seed Tray follows one tray of one crop. Add an entry per tray. It is purely a calendar tracker and does not control grow lights or any hardware.

## Setup

1. Open Settings, Devices and services, Add integration, and choose **Seed Tray**.
2. Enter a name such as `Tomatoes`.
3. Pick the sow date (a future date shows the tray as planned).
4. Enter days to germinate and days from sowing until transplant (transplant must be later than germination).

## Entities

- `sensor.<name>_stage`: one of `planned`, `germinating`, `growing`, `ready_to_transplant`. Attributes: `sow_date`, `germination_date`, `transplant_date`.
- `sensor.<name>_days_to_transplant`: days left, never below zero.

## Options

- Sow date.
- Days to germinate.
- Days to transplant.

## Install

Download `seed_tray-1.0.0.hapkg` from the latest release (or the button on the website), then
drag it onto the Marketplace page of home-assistant-material, or use **Install from a package
file**. Restart Home Assistant if asked, then add **Seed Tray** under Settings, Devices and services.
Installed copies update themselves from the release index unless you switch automatic updates off.
