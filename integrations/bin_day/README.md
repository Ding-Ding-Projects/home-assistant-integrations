# Bin Day

Tracks a weekly or every-N-weeks rubbish or recycling collection and tells you when to put the bins out.

Bin Day tracks one collection stream, such as general waste or recycling. Add the integration once per stream. Each stream repeats every N weeks from a start date, so a fortnightly recycling round and a weekly rubbish round can sit side by side.

## Setup

1. Open Settings, Devices and services, Add integration, and choose **Bin Day**.
2. Enter a name for the stream (for example `Recycling`).
3. Pick any date on which a collection happened or will happen.
4. Set how many weeks apart collections are (1 for weekly, 2 for fortnightly).

## Entities

- `sensor.<name>_next_collection`: date of the next collection (today counts).
- `sensor.<name>_days_until_collection`: whole days until it.
- `binary_sensor.<name>_put_the_bins_out_tonight`: on from the evening before collection until the collection day ends. It has a `next_collection` attribute.

## Options

- Interval in weeks.
- Evening hour (0 to 23, default 17) when the put-out sensor switches on.

## Install

Download `bin_day-1.0.0.hapkg` from the latest release (or the button on the website), then
drag it onto the Marketplace page of home-assistant-material, or use **Install from a package
file**. Restart Home Assistant if asked, then add **Bin Day** under Settings, Devices and services.
Installed copies update themselves from the release index unless you switch automatic updates off.
