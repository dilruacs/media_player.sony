"""
Support for interface with a Sony Remote.

For more details about this platform, please refer to the documentation at
https://github.com/dilruacs/media_player.sony
"""
from __future__ import annotations

import logging
import time
from typing import Iterable, Any
from sonyapilib.device import SonyDevice

import voluptuous as vol

from homeassistant.components.remote import (
    ATTR_DELAY_SECS,
    ATTR_HOLD_SECS,
    ATTR_NUM_REPEATS,
    DEFAULT_DELAY_SECS,
    DEFAULT_HOLD_SECS,
    DEFAULT_NUM_REPEATS,
    RemoteEntity,
    PLATFORM_SCHEMA, RemoteEntityFeature)

from homeassistant.const import (
    CONF_HOST, CONF_NAME, STATE_OFF, STATE_ON, STATE_PLAYING, STATE_PAUSED)
import homeassistant.helpers.config_validation as cv

from homeassistant.util.json import load_json, save_json

VERSION = '0.0.1'

REQUIREMENTS = ['sonyapilib==0.4.3']

SONY_CONFIG_FILE = 'sony.conf'

CLIENTID_PREFIX = 'HomeAssistant'

DEFAULT_NAME = 'Sony Remote'

NICKNAME = 'Home Assistant'

CONF_BROADCAST_ADDRESS = 'broadcast_address'
CONF_APP_PORT = 'app_port'
CONF_DMR_PORT = 'dmr_port'
CONF_IRCC_PORT = 'ircc_port'
DEFAULT_APP_PORT = 50202
DEFAULT_DMR_PORT = 52323
DEFAULT_IRCC_PORT = 50001


# Map ip to request id for configuring
_CONFIGURING = {}

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_BROADCAST_ADDRESS): cv.string,
    vol.Optional(CONF_APP_PORT, default=DEFAULT_APP_PORT): cv.port,
    vol.Optional(CONF_DMR_PORT, default=DEFAULT_DMR_PORT): cv.port,
    vol.Optional(CONF_IRCC_PORT, default=DEFAULT_IRCC_PORT): cv.port
})


# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Sony Remote platform."""
    host = config.get(CONF_HOST)

    if host is None:
        return

    pin = None
    sony_config = load_json(hass.config.path(SONY_CONFIG_FILE))

    while sony_config:
        # Set up a configured TV
        host_ip, host_config = sony_config.popitem()
        if host_ip == host:
            device = SonyDevice.load_from_json(host_config)
            hass_device = SonyRemoteEntity(device)
            add_devices([hass_device])
            return

    setup_sonyremote(config, pin, hass, add_devices)


def setup_sonyremote(config, sony_device, hass, add_devices):
    """Set up a Sony Media Player based on host parameter."""
    host = config.get(CONF_HOST)
    broadcast = config.get(CONF_BROADCAST_ADDRESS)

    if sony_device is None:
        request_configuration(config, hass, add_devices)
    else:
        # If we came here and configuring this host, mark as done
        if host in _CONFIGURING:
            request_id = _CONFIGURING.pop(host)
            configurator = hass.components.configurator
            configurator.request_done(request_id)
            _LOGGER.info("Discovery configuration done")

        if broadcast:
            sony_device.broadcast = broadcast

        hass_device = SonyRemoteEntity(sony_device)
        config[host] = hass_device.sonydevice.save_to_json()

        # Save config, we need the mac address to support wake on LAN
        save_json(hass.config.path(SONY_CONFIG_FILE), config)

        add_devices([hass_device])


