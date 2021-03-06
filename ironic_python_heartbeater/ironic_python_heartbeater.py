#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Very simplified lookup and continuous heartbeat client for Ironic API."""

import json
import random
import sys
import time

import netifaces
import requests


_GET_ADDR_MAX_ITERATION = 50
_LOOKUP_MAX_ITERATION = 50
_RETRY_INTERVAL = 5

# NOTE(pas-ha) supporting only Ironic API >= 1.22 !!!
HEADERS = {'Content-Type': 'application/json',
           'Accept': 'application/json',
           'X-OpenStack-Ironic-API-Version': '1.22'}


# TODO(pas-ha) use Python logging
def _log_error(message):
    sys.stderr.write(message)
    sys.stderr.write('\n')


def _process_error(message):
    _log_error(message)
    sys.exit(1)


def _parse_kernel_cmdline():
    """Parse linux kernel command line"""
    with open('/proc/cmdline', 'rt') as f:
        cmdline = f.read()
    return {k: v for k, v in [opt.split('=', 1) for opt in cmdline.split()]}


def _get_interface_ip(mac_addr):
    """"Get IP address of interface by mac."""
    interfaces = netifaces.interfaces()
    for iface in interfaces:
        addresses = netifaces.ifaddresses(iface)
        link_addresses = addresses.get(netifaces.AF_LINK, [])
        for link_addr in link_addresses:
            if link_addr.get('addr') == mac_addr:
                ip_addresses = addresses.get(netifaces.AF_INET)
                if ip_addresses:
                    # NOTE: return first address, ironic API does not
                    # support multiple
                    return ip_addresses[0].get('addr')
                else:
                    break


def lookup(api_url, macs, node_uuid=None):
    lookup_api = '{api_url}/v1/lookup'.format(api_url=api_url)

    params = {
        'addresses': ','.join(macs)
    }
    if node_uuid:
        params['node_uuid'] = node_uuid

    for attempt in range(_LOOKUP_MAX_ITERATION):
        try:
            resp = requests.get(lookup_api, params=params, headers=HEADERS)
        except Exception as e:
            error = str(e)
        else:
            if resp.status_code != requests.codes.OK:
                error = ('Wrong status code %d returned from Ironic API. '
                         'Last response: %s') % (
                             resp.status_code, resp.content)
            else:
                break

        if attempt == (_LOOKUP_MAX_ITERATION - 1):
            _process_error(error)

        time.sleep(_RETRY_INTERVAL)

    return resp.json()


def heartbeat(heartbeat_url, boot_ip, timeout):
    data = {"callback_url": "http://" + boot_ip}
    attempt = 0
    while True:
        error = None
        try:
            resp = requests.post(heartbeat_url, data=json.dumps(data),
                                 headers=HEADERS)
        except Exception as e:
            error = str(e)
        else:
            if resp.status_code != requests.codes.ACCEPTED:
                error = ('Wrong status code %d returned from Ironic API. '
                         'Last response: %s') % (
                             resp.status_code, resp.content)
            else:
                attempt = 0
                time.sleep(timeout)
        if error:
            _log_error(error)
            attempt += 1
            # exponential backoff
            time.sleep(timeout * random.choice(range(1 << attempt)))


# TODO(pas-ha) rewrite with classes and requests session

def main():
    """Script informs Ironic that bootstrap loading is done.

    There are two mandatory parameters in kernel command line.
        'BOOTIF' - MAC address of the boot interface.
                   Passed from PXE boot loader
        'ipa-api-url' - URL of Ironic API service, passed from Ironic
    """
    kernel_params = _parse_kernel_cmdline()
    api_url = kernel_params.get('ipa-api-url')
    if api_url is None:
        _process_error('Mandatory kernel parameter "ipa-api-url" is missing.')

    boot_mac = kernel_params.get('BOOTIF')
    if boot_mac is None:
        _process_error('Cannot define boot interface, "BOOTIF" kernel '
                       'parameter is missing.')

    # There is a difference in syntax in BOOTIF variable between pxe and ipxe
    # boot with Ironic.
    # For pxe boot the the leading `01-' denotes the device type (Ethernet)
    # and is not a part of the MAC address
    if boot_mac.startswith('01-'):
        boot_mac = boot_mac[3:].replace('-', ':')

    # FIXME(pas-ha) discover all MACs
    node = lookup(api_url, [boot_mac])
    uuid = node['node']['uuid']
    timeout = node['config']['heartbeat_timeout']

    heartbeat_url = '{api_url}/v1/heartbeat/{uuid}'.format(api_url=api_url,
                                                           uuid=uuid)
    for n in range(_GET_ADDR_MAX_ITERATION):
        boot_ip = _get_interface_ip(boot_mac)
        if boot_ip is not None:
            break
        time.sleep(_RETRY_INTERVAL)
    else:
        _process_error('Cannot find IP address of boot interface.')

    heartbeat(heartbeat_url, boot_ip, timeout)

if __name__ == '__main__':
    sys.exit(main())
