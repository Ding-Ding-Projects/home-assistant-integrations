# Hello Package

A minimal example integration that creates one sensor reporting its own version.

It exists so the packaging pipeline has a real, valid integration to build, and as a template for new ones.

## Setup

1. Open Settings, Devices and services, Add integration, and choose **Hello Package**.
2. Confirm. Only one instance is allowed.

## Entities

- `sensor.hello_package_package_demo`: state is the integration version from `manifest.json`.

## Options

- None.

## Install

Download `hello_package-1.0.0.hapkg` from the latest release (or the button on the website), then
drag it onto the Marketplace page of home-assistant-material, or use **Install from a package
file**. Restart Home Assistant if asked, then add **Hello Package** under Settings, Devices and services.
Installed copies update themselves from the release index unless you switch automatic updates off.
