![Travis-CI](https://travis-ci.org/dilruacs/media_player.sony.svg?branch=master)

# media_player.sony

## Important!

The device needs to be in the same subnet as the Home Assistant software.
This is a limitation of the Sony Firmware, the device will not react properly to requests if the client is in a different subnet.

## Getting Started

The `sonyapilib` library is required, install it in the same environment as the Home Assistant software:

`pip install sonyapilib`

To get started put `/custom_components/sony/media_player.py` here: `<config_directory>/custom_components/sony/media_player.py`

## Using custom_updater

- Get and install `custom_updater` from here: https://github.com/custom-components/custom_updater
- Use the following configuration snippet:

```yaml
custom_updater:
  track:
    - components
  component_urls:
    - https://raw.githubusercontent.com/dilruacs/media_player.sony/master/custom_components.json
```

## Configuration

To add a device to your installation, add the following to your `configuration.yaml` file:

```yaml
media_player:
  - platform: sony
    host: 192.168.0.10
```

**Configuration variables**

key | description
:--- | :---
**platform (Required)** | The platform name (`sony`)
**host (Required)** | IP Address or hostname of the device
**name (Optional)** | Descriptive name for the device
