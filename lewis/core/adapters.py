# -*- coding: utf-8 -*-
# *********************************************************************
# lewis - a library for creating hardware device simulators
# Copyright (C) 2016-2017 European Spallation Source ERIC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# *********************************************************************

"""
This module contains :class:`Adapter`, which serves as a base class for concrete adapter
implementations in :mod:`lewis.adapters`. It also contains :class:`AdapterContainer` which can
be used to store multiple adapters and manage them together.
"""
import inspect
from time import sleep

from lewis.core.logging import has_log


@has_log
class Adapter(object):
    """
    Base class for adapters

    This class serves as a base class for concrete adapter implementations that expose a device via
    a certain communication protocol. It defines the minimal interface that an adapter must provide
    in order to fit seamlessly into other parts of the framework
    (most importantly :class:`~lewis.core.simulation.Simulation`).

    Sub-classes should re-define the ``protocol``-member to something appropriate. While it is
    explicitly supported to modify it in concrete device interface implementations, it is good
    to have a default (for example ``epics`` or ``stream``).

    An adapter should provide everything that is needed for the communication via the protocol it
    defines. This might involve constructing a server-object, configuring it and starting the
    service (this should happen in :meth:`start_server`). Due to the large differences between
    protocols it is very hard to provide general guidelines here. Please take a look at the
    implementations of existing adapters (:class:`~lewis.adapters.epics.EpicsAdapter`,
    :class:`~lewis.adapters.stream.StreamAdapter`),to get some examples.

    :param device: Device that is supposed to be exposed. Available as ``_device``.
    :param arguments: Command line arguments to the adapter, currently ignored.
    """
    protocol = None

    def __init__(self, device, arguments=None):
        super(Adapter, self).__init__()
        self._device = device

    @property
    def documentation(self):
        """
        This property can be overridden in a sub-class to provide protocol documentation to users
        at runtime. By default it returns the indentation cleaned-up docstring of the class.
        """
        return inspect.getdoc(self) or ''

    def start_server(self):
        """
        This method must be re-implemented to start the infrastructure required for the
        protocol in question. These startup operations are not supposed to be carried out on
        construction of the adapter in order to preserve control over when services are
        started during a run of a simulation.

        .. note::

            This method may be called multiple times over the lifetime of the Adapter, so it is
            important to make sure that this does not cause problems.

        .. seealso:: See :meth:`stop_server` for shutting down the adapter.
        """
        raise NotImplementedError(
            'Adapters must implement start_server to construct and setup any servers or mechanism '
            'required for network communication.')

    def stop_server(self):
        """
        This method must be re-implemented to stop and tear down anything that has been setup
        in :meth:`start_server`. This method should close all connections to clients that have
        been established since the adapter has been started.

        .. note::

            This method may be called multiple times over the lifetime of the Adapter, so it is
            important to make sure that this does not cause problems.
        """
        raise NotImplementedError(
            'Adapters must implement stop_server to tear down anything that has been setup in '
            'start_server.')

    @property
    def is_running(self):
        """
        This property indicates whether the Adapter's server is running and listening. The result
        of calls to :meth:`start_server` and :meth:`stop_server` should be reflected as expected.
        """
        raise NotImplementedError(
            'Adapters must implement the is_running property to indicate whether '
            'a server is currently running and listening for requests.')

    def handle(self, cycle_delay=0.1):
        """
        This function is called on each cycle of a simulation. It should process requests that are
        made via the protocol that exposes the device. The time spent processing should be
        approximately ``cycle_delay`` seconds, during which the adapter may block the current
        process. It is desirable to stick to the provided time, but deviations are permissible if
        necessary due to the way the protocol works.

        :param cycle_delay: Approximate time spent processing requests.
        """
        pass


def is_adapter(obj):
    """
    Returns True if obj is an interface (derived from Adapter), but not defined in
    :mod:`lewis.adapters`.

    :param obj: Object to test.
    :return: True if obj is an interface type.
    """
    return isinstance(obj, type) and issubclass(
        obj, Adapter) and not (
        obj.__module__.startswith('lewis.core.adapters') or obj.__module__.startswith(
            'lewis.adapters'))


