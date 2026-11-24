# Countdown

Counts down to any number of named dates, repeating yearly (birthdays, anniversaries, renewals) or one-off.

Countdown tracks one named date per entry. Add the integration once for each birthday, anniversary, renewal or event.

## Setup

1. Open Settings, Devices and services, Add integration, and choose **Countdown**.
2. Enter a name (for example `Mum's birthday`).
3. Pick the date. For a yearly event use the original date, such as the birth date.
4. Leave **Repeats every year** on for birthdays and anniversaries, or turn it off for a one-off event.

## Entities

- `sensor.<name>_days_until`: whole days until the next occurrence, unknown once a one-off date has passed. Attributes: `yearly`, `original_date`, and `years` (age or anniversary number) for yearly dates.
- `sensor.<name>_next_date`: date of the next occurrence.

## Options

- Change the date.
- Switch between yearly and one-off.

## Install

Download `countdown-1.0.0.hapkg` from the latest release (or the button on the website), then
drag it onto the Marketplace page of home-assistant-material, or use **Install from a package
file**. Restart Home Assistant if asked, then add **Countdown** under Settings, Devices and services.
Installed copies update themselves from the release index unless you switch automatic updates off.
