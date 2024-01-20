[![Build Status](https://travis-ci.com/alexmohr/media_player.sony.svg?branch=master)](https://travis-ci.com/alexmohr/media_player.sony)
# media_player.sony

## Important!

The device needs to be in the same subnet as the Home Assistant software.
This is a limitation of the Sony Firmware, the device will not react properly to requests if the client is in a different subnet.

## Getting Started

To get started put :
* `/custom_components/sony/media_player.py` here: `<config_directory>/custom_components/sony/media_player.py`
* `/custom_components/sony/remote.py` here: `<config_directory>/custom_components/sony/remote.py`
When using home assistant supervised put the  contents of this repo into ````/usr/share/hassio/homeassistant/````

**Using custom_updater (optional, and deprecated)**

- Get and install `custom_updater` from here: https://github.com/custom-components/custom_updater
- Use the following configuration snippet:

```yaml
custom_updater:
  track:
    - components
  component_urls:
    - https://raw.githubusercontent.com/alexmohr/media_player.sony/master/tracker.json
```


## Configuration

To add a device to your installation, add the following to your `configuration.yaml` file:

```yaml
media_player:
  - platform: sony
    host: 192.168.0.10
```
Optional if you want to have additional commands, declare the remote entity too :
```yaml
remote:
  - platform: sony
    name: Sony remote
    host: 192.168.0.10
```

**Configuration variables**

Key | Description
:--- | :---
**platform (Required)** | The platform name (`sony`)
**host (Required)** | IP Address or hostname of the device
**name (Required)** | Descriptive name for the device
**broadcast (Optional)** | The broadcast ip of the subnet
**app_port (Optional)** | The app port, defaults to 50202,
**dmr_port (Optional)** | The dmr port, defaults to 52323,
**ircc_port (Optional)** | The ircc port, defaults to 50001

### Devices
Devices listed here configure the ports different. This list is not complete. If you devices does work with other ports please add it via a PR

Device | App Port | Dmr Port | Ircc
:--- | : ---
BDP-S590 | 52323 | 50202 | 52323

## Pair a device

You will need to configure your device to allow the Home Assistant for remote usage. To do that, ensure that your device is turned on. Open the configuration popup on Home Assistant and enter a random PIN (for example 0000). After that, the device will show you a PIN and Home Assistant will allow you to re-enter that PIN. Enter the PIN shown on your TV and Home Assistant will be able to control your Sony device.

## Send commands through remote control entity
Example to trigger a command from the remote entity :
```yaml
service: remote.send_command
data:
  command: Up
target:
  entity_id: remote.sony_remote

Available commands for remote entity :
```

Here is the list of available commands, depending on your device

Command|Description
--|--
Num1|1
Num2|2
Num3|3
Num4|4
Num5|5
Num6|6
Num7|7
Num8|8
Num9|9
Num0|0
Power|Power
Eject|Eject
Stop|Stop
Pause|Pause
Play|Play
Rewind|Rewind
Forward|Forward
PopUpMenu|Popup Menu
TopMenu|Top Menu
Up|Up
Down|Down
Left|Left
Right|Right
Confirm|Confirm
Options|Options
Display|Display
Home|Home
Return|Return
Karaoke|Karaoke
Netflix|Netflix
Mode3D|3D mode
Next|Next chapter
Prev|Previous chapter
Favorites|Favorites
SubTitle|SubTitle
Audio|Audio
Angle|Angle
Blue|Blue
Red|Red
Green|Green
Yellow|Yellow
Advance|Advance
Replay|Replay