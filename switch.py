"""
This component provides HA switch support for blocking / unblocking devices with a Ubiquiti Unifi Controller.

Copyright 2018 Matthew Emerson

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import logging
import voluptuous as vol

from homeassistant.components.switch import (SwitchDevice, PLATFORM_SCHEMA)
from homeassistant.const import (
    STATE_ON, STATE_OFF, STATE_UNKNOWN, CONF_NAME, CONF_FILENAME)
import homeassistant.helpers.config_validation as cv

DOMAIN = 'unifi_device_block'

"""Require the pyunifi library"""
REQUIREMENTS = ['pyunifi==2.13']

"""Start the logger"""
_LOGGER = logging.getLogger(__name__)
"""configuration for accessing the Unifi Controller"""
CONF_HOST = 'host'
CONF_PORT = 'port'
CONF_SITE_ID = 'site_id'
CONF_USERNAME = 'username'
CONF_PASSWORD = 'password'
CONF_VERIFY_SSL = True
CONF_TIMEOUT = 'timeout'
CONF_WRITE_TIMEOUT = 'write_timeout'
CONF_USER_GROUP_NAME = 'user_group_name'

DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 8443
DEFAULT_SITE_ID = 'default'
DEFAULT_VERIFY_SSL = True
DEFAULT_TIMEOUT = 1
DEFAULT_WRITE_TIMEOUT = 1

NOTIFICATION_ID = 'unifi_device_block'
NOTIFICATION_TITLE = 'Unifi Device Block'

"""Define the schema for the Switch Platform"""
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_HOST, default=DEFAULT_HOST): cv.string,
    vol.Optional(CONF_SITE_ID, default='default'): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.port,
    vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): vol.Any(
        cv.boolean, cv.isfile),
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
    vol.Optional(CONF_WRITE_TIMEOUT, default=DEFAULT_WRITE_TIMEOUT):
        cv.positive_int,
    vol.Required(CONF_USER_GROUP_NAME): cv.string,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """begin using the pyunifi import """
    from pyunifi.controller import Controller, APIError
    """get all the parameters passed by the user to access the controller"""
    host = config.get(CONF_HOST)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    site_id = config.get(CONF_SITE_ID)
    port = config.get(CONF_PORT)
    user_group_name = config.get(CONF_USER_GROUP_NAME)
    """verify ssl isn't functioning, I've bypassed it for the moment"""
    verify_ssl = False
    """config.get(CONF_VERIFY_SSL)"""
    try:
        ctrl = Controller(host, username, password, port, version='v4', site_id=site_id, ssl_verify=verify_ssl)
    except APIError as ex:
        _LOGGER.error("Failed to connect to Unifi: %s", ex)
        hass.components.persistent_notification.create(
            'Failed to connect to Unifi. '
            'Error: {}<br />'
            'You will need to restart hass after fixing.'
            ''.format(ex),
            title=NOTIFICATION_TITLE,
            notification_id=NOTIFICATION_ID)
        return False
    # the controller was loaded properly now get the user groups to find the one you want
    user_group_found = False
    user_group_id = 0
    # Loop through all of the User Groups looking for the one specified
    for user_group in ctrl.get_user_groups():
        if 'name' in user_group:
            if user_group['name'] == user_group_name:
                # The user group was found store it
                user_group_found = True
                user_group_id = user_group['_id']
    # if user group was not found return false give error message
    if not user_group_found:
        _LOGGER.error("Failed to find Unifi userGroup with name of: %s", user_group_name)
        hass.components.persistent_notification.create(
            'Failed to find Unifi User Group '
            'Name: {}<br />'
            'You will need to restart hass after fixing.'
            ''.format(user_group_name),
            title=NOTIFICATION_TITLE,
            notification_id=NOTIFICATION_ID)
        return False

    # define an array for storing the HASS devices, each Hass Device will be a Unifi User
    devices = []
    # Get all users in group requested (in Unifi users are all known devices regardless of connection status, clients
    # are connected users)

    for user in ctrl.get_users():
        if 'usergroup_id' in user:
            if user['usergroup_id'] == user_group_id:
                # we have found a user that we should add
                if 'name' in user:
                    hostname = user['name']
                else:
                    hostname = 'no name'
                if 'blocked' in user:
                    not_blocked = not bool(user['blocked'])
                else:
                    not_blocked = True
                # LOGGER.error('blocked from user ' + str(tempb) + ' from conversion: ' + str(not_blocked))
                mac_address = user['mac']
                devices.append(UnifiClientSwitch(hostname, mac_address, not_blocked, ctrl, 60, 60))
                continue
    # All the users been appended to device array
    add_devices(devices)

class UnifiClientSwitch(SwitchDevice):
    """Represents an Unifi Client as a switch."""

    def __init__(self, name, mac_address, not_blocked, controller, timeout, write_timeout, **kwargs):
        """Init of the Unifi Client."""
        self._name = name
        self._not_blocked = not_blocked
        self._mac_address = mac_address
        self._state = False
        self._available = False
        self._controller = controller

    @property
    def name(self):
        """Return host name of the client."""
        return self._name

    @property
    def is_on(self) -> bool:
        return self._not_blocked

    def turn_on(self, **kwargs) -> None:
        self._controller.unblock_client(self._mac_address)

    def turn_off(self, **kwargs) -> None:
        self._controller.block_client(self._mac_address)

    def update(self):
        client = self._controller.get_client(self._mac_address)
        if 'blocked' in client:
            # tempb = user['blocked']
            not_blocked = not bool(client['blocked'])
        else:
            not_blocked = True
        self._not_blocked = not_blocked