@has_log
class AdapterContainer(object):
    """
    A container to manage the adapters of a device

    This container is designed to keep all adapters that expose a device in one place and interact
    with them in a uniform way.

    Adapters can be passed as arguments upon construction or added later on using
    :meth:`add_adapter` (and removed using :meth:`remove_adapter`). The available protocols can be
    queried using the :meth:`protocols` property.

    Each adapter can be started and stopped separately by supplying protocol names to
    :meth:`connect` and :meth:`disconnect`, both methods accept an arbitrary number of arguments,
    so that any subset of the stored protocols can be handled at any time. Supplying no protocol
    names at all will start/stop all adapters. These semantics also apply for :meth:`is_connected`
    and `documentation`.

    The :meth:`handle` implementation will call all the stored adapters' ``handle`` methods if they
    are running, otherwise ``time.sleep`` is called.

    :param args: List of adapters to add to the container
    """

    def __init__(self, *args):
        self._adapters = {}

        for adapter in args:
            self.add_adapter(adapter)

    def add_adapter(self, adapter):
        """
        Adds the supplied adapter to the container but raises a ``RuntimeError`` if there's
        already an adapter registered for the same protocol.

        :param adapter: Adapter to add to the container
        """
        if adapter.protocol in self._adapters:
            raise RuntimeError('Adapter for protocol \'{}\' is already registered.'.format(adapter))

        self._adapters[adapter.protocol] = adapter

    def remove_adapter(self, protocol):
        """
        Tries to remove the adapter for the specified protocol, raises a ``RuntimeError`` if there
        is no adapter registered for that particular protocol.

        :param protocol: Protocol to remove from container
        """
        if protocol not in self._adapters:
            raise RuntimeError(
                'Can not remove adapter for protocol \'{}\', none registered.'.format(protocol))

        del self._adapters[protocol]

    def handle(self, cycle_delay):
        """
        Calls all stored and running adapters' ``handle``-methods or sleeps for the specified
        amount in the rest of the cases.

        :param cycle_delay: Approximate time to spend processing adapters.
        """
        for adapter in self._adapters.values():
            if adapter.is_running:
                adapter.handle(cycle_delay)
            else:
                sleep(cycle_delay)

    @property
    def protocols(self):
        """List of protocols for which adapters are registered."""
        return list(self._adapters.keys())

    def connect(self, *args):
        """
        Calls :meth:`~Adapter.start_server` on each adapter that correspond to the supplied
        protocols. If no arguments are supplied, all adapters are started.

        :param args: List of protocols for which to start adapters or empty for all.
        """
        for adapter in self._get_adapters(args):
            self.log.info('Connecting device interface for protocol \'%s\'', adapter.protocol)
            adapter.start_server()

    def disconnect(self, *args):
        """
        Calls :meth:`~Adapter.stop_server` on each adapter that correspond to the supplied
        protocols. If no arguments are supplied, all adapters are stopped.

        :param args: List of protocols for which to stop adapters or empty for all.
        """
        for adapter in self._get_adapters(args):
            self.log.info('Disonnecting device interface for protocol \'%s\'', adapter.protocol)
            adapter.stop_server()

    def is_connected(self, *args):
        """
        If only one protocol is supplied, a single bool is returned with the connection status.
        Otherwise, this method returns a dictionary of adapter connection statuses for the supplied
        protocols. If no protocols are supplied, all adapter statuses are returned.

        :param args: List of protocols for which to start adapters or empty for all.
        :return: Boolean for single adapter or dict of statuses for multiple.
        """
        status_dict = {adapter.protocol: adapter.is_running for adapter in self._get_adapters(args)}

        if len(args) == 1:
            return list(status_dict.values())[0]

        return status_dict

    def documentation(self, *args):
        """
        Returns the concatenated documentation for the adapters specified by the supplied
        protocols or all of them if no arguments are provided.

        :param args: List of protocols for which to get documentation or empty for all.
        :return: Documentation for all selected adapters.
        """
        return '\n\n'.join(adapter.documentation for adapter in self._get_adapters(args))

    def _get_adapters(self, protocols):
        """
        Internal method to map protocols back to adapters. If the list of protocols contains an
        invalid entry (e.g. a protocol for which there is no adapter), a ``RuntimeError`` is raised.
        :param protocols:
        :return:
        """
        invalid_protocols = set(protocols) - set(self.protocols)

        if invalid_protocols:
            raise RuntimeError(
                'No adapter registered for protocols: {}'.format(', '.join(invalid_protocols)))

        return [self._adapters[proto] for proto in protocols or self.protocols]
