=========================
Ironic Python Heartbeater
=========================

.. image:: https://api.shippable.com/projects/584fd251ea2e1e0f00a1c57e/badge?branch=master
   :target: https://app.shippable.com/github/pshchelo/ironic-python-heartbeater

.. image:: https://api.shippable.com/projects/584fd251ea2e1e0f00a1c57e/coverageBadge?branch=master
   :target: https://app.shippable.com/github/pshchelo/ironic-python-heartbeater

OpenStack Baremetal provisioning service (Ironic) exposes very useful
functionality of node pinging back to the service when the deploy in-memory
ramdisk is up and running and is ready to proceed with actual node
deployment - these are ``lookup`` and ``heartbeat`` core ironic API endpoints,
available since ironic API v1.22.

In upstream, the code for this is residing in the ``Ironic Python Agent``
(IPA) project and assumes that it is started and running in the ramdisk.

Nevertheless, if presence of the complete IPA (and its requirements)
is not required by a given ironic driver that still would like use
the ironic's heartbeats functionality, it is possible to implement
the required API calls in a much smaller script with less dependencies.

This project gives an example of such script written in Python.

The main downside comparing to IPA is that currently only the MAC address
of the interface the node has booted from is passed to ironic
during the lookup, so any interface that the node can potentially boot from
must be enrolled into ironic as ironic port.
