# Sun Hours

Reports minutes of daylight today and how much that changed since yesterday, from your Home Assistant location.

Sun Hours computes sunrise to sunset with astral, which Home Assistant already includes, using the latitude, longitude and time zone from your Home Assistant configuration. It needs no accounts or internet access. In polar day it reports 1440 minutes and in polar night 0.

## Setup

1. Open Settings, Devices and services, Add integration, and choose **Sun Hours**.
2. Confirm. There is nothing to configure; only one instance is allowed.

## Entities

- `sensor.sun_hours_daylight_today`: minutes of daylight today.
- `sensor.sun_hours_daylight_change`: minutes gained (positive) or lost (negative) compared with yesterday.

## Options

- None. Change your location under Settings, System, General.

## Install

Download `sun_hours-1.0.0.hapkg` from the latest release (or the button on the website), then
drag it onto the Marketplace page of home-assistant-material, or use **Install from a package
file**. Restart Home Assistant if asked, then add **Sun Hours** under Settings, Devices and services.
Installed copies update themselves from the release index unless you switch automatic updates off.