def request_configuration(config, hass, add_devices):
    """Request configuration steps from the user."""
    host = config.get(CONF_HOST)
    name = config.get(CONF_NAME)
    app_port = config.get(CONF_APP_PORT)
    dmr_port = config.get(CONF_DMR_PORT)
    ircc_port = config.get(CONF_IRCC_PORT)
    psk = None

    configurator = hass.components.configurator

    # We got an error if this method is called while we are configuring
    if host in _CONFIGURING:
        configurator.notify_errors(
            _CONFIGURING[host], "Failed to register, please try again.")
        return

    def sony_configuration_callback(data):
        """Handle the entry of user PIN."""
        from sonyapilib.device import AuthenticationResult

        pin = data.get('pin')
        sony_device = SonyDevice(host, name,
                                 psk=psk, app_port=app_port,
                                 dmr_port=dmr_port, ircc_port=ircc_port)

        authenticated = False

        # make sure we only send the authentication to the device
        # if we have a valid pin
        if pin == '0000' or pin is None or pin == '':
            register_result = sony_device.register()
            if register_result == AuthenticationResult.SUCCESS:
                authenticated = True
            elif register_result == AuthenticationResult.PIN_NEEDED:
                # return so next call has the correct pin
                return
            else:
                _LOGGER.error("An unknown error occured during registration")

        authenticated = sony_device.send_authentication(pin)
        if authenticated:
            setup_sonyremote(config, sony_device, hass, add_devices)
        else:
            request_configuration(config, hass, add_devices)

    _CONFIGURING[host] = configurator.request_config(
        name, sony_configuration_callback,
        description='Enter the Pin shown on your Sony Device. '
        'If no Pin is shown, enter 0000 '
        'to let the device show you a Pin.',
        description_image="/static/images/smart-tv.png",
        submit_caption="Confirm",
        fields=[{'id': 'pin', 'name': 'Enter the pin', 'type': ''}]
    )


class SonyRemoteEntity(RemoteEntity):
    # pylint: disable=too-many-instance-attributes
    """Representation of a Sony mediaplayer."""
    _attr_supported_features: RemoteEntityFeature = RemoteEntityFeature(0)
    sonydevice: SonyDevice

    def __init__(self, sony_device):
        """
        Initialize the Sony mediaplayer device.

        Mac address is optional but neccessary for wake on LAN
        """
        self.sonydevice = sony_device
        self._state = STATE_OFF
        self._muted = False
        self._id = None
        self._playing = False
        _LOGGER.debug(sony_device.pin)
        _LOGGER.debug(sony_device.client_id)

        try:
            self.update()
        except Exception:  # pylint: disable=broad-except
            self._state = STATE_OFF

    def update(self):
        """Update TV info."""
        self.sonydevice.init_device()
        if not self.sonydevice.get_power_status():
            self._state = STATE_OFF
            return

        self._state = STATE_ON

        # Retrieve the latest data.
        try:
            if self._state == STATE_ON:
                power_status = self.sonydevice.get_power_status()
                if power_status:
                    playback_info = self.sonydevice.get_playing_status()
                    if playback_info == "PLAYING":
                        self._state = STATE_PLAYING
                    elif playback_info == "PAUSED_PLAYBACK":
                        self._state = STATE_PAUSED
                    else:
                        self._state = STATE_ON
                else:
                    self._state = STATE_OFF

        except Exception as exception_instance:  # pylint: disable=broad-except
            _LOGGER.error(exception_instance)
            self._state = STATE_OFF

    @property
    def name(self):
        """Return the name of the device."""
        return self.sonydevice.nickname

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return self._attr_supported_features

    def turn_on(self):
        """Turn the media player on."""
        self.sonydevice.power(True)

    def turn_off(self):
        """Turn off media player."""
        self.sonydevice.power(False)

    def toggle(self, activity: str = None, **kwargs):
        """Toggle a device."""
        if self._state == STATE_ON:
            self.turn_off()
        else:
            self.turn_on()

    def send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        """Send commands to one device."""
        num_repeats = kwargs.get(ATTR_NUM_REPEATS, DEFAULT_NUM_REPEATS)
        delay_secs = kwargs.get(ATTR_DELAY_SECS, DEFAULT_DELAY_SECS)
        hold_secs = kwargs.get(ATTR_HOLD_SECS, DEFAULT_HOLD_SECS)

        _LOGGER.debug("async_send_command %s %d repeats %d delay", ''.join(list(command)), num_repeats, delay_secs)

        for _ in range(num_repeats):
            for single_command in command:
                # Not supported : hold and release modes
                # if hold_secs > 0:
                #     self.sonydevice._send_command(single_command)
                #     time.sleep(hold_secs)
                # else:
                self.sonydevice._send_command(single_command)
                time.sleep(delay_secs)